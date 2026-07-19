"""Tests for LLM retry with exponential backoff (tenacity)."""
from unittest.mock import MagicMock, patch

import pytest

from src.core.llm_client import invoke_llm_with_retry


class TestRetryBackoff:
    """Verify retry behavior on DeepSeek failures."""

    def test_retry_succeeds_on_third_attempt(self):
        """Chain fails twice then succeeds — returns result on 3rd attempt."""
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = [
            Exception("DeepSeek timeout"),
            Exception("DeepSeek rate limit"),
            {"skills": [], "overall_readiness_percent": 50},
        ]

        result = invoke_llm_with_retry(mock_chain, {"input": "test"})
        assert result["overall_readiness_percent"] == 50
        assert mock_chain.invoke.call_count == 3

    def test_retry_raises_after_max_attempts(self):
        """Chain always fails — raises exception after 3 attempts."""
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = Exception("DeepSeek down")

        with pytest.raises(Exception, match="DeepSeek down"):
            invoke_llm_with_retry(mock_chain, {"input": "test"})

        assert mock_chain.invoke.call_count == 3

    def test_first_attempt_succeeds_no_retry(self):
        """Chain succeeds immediately — only 1 call, no retries."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {"result": "ok"}

        result = invoke_llm_with_retry(mock_chain, {"input": "test"})
        assert result == {"result": "ok"}
        assert mock_chain.invoke.call_count == 1

    def test_custom_max_attempts(self):
        """Custom max_attempts=5 — retries 5 times before succeeding."""
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = [
            Exception("fail 1"),
            Exception("fail 2"),
            Exception("fail 3"),
            Exception("fail 4"),
            {"ok": True},
        ]

        result = invoke_llm_with_retry(mock_chain, {"input": "test"}, max_attempts=5)
        assert result == {"ok": True}
        assert mock_chain.invoke.call_count == 5

    def test_backoff_waits_between_retries(self):
        """Verify tenacity waits between retries (time.sleep is called)."""
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = [
            Exception("fail 1"),
            Exception("fail 2"),
            {"result": "ok"},
        ]

        with patch("tenacity.nap.time.sleep") as mock_sleep:
            result = invoke_llm_with_retry(mock_chain, {"input": "test"})
            assert result == {"result": "ok"}
            # Two failures → two sleep calls
            assert mock_sleep.call_count == 2
