import asyncio
import json
import sys
import uuid

from papermind.agent.graph import compiled_graph
from papermind.agent.initial_state import get_initial_state


async def run(topic: str) -> None:
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state = get_initial_state(topic)
    
    print(f"\n{'='*60}")
    print(f"PAPERMIND MULTI-AGENT RESEARCH BRIEFING")
    print(f"Topic: {topic}")
    print(f"{'='*60}\n")
    
    async for event in compiled_graph.astream(initial_state, config):
        node_name = list(event.keys())[0]
        node_data = event[node_name]
        
        active_agent = node_data.get("active_agent", "")
        reasoning = node_data.get("supervisor_reasoning", "")
        status = node_data.get("status", "")
        
        if node_name == "supervisor" and reasoning:
            print(f"[SUPERVISOR] -> {active_agent}: {reasoning}")
        elif node_name in ("planner", "reader", "critic"):
            print(f"  [{node_name.upper()}] status={status}")
        else:
            print(f"  [{node_name}] status={status}")

    final = compiled_graph.get_state(config)
    values = final.values
    
    print(f"\n{'='*60}")
    print("FINAL BRIEFING")
    print(f"{'='*60}")
    
    briefing = values.get("draft_briefing", {})
    if isinstance(briefing, dict):
        print(json.dumps(briefing, indent=2))
    else:
        print(briefing)
    
    print(f"\n{'='*60}")
    print("STATISTICS")
    print(f"{'='*60}")
    print(f"Papers fetched: {len(values.get('fetched_papers', []))}")
    print(f"Findings extracted: {len(values.get('extracted_findings', []))}")
    print(f"Critique score: {values.get('critique_score', 0)}/10")
    print(f"Revision iterations: {values.get('iterations', 0)}")
    
    if values.get("errors"):
        print(f"\nErrors encountered: {len(values['errors'])}")
        for err in values["errors"]:
            print(f"  - [{err.get('node')}] {err.get('error')}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m papermind.agent.runner '<topic>'")
        sys.exit(1)
    asyncio.run(run(sys.argv[1]))


if __name__ == "__main__":
    main()
