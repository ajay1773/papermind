from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from slowapi.errors import RateLimitExceeded

WEB_DIR = Path(__file__).resolve().parent
_templates = Jinja2Templates(directory=WEB_DIR / "templates")


async def briefing_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Return HTMX-friendly HTML for briefing form rate limits."""
    if request.method == "POST" and request.url.path.rstrip("/") == "/briefing":
        return _templates.TemplateResponse(
            request,
            "partials/briefing_result.html",
            {
                "topic": "",
                "error": (
                    f"Rate limit exceeded ({exc.detail}). "
                    "Each briefing uses multiple LLM calls — try again later."
                ),
                "briefing": {},
                "papers_fetched": [],
                "tools_used": [],
                "critique_score": 0,
                "iterations": 0,
                "agent_messages": [],
            },
            status_code=429,
        )

    return _templates.TemplateResponse(
        request,
        "partials/briefing_result.html",
        {
            "topic": "",
            "error": f"Rate limit exceeded: {exc.detail}",
            "briefing": {},
            "papers_fetched": [],
            "tools_used": [],
            "critique_score": 0,
            "iterations": 0,
            "agent_messages": [],
        },
        status_code=429,
    )
