"""Agent 3b — Quiz Conductor.

Public surface:
  generate_quiz(topic, milestone_description) -> list[QuizQuestion]
  save_quiz(user_id, quiz_id, questions)      -> None
  send_quiz_email(user_email, quiz_id, topic) -> None
  run_quiz_conductor(user)                    -> dict | None
  send_links_for_all_users()                  -> None  (async, cron entry point)
"""
import asyncio
import logging
from pathlib import Path

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.agents.daily_checkin.schemas import QuizList, QuizQuestion
from src.core.llm_client import get_llm, invoke_llm_with_retry
from src.db.client import get_supabase
from src.email.client import send_email

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "quiz_generator.md"

# Protects DeepSeek from a 50-user burst during the 4:00 PM cron
_SEMAPHORE = asyncio.Semaphore(10)
logger = logging.getLogger(__name__)


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


# ── Core LLM node ─────────────────────────────────────────────────────────────


def generate_quiz(topic: str, milestone_description: str) -> list[QuizQuestion]:
    """Call DeepSeek (temp=0.3) and return exactly 5 QuizQuestion objects.

    Separated from run_quiz_conductor() so unit tests can mock just this function.
    """
    llm = get_llm(temperature=0.3)
    parser = PydanticOutputParser(pydantic_object=QuizList)

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
    result: QuizList = invoke_llm_with_retry(chain, {
        "topic": topic,
        "milestone_description": milestone_description,
        "format_instructions": parser.get_format_instructions(),
    })
    return result.questions


# ── DB helpers ────────────────────────────────────────────────────────────────


def save_quiz(user_id: str, quiz_id: str, questions: list[QuizQuestion]) -> None:
    """UPDATE the existing quiz_results row (created by morning brief) with MCQs.

    Sprint 4's morning_brief inserted the row with questions.items = [].
    We fill it in here so the student can fetch the quiz via quiz_id.
    """
    supabase = get_supabase()
    questions_payload = {
        "items": [q.model_dump() for q in questions],
    }
    (
        supabase.table("quiz_results")
        .update({"questions": questions_payload})
        .eq("quiz_id", quiz_id)
        .execute()
    )


# ── Email ─────────────────────────────────────────────────────────────────────

_QUIZ_BASE_URL = "https://skillbridge.app/quiz"  # Sprint 7 Vercel URL


def send_quiz_email(user_email: str, quiz_id: str, topic: str) -> None:
    """Send the quiz link email via Resend."""
    quiz_url = f"{_QUIZ_BASE_URL}?id={quiz_id}"
    html = f"""
    <html>
    <body style="font-family: sans-serif; background: #0f172a; color: #e2e8f0; padding: 32px;">
      <h2 style="color: #38bdf8;">⚡ Quiz Time: {topic}</h2>
      <p>You've studied today's topic — now let's test your understanding!</p>
      <p>
        <a href="{quiz_url}"
           style="background: #38bdf8; color: #0f172a; padding: 12px 24px;
                  border-radius: 6px; text-decoration: none; font-weight: bold;">
          Take the Quiz →
        </a>
      </p>
      <p style="color: #94a3b8; font-size: 13px;">
        Score 70% or above to advance to the next milestone. You've got this!
      </p>
      <hr style="border-color: #1e293b;" />
      <p style="color: #475569; font-size: 12px;">Powered by SkillBridge</p>
    </body>
    </html>
    """
    send_email(to=user_email, subject=f"⚡ Quiz: {topic}", html=html)


# ── Per-user runner ────────────────────────────────────────────────────────────


def run_quiz_conductor(user: dict) -> dict | None:
    """Run Agent 3b for a single user.

    Returns:
        dict with quiz_id + question count on success.
        None if quiz was already generated today (idempotency skip).

    user dict must have keys:
        id                      (str UUID)
        email                   (str)
        quiz_id                 (str)   — built by morning brief (same day)
        milestones              (list[dict])
        current_milestone_index (int)
    """
    quiz_id = user["quiz_id"]

    # ── Idempotency: skip if quiz already has items ────────────────────────
    supabase = get_supabase()
    row = (
        supabase.table("quiz_results")
        .select("questions")
        .eq("quiz_id", quiz_id)
        .maybe_single()
        .execute()
    )

    if row.data and row.data.get("questions", {}).get("items"):
        # Quiz already generated for this quiz_id — just re-send the email
        milestones = user["milestones"]
        idx = user.get("current_milestone_index", 0)
        milestone = milestones[idx] if idx < len(milestones) else milestones[-1]
        send_quiz_email(user["email"], quiz_id, milestone["topic"])
        return None  # Skipped generation, email resent

    # ── Derive topic from current milestone ─────────────────────────────────
    milestones = user["milestones"]
    idx = user.get("current_milestone_index", 0)
    milestone = milestones[idx] if idx < len(milestones) else milestones[-1]
    topic = milestone["topic"]
    milestone_desc = ", ".join(milestone.get("daily_subtopics", []))

    # ── Generate → save → email ─────────────────────────────────────────────
    questions = generate_quiz(topic=topic, milestone_description=milestone_desc)
    save_quiz(user_id=user["id"], quiz_id=quiz_id, questions=questions)
    send_quiz_email(user_email=user["email"], quiz_id=quiz_id, topic=topic)

    return {"quiz_id": quiz_id, "question_count": len(questions)}


# ── Cron batch runner ──────────────────────────────────────────────────────────


async def send_links_for_all_users() -> None:
    """Fetch all users with an active plan and run quiz conductor concurrently.

    Called by quiz_conductor_cron.py (Modal cron, wired in Sprint 6).
    asyncio.Semaphore(10) prevents DeepSeek rate-limit errors during the burst.

    Reads today's quiz_id from quiz_results (set by morning brief at 7:30 AM).
    """
    from datetime import datetime, timezone

    supabase = get_supabase()
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

    # Fetch today's quiz_results rows (created by morning brief)
    quiz_rows = (
        supabase.table("quiz_results")
        .select("quiz_id, user_id, questions")
        .gte("sent_at", f"{today}T00:00:00+00:00")
        .execute()
    )

    if not quiz_rows.data:
        logger.info("quiz_conductor batch: no quiz_results rows for today — skip")
        return

    # Fetch profiles + learning_plans separately (no FK between quiz_results and those tables)
    user_ids = [r["user_id"] for r in quiz_rows.data]
    # Fetch profiles in one query
    profile_rows = (
        supabase.table("profiles")
        .select("id, email")
        .in_("id", user_ids)
        .execute()
    )
    profiles = {r["id"]: r for r in profile_rows.data}

    # Fetch active learning plans in one query
    plan_rows = (
        supabase.table("learning_plans")
        .select("user_id, milestones, current_milestone_index")
        .in_("user_id", user_ids)
        .eq("is_active", True)
        .execute()
    )
    plans = {r["user_id"]: r for r in plan_rows.data}

    # Collect users that have both a quiz row and an active plan
    users = []
    for quiz_row in quiz_rows.data:
        uid = quiz_row["user_id"]
        profile = profiles.get(uid)
        plan = plans.get(uid)
        if profile and plan:
            users.append({
                "id": uid,
                "email": profile["email"],
                "quiz_id": quiz_row["quiz_id"],
                "milestones": plan["milestones"],
                "current_milestone_index": plan["current_milestone_index"],
            })

    async def _run_one(user: dict) -> None:
            try:
                run_quiz_conductor(user)
            except Exception as exc:  # noqa: BLE001 — log and continue batch
                logger.error("quiz_conductor failed for user=%s: %s", user["id"], exc, exc_info=True)

    results = await asyncio.gather(
        *[_run_one(u) for u in users],
        return_exceptions=True,
    )
    failed = sum(1 for r in results if isinstance(r, Exception))
    if failed:
        logger.warning("quiz_conductor batch: %d/%d failed", failed, len(users))
    else:
        logger.info("quiz_conductor batch: %d users processed", len(users))
