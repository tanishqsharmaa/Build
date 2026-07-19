"""Tests for LangSmith observability setup."""
import os
import sys
from unittest.mock import patch

import pytest


class TestObservabilityEnvVars:
    """Verify LangSmith env vars are set when observability is imported."""

    def test_langsmith_env_vars_set(self, monkeypatch):
        """All 3 LangSmith env vars are set correctly by the observability module."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek")
        monkeypatch.setenv("GEMINI_API_KEY", "test-gemini")
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
        monkeypatch.setenv("RESEND_API_KEY", "test-resend")
        monkeypatch.setenv("LANGSMITH_API_KEY", "test-langsmith-key")

        for var in ("LANGCHAIN_TRACING_V2", "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT"):
            monkeypatch.delenv(var, raising=False)

        import importlib

        # Remove pytest from sys.modules so observability sees non-pytest context
        saved_pytest = sys.modules.pop("pytest", None)
        try:
            mod = importlib.import_module("src.core.observability")
            importlib.reload(mod)

            assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
            assert os.environ["LANGCHAIN_API_KEY"] == "test-langsmith-key"
            assert os.environ["LANGCHAIN_PROJECT"] == "skillbridge"
        finally:
            if saved_pytest:
                sys.modules["pytest"] = saved_pytest

    def test_no_error_on_reimport(self, monkeypatch):
        """Re-importing observability should not crash (idempotent env var sets)."""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek")
        monkeypatch.setenv("GEMINI_API_KEY", "test-gemini")
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
        monkeypatch.setenv("RESEND_API_KEY", "test-resend")
        monkeypatch.setenv("LANGSMITH_API_KEY", "test-langsmith-key")

        import importlib
        import src.core.observability
        importlib.reload(src.core.observability)

        assert os.environ["LANGCHAIN_TRACING_V2"] in ("true", "false")
