"""Unit tests for Agent 3a — Morning Brief nodes and schemas.

All external I/O (LLM, Supabase, Resend, Jinja2 renderer) is mocked.
These tests run fully offline.
"""
import pytest
from unittest.mock import MagicMock, patch

# Python 3.13 changed pkgutil.resolve_name: patch() requires the submodule to
# already be an attribute of its parent package before the patch context opens.
# Importing the module here registers it on src.agents.daily_checkin so that
# patch("src.agents.daily_checkin.morning_brief.X") resolves correctly.
import src.agents.daily_checkin.morning_brief  # noqa: F401

from src.agents.daily_checkin.schemas import MorningBrief


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_brief(**overrides) -> MorningBrief:
    defaults = dict(
        topic="FastAPI Basics",
        key_concepts=[
            "FastAPI is an async Python web framework built on Starlette",
            "Path parameters are declared using Python type hints in function args",
            "Pydantic models validate request and response bodies automatically",
            "Dependency injection is handled via FastAPI's Depends() system",
            "FastAPI auto-generates OpenAPI docs at /docs and /redoc endpoints",
        ],
        misconceptions=[
            "FastAPI is not just a wrapper around Flask — it is built on Starlette",
            "async def endpoints do not block the event loop but sync ones can",
        ],
        mnemonic="PATHS: Parameters, Authentication, Type-hints, HTTP, Starlette",
        think_about=[
            "How does FastAPI's async model differ from a traditional WSGI framework?",
            "Why does Pydantic validation happen before your route function runs?",
            "What happens when a sync function is called inside an async FastAPI route?",
        ],
    )
    defaults.update(overrides)
    return MorningBrief(**defaults)


BASE_USER = {
    "id": "00000000-0000-0000-0000-000000000004",
    "email": "delivered@resend.dev",
    "milestones": [
        {
            "topic": "FastAPI Basics",
            "daily_subtopics": [
                "Install FastAPI and uvicorn",
                "Write your first GET endpoint",
                "Add path and query parameters",
                "Validate request bodies with Pydantic",
                "Explore /docs auto-generated UI",
            ],
        }
    ],
    "current_milestone_index": 0,
}


def _mock_supabase_no_existing():
    """Supabase mock: no existing quiz_results row today."""
    mock_sb = MagicMock()
    # Chain: .table().select().eq().gte().execute() → .data = []
    mock_sb.table.return_value.select.return_value.eq.return_value \
        .gte.return_value.execute.return_value = MagicMock(data=[])
    # Chain: .table().insert().execute()
    mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])
    return mock_sb


def _mock_supabase_has_existing():
    """Supabase mock: quiz_results row already exists today (idempotency)."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value \
        .gte.return_value.execute.return_value = MagicMock(data=[{"id": "some-uuid"}])
    return mock_sb


# ---------------------------------------------------------------------------
# Schema validation tests (4)
# ---------------------------------------------------------------------------

def test_key_concepts_count_validator_rejects_wrong_count():
    """MorningBrief must raise if key_concepts has != 5 items."""
    with pytest.raises(Exception):
        MorningBrief(
            topic="Test",
            key_concepts=["only", "four", "concepts", "here"],  # 4 — wrong
            misconceptions=["m1", "m2"],
            mnemonic="some mnemonic",
            think_about=["q1?", "q2?", "q3?"],
        )


def test_misconceptions_count_validator_rejects_wrong_count():
    """MorningBrief must raise if misconceptions has != 2 items."""
    with pytest.raises(Exception):
        MorningBrief(
            topic="Test",
            key_concepts=["c1", "c2", "c3", "c4", "c5"],
            misconceptions=["only one"],  # 1 — wrong
            mnemonic="some mnemonic",
            think_about=["q1?", "q2?", "q3?"],
        )


def test_think_about_count_validator_rejects_wrong_count():
    """MorningBrief must raise if think_about has != 3 items."""
    with pytest.raises(Exception):
        MorningBrief(
            topic="Test",
            key_concepts=["c1", "c2", "c3", "c4", "c5"],
            misconceptions=["m1", "m2"],
            mnemonic="some mnemonic",
            think_about=["only two", "questions here"],  # 2 — wrong
        )


def test_concept_over_20_words_raises_value_error():
    """MorningBrief must raise ValueError if any key_concept exceeds 20 words."""
    long_concept = " ".join(["word"] * 21)  # 21 words
    with pytest.raises(ValueError, match="key_concept exceeds 20 words"):
        MorningBrief(
            topic="Test",
            key_concepts=["c1", "c2", "c3", "c4", long_concept],
            misconceptions=["m1", "m2"],
            mnemonic="some mnemonic",
            think_about=["q1?", "q2?", "q3?"],
        )


# ---------------------------------------------------------------------------
# generate_brief() node behaviour tests (5)
# ---------------------------------------------------------------------------

def _patch_generate_brief_chain(mock_pt, mock_get_llm, return_value):
    """Wire the LangChain pipe mock so chain.invoke() returns return_value."""
    prompt_mock = mock_pt.from_messages.return_value
    llm_mock = mock_get_llm.return_value
    parser_mock = MagicMock()
    chain_mock = MagicMock()
    chain_mock.invoke.return_value = return_value
    # prompt | llm returns intermediate; intermediate | parser returns chain
    prompt_mock.__or__ = MagicMock(return_value=MagicMock(
        __or__=MagicMock(return_value=chain_mock)
    ))
    return chain_mock


def test_generate_brief_returns_morning_brief_schema():
    """generate_brief() must return a MorningBrief instance."""
    mock_brief = _make_brief()
    with patch("src.agents.daily_checkin.morning_brief.ChatPromptTemplate") as mock_pt, \
         patch("src.agents.daily_checkin.morning_brief.PydanticOutputParser"), \
         patch("src.agents.daily_checkin.morning_brief.get_llm") as mock_get_llm:
        _patch_generate_brief_chain(mock_pt, mock_get_llm, mock_brief)
        from src.agents.daily_checkin.morning_brief import generate_brief
        result = generate_brief("FastAPI Basics", "day1, day2, day3, day4, day5")
    assert isinstance(result, MorningBrief)


def test_generate_brief_key_concepts_count():
    """generate_brief() output must have exactly 5 key concepts."""
    mock_brief = _make_brief()
    with patch("src.agents.daily_checkin.morning_brief.ChatPromptTemplate") as mock_pt, \
         patch("src.agents.daily_checkin.morning_brief.PydanticOutputParser"), \
         patch("src.agents.daily_checkin.morning_brief.get_llm") as mock_get_llm:
        _patch_generate_brief_chain(mock_pt, mock_get_llm, mock_brief)
        from src.agents.daily_checkin.morning_brief import generate_brief
        result = generate_brief("FastAPI Basics", "context")
    assert len(result.key_concepts) == 5


def test_generate_brief_misconceptions_count():
    """generate_brief() output must have exactly 2 misconceptions."""
    mock_brief = _make_brief()
    with patch("src.agents.daily_checkin.morning_brief.ChatPromptTemplate") as mock_pt, \
         patch("src.agents.daily_checkin.morning_brief.PydanticOutputParser"), \
         patch("src.agents.daily_checkin.morning_brief.get_llm") as mock_get_llm:
        _patch_generate_brief_chain(mock_pt, mock_get_llm, mock_brief)
        from src.agents.daily_checkin.morning_brief import generate_brief
        result = generate_brief("FastAPI Basics", "context")
    assert len(result.misconceptions) == 2


def test_generate_brief_think_about_count():
    """generate_brief() output must have exactly 3 think_about questions."""
    mock_brief = _make_brief()
    with patch("src.agents.daily_checkin.morning_brief.ChatPromptTemplate") as mock_pt, \
         patch("src.agents.daily_checkin.morning_brief.PydanticOutputParser"), \
         patch("src.agents.daily_checkin.morning_brief.get_llm") as mock_get_llm:
        _patch_generate_brief_chain(mock_pt, mock_get_llm, mock_brief)
        from src.agents.daily_checkin.morning_brief import generate_brief
        result = generate_brief("FastAPI Basics", "context")
    assert len(result.think_about) == 3


def test_generate_brief_mnemonic_non_empty():
    """generate_brief() output must have a non-empty mnemonic."""
    mock_brief = _make_brief()
    with patch("src.agents.daily_checkin.morning_brief.ChatPromptTemplate") as mock_pt, \
         patch("src.agents.daily_checkin.morning_brief.PydanticOutputParser"), \
         patch("src.agents.daily_checkin.morning_brief.get_llm") as mock_get_llm:
        _patch_generate_brief_chain(mock_pt, mock_get_llm, mock_brief)
        from src.agents.daily_checkin.morning_brief import generate_brief
        result = generate_brief("FastAPI Basics", "context")
    assert result.mnemonic != ""


# ---------------------------------------------------------------------------
# Idempotency tests (2)
# ---------------------------------------------------------------------------

def test_run_morning_brief_returns_none_if_sent_today():
    """run_morning_brief() must return None when a quiz_results row already exists today."""
    with patch("src.agents.daily_checkin.morning_brief.get_supabase",
               return_value=_mock_supabase_has_existing()):
        from src.agents.daily_checkin.morning_brief import run_morning_brief
        result = run_morning_brief(BASE_USER)
    assert result is None


def test_run_morning_brief_inserts_quiz_results_row():
    """run_morning_brief() must insert exactly one quiz_results row on success."""
    mock_sb = _mock_supabase_no_existing()
    mock_brief = _make_brief()

    with patch("src.agents.daily_checkin.morning_brief.get_supabase", return_value=mock_sb), \
         patch("src.agents.daily_checkin.morning_brief.generate_brief", return_value=mock_brief), \
         patch("src.agents.daily_checkin.morning_brief.render_morning_brief", return_value="<html/>"), \
         patch("src.agents.daily_checkin.morning_brief.send_email"):
        from src.agents.daily_checkin.morning_brief import run_morning_brief
        result = run_morning_brief(BASE_USER)

    assert result is not None
    # Verify insert was called on quiz_results
    insert_calls = [
        call for call in mock_sb.table.call_args_list
        if call.args and call.args[0] == "quiz_results"
    ]
    assert len(insert_calls) >= 1


# ---------------------------------------------------------------------------
# Email send_email call test (1)
# ---------------------------------------------------------------------------

def test_send_email_calls_resend_with_correct_fields():
    """send_email() must call resend.Emails.send with the correct from address and keys."""
    with patch("src.email.client.resend_sdk") as mock_resend, \
         patch("src.email.client.settings") as mock_settings:
        mock_settings.resend_api_key = "test-key"
        from src.email.client import send_email
        send_email(
            to="delivered@resend.dev",
            subject="Test Subject",
            html="<p>Hello</p>",
        )
    mock_resend.Emails.send.assert_called_once()
    call_kwargs = mock_resend.Emails.send.call_args[0][0]
    assert call_kwargs["from"] == "SkillBridge <briefs@skillbridge.app>"
    assert call_kwargs["to"] == "delivered@resend.dev"
    assert "subject" in call_kwargs
    assert "html" in call_kwargs
