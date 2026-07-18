"""Integration tests — Quiz E2E pipeline (Task 15).

Tests: 3 total
  - test_full_quiz_advance_path
  - test_full_quiz_replan_path
  - test_max_rewrites_enforced

These tests hit real Supabase. They create a test profile + learning plan,
simulate the morning brief row, run the quiz pipeline, then verify DB state.

Fixtures:
  - Uses the same conftest.py test_user UUID as Sprint 3 / Sprint 4.
  - Cleans up after each test (quiz_results row, learning_plans update reversal).
"""
import pytest
from datetime import datetime, timezone

from src.agents.daily_checkin.schemas import QuizOption, QuizQuestion
from src.agents.daily_checkin.quiz_evaluator import (
    score_quiz,
    advance_milestone,
    evaluate_and_route,
)
from src.agents.daily_checkin.replanner import replanner_node, _MAX_REWRITES
from src.db.client import get_supabase


# ── Shared test data ──────────────────────────────────────────────────────────

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_EMAIL = "delivered@resend.dev"

_FIVE_QUESTIONS = [
    QuizQuestion(
        question_id=f"q{i}",
        question=f"What is concept {i}?",
        options=[
            QuizOption(index=0, text="Option A"),
            QuizOption(index=1, text="Option B"),
            QuizOption(index=2, text="Option C"),
            QuizOption(index=3, text="Option D"),
        ],
        correct_index=0,  # All correct answers are index 0
    )
    for i in range(1, 6)
]

_ALL_CORRECT = [0, 0, 0, 0, 0]   # 100% → advance
_ALL_WRONG   = [1, 1, 1, 1, 1]   # 0%   → replan


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def supabase():
    return get_supabase()


@pytest.fixture(autouse=True)
def manage_test_user(supabase):
    """Upsert test profile before each test; clean up all test data after.

    Same pattern as Sprint 3 test_planner_e2e.py — required because
    learning_plans.user_id has a FK → profiles.id.
    """
    supabase.table("profiles").upsert({
        "id": TEST_USER_ID,
        "email": TEST_EMAIL,
        "name": "Test User Sprint5",
    }).execute()

    yield  # run the test

    # Teardown: delete in FK dependency order
    supabase.table("quiz_results").delete().eq("user_id", TEST_USER_ID).execute()
    supabase.table("learning_plans").delete().eq("user_id", TEST_USER_ID).execute()
    supabase.table("skill_gaps").delete().eq("user_id", TEST_USER_ID).execute()
    supabase.table("profiles").delete().eq("id", TEST_USER_ID).execute()


@pytest.fixture()
def learning_plan_fixture(supabase):
    """Ensure the test user has an active learning plan with 3 milestones.

    Yields the plan row. Cleans up (resets milestone index + revision_count) after test.
    """
    def _make_milestone(w: int) -> dict:
        return {
            "week": w,
            "topic": f"Test Topic {w}",
            "daily_subtopics": [f"Day {d}" for d in range(1, 6)],
            "free_resources": ["https://youtube.com/test"],
            "milestone_id": f"test-topic-{w}",
        }

    milestones = [_make_milestone(w) for w in range(1, 4)]

    # Upsert: deactivate any existing plan first
    supabase.table("learning_plans").update({"is_active": False}).eq(
        "user_id", TEST_USER_ID
    ).execute()

    row = (
        supabase.table("learning_plans")
        .insert({
            "user_id": TEST_USER_ID,
            "milestones": milestones,
            "current_milestone_index": 0,
            "plan_revision_count": 0,
            "is_active": True,
        })
        .execute()
    )
    plan_id = row.data[0]["id"]

    yield row.data[0]

    # Cleanup: delete the inserted plan
    supabase.table("learning_plans").delete().eq("id", plan_id).execute()


@pytest.fixture()
def quiz_row_fixture(supabase, learning_plan_fixture):
    """Insert a quiz_results row (as morning brief would) and yield its quiz_id.

    Deletes the row after the test.
    """
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    quiz_id = f"{TEST_USER_ID[:8]}_{today}_test-topic-1"

    # Delete any stale row with the same quiz_id
    supabase.table("quiz_results").delete().eq("quiz_id", quiz_id).execute()

    supabase.table("quiz_results").insert({
        "user_id": TEST_USER_ID,
        "quiz_id": quiz_id,
        "questions": {"topic": "Test Topic 1", "milestone_index": 0, "items": []},
        "sent_at": datetime.now(tz=timezone.utc).isoformat(),
    }).execute()

    yield quiz_id

    # Cleanup
    supabase.table("quiz_results").delete().eq("quiz_id", quiz_id).execute()


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_full_quiz_advance_path(supabase, learning_plan_fixture, quiz_row_fixture):
    """Submit all-correct answers → current_milestone_index incremented to 1."""
    score = score_quiz(_FIVE_QUESTIONS, _ALL_CORRECT)
    assert score == 100.0

    advance_milestone(user_id=TEST_USER_ID)

    # Verify DB
    row = (
        supabase.table("learning_plans")
        .select("current_milestone_index")
        .eq("user_id", TEST_USER_ID)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    assert row.data is not None, "Active learning plan must exist"
    assert row.data["current_milestone_index"] == 1, (
        f"Expected index=1, got {row.data['current_milestone_index']}"
    )


def test_full_quiz_replan_path(supabase, learning_plan_fixture, quiz_row_fixture):
    """Submit all-wrong answers → replanner updates milestones + revision_count == 1."""
    from unittest.mock import patch, MagicMock
    from src.agents.learning_planner.schemas import Milestone, MilestoneList

    score = score_quiz(_FIVE_QUESTIONS, _ALL_WRONG)
    assert score == 0.0

    plan = learning_plan_fixture["milestones"]
    state = {
        "user_id": TEST_USER_ID,
        "todays_topic": "Test Topic 1",
        "learning_plan": plan,
        "current_milestone_index": 0,
        "plan_revision_count": 0,
        "quiz_scores": [score],
        "progress_log": [],
    }

    updated_ms = MilestoneList(
        milestones=[
            Milestone(
                week=1,
                topic="Test Topic 1",
                daily_subtopics=[
                    "Day 1: Prerequisites review",
                    "Day 2: Core concepts",
                    "Day 3: Practice",
                    "Day 4: Advanced topics",
                    "Day 5: Mini project",
                ],
                free_resources=["https://youtube.com/revised"],
                milestone_id="test-topic-1",
            ),
            Milestone(
                week=2,
                topic="Test Topic 2",
                daily_subtopics=[f"Day {d}: content" for d in range(1, 6)],
                free_resources=["https://youtube.com/next"],
                milestone_id="test-topic-2",
            ),
        ],
        total_weeks=2,
    )

    mock_chain = MagicMock()
    mock_chain.invoke.return_value = updated_ms
    with patch(
        "src.agents.daily_checkin.replanner.get_llm",
        return_value=mock_chain,
    ), patch(
        "src.agents.daily_checkin.replanner.ChatPromptTemplate"
    ) as mock_pt, patch(
        "src.agents.daily_checkin.replanner.PydanticOutputParser"
    ) as mock_parser:
        mock_chain.__or__ = MagicMock(return_value=mock_chain)
        mock_parser.return_value.get_format_instructions.return_value = ""
        mock_pt.from_messages.return_value.__or__ = MagicMock(
            return_value=mock_chain
        )
        replanner_node(state)

    # Verify DB
    row = (
        supabase.table("learning_plans")
        .select("plan_revision_count, milestones")
        .eq("user_id", TEST_USER_ID)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    assert row.data["plan_revision_count"] == 1, (
        f"Expected plan_revision_count=1, got {row.data['plan_revision_count']}"
    )
    assert row.data["milestones"][0]["topic"] == "Test Topic 1", (
        "Revised milestone topic must still be 'Test Topic 1'"
    )


def test_max_rewrites_enforced(supabase, learning_plan_fixture, quiz_row_fixture):
    """When revision_count==3, replanner does NOT update milestones or call LLM."""
    from unittest.mock import patch

    plan = learning_plan_fixture["milestones"]
    state = {
        "user_id": TEST_USER_ID,
        "todays_topic": "Test Topic 1",
        "learning_plan": plan,
        "current_milestone_index": 0,
        "plan_revision_count": _MAX_REWRITES,  # == 3
        "quiz_scores": [20.0],
        "progress_log": [],
    }

    with patch("src.agents.daily_checkin.replanner.get_llm") as mock_llm:
        result_state = replanner_node(state)

    # LLM must not be called
    mock_llm.assert_not_called()

    # progress_log must contain cap message
    assert any("MAX REWRITES REACHED" in e for e in result_state["progress_log"]), (
        "Expected 'MAX REWRITES REACHED' in progress_log"
    )

    # DB revision_count must still be 0 (no update was written)
    row = (
        supabase.table("learning_plans")
        .select("plan_revision_count")
        .eq("user_id", TEST_USER_ID)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    assert row.data["plan_revision_count"] == 0, (
        f"DB plan_revision_count must remain 0 when cap is hit, got {row.data['plan_revision_count']}"
    )
