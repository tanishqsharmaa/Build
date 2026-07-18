"""Agent 3b — Quiz Evaluation LangGraph.

Graph topology:
  evaluate_quiz_node
        |
        v
  route_after_quiz  (conditional edge)
    /              \\
"advance"       "review"
    |                |
advance_node    replanner_node
    |                |
    +------→ END ←--+

This graph is invoked by the POST /submit FastAPI endpoint (Sprint 6).

Public export:
  quiz_graph  — compiled LangGraph StateGraph
"""
from langgraph.graph import StateGraph, END

from src.agents.state import SkillBridgeState


# ── Node: evaluate the submitted answers ──────────────────────────────────────


def evaluate_quiz_node(state: SkillBridgeState) -> SkillBridgeState:
    """Score the quiz and generate LLM feedback.

    Reads quiz_id, quiz_answers, quiz_questions from state.
    Writes quiz_result + quiz_scores to state.
    Also writes result to DB and sends result email (via evaluate_and_route).
    """
    from src.agents.daily_checkin.schemas import QuizQuestion
    from src.agents.daily_checkin.quiz_evaluator import evaluate_and_route

    quiz_id: str = state["quiz_id"]
    user_id: str = state["user_id"]
    user_email: str = state.get("user_email", "delivered@resend.dev")
    answers: list[int] = state.get("quiz_answers", [])
    todays_topic: str = state.get("todays_topic", "")

    # Deserialise questions from state (stored as list[dict])
    raw_questions: list[dict] = state.get("quiz_questions", [])
    questions = [QuizQuestion(**q) for q in raw_questions]

    result = evaluate_and_route(
        user_id=user_id,
        quiz_id=quiz_id,
        topic=todays_topic,
        questions=questions,
        answers=answers,
        user_email=user_email,
    )

    quiz_scores: list[float] = list(state.get("quiz_scores", []))
    quiz_scores.append(result.overall_score)

    log_entry = (
        f"quiz_eval: score={result.overall_score:.0f}% "
        f"recommendation={result.recommendation} "
        f"quiz_id={quiz_id}"
    )

    return {
        **state,
        "quiz_result": result.model_dump(),
        "quiz_scores": quiz_scores,
        "progress_log": state.get("progress_log", []) + [log_entry],
    }


# ── Conditional edge router ───────────────────────────────────────────────────


def route_after_quiz(state: SkillBridgeState) -> str:
    """Return 'advance' or 'review' based on the quiz result.

    This is the core adaptive edge of SkillBridge.
    """
    result = state.get("quiz_result", {})
    return result.get("recommendation", "review")


# ── Node: advance to next milestone (score >= 70) ─────────────────────────────


def advance_node(state: SkillBridgeState) -> SkillBridgeState:
    """No-op node: advance_milestone was already called inside evaluate_quiz_node.

    Exists as a named node so the LangGraph conditional edge can target it
    and the graph trace shows a clear 'advance' branch.
    """
    log_entry = (
        f"advance_milestone: user={state['user_id']} "
        f"new_index={state.get('current_milestone_index', 0) + 1}"
    )
    # current_milestone_index is updated in DB by advance_milestone() inside
    # evaluate_and_route(). We mirror it in state here for consistency.
    new_index = state.get("current_milestone_index", 0) + 1
    total = len(state.get("learning_plan", []))
    new_index = min(new_index, total - 1)

    return {
        **state,
        "current_milestone_index": new_index,
        "progress_log": state.get("progress_log", []) + [log_entry],
    }


# ── Node: import replanner from replanner.py ─────────────────────────────────


def replan_node(state: SkillBridgeState) -> SkillBridgeState:
    """Thin wrapper so the graph imports cleanly without circular imports."""
    from src.agents.daily_checkin.replanner import replanner_node
    return replanner_node(state)


# ── Build the graph ────────────────────────────────────────────────────────────

_builder = StateGraph(SkillBridgeState)

_builder.add_node("evaluate_quiz_node", evaluate_quiz_node)
_builder.add_node("advance_node", advance_node)
_builder.add_node("replan_node", replan_node)

_builder.set_entry_point("evaluate_quiz_node")

_builder.add_conditional_edges(
    "evaluate_quiz_node",
    route_after_quiz,
    {
        "advance": "advance_node",
        "review": "replan_node",
    },
)

_builder.add_edge("advance_node", END)
_builder.add_edge("replan_node", END)

# Public export — Sprint 6 FastAPI /submit router imports this.
quiz_graph = _builder.compile()
