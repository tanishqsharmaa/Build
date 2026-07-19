"""Unit tests for Agent 4 — Progress Report nodes and runner.

All external I/O (LLM, Supabase, Resend, Jinja2 renderer) is mocked.
"""
import pytest
from unittest.mock import MagicMock, patch

import src.agents.progress_report.report_runner  # noqa: F401
import src.agents.progress_report.nodes  # noqa: F401

from src.agents.progress_report.schemas import WeeklyReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_chain(return_value):
    """Return a MagicMock whose .invoke() returns return_value and .__or__ returns itself."""
    mock = MagicMock()
    mock.invoke.return_value = return_value
    mock.__or__ = MagicMock(return_value=mock)
    return mock


def _mock_supabase_quiz_data(scores=None, topics=None):
    """Supabase mock returning quiz_results rows with given scores/topics."""
    if scores is None:
        scores = [75.0, 80.0, 65.0]
    if topics is None:
        topics = ["FastAPI Basics", "Pydantic Models", "Dependency Injection"]

    mock_sb = MagicMock()

    # quiz_results query chain
    quiz_data = [
        {"score": s, "topic": t} for s, t in zip(scores, topics)
    ]
    quiz_response = MagicMock()
    quiz_response.data = quiz_data
    mock_sb.table.return_value.select.return_value.eq.return_value \
        .gte.return_value.not_.return_value.is_.return_value.execute.return_value = quiz_response

    return mock_sb


def _mock_supabase_plan_data(milestones=None, current_index=3):
    """Supabase mock returning learning_plans row."""
    if milestones is None:
        milestones = [
            {"topic": "FastAPI Basics", "week": 1},
            {"topic": "Pydantic Models", "week": 2},
            {"topic": "Dependency Injection", "week": 3},
            {"topic": "Databases", "week": 4},
            {"topic": "Auth", "week": 5},
        ]

    mock_sb = MagicMock()

    plan_data = [{"milestones": milestones, "current_milestone_index": current_index}]
    plan_response = MagicMock()
    plan_response.data = plan_data

    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value \
        .limit.return_value.execute.return_value = plan_response

    return mock_sb


def _mock_supabase_full(quiz_scores=None, quiz_topics=None, milestones=None, current_index=3):
    """Combined Supabase mock handling both quiz_results and learning_plans queries."""
    if quiz_scores is None:
        quiz_scores = [75.0, 80.0, 65.0]
    if quiz_topics is None:
        quiz_topics = ["FastAPI Basics", "Pydantic Models", "Dependency Injection"]
    if milestones is None:
        milestones = [
            {"topic": "FastAPI Basics", "week": 1},
            {"topic": "Pydantic Models", "week": 2},
            {"topic": "Dependency Injection", "week": 3},
            {"topic": "Databases", "week": 4},
            {"topic": "Auth", "week": 5},
        ]

    mock_sb = MagicMock()
    quiz_data = [{"score": s, "topic": t} for s, t in zip(quiz_scores, quiz_topics)]
    plan_data = [{"milestones": milestones, "current_milestone_index": current_index}]

    # Need to handle two different query chains, so we use side_effect on the first call
    quiz_response = MagicMock()
    quiz_response.data = quiz_data
    plan_response = MagicMock()
    plan_response.data = plan_data

    # The query chain will be called multiple times — mock_sb.table() returns different things
    # We'll use a side_effect function
    def _table_side_effect(table_name):
        table_mock = MagicMock()
        if table_name == "quiz_results":
            select_mock = MagicMock()
            eq_mock = MagicMock()
            gte_mock = MagicMock()
            not_mock = MagicMock()
            is_mock = MagicMock()
            is_mock.execute.return_value = quiz_response
            not_mock.is_.return_value = is_mock
            gte_mock.not_.return_value = not_mock
            eq_mock.gte.return_value = gte_mock
            select_mock.eq.return_value = eq_mock
            table_mock.select.return_value = select_mock
        elif table_name == "learning_plans":
            select_mock = MagicMock()
            eq_mock1 = MagicMock()
            eq_mock2 = MagicMock()
            limit_mock = MagicMock()
            limit_mock.execute.return_value = plan_response
            eq_mock2.limit.return_value = limit_mock
            eq_mock1.eq.return_value = eq_mock2
            select_mock.eq.return_value = eq_mock1
            table_mock.select.return_value = select_mock
        elif table_name == "weekly_reports":
            select_mock = MagicMock()
            eq_mock1 = MagicMock()
            eq_mock2 = MagicMock()
            eq_mock2.execute.return_value = MagicMock(data=[])
            eq_mock1.eq.return_value = eq_mock2
            select_mock.eq.return_value = eq_mock1
            table_mock.select.return_value = select_mock
            # Also handle insert
            table_mock.insert.return_value.execute.return_value = MagicMock(data=[])
        return table_mock

    mock_sb.table = MagicMock(side_effect=_table_side_effect)
    return mock_sb


# ---------------------------------------------------------------------------
# Tests — aggregate_scores
# ---------------------------------------------------------------------------

class TestAggregateScores:
    def test_aggregate_scores_correct(self):
        from src.agents.progress_report.nodes import aggregate_scores

        mock_sb = _mock_supabase_quiz_data(
            scores=[75.0, 80.0, 65.0],
            topics=["FastAPI", "Pydantic", "DI"],
        )
        # Need to handle learning_plans query too
        mock_sb2 = _mock_supabase_plan_data(current_index=3)

        call_count = [0]

        def table_side_effect(table_name):
            if table_name == "quiz_results":
                return mock_sb.table(table_name)
            elif table_name == "learning_plans":
                return mock_sb2.table(table_name)
            return MagicMock()

        combined = MagicMock()
        combined.table = MagicMock(side_effect=table_side_effect)

        with patch(
            "src.agents.progress_report.nodes.get_supabase", return_value=combined
        ):
            avg, completed, details = aggregate_scores("user-1", "2026-07-13")

        assert avg == pytest.approx(73.33, rel=0.01)
        assert completed == 3
        assert details["plan_pct"] == 60.0
        assert len(details["topics"]) == 3
        assert details["topics"][0] == "FastAPI Basics"

    def test_aggregate_scores_no_quizzes(self):
        from src.agents.progress_report.nodes import aggregate_scores

        mock_sb = _mock_supabase_quiz_data(scores=[], topics=[])
        mock_sb2 = _mock_supabase_plan_data(current_index=0)

        combined = MagicMock()
        def table_side_effect(table_name):
            if table_name == "quiz_results":
                return mock_sb.table(table_name)
            elif table_name == "learning_plans":
                return mock_sb2.table(table_name)
            return MagicMock()

        combined.table = MagicMock(side_effect=table_side_effect)

        with patch(
            "src.agents.progress_report.nodes.get_supabase", return_value=combined
        ):
            avg, completed, details = aggregate_scores("user-1", "2026-07-13")

        assert avg == 0.0
        assert completed == 0
        assert details["plan_pct"] == 0.0


# ---------------------------------------------------------------------------
# Tests — generate_report
# ---------------------------------------------------------------------------

class TestGenerateReport:
    def test_generate_report_returns_html(self):
        from src.agents.progress_report.nodes import generate_report

        html_content = "<!DOCTYPE html><html><body><h1>Weekly Report</h1></body></html>"
        mock_response = MagicMock()
        mock_response.content = html_content
        mock_chain = _make_mock_chain(mock_response)

        with patch("src.agents.progress_report.nodes.get_llm", return_value=mock_chain):
            result = generate_report(
                week_start="2026-07-13",
                milestones_completed=3,
                avg_quiz_score=73.3,
                milestone_details={
                    "topics": ["FastAPI Basics"],
                    "topics_quizzed": ["FastAPI Basics"],
                    "plan_pct": 60.0,
                    "total_milestones": 5,
                },
            )

        assert "<html" in result.lower() or "<!doctype" in result.lower()


# ---------------------------------------------------------------------------
# Tests — generate_linkedin_post
# ---------------------------------------------------------------------------

class TestGenerateLinkedinPost:
    def test_generate_linkedin_post_non_empty(self):
        from src.agents.progress_report.nodes import generate_linkedin_post

        post_text = "This week I completed FastAPI Basics and Pydantic models. #python #backend"
        mock_response = MagicMock()
        mock_response.content = post_text
        mock_chain = _make_mock_chain(mock_response)

        with patch("src.agents.progress_report.nodes.get_llm", return_value=mock_chain):
            result = generate_linkedin_post(
                topics=["FastAPI Basics", "Pydantic Models"],
                milestones_completed=3,
                avg_quiz_score=73.3,
            )

        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Tests — WeeklyReport schema
# ---------------------------------------------------------------------------

class TestWeeklyReportSchema:
    def test_weekly_report_schema_valid(self):
        report = WeeklyReport(
            week_start="2026-07-13",
            milestones_completed=3,
            avg_quiz_score=73.3,
            linkedin_post_text="I learned FastAPI this week. #python #backend #learning",
            report_html="<html><body>Great progress this week!</body></html>",
        )
        assert report.milestones_completed == 3
        assert report.avg_quiz_score == 73.3

    def test_milestones_completed_exceeds_7_raises(self):
        with pytest.raises(ValueError, match="cannot exceed 7"):
            WeeklyReport(
                week_start="2026-07-13",
                milestones_completed=10,
                avg_quiz_score=80.0,
                linkedin_post_text="Great week learning backend development. #python",
                report_html="<html><body>Report</body></html>",
            )


# ---------------------------------------------------------------------------
# Tests — run_weekly_report (runner)
# ---------------------------------------------------------------------------

class TestRunWeeklyReport:
    def test_idempotency_skips_duplicate(self):
        from src.agents.progress_report.report_runner import run_weekly_report

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value \
            .eq.return_value.execute.return_value = MagicMock(data=[{"id": "existing"}])

        with patch(
            "src.agents.progress_report.report_runner.get_supabase",
            return_value=mock_sb,
        ):
            result = run_weekly_report({
                "id": "user-1",
                "email": "test@test.com",
            })

        assert result is None

    def test_run_for_all_users_batches(self):
        from src.agents.progress_report.report_runner import run_for_all_users
        import asyncio

        mock_sb = MagicMock()
        user_rows = [
            {"user_id": f"user-{i}", "profiles": {"email": f"user{i}@test.com"}}
            for i in range(10)
        ]
        mock_sb.table.return_value.select.return_value.eq.return_value \
            .execute.return_value = MagicMock(data=user_rows)

        # Make get_supabase return our mock, and patch run_weekly_report to track calls
        async def run_one(_user):
            pass  # No-op

        with patch(
            "src.agents.progress_report.report_runner.get_supabase",
            return_value=mock_sb,
        ):
            with patch(
                "src.agents.progress_report.report_runner.run_weekly_report",
                side_effect=lambda u: None,
            ) as mock_run:
                asyncio.run(run_for_all_users())
                assert mock_run.call_count == 10
