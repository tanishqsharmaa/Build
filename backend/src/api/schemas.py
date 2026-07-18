"""Pydantic request/response schemas for all SkillBridge API endpoints.

No business logic here — pure data contracts between HTTP layer and agents.
"""
from pydantic import BaseModel


# ── /analyze ──────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    user_id: str
    user_email: str
    user_goal: str
    current_skills: list[str]
    hours_per_week: int


class AnalyzeResponse(BaseModel):
    skill_gap_report: dict
    overall_readiness_percent: int
    recommended_timeline_weeks: int


# ── /plan ─────────────────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    user_id: str
    user_email: str
    user_goal: str
    current_skills: list[str]
    hours_per_week: int
    skill_gap_report: dict          # output from /analyze


class PlanResponse(BaseModel):
    milestones: list[dict]
    total_weeks: int


# ── /quiz ─────────────────────────────────────────────────────────────────────

class QuizResponse(BaseModel):
    quiz_id: str
    topic: str
    questions: list[dict]           # list[QuizQuestion] serialised as dicts


# ── /submit ───────────────────────────────────────────────────────────────────

class SubmitRequest(BaseModel):
    user_id: str
    user_email: str
    quiz_id: str
    answers: list[int]              # student's selected option indices (0-indexed)


class SubmitResponse(BaseModel):
    overall_score: float
    recommendation: str             # "advance" | "review"
    per_question: list[dict]
    summary_feedback: str


# ── /report ───────────────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    message: str                    # Sprint 8 stub placeholder
