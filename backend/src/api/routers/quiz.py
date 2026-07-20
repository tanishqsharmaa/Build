"""Quiz routes — GET /quiz/{quiz_id} and POST /quiz/submit.

GET /quiz/{quiz_id}
    Fetches pre-generated MCQs from Supabase quiz_results table.
    No LLM call — questions were saved by the 4 PM cron (quiz_conductor).

POST /quiz/submit
    Receives student answers, invokes quiz_graph (Agent 3b).
    The graph scores answers, applies the conditional edge:
      score >= 70 → advance_node (increment milestone index)
      score < 70  → replan_node (surgical splice + revision_count++)

Note on Supabase queries:
    Uses .limit(1).execute() + list check instead of .maybe_single() because
    maybe_single() returns None (not a response object) when no row is found
    in this version of supabase-py, causing AttributeError on .data access.
    Two-step queries (quiz_results then learning_plans) avoid the PGRST200
    join error — the two tables share no direct FK (both FK to profiles.id).
"""
import logging

from fastapi import APIRouter, HTTPException

from src.agents.daily_checkin.quiz_graph import quiz_graph
from src.api.schemas import QuizResponse, SubmitRequest, SubmitResponse
from src.db.client import get_supabase

router = APIRouter()
logger = logging.getLogger(__name__)


def _fetch_quiz_row(quiz_id: str) -> dict | None:
    """Return the quiz_results row for quiz_id, or None if not found."""
    supabase = get_supabase()
    rows = (
        supabase.table("quiz_results")
        .select("quiz_id, questions, user_id")
        .eq("quiz_id", quiz_id)
        .limit(1)
        .execute()
    )
    return rows.data[0] if rows.data else None


def _fetch_plan_row(user_id: str) -> dict | None:
    """Return the active learning_plans row for user_id, or None if not found."""
    supabase = get_supabase()
    rows = (
        supabase.table("learning_plans")
        .select("milestones, current_milestone_index")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    return rows.data[0] if rows.data else None


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: str) -> QuizResponse:
    """Fetch pre-generated MCQs for the given quiz_id (no LLM call)."""
    quiz_data = _fetch_quiz_row(quiz_id)
    if quiz_data is None:
        raise HTTPException(status_code=404, detail=f"Quiz {quiz_id!r} not found")

    items = (quiz_data.get("questions") or {}).get("items", [])
    if not items:
        raise HTTPException(
            status_code=404,
            detail="Quiz questions not generated yet — check back after the 4 PM cron",
        )

    # Best-effort topic lookup — doesn't 404 if plan is missing
    topic = "General"
    plan_data = _fetch_plan_row(quiz_data["user_id"])
    if plan_data:
        milestones = plan_data["milestones"]
        idx = plan_data["current_milestone_index"]
        topic = milestones[idx]["topic"] if idx < len(milestones) else "General"

    return QuizResponse(quiz_id=quiz_id, topic=topic, questions=items)


@router.post("/submit", response_model=SubmitResponse)
async def submit_quiz(body: SubmitRequest) -> SubmitResponse:
    """Score student answers and trigger the adaptive quiz_graph."""
    quiz_data = _fetch_quiz_row(body.quiz_id)
    if quiz_data is None:
        raise HTTPException(status_code=404, detail="Quiz not found")

    items = (quiz_data.get("questions") or {}).get("items", [])
    user_id = quiz_data["user_id"]

    milestones: list[dict] = []
    idx = 0
    topic = "General"
    plan_data = _fetch_plan_row(user_id)
    if plan_data:
        milestones = plan_data["milestones"]
        idx = plan_data["current_milestone_index"]
        topic = milestones[idx]["topic"] if idx < len(milestones) else "General"

    state = {
        "user_id": body.user_id,
        "user_email": body.user_email,
        "quiz_id": body.quiz_id,
        "quiz_questions": items,
        "quiz_answers": body.answers,
        "todays_topic": topic,
        "learning_plan": milestones,
        "current_milestone_index": idx,
        "plan_revision_count": 0,
        "progress_log": [],
    }

    try:
        result = await quiz_graph.ainvoke(state)
    except Exception as exc:
        logger.exception("submit_quiz failed for quiz_id=%s", body.quiz_id)
        raise HTTPException(status_code=500, detail="Internal server error. Our team has been notified.") from exc

    qr = result["quiz_result"]
    return SubmitResponse(
        overall_score=qr["overall_score"],
        recommendation=qr["recommendation"],
        per_question=qr["per_question"],
        summary_feedback=qr["summary_feedback"],
    )
