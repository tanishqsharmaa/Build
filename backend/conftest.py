"""pytest configuration for SkillBridge backend tests.

Adds build/backend/ to sys.path so `from src.xxx import yyy` works without
installing the package.
"""
import sys
from pathlib import Path

import pytest

# Ensure src/ is importable from any pytest invocation location
sys.path.insert(0, str(Path(__file__).parent))


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def skill_gap_fixture() -> dict:
    """Minimal valid SkillGapReport dict — hardcoded, no LLM call.

    Used by /plan integration tests and replanner unit tests so they don't
    depend on a live /analyze round-trip.
    """
    return {
        "skills": [
            {
                "name": "Python",
                "required_level": 8,
                "current_level": 3,
                "gap_score": 5,
                "priority": 1,
            },
            {
                "name": "FastAPI",
                "required_level": 7,
                "current_level": 2,
                "gap_score": 5,
                "priority": 2,
            },
        ],
        "overall_readiness_percent": 35,
        "recommended_timeline_weeks": 8,
    }
