"""Integration tests for all SkillBridge FastAPI endpoints.

Uses FastAPI's built-in TestClient (synchronous WSGI adapter).
No Modal process required — tests run directly against the app object.

Tests that hit real agents (test_analyze_*, test_plan_*, test_chain)
require secrets in .env and a live Supabase + DeepSeek connection.

Tests that do NOT call agents (health, 404s, 422s, report stub)
run without any secrets and are safe for CI.
"""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.db.client import get_supabase

client = TestClient(app)

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_EMAIL = "delivered@resend.dev"


@pytest.fixture(scope="module")
def test_profile():
    """Insert a profiles row for TEST_USER_ID before LLM tests; delete after.

    skill_gaps and learning_plans both FK to profiles.id, so this row must
    exist before any agent writes to those tables.
    """
    supabase = get_supabase()
    supabase.table("profiles").upsert({
        "id": TEST_USER_ID,
        "email": TEST_EMAIL,
        "full_name": "API Test User",
        "goal": "Get a backend developer job",
        "hours_per_week": 10,
    }).execute()
    yield
    # Teardown — cascades to skill_gaps and learning_plans via ON DELETE CASCADE
    supabase.table("profiles").delete().eq("id", TEST_USER_ID).execute()


# ── /health ───────────────────────────────────────────────────────────────────

def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "skillbridge-api"}


# ── /analyze — validation (no LLM call) ──────────────────────────────────────

def test_analyze_missing_field_returns_422():
    """Pydantic validation: missing required fields → 422 Unprocessable Entity."""
    r = client.post("/analyze/", json={"user_id": TEST_USER_ID})
    assert r.status_code == 422


def test_analyze_wrong_type_returns_422():
    """Pydantic validation: hours_per_week must be int."""
    r = client.post("/analyze/", json={
        "user_id": TEST_USER_ID,
        "user_email": TEST_EMAIL,
        "user_goal": "Backend dev",
        "current_skills": ["Python"],
        "hours_per_week": "not-an-int",   # wrong type
    })
    assert r.status_code == 422


# ── /quiz — 404 tests (no LLM call, no secrets) ───────────────────────────────

def test_quiz_get_404_on_invalid_id():
    r = client.get("/quiz/invalid-quiz-id-that-does-not-exist-xyz")
    assert r.status_code == 404


def test_quiz_submit_404_on_invalid_id():
    r = client.post("/quiz/submit", json={
        "user_id": TEST_USER_ID,
        "user_email": TEST_EMAIL,
        "quiz_id": "nonexistent-quiz-id-xyz",
        "answers": [0, 1, 2, 3, 0],
    })
    assert r.status_code == 404


# ── /report — stub (no LLM call, no secrets) ─────────────────────────────────

def test_report_stub_returns_200():
    r = client.get(f"/report/{TEST_USER_ID}")
    assert r.status_code == 200
    assert "Sprint 8" in r.json()["message"]


# ── /analyze — real LLM call (requires .env secrets) ─────────────────────────

def test_analyze_endpoint_returns_200(test_profile):
    r = client.post("/analyze/", json={
        "user_id": TEST_USER_ID,
        "user_email": TEST_EMAIL,
        "user_goal": "Get a backend developer job at a product startup",
        "current_skills": ["Python basics", "SQL"],
        "hours_per_week": 10,
    })
    assert r.status_code == 200
    body = r.json()
    assert "skill_gap_report" in body
    assert 0 <= body["overall_readiness_percent"] <= 100
    assert body["recommended_timeline_weeks"] > 0


# ── /plan — real LLM call (requires .env secrets + skill_gap_fixture) ─────────

def test_plan_endpoint_returns_200(test_profile, skill_gap_fixture):
    r = client.post("/plan/", json={
        "user_id": TEST_USER_ID,
        "user_email": TEST_EMAIL,
        "user_goal": "Get a backend developer job at a product startup",
        "current_skills": ["Python basics"],
        "hours_per_week": 10,
        "skill_gap_report": skill_gap_fixture,
    })
    assert r.status_code == 200
    body = r.json()
    assert "milestones" in body
    assert len(body["milestones"]) > 0
    assert body["total_weeks"] == len(body["milestones"])


# ── /analyze → /plan chain (requires .env secrets) ───────────────────────────

def test_analyze_then_plan_chain(test_profile):
    """End-to-end: /analyze output feeds directly into /plan input."""
    analyze_r = client.post("/analyze/", json={
        "user_id": TEST_USER_ID,
        "user_email": TEST_EMAIL,
        "user_goal": "Get a data analyst job",
        "current_skills": ["Excel"],
        "hours_per_week": 5,
    })
    assert analyze_r.status_code == 200
    skill_gap_report = analyze_r.json()["skill_gap_report"]

    plan_r = client.post("/plan/", json={
        "user_id": TEST_USER_ID,
        "user_email": TEST_EMAIL,
        "user_goal": "Get a data analyst job",
        "current_skills": ["Excel"],
        "hours_per_week": 5,
        "skill_gap_report": skill_gap_report,
    })
    assert plan_r.status_code == 200
    assert len(plan_r.json()["milestones"]) > 0
