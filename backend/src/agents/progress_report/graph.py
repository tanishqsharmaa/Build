"""Agent 4 — LangGraph StateGraph for on-demand progress report generation.

Used by the FastAPI router when the frontend triggers an on-demand report.
"""
from langgraph.graph import END, StateGraph

from src.agents.state import SkillBridgeState


def progress_report_node(state: SkillBridgeState) -> SkillBridgeState:
    """LangGraph node wrapper around run_weekly_report."""
    from src.agents.progress_report.report_runner import run_weekly_report

    user = {
        "id": state["user_id"],
        "email": state.get("user_email", "delivered@resend.dev"),
    }

    report_dict = run_weekly_report(user)

    if report_dict is not None:
        log_entry = f"progress_report: generated for user={state['user_id']}"
    else:
        log_entry = (
            f"progress_report: skipped (already generated) for user={state['user_id']}"
        )

    return {
        **state,
        "weekly_report": report_dict or state.get("weekly_report", {}),
        "progress_log": state.get("progress_log", []) + [log_entry],
    }


_builder = StateGraph(SkillBridgeState)
_builder.add_node("progress_report_node", progress_report_node)
_builder.set_entry_point("progress_report_node")
_builder.add_edge("progress_report_node", END)

progress_report_graph = _builder.compile()
