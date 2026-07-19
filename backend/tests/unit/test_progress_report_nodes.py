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

def _make_llm_response(text: str) -> MagicMock:
    """Return a MagicMock whose .content is text (simulates an AIMessage)."""
    resp = MagicMock()
    resp.content = text
    return resp


def _mock_chain_with_result(text: str) -> MagicMock:
    """Return a MagicMock that acts as a LangChain chain — .invoke() returns the response.

    Must handle `prompt | mock_chain` (calls prompt.__or__) by mocking
    ChatPromptTemplate separately. Use alongside patch("...ChatPromptTemplate.from_messages").
    """
    resp = _make_llm_response(text)
    chain = MagicMock()
    chain.invoke.return_value = resp
    return chain


def _setup_llm_patch(text: str):
    """Return a patch-stack that mocks both get_llm and ChatPromptTemplate.

    Usage:
        patches = _setup_llm_patch("response text")
        with patches[0], patches[1]:
            result = generate_report(...)
    """
    chain = _mock_chain_with_result(text)

    # Mock ChatPromptTemplate.from_messages so prompt | llm works:
    #   prompt_mock.__or__ returns our chain
    prompt_mock = MagicMock()
    prompt_mock.__or__ = MagicMock(return_value=chain)

    return (
        patch("src.agents.progress_report.nodes.ChatPromptTemplate.from_messages", return_value=prompt_mock),
        patch("src.agents.progress_report.nodes.get_llm", return_value=chain),
    )


def _mock_supabase_dispatch(quiz_scores=None, quiz_topics=None, milestones=None, current_index=3):
    """Return a MagicMock that handles table() dispatch for quiz_results + learning_plans.

    Uses side_effect on .table() to return different mocks depending on table name.
    """
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

    quiz_data = [{"score": s, "topic": t} for s, t in zip(quiz_scores, quiz_topics)]
    plan_data = [{"milestones": milestones, "current_milestone_index": current_index}]

    quiz_response = MagicMock()
    quiz_response.data = quiz_data
    plan_response = MagicMock()
    plan_response.data = plan_data

    def _build_full_chain(table_mock, steps):
        """Build a .return_value chain: table_mock.attr1 = attr2, attr2.attr3 = attr4, etc.

        steps is a list of (parent_mock, attr_name, child_mock) tuples.
        The last child gets .execute.return_value set to the response.
        """
        for i, (parent, attr, child) in enumerate(steps):
            setattr(parent, attr, child)
        return child

    def _table_side_effect(table_name):
        tm = MagicMock()

        if table_name == "quiz_results":
            sel = MagicMock()
            e1 = MagicMock()
            e2 = MagicMock()
            e3 = MagicMock()
            n1 = MagicMock()
            n2 = MagicMock()
            n2.execute.return_value = quiz_response
            n1.is_.return_value = n2
            e3.not_.return_value = n1
            e2.gte.return_value = e3
            e1.eq.return_value = e2
            sel.eq.return_value = e1
            tm.select.return_value = sel

        elif table_name == "learning_plans":
            sel = MagicMock()
            e1 = MagicMock()
            e2 = MagicMock()
            e3 = MagicMock()
            e3.execute.return_value = plan_response
            e2.limit.return_value = e3
            e1.eq.return_value = e2
            sel.eq.return_value = e1
            tm.select.return_value = sel

        elif table_name == "weekly_reports":
            sel = MagicMock()
            e1 = MagicMock()
            e2 = MagicMock()
            e2.execute.return_value = MagicMock(data=[])
            e1.eq.return_value = e2
            sel.eq.return_value = e1
            tm.select.return_value = sel
            tm.insert.return_value.execute.return_value = MagicMock(data=[])

        return tm

    mock_sb = MagicMock()
    mock_sb.table = MagicMock(side_effect=_table_side_effect)
    return mock_sb


# ---------------------------------------------------------------------------
# Tests — aggregate_scores
# ---------------------------------------------------------------------------

class TestAggregateScores:
    def test_aggregate_scores_correct(self):
        from src.agents.progress_report.nodes import aggregate_scores

        mock_sb = _mock_supabase_dispatch(
            quiz_scores=[75.0, 80.0, 65.0],
            quiz_topics=["FastAPI", "Pydantic", "DI"],
            current_index=3,
        )

        with patch(
            "src.agents.progress_report.nodes.get_supabase", return_value=mock_sb
        ):
            avg, completed, details = aggregate_scores("user-1", "2026-07-13")

        assert avg == pytest.approx(73.33, rel=0.01)
        assert completed == 3
        assert details["plan_pct"] == 60.0
        assert len(details["topics"]) == 3
        assert details["topics"][0] == "FastAPI Basics"

    def test_aggregate_scores_no_quizzes(self):
        from src.agents.progress_report.nodes import aggregate_scores

        mock_sb = _mock_supabase_dispatch(
            quiz_scores=[], quiz_topics=[], current_index=0
        )

        with patch(
            "src.agents.progress_report.nodes.get_supabase", return_value=mock_sb
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
        p1, p2 = _setup_llm_patch(html_content)

        with p1, p2:
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
        p1, p2 = _setup_llm_patch(post_text)

        with p1, p2:
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
            report_html="<html><body><h1>Great progress!</h1><p>You completed 3 milestones this week with an average score of 73%.</p></body></html>",
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
                report_html="<html><body><h1>Weekly Report</h1><p>Good progress this week.</p></body></html>",
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
