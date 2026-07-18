"""SkillBridge FastAPI application — Sprint 6.

Endpoints:
    POST /analyze           → Agent 1 (Skill Gap Analyzer)
    POST /plan              → Agent 2 (Learning Path Planner)
    GET  /quiz/{quiz_id}    → fetch pre-generated MCQs
    POST /quiz/submit       → Agent 3b (Quiz Evaluator + conditional edge)
    GET  /report/{user_id}  → Agent 4 stub (Sprint 8)
    GET  /health            → liveness probe

This module is imported by modal_app.py via:
    from src.api.main import app as api
"""
from fastapi import FastAPI

from src.api.routers import analyze, plan, quiz, report

app = FastAPI(
    title="SkillBridge API",
    description=(
        "Multi-Agent Adaptive Learning System — "
        "AICTE AI Automation & Intelligent Solutions, IBM SkillsBuild 2026"
    ),
    version="0.1.0",
)

app.include_router(analyze.router, prefix="/analyze", tags=["Agent 1 — Skill Gap"])
app.include_router(plan.router,    prefix="/plan",    tags=["Agent 2 — Learning Planner"])
app.include_router(quiz.router,    prefix="/quiz",    tags=["Agent 3b — Quiz"])
app.include_router(report.router,  prefix="/report",  tags=["Agent 4 — Report (stub)"])


@app.get("/health", tags=["infra"])
async def health() -> dict:
    """Liveness probe — used by Modal and Vercel to confirm the app is up."""
    return {"status": "ok", "service": "skillbridge-api"}
