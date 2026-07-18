"""Integration tests for Agent 3a — Morning Brief.

These tests make real Supabase and Resend calls.
Resend is called with to='delivered@resend.dev' (Resend test address — no real email sent).
All inserted rows are cleaned up after each test.

Run from Build/backend/ with virt activated:
    python -m pytest tests/integration/test_morning_brief_e2e.py -v
"""
import pytest

TEST_USER_ID = "00000000-0000-0000-0000-000000000004"
TEST_EMAIL = "delivered@resend.dev"

# A minimal learning_plans milestone list — mirrors Sprint 3 output shape
FIXTURE_MILESTONES = [
    {
        "week": 1,
        "topic": "FastAPI Basics",
        "daily_subtopics": [
            "Install FastAPI and uvicorn",
            "Write your first GET endpoint",
            "Add path and query parameters",
            "Validate request bodies with Pydantic",
            "Explore /docs auto-generated UI",
        ],
        "free_resources": ["https://www.youtube.com/watch?v=0sOvCWFmrtA"],
        "milestone_id": "fastapi-basics-week-1",
    }
]

FIXTURE_USER = {
    "id": TEST_USER_ID,
    "email": TEST_EMAIL,
    "milestones": FIXTURE_MILESTONES,
    "current_milestone_index": 0,
}


@pytest.fixture(autouse=True)
def manage_test_user():
    """Upsert profiles + learning_plans rows before each test; clean up after.

    quiz_results.user_id → profiles.id (FK), so both must exist.
    """
    from src.db.client import get_supabase
    sb = get_supabase()

    # Upsert profile
    sb.table("profiles").upsert({
        "id": TEST_USER_ID,
        "email": TEST_EMAIL,
        "goal": "Get a backend dev job",
    }).execute()

    # Insert one active learning_plans row
    sb.table("learning_plans").delete().eq("user_id", TEST_USER_ID).execute()
    sb.table("learning_plans").insert({
        "user_id": TEST_USER_ID,
        "milestones": FIXTURE_MILESTONES,
        "current_milestone_index": 0,
        "is_active": True,
        "plan_revision_count": 0,
    }).execute()

    yield  # test runs here

    # Always clean up — even if the test fails
    sb.table("quiz_results").delete().eq("user_id", TEST_USER_ID).execute()
    sb.table("learning_plans").delete().eq("user_id", TEST_USER_ID).execute()
    sb.table("profiles").delete().eq("id", TEST_USER_ID).execute()


def _cleanup_quiz_results(supabase) -> None:
    supabase.table("quiz_results").delete().eq("user_id", TEST_USER_ID).execute()


def test_run_morning_brief_inserts_quiz_results_row_with_sent_at():
    """Agent 3a must insert one quiz_results row with sent_at populated."""
    from src.agents.daily_checkin.morning_brief import run_morning_brief
    from src.db.client import get_supabase

    supabase = get_supabase()
    _cleanup_quiz_results(supabase)  # start clean

    result = run_morning_brief(FIXTURE_USER)

    assert result is not None, "run_morning_brief() returned None on first run"
    assert "key_concepts" in result
    assert len(result["key_concepts"]) == 5

    # Verify DB row
    rows = (
        supabase.table("quiz_results")
        .select("id, quiz_id, sent_at, questions")
        .eq("user_id", TEST_USER_ID)
        .execute()
        .data
    )
    assert len(rows) == 1, f"Expected 1 quiz_results row, got {len(rows)}"
    assert rows[0]["sent_at"] is not None, "sent_at must be populated"
    # topic is stored inside the questions JSONB
    questions_data = rows[0]["questions"]
    assert isinstance(questions_data, dict)
    assert questions_data.get("topic") == "FastAPI Basics"


def test_idempotency_double_run():
    """Calling run_morning_brief() twice in the same day must produce only 1 DB row."""
    from src.agents.daily_checkin.morning_brief import run_morning_brief
    from src.db.client import get_supabase

    supabase = get_supabase()
    _cleanup_quiz_results(supabase)  # start clean

    # First call — must succeed
    result1 = run_morning_brief(FIXTURE_USER)
    assert result1 is not None, "First run must return a MorningBrief dict"

    # Second call — must skip (idempotency)
    result2 = run_morning_brief(FIXTURE_USER)
    assert result2 is None, "Second run same day must return None"

    # Exactly 1 row in DB
    rows = (
        supabase.table("quiz_results")
        .select("id")
        .eq("user_id", TEST_USER_ID)
        .execute()
        .data
    )
    assert len(rows) == 1, f"Expected 1 row after double run, got {len(rows)}"
