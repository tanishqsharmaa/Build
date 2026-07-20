"""Unit tests for src/email/client.py — send_email() wrapper.

All tests mock the resend SDK — no real email is sent.
"""
from unittest.mock import patch, MagicMock


def test_send_email_calls_resend_api():
    """send_email() must call resend.Emails.send exactly once."""
    with patch("src.email.client.resend_sdk") as mock_resend, \
         patch("src.email.client.settings") as mock_settings:
        mock_settings.resend_api_key = "test-key"
        from src.email.client import send_email
        send_email(
            to="delivered@resend.dev",
            subject="Test",
            html="<p>hi</p>",
        )
    mock_resend.Emails.send.assert_called_once()


def test_send_email_sets_from_address():
    """send_email() must set the 'from' field to the SkillBridge brand address."""
    with patch("src.email.client.resend_sdk") as mock_resend, \
         patch("src.email.client.settings") as mock_settings:
        mock_settings.resend_api_key = "test-key"
        from src.email.client import send_email
        send_email(
            to="delivered@resend.dev",
            subject="Subject",
            html="<p>body</p>",
        )
    payload = mock_resend.Emails.send.call_args[0][0]
    assert payload["from"] == "SkillBridge <onboarding@resend.dev>"
