from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from papermind.agent.state import PaperMindState
from papermind.agent.nodes.supervisor import supervisor
from papermind.agent.subgraphs import planner_subgraph, reader_subgraph, critic_subgraph
from papermind.config import settings
from papermind.evaluation.collect import build_eval_sample_from_state, save_eval_sample
from papermind.memory import MemoryService


def route_from_supervisor(state: PaperMindState) -> str:
    active_agent = state.get("active_agent", "planner")
    if active_agent == "complete":
        return "complete"
    return active_agent


def save_briefing_on_complete(state: PaperMindState) -> dict:
    if state.get("draft_briefing") and state.get("user_topic"):
        memory_service = MemoryService()
        briefing = state["draft_briefing"]
        if isinstance(briefing, dict):
            memory_service.save_briefing(state["user_topic"], briefing)

    if settings.eval_collect_enabled:
        sample = build_eval_sample_from_state(state)
        if sample:
            save_eval_sample(sample, settings.eval_samples_path)

    return {"status": "complete"}


def build_multi_agent_graph() -> StateGraph:
    builder = StateGraph(PaperMindState)

    builder.add_node("supervisor", supervisor)
    builder.add_node("planner", planner_subgraph.compile())
    builder.add_node("reader", reader_subgraph.compile())
    builder.add_node("critic", critic_subgraph.compile())
    builder.add_node("finalize", save_briefing_on_complete)

    builder.set_entry_point("supervisor")

    builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "planner": "planner",
            "reader": "reader",
            "critic": "critic",
            "complete": "finalize",
        },
    )

    builder.add_edge("planner", "supervisor")
    builder.add_edge("reader", "supervisor")
    builder.add_edge("critic", "supervisor")
    builder.add_edge("finalize", END)

    return builder


compiled_graph = build_multi_agent_graph().compile(checkpointer=MemorySaver())
