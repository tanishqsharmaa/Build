"""Tests for LangSmith observability setup."""
import os
from unittest.mock import patch

import pytest


class TestObservabilityEnvVars:
    """Verify LangSmith env vars are set when observability is imported."""

    def test_langsmith_env_vars_set(self, monkeypatch):
        """All 3 LangSmith env vars are set correctly by the observability module."""
        # Set config values so the module can read them
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek")
        monkeypatch.setenv("GEMINI_API_KEY", "test-gemini")
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
        monkeypatch.setenv("RESEND_API_KEY", "test-resend")
        monkeypatch.setenv("LANGSMITH_API_KEY", "test-langsmith-key")

        # Clear any pre-existing env vars
        for var in ("LANGCHAIN_TRACING_V2", "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT"):
            monkeypatch.delenv(var, raising=False)

        # import triggers the module-level code
        import importlib
        mod = importlib.import_module("src.core.observability")

        assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
        assert os.environ["LANGCHAIN_API_KEY"] == "test-langsmith-key"
        assert os.environ["LANGCHAIN_PROJECT"] == "skillbridge"

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
        # Second import should be a no-op (module already loaded)
        importlib.reload(src.core.observability)

        assert os.environ["LANGCHAIN_TRACING_V2"] in ("true", "false")
