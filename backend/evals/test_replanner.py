"""Evals — Replanner quality (Task 13).

Gated: RUN_EVALS=1 environment variable required.
Tests: 3 total
  - test_replanner_valid_output
  - test_replanner_length_correct
  - test_replanner_adds_prerequisites
"""
import os

import pytest

# Gate: skip unless RUN_EVALS=1
if not os.getenv("RUN_EVALS"):
    pytest.skip("Set RUN_EVALS=1 to run eval tests", allow_module_level=True)


from src.agents.daily_checkin.replanner import replanner_node
from src.agents.learning_planner.schemas import MilestoneList


def _make_milestone(week: int, topic: str) -> dict:
    return {
        "week": week,
        "topic": topic,
        "daily_subtopics": [f"Day {i}: subtopic" for i in range(1, 6)],
        "free_resources": ["https://youtube.com/example"],
        "milestone_id": topic.lower().replace(" ", "-"),
    }


@pytest.fixture()
def replan_state():
    """Realistic state for a student who failed the FastAPI quiz."""
    plan = [
        _make_milestone(1, "Python Basics"),
        _make_milestone(2, "FastAPI Basics"),
        _make_milestone(3, "Database with SQLAlchemy"),
        _make_milestone(4, "Authentication and JWT"),
        _make_milestone(5, "Deployment with Docker"),
    ]
    return {
        "user_id": "eval-test-user-id",
        "todays_topic": "FastAPI Basics",
        "learning_plan": plan,
        "current_milestone_index": 1,
        "plan_revision_count": 0,
        "quiz_scores": [40.0],
        "progress_log": [],
    }


def test_replanner_valid_output(replan_state):
    """Real LLM call → output spliced into plan with valid milestone dicts."""
    from unittest.mock import patch, MagicMock

    # Use real LLM but mock DB write to avoid touching Supabase during eval
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch(
        "src.agents.daily_checkin.replanner.get_supabase",
        return_value=mock_supabase,
    ):
        result_state = replanner_node(replan_state)

    new_plan = result_state["learning_plan"]
    assert isinstance(new_plan, list), "learning_plan must be a list"
    assert len(new_plan) > 0, "Replanned plan must not be empty"

    # Each milestone must have required keys
    for milestone in new_plan:
        assert "topic" in milestone
        assert "daily_subtopics" in milestone
        assert isinstance(milestone["daily_subtopics"], list)


def test_replanner_length_correct(replan_state):
    """After replan, only positions [idx:idx+2] are replaced — total length unchanged."""
    from unittest.mock import patch, MagicMock

    original_length = len(replan_state["learning_plan"])
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch(
        "src.agents.daily_checkin.replanner.get_supabase",
        return_value=mock_supabase,
    ):
        result_state = replanner_node(replan_state)

    new_plan = result_state["learning_plan"]
    assert len(new_plan) == original_length, (
        f"Plan length must remain {original_length}, got {len(new_plan)}"
    )


def test_replanner_adds_prerequisites(replan_state):
    """The replanned failed milestone Day 1 must reference prerequisites or review."""
    from unittest.mock import patch, MagicMock

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch(
        "src.agents.daily_checkin.replanner.get_supabase",
        return_value=mock_supabase,
    ):
        result_state = replanner_node(replan_state)

    idx = replan_state["current_milestone_index"]
    revised_milestone = result_state["learning_plan"][idx]
    day1 = revised_milestone["daily_subtopics"][0].lower()

    assert any(
        kw in day1 for kw in ["review", "prerequisite", "recap", "foundation", "basics", "intro"]
    ), (
        f"Day 1 of replanned milestone must include a review/prerequisite focus, got: '{day1}'"
    )
