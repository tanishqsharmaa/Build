"""POST /analyze — invoke Agent 1 (Skill Gap Analyzer).

Builds SkillBridgeState from request body, invokes skill_gap_graph,
and returns the SkillGapReport written to state by safety_net node.
"""
from fastapi import APIRouter, HTTPException

from src.agents.skill_gap.graph import skill_gap_graph
from src.api.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter()


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
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    report = result["skill_gap_report"]
    return AnalyzeResponse(
        skill_gap_report=report,
        overall_readiness_percent=report["overall_readiness_percent"],
        recommended_timeline_weeks=report["recommended_timeline_weeks"],
    )
