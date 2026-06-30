import logging
from typing import Literal

from pydantic import BaseModel, Field

from papermind.agent.state import PaperMindState
from papermind.common.llm import get_llm
from papermind.agent.prompts import DRAFT_BRIEFING

logger = logging.getLogger(__name__)


class PaperBreakdown(BaseModel):
    openalex_id: str = Field(description="OpenAlex ID of the paper")
    title: str = Field(description="Full title of the paper")
    contribution: str = Field(description="One sentence summary of the paper's main claim")
    key_result: str = Field(description="Specific benchmark number or metric. If not available, say 'not available'")
    relevant_to: str = Field(description="The specific sub-question from the research plan this paper answers")
    confidence: Literal["high (full text)", "limited (tldr only)"] = Field(description="'high (full text)' if source_type is full_text, 'limited (tldr only)' if source_type is tldr_only")


class Briefing(BaseModel):
    executive_summary: str = Field(description='2-3 sentences: what is the overall state of this topic')
    paper_breakdowns: list[PaperBreakdown]
    synthesis: str = Field(description='what do these papers collectively tell us')
    gaps: str = Field(description='what sub-questions remain unanswered by these papers')
    recommended_reading: str = Field(description='which paper to read first and why')
    data_quality_note: str = Field(description='honest note about how many papers were tldr_only')


def format_extracted_findings(extracted_findings: list[dict]) -> str:
    findings_string = ""
    for i, paper in enumerate(extracted_findings):
        findings_string += f"""
Paper {i + 1}:
  ID: {paper.get('openalex_id', 'not available')}
  Title: {paper.get('title', 'not available')}
  Main claim: {paper.get('main_claim', 'not available')}
  Key results: {paper.get('key_results', 'not available')}
  Novelty: {paper.get('novelty', 'not available')}
  Limitations: {paper.get('limitations', 'not available')}
  Relevant to: {paper.get('relevant_to', 'not available')}
  Source type: {paper.get('source_type', 'not available')}
  Confidence: {paper.get('confidence', 'unknown')}\n
---
"""
    return findings_string


def format_research_questions(research_questions: list[str]) -> str:
    return "\n".join(f"- {step}" for step in research_questions)


async def draft_briefing(state: PaperMindState) -> dict:
    errors = state.get("errors", [])
    topic = state.get("user_topic", "unknown topic")
    findings = state.get("extracted_findings", [])

    if not findings:
        errors.append({"node": "draft_briefing", "error": "No findings to draft from", "recoverable": True})
        briefing = f"## Research Briefing: {topic.title()}\n\nNo findings were available to generate a briefing."
        return {"draft_briefing": briefing, "errors": errors, "status": "reviewing"}

    try:
        structured_llm = get_llm().with_structured_output(Briefing)
        user_message = f"""Topic: {state['user_topic']}
        
        Research plan sub-questions:
        {format_research_questions(state['research_questions'])}

        Extracted findings:
        {format_extracted_findings(state['extracted_findings'])}"""

        response = await structured_llm.ainvoke([
                {"role": "system", "content": DRAFT_BRIEFING},
                {"role": "user", "content": user_message}
        ])

        return {
                **state,
                "draft_briefing": response.model_dump(),
                "status": "reviewing"
        }

    except Exception as e:
        logger.exception("draft_briefing: unexpected error")
        errors.append({"node": "draft_briefing", "error": str(e), "recoverable": False})
        briefing = f"## Research Briefing: {topic.title()}\n\nFailed to generate briefing due to an internal error."
        return {"draft_briefing": briefing, "errors": errors, "status": "reviewing"}
