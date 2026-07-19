"""Integration tests for Agent 4 — Weekly Progress Report.

These tests use real Supabase. DeepSeek calls and Resend are mocked.
All inserted rows are cleaned up after each test.

Run from Build/backend/ with virt activated:
    python -m pytest tests/integration/test_progress_report_e2e.py -v
"""
import pytest
from unittest.mock import patch

TEST_USER_ID = "00000000-0000-0000-0000-000000000008"
TEST_EMAIL = "delivered@resend.dev"

FIXTURE_MILESTONES = [
    {
        "week": 1,
        "topic": "FastAPI Basics",
        "daily_subtopics": ["Install FastAPI", "First endpoint", "Path params", "Pydantic", "OpenAPI docs"],
        "free_resources": ["https://www.youtube.com/watch?v=0sOvCWFmrtA"],
        "milestone_id": "fastapi-basics-week-1",
    },
    {
        "week": 2,
        "topic": "Pydantic Models",
        "daily_subtopics": ["Model fields", "Validators", "Nested models", "Config", "Serialization"],
        "free_resources": ["https://www.youtube.com/watch?v=Vj-iU-8_xL8"],
        "milestone_id": "pydantic-models-week-2",
    },
    {
        "week": 3,
        "topic": "Dependency Injection",
        "daily_subtopics": ["Depends()", "Sub-dependencies", "Override", "Yield deps", "Global deps"],
        "free_resources": ["https://www.youtube.com/watch?v=0sOvCWFmrtA"],
        "milestone_id": "dependency-injection-week-3",
    },
]


@pytest.fixture(autouse=True)
def manage_test_user():
    """Upsert profiles + learning_plans before each test; clean up after."""
    from src.db.client import get_supabase
    sb = get_supabase()

    sb.table("profiles").upsert({
        "id": TEST_USER_ID,
        "email": TEST_EMAIL,
        "goal": "Get a backend dev job",
    }).execute()

    sb.table("learning_plans").delete().eq("user_id", TEST_USER_ID).execute()
    sb.table("learning_plans").insert({
        "user_id": TEST_USER_ID,
        "milestones": FIXTURE_MILESTONES,
        "current_milestone_index": 2,
        "is_active": True,
        "plan_revision_count": 0,
    }).execute()

    yield

    sb.table("weekly_reports").delete().eq("user_id", TEST_USER_ID).execute()
    sb.table("learning_plans").delete().eq("user_id", TEST_USER_ID).execute()
    sb.table("quiz_results").delete().eq("user_id", TEST_USER_ID).execute()
    sb.table("profiles").delete().eq("id", TEST_USER_ID).execute()


def _cleanup_weekly_reports(supabase):
    supabase.table("weekly_reports").delete().eq("user_id", TEST_USER_ID).execute()


def test_report_stored_in_db():
    """Agent 4 must insert a row into weekly_reports with correct user_id + week_start."""
    from unittest.mock import patch, MagicMock
    from src.agents.progress_report.report_runner import run_weekly_report
    from src.db.client import get_supabase
    supabase = get_supabase()
    _cleanup_weekly_reports(supabase)

    # Mock DeepSeek calls
    mock_html_response = MagicMock()
    mock_html_response.content = "<html><body><h1>Weekly Report</h1><p>Great week!</p></body></html>"

    mock_post_response = MagicMock()
    mock_post_response.content = "I learned FastAPI this week. Making progress every day. #python #backend"

    mock_chain_html = MagicMock()
    mock_chain_html.invoke.return_value = mock_html_response
    mock_chain_html.__or__ = MagicMock(return_value=mock_chain_html)

    mock_chain_post = MagicMock()
    mock_chain_post.invoke.return_value = mock_post_response
    mock_chain_post.__or__ = MagicMock(return_value=mock_chain_post)

    def get_llm_side_effect(temperature=None):
        if temperature == 0.7:
            return mock_chain_html
        return mock_chain_post

    user = {"id": TEST_USER_ID, "email": TEST_EMAIL}

    with patch("src.agents.progress_report.report_runner.send_email"):
        with patch(
            "src.agents.progress_report.nodes.get_llm",
            side_effect=get_llm_side_effect,
        ):
            result = run_weekly_report(user)

    assert result is not None, "run_weekly_report returned None"
    assert "week_start" in result
    assert "report_html" in result
    assert "linkedin_post_text" in result

    # Verify DB row
    rows = (
        supabase.table("weekly_reports")
        .select("*")
        .eq("user_id", TEST_USER_ID)
        .execute()
        .data
    )
    assert len(rows) == 1, f"Expected 1 weekly_reports row, got {len(rows)}"
    assert rows[0]["user_id"] == TEST_USER_ID
    assert rows[0]["milestones_completed"] == 2  # current_milestone_index = 2
    assert rows[0]["linkedin_post_text"] is not None
    assert rows[0]["report_html"] is not None


def test_unique_week_constraint():
    """Running twice in the same week must not insert a duplicate row (idempotency)."""
    from unittest.mock import patch, MagicMock
    from src.agents.progress_report.report_runner import run_weekly_report
    from src.db.client import get_supabase

    supabase = get_supabase()
    _cleanup_weekly_reports(supabase)

    user = {"id": TEST_USER_ID, "email": TEST_EMAIL}

    mock_html_response = MagicMock()
    mock_html_response.content = "<html><body><h1>Report</h1></body></html>"
    mock_post_response = MagicMock()
    mock_post_response.content = "I learned FastAPI. #python"
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = mock_html_response
    mock_chain.__or__ = MagicMock(return_value=mock_chain)

    def get_llm_side(temperature=None):
        mock_chain.invoke.return_value = (
            mock_html_response if temperature == 0.7 else mock_post_response
        )
        return mock_chain

    with patch("src.agents.progress_report.report_runner.send_email"):
        with patch(
            "src.agents.progress_report.nodes.get_llm",
            side_effect=get_llm_side,
        ):
            result1 = run_weekly_report(user)
            assert result1 is not None, "First run must succeed"

            result2 = run_weekly_report(user)
            assert result2 is None, "Second run same week must return None (idempotent)"

    # Exactly 1 row in DB
    rows = (
        supabase.table("weekly_reports")
        .select("id")
        .eq("user_id", TEST_USER_ID)
        .execute()
        .data
    )
    assert len(rows) == 1, f"Expected 1 row after double run, got {len(rows)}"


def test_report_endpoint_returns_data():
    """GET /report/{user_id} must return HTTP 200 with reports array."""
    from src.db.client import get_supabase
    from datetime import date, datetime, timezone
    from fastapi.testclient import TestClient
    from src.api.main import app

    supabase = get_supabase()
    _cleanup_weekly_reports(supabase)

    # Seed a test report row
    supabase.table("weekly_reports").insert({
        "user_id": TEST_USER_ID,
        "week_start": "2026-07-13",
        "milestones_completed": 2,
        "avg_quiz_score": 75.0,
        "linkedin_post_text": "Test post for API verification.",
        "report_html": "<html><body>API test report</body></html>",
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }).execute()

    client = TestClient(app)
    response = client.get(f"/report/{TEST_USER_ID}")

    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert len(data["reports"]) >= 1
    assert data["reports"][0]["week_start"] == "2026-07-13"
26-07-13"
