import json
import logging
from typing import cast

from papermind.agent.nodes.critique import Critique
from papermind.agent.state import PaperMindState
from papermind.common.llm import get_llm
from papermind.agent.prompts import REVISE
from papermind.agent.nodes.draft_briefing import Briefing, format_extracted_findings

logger = logging.getLogger(__name__)

async def revise(state: PaperMindState) -> dict:
    errors = state.get("errors", [])
    iterations = state.get("iterations", 0)

    try:
        draft = state.get("draft_briefing")
        critique_data = state.get("critique") or {}

        if not draft:
            errors.append({"node": "revise", "error": "Empty draft to revise", "recoverable": True})
            return {
                "draft_briefing": draft,
                "iterations": iterations + 1,
                "errors": errors,
                "status": "reviewing",
            }

        if isinstance(draft, Briefing):
            draft_text = draft.model_dump_json(indent=2)
        elif isinstance(draft, dict):
            draft_text = json.dumps(draft, indent=2)
        else:
            draft_text = str(draft)

        critique_obj = state.get("critique")

        if isinstance(critique_obj, Critique):
            critique_data = critique_obj.model_dump()
        elif isinstance(critique_obj, dict):
            critique_data = critique_obj
        else:
            critique_data = {}

        user_message = f"""
            Original briefing: {draft_text}

            Critique feedback:
            Citation feedback: {critique_data.get('citation_feedback', '')}
            Novelty feedback: {critique_data.get('novelty_feedback', '')}
            Completeness feedback: {critique_data.get('completeness_feedback', '')}
            Revision instructions: {critique_data.get('revision_instructions', '')}

            Extracted findings (source of truth):
            {format_extracted_findings(state['extracted_findings'])}
        """
        structured_llm = get_llm().with_structured_output(Briefing)
        response = cast(Briefing, await structured_llm.ainvoke([
            {"role": "system", "content": REVISE},
            {"role": "user", "content": user_message}
        ]))

        valid_ids = {p["openalex_id"] for p in state["extracted_findings"]}
        hallucinated = [
            b.openalex_id for b in response.paper_breakdowns
            if b.openalex_id not in valid_ids
        ]

        if hallucinated:
            errors.append({
                "node": "revise",
                "error": f"Hallucinated papers in revision: {hallucinated}",
                "recoverable": True
            })
            return {
                "draft_briefing": state.get("draft_briefing"),
                "iterations": iterations + 1,
                "errors": errors,
                "status": "reviewing",
            }

        return {
            "draft_briefing": response.model_dump(),
            "iterations": iterations + 1,
            "errors": errors,
            "status": "reviewing",
        }

    except Exception as e:
        logger.exception("revise: unexpected error")
        errors.append({"node": "revise", "error": str(e), "recoverable": False})
        return {
            "draft_briefing": state.get("draft_briefing"),
            "iterations": iterations + 1,
            "errors": errors,
            "status": "reviewing",
        }
