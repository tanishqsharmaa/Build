"""Pydantic request/response schemas for all SkillBridge API endpoints.

No business logic here — pure data contracts between HTTP layer and agents.
"""
from pydantic import BaseModel, Field

UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


# ── /analyze ──────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    user_id: str = Field(..., pattern=UUID_RE)
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
    user_id: str = Field(..., pattern=UUID_RE)
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
    user_id: str = Field(..., pattern=UUID_RE)
    user_email: str
    quiz_id: str
    answers: list[int]              # student's selected option indices (0-indexed)


class SubmitResponse(BaseModel):
    overall_score: float
    recommendation: str             # "advance" | "review"
    per_question: list[dict]
    summary_feedback: str


# ── /quiz/{quiz_id}/result (reload-safe result fetch) ─────────────────────────

class QuizResultResponse(BaseModel):
    quiz_id: str
    overall_score: float
    recommendation: str


# ── /report ───────────────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    reports: list[dict]             # list of weekly_reports rows as dicts
