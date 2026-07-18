from langgraph.graph import StateGraph, END

from src.agents.state import SkillBridgeState


def morning_brief_node(state: SkillBridgeState) -> SkillBridgeState:
    """LangGraph node wrapper around run_morning_brief.

    Used by the Sprint 6 FastAPI router when the frontend triggers an
    on-demand brief (outside the cron schedule).
    """
    from src.agents.daily_checkin.morning_brief import run_morning_brief

    user = {
        "id": state["user_id"],
        "email": state.get("user_email", "delivered@resend.dev"),
        "milestones": state.get("learning_plan", []),
        "current_milestone_index": state.get("current_milestone_index", 0),
    }

    brief_dict = run_morning_brief(user)

    if brief_dict is not None:
        log_entry = f"morning_brief: sent for user={state['user_id']}"
    else:
        log_entry = (
            f"morning_brief: skipped (already sent today) for user={state['user_id']}"
        )

    return {
        **state,
        "morning_brief": brief_dict or state.get("morning_brief", {}),
        "progress_log": state.get("progress_log", []) + [log_entry],
    }


_builder = StateGraph(SkillBridgeState)
_builder.add_node("morning_brief_node", morning_brief_node)
_builder.set_entry_point("morning_brief_node")
_builder.add_edge("morning_brief_node", END)

# Public export — Sprint 6 FastAPI router imports this directly.
morning_brief_graph = _builder.compile()
