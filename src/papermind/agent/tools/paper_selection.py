import logging

from papermind.common.llm import get_llm
from papermind.agent.tools.paper_utils import get_formatted_candidate_papers
from papermind.agent.prompts import SELECT_AND_FETCH_PROMPT
from papermind.agent.schemas import SelectAndFetchOutputStructure
from papermind.agent.state import PaperMindState

logger = logging.getLogger(__name__)


def _extract_selected_papers(response: object) -> list[dict]:
    try:
        if isinstance(response, SelectAndFetchOutputStructure):
            return [p.model_dump() for p in response.selected_papers]
        if isinstance(response, dict):
            structured = response.get("structured_response")
            if isinstance(structured, SelectAndFetchOutputStructure):
                return [p.model_dump() for p in structured.selected_papers]
            selected = response.get("selected_papers", [])
            return selected if isinstance(selected, list) else []
    except Exception:
        logger.exception("paper_selection: failed to parse LLM response")
    return []


async def select_relevant_papers(state: PaperMindState) -> list[dict]:
    structured_llm = get_llm().with_structured_output(SelectAndFetchOutputStructure).with_retry(
        stop_after_attempt=3,
        wait_exponential_jitter=True,
    )
    response = await structured_llm.ainvoke([
        {"role": "system", "content": SELECT_AND_FETCH_PROMPT},
        {"role": "user", "content": (
            f"Topic: {state['user_topic']}\n\n"
            f"Research plan: {state['research_plan']}\n\n"
            f"Candidate papers: {get_formatted_candidate_papers(state['candidate_papers'])}"
        )},
    ])
    return _extract_selected_papers(response)
