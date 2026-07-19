"""Tests for cron batch error handling patterns."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestBatchErrorHandling:
    """Verify batch cron handlers continue on individual user failures."""

    @pytest.mark.asyncio
    async def test_cron_continues_on_user_failure(self):
        """One user fails — _run_one catches exception, does not propagate."""
        from src.agents.daily_checkin.morning_brief import _run_one

        mock_user = {"id": "user-1", "email": "fail@test.com"}

        with patch(
            "src.agents.daily_checkin.morning_brief.run_morning_brief",
            side_effect=Exception("DeepSeek timeout"),
        ) as mock_run:
            # _run_one catches exceptions internally, should not raise
            await _run_one({"user_id": "user-1", "profiles": {"email": "fail@test.com"}})
            mock_run.assert_called_once()

    def test_max_rewrite_logs_correctly(self):
        """Replanner at max rewrites logs 'MAX REWRITES' and returns state unchanged."""
        from src.agents.daily_checkin.replanner import replanner_node

        state = {
            "user_id": "test-user",
            "plan_revision_count": 3,
            "learning_plan": [
                {
                    "topic": "Test Topic",
                    "week": 1,
                    "daily_subtopics": [],
                    "free_resources": [],
                    "milestone_id": "test-1",
                }
            ],
            "current_milestone_index": 0,
            "quiz_scores": [50.0],
            "todays_topic": "Test Topic",
            "progress_log": [],
        }

        result = replanner_node(state)

        # Should have logged the max rewrites message
        log_entries = result.get("progress_log", [])
        assert any("MAX REWRITES" in entry for entry in log_entries)
        # Plan should be unchanged
        assert result["plan_revision_count"] == 3
        assert result["learning_plan"] == state["learning_plan"]
