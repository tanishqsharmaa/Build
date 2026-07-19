"""Agent 3b — Quiz Evaluator.

Public surface:
  score_quiz(questions, answers)                      -> float
  generate_feedback(topic, questions, answers, score) -> QuizResult
  advance_milestone(user_id)                          -> None
  send_result_email(user_email, result, topic)        -> None
  evaluate_and_route(user_id, quiz_id, answers)       -> QuizResult
"""
from pathlib import Path

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.agents.daily_checkin.schemas import QuizQuestion, QuizResult
from src.core.llm_client import get_llm
from src.db.client import get_supabase
from src.email.client import send_email

_EVAL_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "quiz_evaluator.md"


def _load_eval_prompt() -> str:
    return _EVAL_PROMPT_PATH.read_text(encoding="utf-8")


# ── Arithmetic scorer (no LLM) ────────────────────────────────────────────────


def score_quiz(questions: list[QuizQuestion], answers: list[int]) -> float:
    """Arithmetic scoring — no LLM needed.

    Args:
        questions: list of QuizQuestion objects (from DB).
        answers:   list of selected option indices, one per question (student input).

    Returns:
        Score as a float 0.0–100.0.  e.g. 3/5 correct → 60.0
    """
    if not questions:
        return 0.0
    correct = sum(
        1 for q, a in zip(questions, answers) if q.correct_index == a
    )
    return round(correct / len(questions) * 100, 1)


# ── LLM feedback generator ────────────────────────────────────────────────────


def generate_feedback(
    topic: str,
    questions: list[QuizQuestion],
    answers: list[int],
    score: float,
) -> QuizResult:
    """Call DeepSeek (temp=0) for per-question feedback + summary.

    The LLM does NOT calculate the score — that is already done by score_quiz().
    The LLM only writes human-readable feedback text.
    recommendation is derived in Python from score >= 70.
    """
    llm = get_llm(temperature=0.0)

    # Build structured context for the LLM
    qa_context = []
    for q, a in zip(questions, answers):
        qa_context.append({
            "question_id": q.question_id,
            "question": q.question,
            "options": [{"index": o.index, "text": o.text} for o in q.options],
            "selected_index": a,
            "is_correct": q.correct_index == a,
        })

    # We build a partial QuizResult from Python; the LLM fills per_question + summary_feedback
    class _FeedbackOnly(QuizResult.__class__.__bases__[0]):  # type: ignore[misc]
        """Minimal schema: only LLM-generated fields."""
        from pydantic import BaseModel as _B

        class _FeedbackOnlyModel(_B):
            per_question: list[dict]
            summary_feedback: str

    # Use a slim Pydantic model so the LLM only generates feedback fields
    from pydantic import BaseModel as _BaseModel

    class FeedbackOutput(_BaseModel):
        per_question: list[dict]
        summary_feedback: str

    parser = PydanticOutputParser(pydantic_object=FeedbackOutput)
    prompt = ChatPromptTemplate.from_messages([
        ("system", _load_eval_prompt()),
        (
            "human",
            "Topic: {topic}\n"
            "Overall score: {score}/100\n"
            "Questions and student answers:\n{qa_context}\n\n"
            "{format_instructions}",
        ),
    ])

    chain = prompt | llm | parser
    feedback: FeedbackOutput = invoke_llm_with_retry(chain, {
        "topic": topic,
        "score": score,
        "qa_context": str(qa_context),
        "format_instructions": parser.get_format_instructions(),
    })

    recommendation: str = "advance" if score >= 70.0 else "review"

    return QuizResult(
        per_question=feedback.per_question,
        overall_score=score,
        summary_feedback=feedback.summary_feedback,
        recommendation=recommendation,  # type: ignore[arg-type]
    )


# ── DB helpers ────────────────────────────────────────────────────────────────


def advance_milestone(user_id: str) -> None:
    """Increment current_milestone_index for the user's active learning plan."""
    supabase = get_supabase()

    # Read current index
    row = (
        supabase.table("learning_plans")
        .select("id, current_milestone_index, milestones")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    if not row.data:
        return

    plan_id = row.data["id"]
    new_index = row.data["current_milestone_index"] + 1
    total = len(row.data.get("milestones", []))

    # Clamp: never exceed last milestone index
    new_index = min(new_index, total - 1)

    from datetime import datetime, timezone
    (
        supabase.table("learning_plans")
        .update({
            "current_milestone_index": new_index,
        })
        .eq("id", plan_id)
        .execute()
    )


def _update_quiz_result(
    quiz_id: str,
    answers: list[int],
    result: QuizResult,
) -> None:
    """Write evaluation results back to the quiz_results row.

    Schema columns available: score, answers (JSONB), recommendation, submitted_at.
    feedback is stored inside the questions JSONB as questions.feedback.
    """
    from datetime import datetime, timezone
    supabase = get_supabase()
    (  
        supabase.table("quiz_results")
        .update({
            "answers": answers,
            "score": result.overall_score,
            "recommendation": result.recommendation,
            "submitted_at": datetime.now(tz=timezone.utc).isoformat(),
        })
        .eq("quiz_id", quiz_id)
        .execute()
    )


# ── Email ─────────────────────────────────────────────────────────────────────


def send_result_email(user_email: str, result: QuizResult, topic: str) -> None:
    """Send pass or review result email via Resend."""
    if result.recommendation == "advance":
        subject = f"🎉 You passed: {topic}!"
        heading = "🎉 Great work — you passed!"
        color = "#22c55e"
        message = "You scored <strong>{:.0f}%</strong> and unlocked the next milestone.".format(
            result.overall_score
        )
    else:
        subject = f"📖 Let's revisit: {topic}"
        heading = "📖 Let's spend more time on this topic"
        color = "#f59e0b"
        message = (
            "You scored <strong>{:.0f}%</strong>. "
            "Your plan has been updated to help you build a stronger foundation.".format(
                result.overall_score
            )
        )

    html = f"""
    <html>
    <body style="font-family: sans-serif; background: #0f172a; color: #e2e8f0; padding: 32px;">
      <h2 style="color: {color};">{heading}</h2>
      <p>{message}</p>
      <p style="color: #94a3b8;">{result.summary_feedback}</p>
      <hr style="border-color: #1e293b;" />
      <p style="color: #475569; font-size: 12px;">Powered by SkillBridge</p>
    </body>
    </html>
    """
    send_email(to=user_email, subject=subject, html=html)


# ── Orchestrator ──────────────────────────────────────────────────────────────


def evaluate_and_route(
    user_id: str,
    quiz_id: str,
    topic: str,
    questions: list[QuizQuestion],
    answers: list[int],
    user_email: str,
) -> QuizResult:
    """Score → feedback → DB update → email → return result.

    Called by the /submit FastAPI endpoint (Sprint 6).
    The conditional edge (advance vs replan) is implemented in quiz_graph.py.
    """
    score = score_quiz(questions, answers)
    result = generate_feedback(topic=topic, questions=questions, answers=answers, score=score)
    _update_quiz_result(quiz_id=quiz_id, answers=answers, result=result)
    send_result_email(user_email=user_email, result=result, topic=topic)

    if result.recommendation == "advance":
        advance_milestone(user_id=user_id)

    return result
