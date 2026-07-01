import re
import uuid
from pathlib import Path
from urllib.parse import quote_plus

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from papermind.agent.graph import compiled_graph
from papermind.agent.initial_state import get_initial_state
from papermind.common.schemas import HealthResponse
from papermind.config import settings
from papermind.web.limiter import limiter

WEB_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=WEB_DIR / "templates")
templates.env.filters["urlencode"] = quote_plus


def _strip_openalex_ids(value: str) -> str:
    if not isinstance(value, str):
        return value
    return re.sub(r"\s*\(openalex_id:\s*W\d+(?:,\s*W\d+)*\)", "", value).strip()


def _parse_bullets(value: str) -> list:
    if not isinstance(value, str):
        return [value] if value else []
    items = []
    for line in value.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("- ", "* ", "• ")):
            items.append(line[2:].strip())
        elif len(line) > 2 and line[0].isdigit() and line[1] in ".)" and line[2] == " ":
            items.append(line[3:].strip())
        else:
            items.append(line)
    return items


templates.env.filters["strip_ids"] = _strip_openalex_ids
templates.env.filters["parse_bullets"] = _parse_bullets

router = APIRouter()

_MAX_TOPIC_LEN = 500


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", collection_count=0)


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "home.html")


@router.get("/homev2")
async def home_v2():
    return RedirectResponse(url="/", status_code=301)


@router.get("/upload-document")
async def upload_document():
    return RedirectResponse(url="/", status_code=301)


@router.get("/briefing")
async def research_briefing(request: Request):
    return templates.TemplateResponse(request, "research-briefing.html")


def _briefing_rate_limit_exempt() -> bool:
    return not settings.briefing_rate_limit_enabled


@router.post("/briefing")
@limiter.limit(settings.briefing_rate_limit, exempt_when=_briefing_rate_limit_exempt)
async def briefing_submit(request: Request, topic: str = Form(...)):
    topic = topic.strip()
    if not topic:
        return templates.TemplateResponse(
            request,
            "partials/briefing_result.html",
            {
                "topic": "",
                "error": "Topic is required.",
                "briefing": {},
                "papers_fetched": [],
                "tools_used": [],
                "critique_score": 0,
                "iterations": 0,
                "agent_messages": [],
            },
            status_code=400,
        )
    if len(topic) > _MAX_TOPIC_LEN:
        return templates.TemplateResponse(
            request,
            "partials/briefing_result.html",
            {
                "topic": topic[:80],
                "error": f"Topic too long (max {_MAX_TOPIC_LEN} characters).",
                "briefing": {},
                "papers_fetched": [],
                "tools_used": [],
                "critique_score": 0,
                "iterations": 0,
                "agent_messages": [],
            },
            status_code=400,
        )

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = get_initial_state(topic)
    
    try:
        async for _ in compiled_graph.astream(initial_state, config):
            pass
        final = compiled_graph.get_state(config)
        values = final.values
        briefing = values.get("draft_briefing", {})
        briefing_is_empty = (
            not briefing
            or (isinstance(briefing, dict)
                and not briefing.get("executive_summary")
                and not briefing.get("paper_breakdowns"))
        )
        agent_errors = values.get("errors", [])
        return templates.TemplateResponse(
            request,
            "partials/briefing_result.html",
            {
                "topic": topic,
                "briefing": briefing,
                "briefing_is_empty": briefing_is_empty,
                "agent_errors": agent_errors,
                "papers_fetched": values.get("fetched_papers", []),
                "tools_used": values.get("tools_used", []),
                "critique_score": values.get("critique_score", 0),
                "iterations": values.get("iterations", 0),
                "agent_messages": values.get("agent_messages", []),
            },
        )
    except Exception as e:
        error_msg = str(e) or type(e).__name__
        return templates.TemplateResponse(
            request,
            "partials/briefing_result.html",
            {
                "topic": topic,
                "error": error_msg,
                "briefing": {},
                "papers_fetched": [],
                "tools_used": [],
                "critique_score": 0,
                "iterations": 0,
                "agent_messages": [],
            },
        )
