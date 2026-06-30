import logging
from typing import cast

from pydantic import BaseModel

from papermind.agent.state import PaperMindState
from papermind.common.llm import get_llm
from papermind.agent.prompts import CRITIQUE
from papermind.agent.nodes.draft_briefing import Briefing as BriefingModel

logger = logging.getLogger(__name__)


class Critique(BaseModel):
    citation_score: int
    novelty_score: int
    completeness_score: int
    overall_score: int
    citation_feedback: str
    novelty_feedback: str
    completeness_feedback: str
    revision_instructions: str
    passed: bool


def format_research_plan(research_plan: list[str]) -> str:
    return "\n".join(f"- {step}" for step in research_plan)


def format_paper_breakdowns(breakdowns: list[dict]) -> str:
    result = ""
    for i, p in enumerate(breakdowns):
        result += f"""
Paper {i + 1}:
  ID: {p['openalex_id']}
  Title: {p['title']}
  Contribution: {p['contribution']}
  Key result: {p['key_result']}
  Relevant to: {p['relevant_to']}
  Confidence: {p['confidence']}
---
"""
    return result


async def critique(state: PaperMindState) -> dict:
    errors = state.get("errors", [])

    try:
        briefing = state.get("draft_briefing")

        if not briefing:
            errors.append({"node": "critique", "error": "Empty draft briefing to critique", "recoverable": True})
            return {
                "critique": None,
                "critique_score": 0,
                "errors": errors,
                "status": "reviewing",
            }

        # Check for meaningful content regardless of type
        if isinstance(briefing, dict) and not briefing.get("executive_summary"):
            errors.append({"node": "critique", "error": "Draft briefing missing executive_summary", "recoverable": True})
            return {
                "critique": None,
                "critique_score": 0,
                "errors": errors,
                "status": "reviewing",
            }

        if isinstance(briefing, BriefingModel):
            b = briefing.model_dump()
        elif isinstance(briefing, dict):
            b = briefing
        else:
            b = {}

        user_message = f"""Topic: {state['user_topic']}

        Research plan sub-questions:
        {format_research_plan(state['research_questions'])}

        Briefing to critique:
        Executive Summary: {b.get('executive_summary', '')}

        Paper Breakdowns:
        {format_paper_breakdowns(b.get('paper_breakdowns', []))}

        Synthesis: {b.get('synthesis', '')}

        Gaps: {b.get('gaps', '')}

        Recommended Reading: {b.get('recommended_reading', '')}

        Data Quality Note: {b.get('data_quality_note', '')}
        """

        structured_llm = get_llm().with_structured_output(Critique)
        response = cast(Critique, await structured_llm.ainvoke([
                {"role": "system", "content": CRITIQUE},
                {"role": "user", "content": user_message}
        ]))

        critique_data = response.model_dump()

        return {
            "critique": critique_data,
            "critique_score": critique_data.get("overall_score", 0),
            "errors": errors,
            "status": "reviewing",
        }

    except Exception as e:
        logger.exception("critique: unexpected error")
        errors.append({"node": "critique", "error": str(e), "recoverable": False})
        return {
            "critique": None,
            "critique_score": 0,
            "errors": errors,
            "status": "reviewing",
        }
