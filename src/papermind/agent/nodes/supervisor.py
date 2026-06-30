import logging

from papermind.agent.state import PaperMindState
from papermind.memory import MemoryService

logger = logging.getLogger(__name__)

MAX_SUPERVISOR_TURNS = 5


async def supervisor(state: PaperMindState) -> dict:
    """Rule-based supervisor. No LLM call - deterministic routing based on state."""
    errors = state.get("errors", [])
    turns = state.get("supervisor_turns", 0)

    memory_service = MemoryService()
    topic = state.get("user_topic", "")

    if turns == 0:
        memory_context = memory_service.get_memory_context(topic)
        papers_to_skip = list(
            memory_service.get_indexed_paper_ids()
            | memory_service.get_papers_with_cached_extractions()
        )
        if memory_context.get("prior_briefing"):
            logger.info(
                "Supervisor: prior briefing found for topic '%s' from %s",
                topic,
                memory_context["prior_briefing"]["created_at"],
            )
    else:
        memory_context = state.get("memory_context", {})
        papers_to_skip = state.get("papers_to_skip", [])

    # Hard cap: prevent infinite loops
    if turns >= MAX_SUPERVISOR_TURNS:
        logger.warning("Supervisor hit max turns (%d), forcing completion", MAX_SUPERVISOR_TURNS)
        return {
            "active_agent": "complete",
            "supervisor_reasoning": f"Forced complete: hit max turns ({MAX_SUPERVISOR_TURNS})",
            "supervisor_turns": turns + 1,
            "memory_context": memory_context,
            "papers_to_skip": papers_to_skip,
            "status": "complete",
        }

    critique_score = state.get("critique_score", 0)
    iterations = state.get("iterations", 0)
    has_plan = bool(state.get("research_plan"))
    has_candidates = bool(state.get("candidate_papers"))
    has_findings = bool(state.get("extracted_findings"))
    has_briefing = isinstance(state.get("draft_briefing"), dict) and bool(state["draft_briefing"])

    # Exit condition: good score OR enough revision attempts with a briefing
    if critique_score >= 7:
        decision = "complete"
        reasoning = f"Critique score {critique_score}/10 meets threshold"
    elif iterations >= 2 and has_briefing:
        decision = "complete"
        reasoning = f"Max revisions reached ({iterations}) with briefing produced"
    # Normal forward flow
    elif not has_plan:
        decision = "planner"
        reasoning = "No research plan yet"
    elif not has_candidates:
        decision = "planner"
        reasoning = "Plan exists but no candidate papers found"
    elif not has_findings:
        decision = "reader"
        reasoning = "Have candidates, need to fetch and extract findings"
    elif not has_briefing:
        decision = "critic"
        reasoning = "Have findings, need to draft and critique briefing"
    else:
        # We have a briefing but score < 7 and iterations < 2
        # This shouldn't happen because critic subgraph handles revisions internally
        decision = "complete"
        reasoning = f"Briefing exists, score={critique_score}, iterations={iterations}"

    logger.info("Supervisor turn %d: -> %s (%s)", turns, decision, reasoning)

    return {
        "active_agent": decision,
        "supervisor_reasoning": reasoning,
        "supervisor_turns": turns + 1,
        "memory_context": memory_context,
        "papers_to_skip": papers_to_skip,
        "errors": errors,
    }
