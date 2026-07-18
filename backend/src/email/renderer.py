from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.agents.daily_checkin.schemas import MorningBrief

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def render_morning_brief(brief: MorningBrief) -> str:
    """Render a MorningBrief to an HTML string using the Jinja2 template."""
    template = _env.get_template("morning_brief.html")
    return template.render(brief=brief)
