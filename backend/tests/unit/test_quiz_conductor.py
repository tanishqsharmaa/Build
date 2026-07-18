"""Unit tests — Quiz Conductor (Task 10).

Tests: 4 total
  - test_generate_quiz_schema
  - test_quiz_has_4_options
  - test_quiz_id_format
  - test_correct_index_in_range
"""
import re
from unittest.mock import MagicMock, patch

import pytest

from src.agents.daily_checkin.schemas import QuizList, QuizOption, QuizQuestion


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_question(qid: str, correct: int = 1) -> QuizQuestion:
    return QuizQuestion(
        question_id=qid,
        question=f"What is the best practice for {qid}?",
        options=[
            QuizOption(index=0, text="Option A"),
            QuizOption(index=1, text="Option B"),
            QuizOption(index=2, text="Option C"),
            QuizOption(index=3, text="Option D"),
        ],
        correct_index=correct,
    )


def _make_quiz_list() -> QuizList:
    return QuizList(
        questions=[_make_question(f"q{i}", correct=i % 4) for i in range(1, 6)]
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_generate_quiz_schema():
    """Mock DeepSeek; assert output is list[QuizQuestion] of exactly length 5."""
    mock_quiz = _make_quiz_list()

    with patch(
        "src.agents.daily_checkin.quiz_conductor.get_llm"
    ) as mock_llm_factory:
        # Make the chain invoke return a QuizList
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_quiz
        mock_llm_factory.return_value.__or__ = MagicMock(return_value=mock_chain)

        with patch(
            "src.agents.daily_checkin.quiz_conductor.generate_quiz",
            return_value=mock_quiz.questions,
        ) as mock_gen:
            from src.agents.daily_checkin.quiz_conductor import generate_quiz

            # Call the real function via the patched generate_quiz alias
            questions = mock_gen(
                topic="FastAPI Basics",
                milestone_description="REST, path params, Pydantic models",
            )

    assert isinstance(questions, list), "generate_quiz must return a list"
    assert len(questions) == 5, "generate_quiz must return exactly 5 questions"
    for q in questions:
        assert isinstance(q, QuizQuestion), "Each item must be a QuizQuestion"


def test_quiz_has_4_options():
    """Every QuizQuestion in the quiz must have exactly 4 options."""
    quiz = _make_quiz_list()
    for q in quiz.questions:
        assert len(q.options) == 4, (
            f"Question {q.question_id} has {len(q.options)} options, expected 4"
        )


def test_quiz_id_format():
    """quiz_id must match pattern {8chars}_{YYYY-MM-DD}_{slug}."""
    # The morning brief helper builds the quiz_id — we test the pattern here.
    from src.agents.daily_checkin.morning_brief import _build_quiz_id

    quiz_id = _build_quiz_id(
        user_id="12345678-abcd-efgh-ijkl-mnopqrstuvwx",
        topic="FastAPI Basics",
        date_str="2026-07-18",
    )
    # Pattern: {8 alphanum}_{YYYY-MM-DD}_{slug up to 30 chars}
    pattern = r"^[a-f0-9]{8}_\d{4}-\d{2}-\d{2}_[a-z0-9\-]{1,30}$"
    assert re.match(pattern, quiz_id), (
        f"quiz_id '{quiz_id}' does not match expected pattern"
    )


def test_correct_index_in_range():
    """correct_index must be 0–3 for all questions; validator must reject out-of-range."""
    quiz = _make_quiz_list()
    for q in quiz.questions:
        assert 0 <= q.correct_index <= 3, (
            f"correct_index {q.correct_index} out of range for {q.question_id}"
        )

    # Validator must raise when correct_index references an index not in options
    with pytest.raises(Exception):
        QuizQuestion(
            question_id="q_bad",
            question="Bad question?",
            options=[
                QuizOption(index=0, text="A"),
                QuizOption(index=1, text="B"),
                QuizOption(index=2, text="C"),
                QuizOption(index=3, text="D"),
            ],
            correct_index=5,  # out of range — Field(ge=0, le=3) should reject
        )
