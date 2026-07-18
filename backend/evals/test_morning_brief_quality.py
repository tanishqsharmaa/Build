"""Eval tests for Agent 3a — Morning Brief quality.

These tests make real DeepSeek calls. Gate with RUN_EVALS=1:
    RUN_EVALS=1 python -m pytest evals/test_morning_brief_quality.py -v
"""
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_EVALS"),
    reason="Set RUN_EVALS=1 to run agent quality evals",
)


def test_output_valid_morning_brief_schema():
    """Real DeepSeek call: output must parse as a valid MorningBrief."""
    from src.agents.daily_checkin.morning_brief import generate_brief
    result = generate_brief(
        topic="Python Decorators",
        milestone_description="functions, closures, @wraps, functools",
    )
    # Validated by Pydantic — if it reaches here the schema is valid
    assert result.topic != ""
    assert len(result.key_concepts) == 5
    assert len(result.misconceptions) == 2
    assert len(result.think_about) == 3


def test_concept_length_under_20_words():
    """Real DeepSeek call: all key_concepts must be <= 20 words."""
    from src.agents.daily_checkin.morning_brief import generate_brief
    result = generate_brief(
        topic="Docker Containers",
        milestone_description="images, containers, Dockerfile, volumes, networking",
    )
    for concept in result.key_concepts:
        word_count = len(concept.split())
        assert word_count <= 20, f"Concept has {word_count} words: '{concept}'"


def test_mnemonic_non_empty_and_no_markdown():
    """Real DeepSeek call: mnemonic must be non-empty and contain no markdown."""
    from src.agents.daily_checkin.morning_brief import generate_brief
    result = generate_brief(
        topic="SQL Joins",
        milestone_description="INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN, ON clause",
    )
    assert result.mnemonic.strip() != "", "mnemonic must not be empty"
    assert "```" not in result.mnemonic, "mnemonic must not contain code blocks"
    assert result.mnemonic.count("#") == 0, "mnemonic must not contain markdown headers"
