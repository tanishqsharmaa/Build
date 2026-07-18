"""Unit tests — Replanner Logic (Task 12).

Tests: 5 total
  - test_surgical_splice
  - test_replanner_hard_cap
  - test_revision_count_increments
  - test_replanner_output_schema
  - test_replanner_preserves_future_milestones
"""
from unittest.mock import MagicMock, patch

from src.agents.learning_planner.schemas import Milestone, MilestoneList
from src.agents.daily_checkin.replanner import replanner_node, _MAX_REWRITES


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_milestone(week: int, topic: str) -> dict:
    return {
        "week": week,
        "topic": topic,
        "daily_subtopics": [f"Day {i}" for i in range(1, 6)],
        "free_resources": ["https://youtube.com/example"],
        "milestone_id": topic.lower().replace(" ", "-"),
    }


def _base_state(revision_count: int = 0, idx: int = 1) -> dict:
    """Build a minimal SkillBridgeState with 5 milestones."""
    plan = [_make_milestone(w, f"Topic {w}") for w in range(1, 6)]
    return {
        "user_id": "test-user-id",
        "todays_topic": f"Topic {idx + 1}",
        "learning_plan": plan,
        "current_milestone_index": idx,
        "plan_revision_count": revision_count,
        "quiz_scores": [55.0],
        "progress_log": [],
    }


def _make_updated_milestones(idx: int) -> MilestoneList:
    return MilestoneList(
        milestones=[
            Milestone(
                week=idx + 1,
                topic=f"Topic {idx + 1} (revised)",
                daily_subtopics=[f"Revised day {d}" for d in range(1, 6)],
                free_resources=["https://youtube.com/revised"],
                milestone_id=f"topic-{idx + 1}",
            ),
            Milestone(
                week=idx + 2,
                topic=f"Topic {idx + 2} (revised)",
                daily_subtopics=[f"Revised day {d}" for d in range(1, 6)],
                free_resources=["https://youtube.com/revised-next"],
                milestone_id=f"topic-{idx + 2}",
            ),
        ],
        total_weeks=2,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


def _make_mock_chain(updated_value) -> MagicMock:
    """Build a mock that behaves as `prompt | llm | parser`.

    When replanner_node does `chain = prompt | llm | parser; chain.invoke(...)`,
    the chain is built by a series of `|` (__or__/__ror__) calls.
    This helper returns a mock whose __or__ always returns itself, so
    chain.invoke() reliably returns `updated_value`.
    """
    mock = MagicMock()
    mock.invoke.return_value = updated_value
    mock.__or__ = MagicMock(return_value=mock)
    return mock


def test_surgical_splice():
    """Prefix before idx and suffix after idx+2 must be unchanged after replan."""
    state = _base_state(revision_count=0, idx=1)
    original_plan = list(state["learning_plan"])
    updated = _make_updated_milestones(idx=1)

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    mock_chain = _make_mock_chain(updated)

    with patch(
        "src.agents.daily_checkin.replanner.get_supabase",
        return_value=mock_supabase,
    ), patch(
        "src.agents.daily_checkin.replanner.get_llm",
        return_value=mock_chain,
    ), patch(
        "src.agents.daily_checkin.replanner.ChatPromptTemplate"
    ) as mock_prompt, patch(
        "src.agents.daily_checkin.replanner.PydanticOutputParser"
    ) as mock_parser:
        mock_parser.return_value.get_format_instructions.return_value = ""
        mock_prompt.from_messages.return_value.__or__ = MagicMock(
            return_value=mock_chain
        )
        result_state = replanner_node(state)

    new_plan = result_state["learning_plan"]

    # Prefix (idx=1 → prefix is plan[0]) must be unchanged
    assert new_plan[0]["topic"] == original_plan[0]["topic"], "Prefix must be unchanged"

    # Suffix (plan[3], plan[4]) must be unchanged
    assert new_plan[-1]["topic"] == original_plan[-1]["topic"], "Suffix must be unchanged"
    assert new_plan[-2]["topic"] == original_plan[-2]["topic"], "Suffix -2 must be unchanged"


def test_replanner_hard_cap():
    """When revision_count >= 3, replanner must NOT call LLM and must log MAX REWRITES."""
    state = _base_state(revision_count=_MAX_REWRITES)  # == 3

    with patch("src.agents.daily_checkin.replanner.get_llm") as mock_llm:
        result_state = replanner_node(state)

    # LLM must not be called
    mock_llm.assert_not_called()

    # Log must contain the cap message
    log = result_state["progress_log"]
    assert any("MAX REWRITES REACHED" in entry for entry in log), (
        f"Expected 'MAX REWRITES REACHED' in log, got: {log}"
    )

    # Plan must be unchanged
    assert result_state["learning_plan"] == state["learning_plan"], (
        "Plan must be unchanged when hard cap is hit"
    )


def test_revision_count_increments():
    """After one successful replan, plan_revision_count must be 1."""
    state = _base_state(revision_count=0, idx=1)
    updated = _make_updated_milestones(idx=1)

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    mock_chain = _make_mock_chain(updated)

    with patch(
        "src.agents.daily_checkin.replanner.get_supabase",
        return_value=mock_supabase,
    ), patch(
        "src.agents.daily_checkin.replanner.get_llm",
        return_value=mock_chain,
    ), patch(
        "src.agents.daily_checkin.replanner.ChatPromptTemplate"
    ) as mock_prompt, patch(
        "src.agents.daily_checkin.replanner.PydanticOutputParser"
    ) as mock_parser:
        mock_parser.return_value.get_format_instructions.return_value = ""
        mock_prompt.from_messages.return_value.__or__ = MagicMock(
            return_value=mock_chain
        )
        result_state = replanner_node(state)

    assert result_state["plan_revision_count"] == 1, (
        f"Expected revision_count=1, got {result_state['plan_revision_count']}"
    )


def test_replanner_output_schema():
    """Mock LLM must produce a valid MilestoneList; replanner splices valid dicts."""
    state = _base_state(revision_count=0, idx=0)  # idx=0 → prefix is empty
    updated = _make_updated_milestones(idx=0)

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    mock_chain = _make_mock_chain(updated)

    with patch(
        "src.agents.daily_checkin.replanner.get_supabase",
        return_value=mock_supabase,
    ), patch(
        "src.agents.daily_checkin.replanner.get_llm",
        return_value=mock_chain,
    ), patch(
        "src.agents.daily_checkin.replanner.ChatPromptTemplate"
    ) as mock_prompt, patch(
        "src.agents.daily_checkin.replanner.PydanticOutputParser"
    ) as mock_parser:
        mock_parser.return_value.get_format_instructions.return_value = ""
        mock_prompt.from_messages.return_value.__or__ = MagicMock(
            return_value=mock_chain
        )
        result_state = replanner_node(state)

    new_plan = result_state["learning_plan"]

    # idx=0 → prefix is empty; new_plan[0] is the first revised milestone
    assert "topic" in new_plan[0], "Replanned milestone must have 'topic'"
    assert "daily_subtopics" in new_plan[0], "Replanned milestone must have 'daily_subtopics'"
    assert len(new_plan[0]["daily_subtopics"]) == 5, "Must have exactly 5 subtopics"



def test_replanner_preserves_future_milestones():
    """Milestones after idx+2 must be identical to the originals.

    Uses the same deep-patch approach as other tests but verifies the plan
    length is correct by using a simpler inner mock for the chain.
    """
    state = _base_state(revision_count=0, idx=1)  # plan has 5 milestones; idx=1
    original_plan = list(state["learning_plan"])
    updated = _make_updated_milestones(idx=1)  # returns MilestoneList with 2 milestones

    mock_supabase = MagicMock()
    mock_supabase.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()

    # Patch the chain at the point where it's assembled (prompt | llm | parser)
    # by replacing the __or__ return value with a mock that returns `updated`
    # when .invoke() is called at any depth.
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = updated
    # Any __or__ operation in the chain returns the same mock_chain
    mock_chain.__or__ = MagicMock(return_value=mock_chain)

    with patch(
        "src.agents.daily_checkin.replanner.get_supabase",
        return_value=mock_supabase,
    ), patch(
        "src.agents.daily_checkin.replanner.get_llm",
        return_value=mock_chain,
    ), patch(
        "src.agents.daily_checkin.replanner.ChatPromptTemplate"
    ) as mock_prompt, patch(
        "src.agents.daily_checkin.replanner.PydanticOutputParser"
    ) as mock_parser:
        mock_parser.return_value.get_format_instructions.return_value = ""
        # prompt | llm returns mock_chain; mock_chain | parser returns mock_chain
        mock_prompt.from_messages.return_value.__or__ = MagicMock(
            return_value=mock_chain
        )
        result_state = replanner_node(state)

    new_plan = result_state["learning_plan"]

    # The splice: plan[:1] + updated[:2] + plan[3:]
    # → 1 prefix + 2 updated + 2 suffix = 5 total
    assert len(new_plan) == len(original_plan), (
        f"Plan length must remain {len(original_plan)}, got {len(new_plan)}"
    )

    # Prefix: plan[0] unchanged
    assert new_plan[0]["topic"] == original_plan[0]["topic"], (
        "Prefix milestone [0] must be unchanged"
    )

    # Suffix: plan[3] and plan[4] unchanged
    assert new_plan[3]["topic"] == original_plan[3]["topic"], (
        "Future milestone [3] must be unchanged"
    )
    assert new_plan[4]["topic"] == original_plan[4]["topic"], (
        "Future milestone [4] must be unchanged"
    )
