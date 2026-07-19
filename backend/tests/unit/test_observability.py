"""Tests for LangSmith observability setup."""
import os
import sys

import pytest


class TestObservabilityEnvVars:
    """Verify LangSmith env vars are set when observability is imported."""

    def test_langsmith_env_vars_set(self, monkeypatch):
        """All 3 LangSmith env vars are set correctly by the observability module."""
        import importlib

        # Patch the settings singleton directly — monkeypatching env vars
        # won't work because pydantic-settings already loaded from .env at import time.
        monkeypatch.setattr(
            "src.core.config.settings.langsmith_api_key", "test-langsmith-key"
        )

        for var in ("LANGCHAIN_TRACING_V2", "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT"):
            monkeypatch.delenv(var, raising=False)

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

    def test_no_error_on_reimport(self):
        """Re-importing observability should not crash (idempotent env var sets)."""
        import importlib
        import src.core.observability
        importlib.reload(src.core.observability)

        assert os.environ["LANGCHAIN_TRACING_V2"] in ("true", "false")
