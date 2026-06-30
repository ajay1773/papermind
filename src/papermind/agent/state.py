from typing import Literal, TypedDict


class PaperMindState(TypedDict):
    user_topic: str
    research_plan: list[str]
    research_questions: list[str]

    suggested_query: str
    concept_ids: list[str]
    date_range_days: int
    target_paper_count: int
    candidate_papers: list[dict]
    fetched_papers: list[dict]

    extracted_findings: list[dict]
    draft_briefing: dict

    critique: dict | None
    critique_score: int
    iterations: int
    tools_used: list[str]
    errors: list[dict]
    status: Literal[
        "planning", "searching", "fetching",
        "extracting", "drafting", "reviewing", "complete"
    ]

    active_agent: Literal["planner", "reader", "critic", "complete"]
    agent_messages: list[dict]

    supervisor_reasoning: str
    supervisor_turns: int
    memory_context: dict
    papers_to_skip: list[str]
