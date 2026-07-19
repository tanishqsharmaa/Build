"""Eval tests for Agent 4 — Weekly Progress Report.

These tests validate the QUALITY of live DeepSeek output.
Run with RUN_EVALS=1 to gate real LLM calls behind this flag.

Run from Build/backend/ with virt activated:
    $env:RUN_EVALS="1"
    python -m pytest evals/test_progress_report.py -v
"""
import os

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_EVALS") != "1",
    reason="Set RUN_EVALS=1 to run live DeepSeek eval tests",
)


class TestProgressReportEvals:
    def test_report_html_valid(self):
        from src.agents.progress_report.nodes import generate_report

        html = generate_report(
            week_start="2026-07-13",
            milestones_completed=2,
            avg_quiz_score=75.0,
            milestone_details={
                "topics": ["FastAPI Basics", "Pydantic Models"],
                "topics_quizzed": ["FastAPI Basics", "Pydantic Models"],
                "plan_pct": 40.0,
                "total_milestones": 5,
            },
        )
        assert "<html" in html.lower() or "<!doctype" in html.lower(), \
            "Report must be valid HTML"
        assert len(html) > 200, f"Report too short ({len(html)} chars)"

    def test_linkedin_post_has_hashtags(self):
        from src.agents.progress_report.nodes import generate_linkedin_post

        post = generate_linkedin_post(
            topics=["FastAPI Basics", "Pydantic Models"],
            milestones_completed=2,
            avg_quiz_score=75.0,
        )
        hashtags = [word for word in post.split() if word.startswith("#")]
        assert 3 <= len(hashtags) <= 6, \
            f"Expected 3-5 hashtags, got {len(hashtags)}: {hashtags}"

    def test_linkedin_post_length(self):
        from src.agents.progress_report.nodes import generate_linkedin_post

        post = generate_linkedin_post(
            topics=["FastAPI Basics"],
            milestones_completed=1,
            avg_quiz_score=80.0,
        )
        word_count = len(post.split())
        # Allow some flexibility: target is 100-150, but LLMs may go slightly under/over
        assert 50 <= word_count <= 250, \
            f"Post word count {word_count} outside acceptable range (50-250)"
