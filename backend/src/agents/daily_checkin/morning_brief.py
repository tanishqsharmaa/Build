"""Agent 3a — Morning Brief Generator.

Public surface:
  generate_brief(topic, milestone_description) -> MorningBrief
  run_morning_brief(user)                      -> dict | None
  run_for_all_users()                          -> None  (async, cron entry point)
"""
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.agents.daily_checkin.schemas import MorningBrief
from src.core.llm_client import get_llm
from src.db.client import get_supabase
from src.email.client import send_email
from src.email.renderer import render_morning_brief

_PROMPT_PATH = (
    Path(__file__).parent.parent.parent / "prompts" / "morning_brief.md"
)

# Protects DeepSeek from a 50-user burst during the 7:30 AM cron
_SEMAPHORE = asyncio.Semaphore(10)


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


# ── Core LLM node ─────────────────────────────────────────────────────────────

def generate_brief(topic: str, milestone_description: str) -> MorningBrief:
    """Call DeepSeek (temp=0.7) and parse the response into a MorningBrief.

    Separated from run_morning_brief() so unit tests can mock just this function.
    """
    llm = get_llm(temperature=0.7)
    parser = PydanticOutputParser(pydantic_object=MorningBrief)

    prompt = ChatPromptTemplate.from_messages([
        ("system", _load_prompt()),
        (
            "human",
            "Topic: {topic}\n"
            "Milestone context: {milestone_description}\n\n"
            "{format_instructions}",
        ),
    ])

    chain = prompt | llm | parser
    return chain.invoke({
        "topic": topic,
        "milestone_description": milestone_description,
        "format_instructions": parser.get_format_instructions(),
    })


# ── Idempotency key builder ────────────────────────────────────────────────────

def _build_quiz_id(user_id: str, topic: str, date_str: str) -> str:
    """Build a unique quiz_id for the day's morning brief row.

    Format: {user_id[:8]}_{YYYY-MM-DD}_{topic-slug[:30]}
    Example: 00000000_2026-07-18_fastapi-basics
    """
    slug = topic.lower().replace(" ", "-")[:30]
    return f"{user_id[:8]}_{date_str}_{slug}"


# ── Per-user runner ────────────────────────────────────────────────────────────

def run_morning_brief(user: dict) -> dict | None:
    """Run Agent 3a for a single user.

    Returns:
        MorningBrief dict on success.
        None if the brief was already sent today (idempotency skip).

    user dict must have keys:
        id                     (str UUID)
        email                  (str)
        milestones             (list[dict] — from learning_plans.milestones JSONB)
        current_milestone_index (int)
    """
    supabase = get_supabase()
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    user_id = user["id"]

    # ── Idempotency check: skip if a quiz_results row already exists today ──
    existing = (
        supabase.table("quiz_results")
        .select("id")
        .eq("user_id", user_id)
        .gte("sent_at", f"{today}T00:00:00+00:00")
        .execute()
    )
    if existing.data:
        return None  # Already sent today — cron is safe to re-fire

    # ── Derive today's topic from the active milestone ──────────────────────
    milestones = user["milestones"]
    idx = user.get("current_milestone_index", 0)
    # Clamp to last milestone if index is out of bounds
    milestone = milestones[idx] if idx < len(milestones) else milestones[-1]
    topic = milestone["topic"]
    milestone_desc = ", ".join(milestone.get("daily_subtopics", []))

    # ── Generate → render → send ────────────────────────────────────────────
    brief = generate_brief(topic=topic, milestone_description=milestone_desc)
    html = render_morning_brief(brief)
    send_email(
        to=user["email"],
        subject=f"☀️ Morning Brief: {topic}",
        html=html,
    )

    # ── Log idempotency sentinel to quiz_results ────────────────────────────
    # quiz_results schema: quiz_id (UNIQUE), date, questions (JSONB), sent_at
    # We store topic inside questions JSONB as {"topic": "..."} so Sprint 5
    # quiz conductor can read it back without an extra column.
    quiz_id = _build_quiz_id(user_id, topic, today)
    supabase.table("quiz_results").insert({
        "user_id": user_id,
        "quiz_id": quiz_id,
        "date": today,
        "questions": {"topic": topic, "milestone_index": idx, "items": []},
        "sent_at": datetime.now(tz=timezone.utc).isoformat(),
    }).execute()

    return brief.model_dump()


# ── Cron batch runner ──────────────────────────────────────────────────────────

async def run_for_all_users() -> None:
    """Fetch all users with an active plan and run morning brief concurrently.

    Called by morning_brief_cron.py (Modal cron, wired in Sprint 6).
    asyncio.Semaphore(10) prevents DeepSeek rate-limit errors during the burst.
    """
    supabase = get_supabase()

    rows = (
        supabase.table("learning_plans")
        .select("user_id, milestones, current_milestone_index, profiles(id, email)")
        .eq("is_active", True)
        .execute()
    )

    async def _run_one(row: dict) -> None:
        async with _SEMAPHORE:
            user = {
                "id": row["user_id"],
                "email": row["profiles"]["email"],
                "milestones": row["milestones"],
                "current_milestone_index": row["current_milestone_index"],
            }
            try:
                run_morning_brief(user)
            except Exception as exc:  # noqa: BLE001 — log and continue batch
                print(f"[morning_brief] ERROR user={user['id']}: {exc}")

    await asyncio.gather(
        *[_run_one(r) for r in rows.data],
        return_exceptions=True,
    )
