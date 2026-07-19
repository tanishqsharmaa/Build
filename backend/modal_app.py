"""modal_app.py — SkillBridge Modal deployment entrypoint.

This is the single file Modal reads for the entire deployment.

Local development (ephemeral URL, live-reload on save):
    modal serve modal_app.py

Production deployment (persistent URL):
    modal deploy modal_app.py

Registered functions (visible in `modal app list`):
    fastapi-app           — ASGI web endpoint
    morning-brief-cron    — 7:30 AM IST daily  (02:00 UTC)
    quiz-conductor-cron   — 4:00 PM IST daily  (10:30 UTC)
    weekly-report-cron    — Sunday 7:00 PM IST (13:30 UTC) — Sprint 8 stub

Prerequisites (one-time, in Modal dashboard):
    Create secret named "skillbridge-secrets" with all keys from .env.example
"""
import modal

import src.core.observability  # noqa: F401 — sets LANGCHAIN_TRACING_V2 + API key at import

# ── Container image ─────────────────────────────────────────────────────────
# pip_install_from_pyproject installs all locked deps.
# add_local_python_source("src") makes the local src/ package importable
# inside the container as `import src` / `from src.xxx import yyy`.
# This is the Modal 1.5.x API — replaces the deprecated copy_local_dir.
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_pyproject("pyproject.toml")
    .add_local_python_source("src")
)

# ── Secrets (from Modal dashboard → https://modal.com/secrets) ───────────────
# All keys in .env must exist in the "skillbridge-secrets" Modal secret.
secrets = [modal.Secret.from_name("skillbridge-secrets")]

# ── Modal App ────────────────────────────────────────────────────────────────
app = modal.App(name="skillbridge", image=image, secrets=secrets)


# ── ASGI web endpoint ─────────────────────────────────────────────────────────
@app.function()
@modal.asgi_app()
def fastapi_app():
    """Mount the SkillBridge FastAPI app. URL printed by `modal serve`."""
    from src.api.main import app as api  # lazy import — runs inside container
    return api


# ── Cron 1: Morning Brief ─────────────────────────────────────────────────────
# 7:30 AM IST = 02:00 UTC  →  cron "0 2 * * *"
@app.function(schedule=modal.Cron("0 2 * * *"))
async def morning_brief_cron():
    """Send morning cheat-sheet email to all active users at 7:30 AM IST."""
    from src.agents.daily_checkin.morning_brief import run_for_all_users
    await run_for_all_users()


# ── Cron 2: Quiz Conductor ───────────────────────────────────────────────────
# 4:00 PM IST = 10:30 UTC  →  cron "30 10 * * *"
@app.function(schedule=modal.Cron("30 10 * * *"))
async def quiz_conductor_cron():
    """Generate MCQs and email quiz links to all active users at 4:00 PM IST."""
    from src.agents.daily_checkin.quiz_conductor import send_links_for_all_users
    await send_links_for_all_users()


# ── Cron 3: Weekly Report ────────────────────────────────────────────────────
# Sunday 7:00 PM IST = 13:30 UTC  →  cron "30 13 * * 0"
@app.function(schedule=modal.Cron("30 13 * * 0"))
async def weekly_report_cron():
    """Generate + email weekly progress reports every Sunday 7:00 PM IST."""
    from src.agents.progress_report.report_runner import run_for_all_users
    await run_for_all_users()
