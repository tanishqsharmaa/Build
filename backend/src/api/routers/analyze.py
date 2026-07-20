"""POST /analyze — invoke Agent 1 (Skill Gap Analyzer).

Builds SkillBridgeState from request body, invokes skill_gap_graph,
and returns the SkillGapReport written to state by safety_net node.
"""
import logging

from fastapi import APIRouter, HTTPException

from src.agents.skill_gap.graph import skill_gap_graph
from src.api.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=AnalyzeResponse)
async def analyze_skills(body: AnalyzeRequest) -> AnalyzeResponse:
    state = {
        "user_id": body.user_id,
        "user_email": body.user_email,
        "user_goal": body.user_goal,
        "current_skills": body.current_skills,
        "hours_per_week": body.hours_per_week,
        "progress_log": [],
    }
    try:
        result = await skill_gap_graph.ainvoke(state)
    except Exception as exc:
        logger.exception("analyze_skills failed for user=%s", body.user_id)
        raise HTTPException(status_code=500, detail="Internal server error. Our team has been notified.") from exc

    report = result["skill_gap_report"]
    return AnalyzeResponse(
        skill_gap_report=report,
        overall_readiness_percent=report["overall_readiness_percent"],
        recommended_timeline_weeks=report["recommended_timeline_weeks"],
    )
