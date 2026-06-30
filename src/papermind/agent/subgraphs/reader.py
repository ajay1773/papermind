from langgraph.graph import StateGraph, END

from papermind.agent.state import PaperMindState
from papermind.agent.nodes.select_and_fetch import select_and_fetch
from papermind.agent.nodes.extract_findings import extract_findings


def build_reader_subgraph() -> StateGraph:
    builder = StateGraph(PaperMindState)

    builder.add_node("select_and_fetch", select_and_fetch)
    builder.add_node("extract_findings", extract_findings)

    builder.set_entry_point("select_and_fetch")
    builder.add_edge("select_and_fetch", "extract_findings")
    builder.add_edge("extract_findings", END)

    return builder


reader_subgraph = build_reader_subgraph()
