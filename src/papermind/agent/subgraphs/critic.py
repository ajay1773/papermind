from langgraph.graph import StateGraph, END

from papermind.agent.state import PaperMindState
from papermind.agent.nodes.draft_briefing import draft_briefing
from papermind.agent.nodes.critique import critique
from papermind.agent.nodes.revise import revise


def route_after_critique(state: PaperMindState) -> str:
    if state.get("critique_score", 0) >= 7:
        return "complete"
    if state.get("iterations", 0) >= 2:
        return "complete"
    return "revise"


def build_critic_subgraph() -> StateGraph:
    builder = StateGraph(PaperMindState)

    builder.add_node("draft_briefing", draft_briefing)
    builder.add_node("critique", critique)
    builder.add_node("revise", revise)

    builder.set_entry_point("draft_briefing")
    builder.add_edge("draft_briefing", "critique")
    builder.add_conditional_edges(
        "critique",
        route_after_critique,
        {"revise": "revise", "complete": END},
    )
    builder.add_edge("revise", "critique")

    return builder


critic_subgraph = build_critic_subgraph()
