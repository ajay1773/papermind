from langgraph.graph import StateGraph, END

from papermind.agent.state import PaperMindState
from papermind.agent.nodes.plan_research import plan_research
from papermind.agent.nodes.search_papers import search_papers


def build_planner_subgraph() -> StateGraph:
    builder = StateGraph(PaperMindState)

    builder.add_node("plan_research", plan_research)
    builder.add_node("search_papers", search_papers)

    builder.set_entry_point("plan_research")
    builder.add_edge("plan_research", "search_papers")
    builder.add_edge("search_papers", END)

    return builder


planner_subgraph = build_planner_subgraph()
