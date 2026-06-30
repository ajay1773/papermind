from papermind.agent.state import PaperMindState


def get_initial_state(topic: str) -> PaperMindState:
    return {
        "user_topic": topic,
        "research_plan": [],
        "research_questions": [],
        "suggested_query": "",
        "concept_ids": [],
        "date_range_days": 365,
        "target_paper_count": 20,
        "candidate_papers": [],
        "fetched_papers": [],
        "extracted_findings": [],
        "draft_briefing": {},
        "critique": None,
        "critique_score": 0,
        "iterations": 0,
        "tools_used": [],
        "errors": [],
        "status": "planning",
        "active_agent": "planner",
        "agent_messages": [],
        "supervisor_reasoning": "",
        "supervisor_turns": 0,
        "memory_context": {},
        "papers_to_skip": [],
    }
