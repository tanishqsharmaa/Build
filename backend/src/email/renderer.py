from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.agents.daily_checkin.schemas import MorningBrief
from src.agents.progress_report.schemas import WeeklyReport

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def render_morning_brief(brief: MorningBrief) -> str:
    """Render a MorningBrief to an HTML string using the Jinja2 template."""
    try:
        template = _env.get_template("morning_brief.html")
    except Exception:
        raise RuntimeError(
            "morning_brief.html template not found in "
            f"{_TEMPLATE_DIR}. Ensure the template file exists."
        )
    return template.render(brief=brief)


def render_weekly_report(report: WeeklyReport) -> str:
    """Render a WeeklyReport to an HTML string using the Jinja2 template."""
    try:
        template = _env.get_template("weekly_report.html")
    except Exception:
        raise RuntimeError(
            "weekly_report.html template not found in "
            f"{_TEMPLATE_DIR}. Ensure the template file exists."
        )
    return template.render(report=report)
