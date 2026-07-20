import logging

import resend as resend_sdk

from src.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html: str) -> None:
    """Send a transactional email via Resend SDK.

    Uses the service API key from Settings.
    In tests, pass to='delivered@resend.dev' to avoid real delivery.
    """
    resend_sdk.api_key = settings.resend_api_key
    try:
        resend_sdk.Emails.send({
            "from": "SkillBridge <onboarding@resend.dev>",
            "to": to,
            "subject": subject,
            "html": html,
        })
    except Exception:
        logger.warning("email skipped (Resend domain not verified): to=%s subj=%s", to, subject)
