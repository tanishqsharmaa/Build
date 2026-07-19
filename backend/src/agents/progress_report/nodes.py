"""Agent 4 nodes — pure functions (no orchestration, no Supabase mutations).

Public surface:
  aggregate_scores(user_id, week_start)     -> tuple[float, int, dict]
  generate_report(...)                       -> str   (raw HTML)
  generate_linkedin_post(...)               -> str   (raw text)
"""
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

from src.core.llm_client import get_llm
from src.db.client import get_supabase

_PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"
_REPORT_PROMPT_PATH = _PROMPT_DIR / "progress_report.md"
_LINKEDIN_PROMPT_PATH = _PROMPT_DIR / "linkedin_post.md"


def _load_report_prompt() -> str:
    return _REPORT_PROMPT_PATH.read_text(encoding="utf-8")


def _load_linkedin_prompt() -> str:
    return _LINKEDIN_PROMPT_PATH.read_text(encoding="utf-8")


def aggregate_scores(user_id: str, week_start: str) -> tuple[float, int, dict]:
    """Query quiz_results and learning_plans for the week's stats.

    Returns:
        (avg_quiz_score, milestones_completed, milestone_details)

    milestone_details is a dict with:
        topics: list[str] — names of completed milestone topics
        plan_pct: float   — percentage of plan completed
    """
    supabase = get_supabase()

    # ── Quiz scores for the week ──
    quiz_rows = (
        supabase.table("quiz_results")
        .select("score, questions")
        .eq("user_id", user_id)
        .gte("submitted_at", f"{week_start}T00:00:00+00:00")
        .not_.is_("score", "null")
        .execute()
    )
    scores = [r["score"] for r in quiz_rows.data if r.get("score") is not None]
    avg_quiz_score = sum(scores) / len(scores) if scores else 0.0

    # topic is embedded inside questions JSONB as {"topic": "...", ...}
    topics_quizzed = []
    for r in quiz_rows.data:
        q_data = r.get("questions")
        if isinstance(q_data, dict) and q_data.get("topic"):
            topics_quizzed.append(q_data["topic"])
    topics_quizzed = list({t for t in topics_quizzed if t})

    # ── Active learning plan ──
    plan_rows = (
        supabase.table("learning_plans")
        .select("milestones, current_milestone_index")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    milestones_completed = 0
    plan_milestones = []
    plan_total = 1
    plan_pct = 0.0

    if plan_rows.data:
        plan = plan_rows.data[0]
        plan_milestones = plan.get("milestones", [])
        current_idx = plan.get("current_milestone_index", 0)
        plan_total = len(plan_milestones)
        # Count milestones at or behind current index as "completed"
        milestones_completed = min(current_idx, plan_total)
        plan_pct = round((milestones_completed / plan_total) * 100, 1) if plan_total else 0.0

    # ── Completed topic names ──
    completed_topics = []
    if plan_milestones and milestones_completed > 0:
        completed_topics = [
            m.get("topic", f"Week {m.get('week', '?')}")
            for m in plan_milestones[:milestones_completed]
        ]

    milestone_details = {
        "topics": completed_topics[-7:],        # Last 7 completed topics
        "topics_quizzed": topics_quizzed[-7:],   # Topics quizzed this week
        "plan_pct": plan_pct,
        "total_milestones": plan_total,
    }

    return avg_quiz_score, milestones_completed, milestone_details


def generate_report(
    week_start: str,
    milestones_completed: int,
    avg_quiz_score: float,
    milestone_details: dict,
) -> str:
    """Call DeepSeek (temp=0.7) to generate a weekly progress report in HTML.

    Returns raw HTML string — no structured output parsing.
    """
    llm = get_llm(temperature=0.7)

    topics_text = "\n".join(
        f"- {t}" for t in milestone_details.get("topics", [])
    ) or "(no topics completed this week)"

    topics_quizzed_text = "\n".join(
        f"- {t}" for t in milestone_details.get("topics_quizzed", [])
    ) or "(no quizzes this week)"

    prompt = ChatPromptTemplate.from_messages([
        ("system", _load_report_prompt()),
        (
            "human",
            "Week start: {week_start}\n"
            "Milestones completed: {milestones_completed}\n"
            "Average quiz score: {avg_quiz_score:.0f}%\n"
            "Plan progress: {plan_pct:.0f}%\n"
            "\nTopics covered this week:\n{topics}\n"
            "\nTopics quizzed:\n{topics_quizzed}",
        ),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "week_start": week_start,
        "milestones_completed": milestones_completed,
        "avg_quiz_score": avg_quiz_score,
        "plan_pct": milestone_details.get("plan_pct", 0),
        "topics": topics_text,
        "topics_quizzed": topics_quizzed_text,
    })

    return response.content


def generate_linkedin_post(
    topics: list[str],
    milestones_completed: int,
    avg_quiz_score: float,
) -> str:
    """Call DeepSeek (temp=0.8) to generate a celebratory LinkedIn post.

    Returns raw text string.
    """
    llm = get_llm(temperature=0.8)

    topics_text = ", ".join(topics) if topics else "new technical skills"

    prompt = ChatPromptTemplate.from_messages([
        ("system", _load_linkedin_prompt()),
        (
            "human",
            "Topics covered this week: {topics}\n"
            "Milestones completed: {milestones_completed}\n"
            "Average quiz score: {avg_quiz_score:.0f}%",
        ),
    ])

    chain = prompt | llm
    response = chain.invoke({
        "topics": topics_text,
        "milestones_completed": milestones_completed,
        "avg_quiz_score": avg_quiz_score,
    })

    return response.content
