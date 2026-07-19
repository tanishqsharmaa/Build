"""Tests for cron batch error handling patterns."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestBatchErrorHandling:
    """Verify batch cron handlers continue on individual user failures."""

    @pytest.mark.asyncio
    async def test_cron_continues_on_user_failure(self):
        """One user fails — batch handler catches exception, continues."""
        from src.agents.daily_checkin.morning_brief import run_for_all_users

        # Mock get_supabase + run_morning_brief to simulate 2 users, 1 fails
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"user_id": "user-1", "profiles": {"email": "a@test.com"}, "milestones": [], "current_milestone_index": 0},
            {"user_id": "user-2", "profiles": {"email": "b@test.com"}, "milestones": [], "current_milestone_index": 0},
        ]

        call_count = 0
        def mock_run_morning_brief(user):
            nonlocal call_count
            call_count += 1
            if user["id"] == "user-1":
                raise Exception("DeepSeek timeout")
            return None

        with patch("src.agents.daily_checkin.morning_brief.get_supabase", return_value=mock_sb):
            with patch("src.agents.daily_checkin.morning_brief.run_morning_brief", side_effect=mock_run_morning_brief):
                # Should not raise — exceptions caught internally
                await run_for_all_users()
                # Both users should have been attempted
                assert call_count == 2

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

        log_entries = result.get("progress_log", [])
        assert any("MAX REWRITES" in entry for entry in log_entries)
        assert result["plan_revision_count"] == 3
        assert result["learning_plan"] == state["learning_plan"]
