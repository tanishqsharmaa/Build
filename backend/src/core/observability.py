"""LangSmith observability — sets env vars at import time.

LangChain reads these env vars automatically when .invoke() is called on any chain.
All agent nodes (Agent 1–4 + Replanner) use ChatDeepSeek via langchain-core,
so once this module is imported once at app startup, tracing is automatic.
"""
import os
import sys

from src.core.config import settings

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
os.environ["LANGCHAIN_PROJECT"] = "skillbridge"

# Suppress LangSmith warnings in test runs (common during pytest)
if "pytest" in sys.modules:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
