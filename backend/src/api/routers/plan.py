"""POST /plan — invoke Agent 2 (Learning Path Planner).

Accepts the skill_gap_report from /analyze as part of the request body,
invokes learning_planner_graph, and returns the MilestoneList.
"""
from fastapi import APIRouter, HTTPException

from src.agents.learning_planner.graph import learning_planner_graph
from src.api.schemas import PlanRequest, PlanResponse

router = APIRouter()


@router.post("/", response_model=PlanResponse)
async def create_plan(body: PlanRequest) -> PlanResponse:
    state = {
        "user_id": body.user_id,
        "user_email": body.user_email,
        "user_goal": body.user_goal,
        "current_skills": body.current_skills,
        "hours_per_week": body.hours_per_week,
        "skill_gap_report": body.skill_gap_report,
        "progress_log": [],
    }
    try:
        result = await learning_planner_graph.ainvoke(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    plan = result["learning_plan"]
    return PlanResponse(
        milestones=plan,
        total_weeks=len(plan),
    )
