import logging

from papermind.agent.tools.paper_selection import select_relevant_papers
from papermind.agent.tools.paper_utils import enrich_selected_papers
from papermind.agent.state import PaperMindState
from papermind.agent.tools.paper_fetch import fetch_papers

logger = logging.getLogger(__name__)


async def select_and_fetch(state: PaperMindState) -> PaperMindState:
    errors = state.get("errors", [])

    if not state.get("candidate_papers"):
        errors.append({"node": "select_and_fetch", "error": "No candidate papers to select from", "recoverable": True})
        return {**state, "fetched_papers": [], "errors": errors, "status": "extracting"}

    try:
        rel_papers = await select_relevant_papers(state)
    except Exception as e:
        logger.exception("select_and_fetch: LLM selection failed")
        errors.append({"node": "select_and_fetch", "error": f"LLM failed: {e}", "recoverable": False})
        return {**state, "fetched_papers": [], "errors": errors, "status": "extracting"}

    if not rel_papers:
        errors.append({"node": "select_and_fetch", "error": "LLM selected zero papers", "recoverable": True})
        return {**state, "fetched_papers": [], "errors": errors, "status": "extracting"}

    final_papers = enrich_selected_papers(rel_papers, state["candidate_papers"])
    final_papers, new_agent_messages = await fetch_papers(
        final_papers,
        papers_to_skip=state.get("papers_to_skip", []),
    )
    agent_messages = list(state.get("agent_messages", []))
    agent_messages.extend(new_agent_messages)

    failed_count = sum(
        1 for p in final_papers if p.get("fetch_status") in ("failed", "download_failed", "skipped")
    )
    if failed_count:
        errors.append({
            "node": "select_and_fetch",
            "error": f"{failed_count}/{len(final_papers)} papers failed to fetch",
            "recoverable": True,
        })

    return {
        **state,
        "fetched_papers": final_papers,
        "agent_messages": agent_messages,
        "errors": errors,
        "status": "extracting",
    }
