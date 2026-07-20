"""SkillBridge FastAPI application — Sprint 6.app.include_router(session.router, prefix="/session", tags=["Session — Daily"])

Endpoints:
    POST /analyze           → Agent 1 (Skill Gap Analyzer)
    POST /plan              → Agent 2 (Learning Path Planner)
    GET  /quiz/{quiz_id}    → fetch pre-generated MCQs
    POST /quiz/submit       → Agent 3b (Quiz Evaluator + conditional edge)
    GET  /report/{user_id}  → Agent 4 stub (Sprint 8)
    GET  /health            → liveness probe

This module is imported by modal_app.py via:
    from src.api.main import app as api
"""
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.api.routers import analyze, plan, quiz, report, session
from src.core.config import settings

app = FastAPI(
    title="SkillBridge API",
    description=(
        "Multi-Agent Adaptive Learning System — "
        "AICTE AI Automation & Intelligent Solutions, IBM SkillsBuild 2026"
    ),
    version="0.1.0",
)

# ── CORS (env-driven, no wildcard in production) ──────────────────────────
origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate limiter: 5 POST/min per IP, in-memory token bucket ───────────────
# ponytail: in-memory, not shared across Modal containers. Add redis-backed
# limiter if per-IP sync across replicas matters.
_BUCKET: dict[str, tuple[float, int]] = {}  # ip -> (window_start, count)
_RATE_WINDOW = 60.0   # 1 minute
_RATE_LIMIT = 10      # max POST requests per window (10 covers full integration test suite)
_RATE_EXPIRY = 300.0  # purge stale entries every 5 min
_last_purge = time.monotonic()


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        global _last_purge
        if request.method == "POST":
            now = time.monotonic()
            # Periodic purge: drop entries older than _RATE_EXPIRY
            if now - _last_purge > _RATE_EXPIRY:
                cutoff = now - _RATE_WINDOW
                stale = [ip for ip, (t, _) in _BUCKET.items() if t < cutoff]
                for ip in stale:
                    del _BUCKET[ip]
                _last_purge = now

            ip = _get_client_ip(request)
            window_start, count = _BUCKET.get(ip, (now, 0))
            if now - window_start > _RATE_WINDOW:
                window_start = now
                count = 0
            if count >= _RATE_LIMIT:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Try again in a minute."},
                )
            _BUCKET[ip] = (window_start, count + 1)

        return await call_next(request)


app.add_middleware(RateLimitMiddleware)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(analyze.router, prefix="/analyze", tags=["Agent 1 — Skill Gap"])
app.include_router(plan.router,    prefix="/plan",    tags=["Agent 2 — Learning Planner"])
app.include_router(session.router, prefix="/session", tags=["Session — Daily"])
app.include_router(quiz.router,    prefix="/quiz",    tags=["Agent 3b — Quiz"])
app.include_router(report.router,  prefix="/report",  tags=["Agent 4 — Report (stub)"])


@app.get("/health", tags=["infra"])
async def health() -> dict:
    """Liveness probe — used by Modal and Vercel to confirm the app is up."""
    return {"status": "ok", "service": "skillbridge-api"}
