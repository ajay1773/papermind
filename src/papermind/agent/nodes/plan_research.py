import logging
from typing import cast

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from papermind.agent.state import PaperMindState
from papermind.agent.prompts import PLAN_RESEARCH_PROMPT
from papermind.common.llm import get_llm

logger = logging.getLogger(__name__)


class PlanResearchLLMOutput(BaseModel):
    research_plan: list[str] = Field(
        description="The research plan steps."
    )
    research_questions: list[str] = Field(
        description="Research plan sub questions"
    )
    suggested_query: str = Field(
        description="A single OpenAlex search query. One quoted core concept + 1-2 domain keywords. Example: \"large language models\" evaluation benchmark"
    )
    concept_ids: list[str] = Field(
        default_factory=list,
        description="1-2 OpenAlex concept IDs to restrict domain. E.g. ['C41008148', 'C11413529'] for CS + NLP topics."
    )
    date_range_days: int = Field(
        description="Number of days back to search. Max 730 (2 years)."
    )
    target_paper_count: int = Field(
        description="Number of papers to fetch. Between 10 and 25."
    )


async def plan_research(state: PaperMindState) -> PaperMindState:
    errors = state.get("errors", [])
    user_topic = state.get("user_topic", "")

    if not user_topic.strip():
        errors.append({"node": "plan_research", "error": "Empty user topic", "recoverable": False})
        return {**state, "research_plan": [], "errors": errors, "status": "searching", "active_agent": "planner"}

    try:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", PLAN_RESEARCH_PROMPT),
            ("user", "{user_topic}"),
        ])
        messages = prompt_template.invoke({"user_topic": user_topic})
        structured_llm = get_llm().with_structured_output(PlanResearchLLMOutput).with_retry(
            stop_after_attempt=3, wait_exponential_jitter=True,
        )
        response = cast(
            PlanResearchLLMOutput,
            await structured_llm.ainvoke(messages),
        )

        if not response.research_plan:
            errors.append({"node": "plan_research", "error": "LLM returned empty research plan", "recoverable": True})

        return {**state,
        "research_plan": response.research_plan,
        "research_questions": response.research_questions,
        "suggested_query": response.suggested_query,
        "concept_ids": response.concept_ids,
        "date_range_days": response.date_range_days,
        "target_paper_count": response.target_paper_count,
        "errors": errors,
        "active_agent": "planner",
        "status": "searching"}

    except Exception as e:
        logger.exception("plan_research: failed to generate research plan")
        errors.append({"node": "plan_research", "error": str(e), "recoverable": False})
        return {**state, "research_plan": [], "errors": errors, "status": "searching",}
