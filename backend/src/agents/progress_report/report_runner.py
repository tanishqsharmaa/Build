"""Agent 4 runner — weekly progress report orchestrator.

Public surface:
  run_weekly_report(user)  -> WeeklyReport | None
  run_for_all_users()      -> None  (async, cron entry point)
"""
import asyncio
from datetime import date, datetime, timedelta, timezone

from src.agents.progress_report.nodes import (
    aggregate_scores,
    generate_linkedin_post,
    generate_report,
)
from src.agents.progress_report.schemas import WeeklyReport
from src.db.client import get_supabase
from src.email.client import send_email
from src.email.renderer import render_weekly_report

_SEMAPHORE = asyncio.Semaphore(10)
logger = logging.getLogger(__name__)


def _this_monday() -> str:
    """Return the Monday of the current week as an ISO date string (UTC)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return monday.isoformat()


def run_weekly_report(user: dict) -> dict | None:
    """Run Agent 4 for a single user.

    Returns:
        WeeklyReport dict on success.
        None if already generated this week (idempotency skip).

    user dict must have keys: id (str UUID), email (str)
    """
    supabase = get_supabase()
    user_id = user["id"]
    week_start = _this_monday()

    # ── Idempotency check ──
    existing = (
        supabase.table("weekly_reports")
        .select("id")
        .eq("user_id", user_id)
        .eq("week_start", week_start)
        .execute()
    )
    if existing.data:
        return None

    # ── Aggregate stats ──
    avg_quiz_score, milestones_completed, milestone_details = aggregate_scores(
        user_id, week_start
    )

    # ── Generate content ──
    report_html = generate_report(
        week_start, milestones_completed, avg_quiz_score, milestone_details
    )
    linkedin_post_text = generate_linkedin_post(
        milestone_details.get("topics", []),
        milestones_completed,
        avg_quiz_score,
    )

    # ── Build WeeklyReport ──
    report = WeeklyReport(
        week_start=week_start,
        milestones_completed=milestones_completed,
        avg_quiz_score=round(avg_quiz_score, 1),
        linkedin_post_text=linkedin_post_text,
        report_html=report_html,
    )

    # ── Store in DB ──
    supabase.table("weekly_reports").insert({
        "user_id": user_id,
        "week_start": week_start,
        "milestones_completed": report.milestones_completed,
        "avg_quiz_score": report.avg_quiz_score,
        "linkedin_post_text": report.linkedin_post_text,
        "report_html": report.report_html,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }).execute()

    # ── Render + send email ──
    html_email = render_weekly_report(report)
    send_email(
        to=user["email"],
        subject=f"Your SkillBridge Weekly Report — {week_start}",
        html=html_email,
    )

    return report.model_dump()


async def run_for_all_users() -> None:
    """Fetch all users with an active plan and run weekly report concurrently.

    Called by weekly_report_cron (Modal, wired in Sprint 8).
    asyncio.Semaphore(10) prevents DeepSeek rate-limit errors.
    """
    supabase = get_supabase()

    rows = (
        supabase.table("learning_plans")
        .select("user_id, profiles(id, email)")
        .eq("is_active", True)
        .execute()
    )

    async def _run_one(row: dict) -> None:
        async with _SEMAPHORE:
            user = {
                "id": row["user_id"],
                "email": row["profiles"]["email"],
            }
            try:
                result = run_weekly_report(user)
                status = "generated" if result else "skipped (idempotent)"
                logger.info("weekly_report user=%s: %s", user["id"], status)
            except Exception as exc:  # noqa: BLE001
                logger.error("weekly_report failed for user=%s: %s", user["id"], exc, exc_info=True)

    results = await asyncio.gather(
        *[_run_one(r) for r in rows.data],
        return_exceptions=True,
    )
    failed = sum(1 for r in results if isinstance(r, Exception))
    if failed:
        logger.warning("weekly_report batch: %d/%d failed", failed, len(rows.data))
    else:
        logger.info("weekly_report batch: %d users processed", len(rows.data))
