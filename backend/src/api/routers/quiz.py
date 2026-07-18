"""Quiz routes — GET /quiz/{quiz_id} and POST /quiz/submit.

GET /quiz/{quiz_id}
    Fetches pre-generated MCQs from Supabase quiz_results table.
    No LLM call — questions were saved by the 4 PM cron (quiz_conductor).

POST /quiz/submit
    Receives student answers, invokes quiz_graph (Agent 3b).
    The graph scores answers, applies the conditional edge:
      score >= 70 → advance_node (increment milestone index)
      score < 70  → replan_node (surgical splice + revision_count++)
"""
from fastapi import APIRouter, HTTPException

from src.api.schemas import QuizResponse, SubmitRequest, SubmitResponse
from src.agents.daily_checkin.quiz_graph import quiz_graph
from src.db.client import get_supabase

router = APIRouter()


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: str) -> QuizResponse:
    """Fetch pre-generated MCQs for the given quiz_id (no LLM call)."""
    supabase = get_supabase()
    row = (
        supabase.table("quiz_results")
        .select(
            "quiz_id, questions, "
            "learning_plans!inner(milestones, current_milestone_index)"
        )
        .eq("quiz_id", quiz_id)
        .maybe_single()
        .execute()
    )

    if not row.data:
        raise HTTPException(status_code=404, detail=f"Quiz {quiz_id!r} not found")

    items = row.data.get("questions", {}).get("items", [])
    if not items:
        raise HTTPException(
            status_code=404,
            detail="Quiz questions not generated yet — check back after the 4 PM cron",
        )

    milestones = row.data["learning_plans"]["milestones"]
    idx = row.data["learning_plans"]["current_milestone_index"]
    topic = milestones[idx]["topic"] if idx < len(milestones) else "General"

    return QuizResponse(quiz_id=quiz_id, topic=topic, questions=items)


@router.post("/submit", response_model=SubmitResponse)
async def submit_quiz(body: SubmitRequest) -> SubmitResponse:
    """Score student answers and trigger the adaptive quiz_graph."""
    supabase = get_supabase()

    # Fetch questions + current milestone context
    row = (
        supabase.table("quiz_results")
        .select(
            "questions, "
            "learning_plans!inner(milestones, current_milestone_index)"
        )
        .eq("quiz_id", body.quiz_id)
        .maybe_single()
        .execute()
    )

    if not row.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    items = row.data.get("questions", {}).get("items", [])
    milestones = row.data["learning_plans"]["milestones"]
    idx = row.data["learning_plans"]["current_milestone_index"]
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
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    qr = result["quiz_result"]
    return SubmitResponse(
        overall_score=qr["overall_score"],
        recommendation=qr["recommendation"],
        per_question=qr["per_question"],
        summary_feedback=qr["summary_feedback"],
    )
