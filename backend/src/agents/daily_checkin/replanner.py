"""Agent 3b — Replanner node.

Self-correction loop: when a student scores < 70%, the replanner rewrites
the failed milestone and the next one, then splices them back into the plan.

Public surface:
  replanner_node(state) -> SkillBridgeState   (LangGraph node)
"""
import functools
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.agents.learning_planner.schemas import MilestoneList
from src.agents.state import SkillBridgeState
from src.core.llm_client import get_llm, invoke_llm_with_retry
from src.db.client import get_supabase

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "replanner.md"

_MAX_REWRITES = 3


@functools.lru_cache(maxsize=1)
def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


# ── LangGraph node ────────────────────────────────────────────────────────────


def replanner_node(state: SkillBridgeState) -> SkillBridgeState:
    """Rewrite failed + next milestone when score < 70.

    Guard: if plan_revision_count >= 3, append 'MAX REWRITES REACHED' to the
    progress_log and return the state unchanged (no DB write, no LLM call).

    Surgical splice: only replaces plan[idx:idx+2]; prefix and suffix unchanged.
    """
    revision_count: int = state.get("plan_revision_count", 0)
    progress_log: list[str] = list(state.get("progress_log", []))
    user_id: str = state["user_id"]

    # ── Hard cap guard ─────────────────────────────────────────────────────
    if revision_count >= _MAX_REWRITES:
        progress_log.append(
            f"MAX REWRITES REACHED for topic={state.get('todays_topic', '?')} "
            f"— flagged for mentor review"
        )
        return {**state, "progress_log": progress_log}

    # ── Context extraction ─────────────────────────────────────────────────
    plan: list[dict] = list(state.get("learning_plan", []))
    idx: int = state.get("current_milestone_index", 0)
    quiz_scores: list[float] = state.get("quiz_scores", [])
    latest_score: float = quiz_scores[-1] if quiz_scores else 0.0

    failed_milestone = plan[idx] if idx < len(plan) else {}
    next_milestone = plan[idx + 1] if idx + 1 < len(plan) else {}

    topic: str = state.get("todays_topic", failed_milestone.get("topic", "Unknown"))

    # ── LLM call: rewrite 2 milestones ────────────────────────────────────
    llm = get_llm(temperature=0.3)
    parser = PydanticOutputParser(pydantic_object=MilestoneList)

    prompt = ChatPromptTemplate.from_messages([
        ("system", _load_prompt()),
        (
            "human",
            "Failed topic: {topic}\n"
            "Quiz score: {score}/100\n"
            "Revision attempt: {revision_count}\n"
            "Original failed milestone (week {failed_week}):\n{failed_milestone}\n"
            "Original next milestone (week {next_week}):\n{next_milestone}\n\n"
            "{format_instructions}",
        ),
    ])

    chain = prompt | llm | parser
    try:
        updated: MilestoneList = invoke_llm_with_retry(chain, {
            "topic": topic,
            "score": latest_score,
            "revision_count": revision_count + 1,
            "failed_milestone": str(failed_milestone),
            "failed_week": failed_milestone.get("week", idx + 1),
            "next_milestone": str(next_milestone),
            "next_week": next_milestone.get("week", idx + 2),
            "format_instructions": parser.get_format_instructions(),
        })
    except Exception:
        progress_log.append(
            f"REPLAN FAILED for topic={topic} — LLM output could not be parsed"
        )
        return {**state, "progress_log": progress_log}

    # ── Surgical splice ────────────────────────────────────────────────────
    new_milestones = [m.model_dump() for m in updated.milestones[:2]]
    new_plan = plan[:idx] + new_milestones + plan[idx + 2:]

    # ── Persist to DB ──────────────────────────────────────────────────────
    supabase = get_supabase()
    new_revision_count = revision_count + 1

    (
        supabase.table("learning_plans")
        .update({
            "milestones": new_plan,
            "plan_revision_count": new_revision_count,
        })
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )

    # ── Log entry ──────────────────────────────────────────────────────────
    progress_log.append(
        f"REPLAN #{new_revision_count} for topic={topic} score={latest_score:.0f}%"
    )

    return {
        **state,
        "learning_plan": new_plan,
        "plan_revision_count": new_revision_count,
        "progress_log": progress_log,
    }
