import json
import logging
from typing import Any, cast

from papermind.mcp.client import get_mcp_tool
from papermind.agent.state import PaperMindState

logger = logging.getLogger(__name__)


def _parse_tool_response(result: Any) -> list[dict]:
    if isinstance(result, list):
        return cast(list[dict], result)
    if isinstance(result, str):
        parsed = json.loads(result)
        return cast(list[dict], parsed if isinstance(parsed, list) else [parsed])
    return []


async def search_papers(state: PaperMindState) -> PaperMindState:
    errors = state.get("errors", [])

    try:
        search_tool = await get_mcp_tool("search_papers_openalex")
        invoke_args: dict = {
            "query": state["suggested_query"],
            "days_back": state["date_range_days"],
            "max_results": state["target_paper_count"],
        }
        concept_ids = state.get("concept_ids") or []
        if concept_ids:
            invoke_args["concept_ids"] = concept_ids
        result = await search_tool.ainvoke(invoke_args)
        papers = _parse_tool_response(result)
    except Exception as e:
        logger.exception("search_papers: failed")
        errors.append({"node": "search_papers", "error": str(e), "recoverable": False})
        return {**state, "candidate_papers": [], "errors": errors, "status": "fetching"}

    return {**state, "candidate_papers": papers, "errors": errors, "status": "fetching"}
