"""Evals — Quiz generation quality (Task 14).

Gated: RUN_EVALS=1 environment variable required.
Tests: 3 total
  - test_exactly_5_questions
  - test_4_options_per_question
  - test_correct_index_in_range
"""
import os

import pytest

# Gate: skip unless RUN_EVALS=1
if not os.getenv("RUN_EVALS"):
    pytest.skip("Set RUN_EVALS=1 to run eval tests", allow_module_level=True)


from src.agents.daily_checkin.quiz_conductor import generate_quiz
from src.agents.daily_checkin.schemas import QuizQuestion


@pytest.fixture()
def quiz_fixture():
    """Run real generate_quiz for a known topic."""
    return generate_quiz(
        topic="FastAPI Basics",
        milestone_description=(
            "REST endpoints, path parameters, query parameters, "
            "Pydantic request/response models, async handlers"
        ),
    )


def test_exactly_5_questions(quiz_fixture):
    """generate_quiz must return exactly 5 questions."""
    assert len(quiz_fixture) == 5, (
        f"Expected 5 questions, got {len(quiz_fixture)}"
    )


def test_4_options_per_question(quiz_fixture):
    """Every question must have exactly 4 answer options."""
    for q in quiz_fixture:
        assert isinstance(q, QuizQuestion)
        assert len(q.options) == 4, (
            f"Question {q.question_id} has {len(q.options)} options, expected 4"
        )
        option_indices = sorted(o.index for o in q.options)
        assert option_indices == [0, 1, 2, 3], (
            f"Options must have indices [0,1,2,3], got {option_indices}"
        )


def test_correct_index_in_range(quiz_fixture):
    """correct_index must be 0–3 for every question."""
    for q in quiz_fixture:
        assert 0 <= q.correct_index <= 3, (
            f"correct_index {q.correct_index} out of range for {q.question_id}"
        )
        # Must reference an actual option index
        option_indices = [o.index for o in q.options]
        assert q.correct_index in option_indices, (
            f"correct_index {q.correct_index} not in options {option_indices}"
        )
