"""POST /session/start — trigger morning brief + quiz generation for a new user.

Called by the frontend after onboarding completes (analyze → plan chain).
Replaces waiting for the scheduled cron — gives the user instant deliverable.
"""
import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agents.daily_checkin.morning_brief import run_morning_brief
from src.agents.daily_checkin.quiz_conductor import run_quiz_conductor
from src.db.client import get_supabase

router = APIRouter()
logger = logging.getLogger(__name__)

UUID_RE = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


class SessionStartRequest(BaseModel):
    user_id: str = Field(..., pattern=UUID_RE)


@router.post("/start")
async def start_daily_session(body: SessionStartRequest) -> dict:
    """Run morning_brief + quiz_conductor for a single user immediately.

    Called after onboarding completes so the user gets their first
    morning brief and quiz link right away (instead of waiting for
    the 7:30 AM IST cron).
    """
    user_id = body.user_id

    # Fetch user profile + active learning plan
    supabase = get_supabase()

    profile_r = supabase.table("profiles").select("id, email").eq("id", user_id).maybe_single().execute()
    if not profile_r.data:
        raise HTTPException(status_code=404, detail=f"Profile not found: {user_id}")

    plan_r = (
        supabase.table("learning_plans")
        .select("user_id, milestones, current_milestone_index")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    if not plan_r.data:
        raise HTTPException(status_code=404, detail=f"No active learning plan for user: {user_id}")

    user = {
        "id": user_id,
        "email": profile_r.data["email"],
        "milestones": plan_r.data["milestones"],
        "current_milestone_index": plan_r.data["current_milestone_index"],
    }

    # Step 1: morning brief → generates quiz_results row + sends morning email
    try:
        brief = await asyncio.to_thread(run_morning_brief, user)
        if brief is None:
            logger.info("session/start: morning_brief already sent today for user=%s", user_id)
        else:
            logger.info("session/start: morning_brief sent for user=%s", user_id)
    except Exception:
        logger.exception("session/start: morning_brief failed for user=%s", user_id)
        raise HTTPException(status_code=500, detail="Failed to generate morning brief.")

    # Step 2: fetch the quiz_id that morning_brief created
    quiz_r = (
        supabase.table("quiz_results")
        .select("quiz_id")
        .eq("user_id", user_id)
        .order("sent_at", desc=True)
        .limit(1)
        .execute()
    )
    if not quiz_r.data:
        raise HTTPException(status_code=500, detail="Morning brief succeeded but no quiz row found.")

    user["quiz_id"] = quiz_r.data[0]["quiz_id"]

    # Step 3: quiz conductor → generates MCQs + sends quiz email
    try:
        result = await asyncio.to_thread(run_quiz_conductor, user)
        if result:
            logger.info("session/start: quiz sent for user=%s (%d questions)", user_id, result["question_count"])
        else:
            logger.info("session/start: quiz already generated for user=%s (email resent)", user_id)
    except Exception:
        logger.exception("session/start: quiz_conductor failed for user=%s", user_id)
        raise HTTPException(status_code=500, detail="Failed to generate quiz.")

    return {"status": "ok", "user_id": user_id}
