"""Unit tests — Quiz Evaluator (Task 11).

Tests: 6 total
  - test_score_3_of_5
  - test_score_5_of_5
  - test_score_0_of_5
  - test_route_above_70
  - test_route_below_70
  - test_advance_milestone_increments
  - test_deterministic_scoring
"""
from unittest.mock import MagicMock, patch

import pytest

from src.agents.daily_checkin.schemas import QuizOption, QuizQuestion
from src.agents.daily_checkin.quiz_evaluator import score_quiz


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_questions(correct_indices: list[int]) -> list[QuizQuestion]:
    """Build N questions where question i has correct_index = correct_indices[i]."""
    questions = []
    for i, ci in enumerate(correct_indices):
        questions.append(
            QuizQuestion(
                question_id=f"q{i + 1}",
                question=f"Question {i + 1}?",
                options=[
                    QuizOption(index=0, text="A"),
                    QuizOption(index=1, text="B"),
                    QuizOption(index=2, text="C"),
                    QuizOption(index=3, text="D"),
                ],
                correct_index=ci,
            )
        )
    return questions


# ── Score calculation tests ───────────────────────────────────────────────────


def test_score_3_of_5():
    """3 correct answers out of 5 → score == 60.0."""
    # Correct answers are all at index 0
    questions = _make_questions([0, 0, 0, 0, 0])
    # Student gets q1, q2, q3 right; q4, q5 wrong
    answers = [0, 0, 0, 1, 1]
    result = score_quiz(questions, answers)
    assert result == 60.0, f"Expected 60.0, got {result}"


def test_score_5_of_5():
    """All correct → score == 100.0."""
    questions = _make_questions([0, 1, 2, 3, 0])
    answers = [0, 1, 2, 3, 0]
    result = score_quiz(questions, answers)
    assert result == 100.0, f"Expected 100.0, got {result}"


def test_score_0_of_5():
    """All wrong → score == 0.0."""
    questions = _make_questions([0, 0, 0, 0, 0])
    answers = [1, 1, 1, 1, 1]
    result = score_quiz(questions, answers)
    assert result == 0.0, f"Expected 0.0, got {result}"


# ── Routing logic tests ───────────────────────────────────────────────────────


def test_route_above_70():
    """score=70.0 (boundary) → recommendation == 'advance'."""
    questions = _make_questions([0, 0, 0, 0, 0])
    # 5/5 = 100% — well above 70
    answers = [0, 0, 0, 0, 0]
    score = score_quiz(questions, answers)
    recommendation = "advance" if score >= 70.0 else "review"
    assert recommendation == "advance"


def test_route_below_70():
    """score=60.0 → recommendation == 'review'."""
    questions = _make_questions([0, 0, 0, 0, 0])
    # 3/5 = 60%
    answers = [0, 0, 0, 1, 1]
    score = score_quiz(questions, answers)
    recommendation = "advance" if score >= 70.0 else "review"
    assert recommendation == "review"


# ── DB interaction test ────────────────────────────────────────────────────────


def test_advance_milestone_increments():
    """advance_milestone() must increment current_milestone_index by 1 in DB."""
    mock_supabase = MagicMock()

    # Simulate a plan row with current_milestone_index = 2, 5 milestones
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "id": "plan-uuid-123",
        "current_milestone_index": 2,
        "milestones": [{} for _ in range(5)],
    }

    with patch(
        "src.agents.daily_checkin.quiz_evaluator.get_supabase",
        return_value=mock_supabase,
    ):
        from src.agents.daily_checkin.quiz_evaluator import advance_milestone

        advance_milestone(user_id="user-uuid-456")

    # Verify update was called with new_index = 3
    update_call = mock_supabase.table.return_value.update
    assert update_call.called, "update() must be called"
    call_args = update_call.call_args[0][0]
    assert call_args["current_milestone_index"] == 3, (
        f"Expected index 3, got {call_args['current_milestone_index']}"
    )


# ── Determinism test ──────────────────────────────────────────────────────────


def test_deterministic_scoring():
    """Same questions + answers scored twice → same float (no LLM involvement)."""
    questions = _make_questions([1, 2, 3, 0, 1])
    answers = [1, 2, 0, 0, 0]  # 3 correct (q1, q2, q4)

    score_a = score_quiz(questions, answers)
    score_b = score_quiz(questions, answers)

    assert score_a == score_b, "score_quiz must be deterministic (no LLM)"
    assert score_a == 60.0, f"Expected 60.0 (3/5), got {score_a}"
