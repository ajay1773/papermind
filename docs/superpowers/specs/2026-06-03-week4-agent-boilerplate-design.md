# Week 4 Boilerplate Design — PaperMind Research Agent

**Date:** 2026-06-03  
**Scope:** Scaffolding only — folder structure, dependencies, state types, node signatures, graph wiring. No node implementation.

---

## Goal

Set up everything Week 4's build tasks need to start from: correct folder layout, `langgraph` installed, `PaperMindState` defined, all 7 node functions stubbed with the right signatures, the graph assembled (nodes registered, edges wired), and a CLI runner that can be invoked once nodes are implemented.

---

## New Dependency

Add to `pyproject.toml`:

```
langgraph>=0.4.0
```

`langchain-openai` is already installed and provides `ChatOpenAI`. No other new deps required.

---

## Folder Structure

```
agent/
  __init__.py
  state.py              ← PaperMindState TypedDict + PaperMetadata model
  llm.py                ← shared ChatOpenAI(model="gpt-4o") instance
  graph.py              ← assemble + compile the LangGraph StateGraph
  edges.py              ← routing functions used as conditional edges
  runner.py             ← CLI entry: python -m agent.runner "agentic RAG"
  nodes/
    __init__.py
    plan_research.py
    search_papers.py
    select_and_fetch.py
    extract_findings.py
    draft_briefing.py
    critique.py
    revise.py

examples/               ← saved output briefings (5 topics, created during build)
evals/
  week4.md              ← deliverable eval notes (created during build)
```

---

## State — `agent/state.py`

```python
from typing import Literal
from typing_extensions import TypedDict
from pydantic import BaseModel
from app.models.schemas import PaperExtraction


class PaperMetadata(BaseModel):
    title: str
    abstract: str
    doi: str
    openalex_id: str
    pdf_url: str | None
    year: int
    authors: list[str]


class PaperMindState(TypedDict):
    user_topic: str
    research_plan: list[str]
    candidate_papers: list[dict]        # PaperMetadata dicts from OpenAlex search
    fetched_papers: list[str]           # paper IDs fully downloaded + indexed
    extracted_findings: list[dict]      # PaperExtraction dicts from Week 2 extractor
    draft_briefing: str
    critique: str | None
    critique_score: int
    iterations: int
    tools_used: list[str]
    status: Literal[
        "planning", "searching", "fetching",
        "extracting", "drafting", "reviewing", "complete"
    ]
```

`PaperExtraction` is already defined in `app/models/schemas.py` — reused, not duplicated.

---

## Shared LLM — `agent/llm.py`

Single `ChatOpenAI(model="gpt-4o")` instance imported by all nodes. Keeping it in one place makes it trivial to swap the model via env var later.

---

## Nodes — `agent/nodes/`

All nodes share the same signature:

```python
def <node_name>(state: PaperMindState) -> dict:
    raise NotImplementedError
```

They return a `dict` of the state keys they update — LangGraph merges this into the full state.

| File | Updates these state keys |
|---|---|
| `plan_research.py` | `research_plan`, `status` |
| `search_papers.py` | `candidate_papers`, `tools_used`, `status` |
| `select_and_fetch.py` | `fetched_papers`, `tools_used`, `status` |
| `extract_findings.py` | `extracted_findings`, `status` |
| `draft_briefing.py` | `draft_briefing`, `status` |
| `critique.py` | `critique`, `critique_score`, `status` |
| `revise.py` | `draft_briefing`, `iterations`, `status` |

---

## Routing — `agent/edges.py`

One routing function used as a conditional edge out of `critique`:

```python
def route_after_critique(state: PaperMindState) -> str:
    # Returns "revise" or "complete"
```

Logic:
- `critique_score >= 7` → `"complete"`
- `critique_score < 7` and `iterations < 2` → `"revise"`
- `iterations >= 2` → `"complete"` (iteration limit reached; `revise` node appends a warning)

`revise` → `critique` is a direct edge — no second routing function needed.

---

## Graph — `agent/graph.py`

```
plan_research
    ↓
search_papers
    ↓
select_and_fetch
    ↓
extract_findings
    ↓
draft_briefing
    ↓
critique ←──────────────────┐
    ↓                        │
route_after_critique         │
    ├── "complete" → END     │
    └── "revise"             │
           ↓                 │
         revise ─────────────┘  (direct edge back to critique)
```

Compiled with `MemorySaver` checkpointer so each run gets a `thread_id` and traces are resumable.

---

## Runner — `agent/runner.py`

```python
async def main(topic: str) -> None:
    # Invokes compiled_graph with initial state
    # Streams node-by-node output to terminal
    # Prints final draft_briefing
```

Usage: `python -m agent.runner "agentic RAG"`

---

## What This Scaffolding Does NOT Include

- Node implementations (the Week 4 build work)
- MCP client calls
- Parallel fetch concurrency (implemented inside `select_and_fetch` during build)
- LangSmith trace wiring per node (added during build)
- `examples/` briefings and `evals/week4.md` content (created during build)

---

## Constraints

- `PaperExtraction` schema reused from `app/models/schemas.py` — not duplicated
- `ChatOpenAI` import path: `from langchain_openai import ChatOpenAI`
- LangGraph import path: `from langgraph.graph import StateGraph, END`
- Checkpointer: `from langgraph.checkpoint.memory import MemorySaver`
- All agent code lives under `agent/` at project root, consistent with `mcp_servers/`
