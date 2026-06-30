from papermind.agent.state import PaperMindState


def route_after_critique(state: PaperMindState) -> str:
    if state["critique_score"] >= 9:
        return "complete"
    if state["iterations"] >= 2:
        return "complete"
    return "revise"
