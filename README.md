# SkillBridge — Multi-Agent Adaptive Learning System

> **"ChatGPT tells you what to learn. SkillBridge sends you a cheat sheet at breakfast, tests you after school, and automatically rewrites your roadmap when you fail."**

**SDG 4 — Quality Education** · 

---

## What It Does

SkillBridge is a **multi-agent LangGraph system** that doesn't just generate a static learning plan — it takes **daily action** and **adapts when you fall behind**.

Every day, without you opening the app:

| Time | What happens |
|------|-------------|
| **7:30 AM IST** | Morning cheat sheet email — 5 key concepts, 2 misconceptions, 1 mnemonic, 3 practice questions |
| **Evening** | You study from your personalized plan (free YouTube/GitHub resources assigned by AI) |
| **4:00 PM IST** | Quiz link email — 5 MCQs on today's topic |
| **After submit** | Quiz scored instantly. Score ≥ 70% → advance. Score < 70% → **plan rewrites itself** with extra review |
| **Sunday 7 PM IST** | Weekly progress digest + AI-crafted LinkedIn celebration post |

---

## 4-Agent Architecture

```
┌──────────────────────────────────────────────────────┐
│                   LangGraph StateGraph                │
│                                                      │
│  Agent 1: Skill Gap Analyzer                         │
│    RAG over real job market data (pgvector) → finds  │
│    exactly what skills you're missing                │
│                        ↓                             │
│  Agent 2: Learning Path Planner                      │
│    Decomposes gaps into weekly milestones with free   │
│    YouTube/GitHub resources for each topic           │
│                        ↓                             │
│  Agent 3: Daily Check-In (two Modal crons)           │
│    3a. Morning Brief → cheat sheet email             │
│    3b. Quiz Conductor → 5 MCQs → evaluate →          │
│        🟢 score ≥ 70%: advance to next topic          │
│        🔴 score < 70%: replanner rewrites your plan   │
│                        ↓                             │
│  Agent 4: Progress Report                            │
│    Sunday digest + LinkedIn celebration post         │
│    with one-click "Copy & Post" button               │
└──────────────────────────────────────────────────────┘
```

The **replanner subgraph** is the core innovation: it surgically rewrites only the failed milestone + the next one (not the entire plan), with a hard cap of 3 rewrites per topic.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | SvelteKit + Tailwind CSS (Hybrid SSR, Vercel) |
| **Backend** | FastAPI on Modal (ASGI + 3 scheduled crons) |
| **Agent Framework** | LangGraph StateGraph with conditional edges |
| **LLM** | DeepSeek V4 Flash (langchain-deepseek) |
| **Database** | Supabase PostgreSQL + pgvector |
| **RAG Embeddings** | gemini-embedding-001 (Google AI — one-time setup) |
| **Email** | Resend (HTML templates, async batch delivery) |
| **Tracing** | LangSmith (all agent nodes traced) |
| **Scheduling** | Modal Cron (7:30 AM + 4:00 PM IST + Sunday) |
| **Cost** | ~$0/month at demo scale (Modal $30 free credits) |

---

## Project Structure

```
backend/                     # FastAPI + LangGraph on Modal
├── src/
│   ├── agents/              # 4 agents: skill_gap, learning_planner, daily_checkin, progress_report
│   ├── retrieval/           # pgvector RAG pipeline
│   ├── prompts/             # Amit Tiwari 6-part prompt templates (.md files)
│   ├── api/                 # FastAPI routers: /analyze, /plan, /quiz, /report
│   ├── email/               # Resend client + Jinja2 HTML templates
│   ├── db/                  # Supabase client + schema.sql
│   └── core/                # Config, LLM client (retry backoff), LangSmith observability
├── tests/                   # 74 unit + 26 integration tests
├── evals/                   # Agent quality gates
├── scripts/                 # One-time: embed job_skills dataset
└── modal_app.py             # Modal entry point: ASGI endpoint + 3 crons

frontend/                    # SvelteKit on Vercel
└── src/
    ├── routes/              # / · /onboarding · /dashboard · /quiz · /results
    ├── lib/components/      # MilestoneCard · ProgressBar · LinkedInPostCard · QuizOption
    ├── lib/api/             # FastAPI HTTP wrappers
    └── lib/supabase.js      # Supabase client

../documentation/            # Planning docs, sprint plans, error log, auth status
```

---

## How a Student Uses It

1. **Onboard** — Enter your career goal, current skills, and weekly study hours
2. **Get your plan** — AI analyzes gaps against real job market data, generates weekly milestones
3. **Receive morning briefs** — Cheat sheet in your inbox at 7:30 AM every day
4. **Take daily quizzes** — Quiz link arrives at 4:00 PM, get scored instantly
5. **Watch it adapt** — Fail a quiz? Your plan gets rewritten with review material
6. **Track progress** — Dashboard shows milestones, scores, and a LinkedIn post to celebrate wins
7. **Get weekly reports** — Sunday digest summarizes your week + generates a LinkedIn post

---

## Local Development

```bash
# Backend (requires Modal account)
cd backend
modal serve modal_app.py              # Hot-reload tunnel on port 8000

# Frontend
cd frontend
npm install
npm run dev                           # HMR dev server on port 5173
```

Set environment variables as shown in `backend/.env.example` and `frontend/.env.local.example`.

---

## Testing

| Layer | Command | Coverage |
|-------|---------|----------|
| Backend unit | `pytest tests/unit/ -v` | 74 tests |
| Backend integration | `pytest tests/integration/ -v` | 26 tests |
| Agent evals (gated) | `RUN_EVALS=1 pytest evals/ -v` | Quality gates on LLM output |
| Frontend (Vitest) | `npm run test` (in `frontend/`) | 35 tests |
| Frontend build | `npm run build` | 350 modules, 0 errors |

---

## Current Status

**Sprint 10 — Evidence, PPT, Submission** (in progress)

- ✅ Backend: All 4 agents built + tested (74 unit, 26 integration)
- ✅ Frontend: All 5 routes built + styled (35 Vitest tests)
- ✅ Modal: Deployed — web endpoint + 3 crons live
- ✅ Codebase audit: Security hardening, bug fixes, perf, UX resilience
- 🔄 Vercel: Deployed with 502 env var bug (process.env fix applied, pending verification)
- 🔄 Auth: Deferred (hardcoded test user, clean drop-in path documented)

See [`../documentation/sprint_tracker.md`](../documentation/sprint_tracker.md) for full sprint history.

---

## Documentation

- [Project Idea & Vision](../documentation/project_idea.md)
- [System Design (Alex Xu 4-Step)](../documentation/system_design.md)
- [Project Structure](../documentation/project_structure.md)
- [Live Project Map](../documentation/project_map.md)
- [10-Sprint Implementation Plan](../documentation/plan/implementation_plan.md)
- [Auth Status](../documentation/auth_status.md)
- [Error Log](../documentation/error_log.md)

---



