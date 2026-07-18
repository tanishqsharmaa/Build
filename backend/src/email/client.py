import resend as resend_sdk

from src.core.config import settings


def send_email(to: str, subject: str, html: str) -> None:
    """Send a transactional email via Resend SDK.

    Uses the service API key from Settings.
    In tests, pass to='delivered@resend.dev' to avoid real delivery.
    """
    resend_sdk.api_key = settings.resend_api_key
    resend_sdk.Emails.send({
        "from": "SkillBridge <briefs@skillbridge.app>",
        "to": to,
        "subject": subject,
        "html": html,
    })
