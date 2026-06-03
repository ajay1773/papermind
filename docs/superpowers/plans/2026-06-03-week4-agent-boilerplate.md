# Week 4 Agent Boilerplate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the Week 4 research agent — install `langgraph`, define `PaperMindState`, stub all 7 nodes, wire the graph, and add a CLI runner — so the build tasks have a clean starting point with no implementation yet.

**Architecture:** A LangGraph `StateGraph` with 7 nodes (plan → search → select_and_fetch → extract → draft → critique → revise) connected by fixed and conditional edges. All node bodies raise `NotImplementedError`; the graph itself compiles and is importable. One routing function (`route_after_critique`) contains the only real logic at this stage.

**Tech Stack:** Python 3.12, `langgraph>=0.4.0`, `langchain-openai` (already installed), `uv` for package management, `pytest` for tests.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `agent/__init__.py` | Package marker |
| Create | `agent/state.py` | `PaperMindState` TypedDict + `PaperMetadata` Pydantic model |
| Create | `agent/llm.py` | Shared `ChatOpenAI(model="gpt-4o")` instance |
| Create | `agent/edges.py` | `route_after_critique` routing function |
| Create | `agent/graph.py` | Assemble + compile `StateGraph` → `compiled_graph` |
| Create | `agent/runner.py` | CLI entry point: `python -m agent.runner "<topic>"` |
| Create | `agent/nodes/__init__.py` | Package marker |
| Create | `agent/nodes/plan_research.py` | Node stub |
| Create | `agent/nodes/search_papers.py` | Node stub |
| Create | `agent/nodes/select_and_fetch.py` | Node stub |
| Create | `agent/nodes/extract_findings.py` | Node stub |
| Create | `agent/nodes/draft_briefing.py` | Node stub |
| Create | `agent/nodes/critique.py` | Node stub |
| Create | `agent/nodes/revise.py` | Node stub |
| Create | `tests/__init__.py` | Package marker |
| Create | `tests/agent/__init__.py` | Package marker |
| Create | `tests/agent/conftest.py` | Shared `make_state()` fixture |
| Create | `tests/agent/test_state.py` | `PaperMetadata` validation tests |
| Create | `tests/agent/test_edges.py` | `route_after_critique` logic tests |
| Create | `tests/agent/test_nodes.py` | Node import + `NotImplementedError` tests |
| Create | `tests/agent/test_graph.py` | Graph compilation test |
| Create | `examples/.gitkeep` | Placeholder for Week 4 output briefings |
| Create | `evals/week4.md` | Placeholder for deliverable eval notes |
| Modify | `pyproject.toml` | Add `langgraph>=0.4.0` |

---

## Task 1: Install langgraph

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add langgraph to pyproject.toml and install**

```bash
uv add "langgraph>=0.4.0"
```

Expected output includes a line like `+ langgraph 0.4.x` and ends with `Done`.

- [ ] **Step 2: Verify langgraph imports correctly**

```bash
.venv/bin/python -c "from langgraph.graph import StateGraph, END; from langgraph.checkpoint.memory import MemorySaver; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add langgraph dependency"
```

---

## Task 2: Test infrastructure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/agent/__init__.py`
- Create: `tests/agent/conftest.py`

- [ ] **Step 1: Create test package markers**

```bash
mkdir -p tests/agent
touch tests/__init__.py tests/agent/__init__.py
```

- [ ] **Step 2: Create `tests/agent/conftest.py`**

```python
from typing import Any


def make_state(**overrides: Any) -> dict:
    defaults: dict = {
        "user_topic": "agentic RAG",
        "research_plan": [],
        "candidate_papers": [],
        "fetched_papers": [],
        "extracted_findings": [],
        "draft_briefing": "",
        "critique": None,
        "critique_score": 0,
        "iterations": 0,
        "tools_used": [],
        "status": "planning",
    }
    return {**defaults, **overrides}
```

- [ ] **Step 3: Verify pytest discovers tests directory (empty run)**

```bash
.venv/bin/python -m pytest tests/ --collect-only -q
```

Expected: `no tests ran` with no errors.

---

## Task 3: State and models

**Files:**
- Create: `agent/__init__.py`
- Create: `agent/state.py`
- Create: `tests/agent/test_state.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/agent/test_state.py`:

```python
import pytest
from pydantic import ValidationError
from agent.state import PaperMetadata, PaperMindState


def test_paper_metadata_valid():
    m = PaperMetadata(
        title="Attention Is All You Need",
        abstract="We propose a new simple network architecture...",
        doi="10.48550/arXiv.1706.03762",
        openalex_id="W2963403868",
        pdf_url="https://arxiv.org/pdf/1706.03762",
        year=2017,
        authors=["Vaswani", "Shazeer"],
    )
    assert m.title == "Attention Is All You Need"
    assert m.year == 2017


def test_paper_metadata_pdf_url_optional():
    m = PaperMetadata(
        title="Some Paper",
        abstract="Abstract text.",
        doi="10.1234/test",
        openalex_id="W123",
        pdf_url=None,
        year=2024,
        authors=["Author A"],
    )
    assert m.pdf_url is None


def test_paper_metadata_missing_required_field():
    with pytest.raises(ValidationError):
        PaperMetadata(
            abstract="Abstract text.",
            doi="10.1234/test",
            openalex_id="W123",
            pdf_url=None,
            year=2024,
            authors=[],
        )


def test_paper_mind_state_is_typed_dict():
    from typing import get_type_hints
    hints = get_type_hints(PaperMindState)
    required_keys = {
        "user_topic", "research_plan", "candidate_papers",
        "fetched_papers", "extracted_findings", "draft_briefing",
        "critique", "critique_score", "iterations",
        "tools_used", "status",
    }
    assert required_keys.issubset(hints.keys())
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/agent/test_state.py -v
```

Expected: `ERROR` or `ImportError` — `agent.state` does not exist yet.

- [ ] **Step 3: Create `agent/__init__.py` and `agent/state.py`**

```bash
mkdir -p agent
touch agent/__init__.py
```

Create `agent/state.py`:

```python
from typing import Literal
from typing import TypedDict
from pydantic import BaseModel


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
    candidate_papers: list[dict]
    fetched_papers: list[str]
    extracted_findings: list[dict]
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

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/agent/test_state.py -v
```

Expected: all 4 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add agent/__init__.py agent/state.py tests/__init__.py tests/agent/__init__.py tests/agent/conftest.py tests/agent/test_state.py
git commit -m "feat: add PaperMindState and PaperMetadata"
```

---

## Task 4: Shared LLM

**Files:**
- Create: `agent/llm.py`

This file has no logic to test directly (it's just a configured object), so we do a smoke-import check inline.

- [ ] **Step 1: Create `agent/llm.py`**

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0)
```

- [ ] **Step 2: Verify import works (no API call is made at import time)**

```bash
OPENAI_API_KEY=dummy .venv/bin/python -c "from agent.llm import llm; print(llm.model_name)"
```

Expected: `gpt-4o`

- [ ] **Step 3: Commit**

```bash
git add agent/llm.py
git commit -m "feat: add shared ChatOpenAI llm instance"
```

---

## Task 5: Node stubs

**Files:**
- Create: `agent/nodes/__init__.py`
- Create: `agent/nodes/plan_research.py`
- Create: `agent/nodes/search_papers.py`
- Create: `agent/nodes/select_and_fetch.py`
- Create: `agent/nodes/extract_findings.py`
- Create: `agent/nodes/draft_briefing.py`
- Create: `agent/nodes/critique.py`
- Create: `agent/nodes/revise.py`
- Create: `tests/agent/test_nodes.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/agent/test_nodes.py`:

```python
import pytest
from tests.agent.conftest import make_state


def test_plan_research_raises():
    from agent.nodes.plan_research import plan_research
    with pytest.raises(NotImplementedError):
        plan_research(make_state())


def test_search_papers_raises():
    from agent.nodes.search_papers import search_papers
    with pytest.raises(NotImplementedError):
        search_papers(make_state())


def test_select_and_fetch_raises():
    from agent.nodes.select_and_fetch import select_and_fetch
    with pytest.raises(NotImplementedError):
        select_and_fetch(make_state())


def test_extract_findings_raises():
    from agent.nodes.extract_findings import extract_findings
    with pytest.raises(NotImplementedError):
        extract_findings(make_state())


def test_draft_briefing_raises():
    from agent.nodes.draft_briefing import draft_briefing
    with pytest.raises(NotImplementedError):
        draft_briefing(make_state())


def test_critique_raises():
    from agent.nodes.critique import critique
    with pytest.raises(NotImplementedError):
        critique(make_state())


def test_revise_raises():
    from agent.nodes.revise import revise
    with pytest.raises(NotImplementedError):
        revise(make_state())
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/agent/test_nodes.py -v
```

Expected: `ERROR` — `agent.nodes` does not exist yet.

- [ ] **Step 3: Create the nodes package and all 7 stubs**

```bash
mkdir -p agent/nodes
touch agent/nodes/__init__.py
```

Create `agent/nodes/plan_research.py`:

```python
from agent.state import PaperMindState


def plan_research(state: PaperMindState) -> dict:
    raise NotImplementedError
```

Create `agent/nodes/search_papers.py`:

```python
from agent.state import PaperMindState


def search_papers(state: PaperMindState) -> dict:
    raise NotImplementedError
```

Create `agent/nodes/select_and_fetch.py`:

```python
from agent.state import PaperMindState


def select_and_fetch(state: PaperMindState) -> dict:
    raise NotImplementedError
```

Create `agent/nodes/extract_findings.py`:

```python
from agent.state import PaperMindState


def extract_findings(state: PaperMindState) -> dict:
    raise NotImplementedError
```

Create `agent/nodes/draft_briefing.py`:

```python
from agent.state import PaperMindState


def draft_briefing(state: PaperMindState) -> dict:
    raise NotImplementedError
```

Create `agent/nodes/critique.py`:

```python
from agent.state import PaperMindState


def critique(state: PaperMindState) -> dict:
    raise NotImplementedError
```

Create `agent/nodes/revise.py`:

```python
from agent.state import PaperMindState


def revise(state: PaperMindState) -> dict:
    raise NotImplementedError
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/agent/test_nodes.py -v
```

Expected: all 7 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add agent/nodes/ tests/agent/test_nodes.py
git commit -m "feat: add 7 node stubs"
```

---

## Task 6: Routing logic

**Files:**
- Create: `agent/edges.py`
- Create: `tests/agent/test_edges.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/agent/test_edges.py`:

```python
from tests.agent.conftest import make_state
from agent.edges import route_after_critique


def test_route_complete_on_high_score():
    state = make_state(critique_score=7, iterations=0)
    assert route_after_critique(state) == "complete"


def test_route_complete_on_perfect_score():
    state = make_state(critique_score=10, iterations=0)
    assert route_after_critique(state) == "complete"


def test_route_revise_on_low_score_first_iteration():
    state = make_state(critique_score=6, iterations=0)
    assert route_after_critique(state) == "revise"


def test_route_revise_on_low_score_second_iteration():
    state = make_state(critique_score=4, iterations=1)
    assert route_after_critique(state) == "revise"


def test_route_complete_on_iteration_limit():
    state = make_state(critique_score=3, iterations=2)
    assert route_after_critique(state) == "complete"


def test_route_complete_on_iteration_limit_even_if_score_zero():
    state = make_state(critique_score=0, iterations=2)
    assert route_after_critique(state) == "complete"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/agent/test_edges.py -v
```

Expected: `ERROR` — `agent.edges` does not exist yet.

- [ ] **Step 3: Create `agent/edges.py`**

```python
from agent.state import PaperMindState


def route_after_critique(state: PaperMindState) -> str:
    if state["critique_score"] >= 7:
        return "complete"
    if state["iterations"] >= 2:
        return "complete"
    return "revise"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/agent/test_edges.py -v
```

Expected: all 6 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add agent/edges.py tests/agent/test_edges.py
git commit -m "feat: add route_after_critique routing logic"
```

---

## Task 7: Graph assembly

**Files:**
- Create: `agent/graph.py`
- Create: `tests/agent/test_graph.py`

- [ ] **Step 1: Write the failing test**

Create `tests/agent/test_graph.py`:

```python
def test_graph_compiles():
    from agent.graph import compiled_graph
    assert compiled_graph is not None
    assert hasattr(compiled_graph, "invoke")
    assert hasattr(compiled_graph, "astream")


def test_graph_has_expected_nodes():
    from agent.graph import compiled_graph
    node_names = set(compiled_graph.get_graph().nodes.keys())
    expected = {
        "plan_research", "search_papers", "select_and_fetch",
        "extract_findings", "draft_briefing", "critique", "revise",
    }
    assert expected.issubset(node_names)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/python -m pytest tests/agent/test_graph.py -v
```

Expected: `ERROR` — `agent.graph` does not exist yet.

- [ ] **Step 3: Create `agent/graph.py`**

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import PaperMindState
from agent.nodes.plan_research import plan_research
from agent.nodes.search_papers import search_papers
from agent.nodes.select_and_fetch import select_and_fetch
from agent.nodes.extract_findings import extract_findings
from agent.nodes.draft_briefing import draft_briefing
from agent.nodes.critique import critique
from agent.nodes.revise import revise
from agent.edges import route_after_critique


def build_graph() -> StateGraph:
    builder = StateGraph(PaperMindState)

    builder.add_node("plan_research", plan_research)
    builder.add_node("search_papers", search_papers)
    builder.add_node("select_and_fetch", select_and_fetch)
    builder.add_node("extract_findings", extract_findings)
    builder.add_node("draft_briefing", draft_briefing)
    builder.add_node("critique", critique)
    builder.add_node("revise", revise)

    builder.set_entry_point("plan_research")
    builder.add_edge("plan_research", "search_papers")
    builder.add_edge("search_papers", "select_and_fetch")
    builder.add_edge("select_and_fetch", "extract_findings")
    builder.add_edge("extract_findings", "draft_briefing")
    builder.add_edge("draft_briefing", "critique")
    builder.add_conditional_edges(
        "critique",
        route_after_critique,
        {"revise": "revise", "complete": END},
    )
    builder.add_edge("revise", "critique")

    return builder


compiled_graph = build_graph().compile(checkpointer=MemorySaver())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/agent/test_graph.py -v
```

Expected: both tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add agent/graph.py tests/agent/test_graph.py
git commit -m "feat: assemble and compile LangGraph state machine"
```

---

## Task 8: CLI runner

**Files:**
- Create: `agent/runner.py`

No unit test here — the runner requires a live LLM API key and running nodes. It is verified manually after nodes are implemented in Week 4. We just verify it imports cleanly.

- [ ] **Step 1: Create `agent/runner.py`**

```python
import asyncio
import sys
import uuid

from agent.graph import compiled_graph
from agent.state import PaperMindState


async def run(topic: str) -> None:
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_state: PaperMindState = {
        "user_topic": topic,
        "research_plan": [],
        "candidate_papers": [],
        "fetched_papers": [],
        "extracted_findings": [],
        "draft_briefing": "",
        "critique": None,
        "critique_score": 0,
        "iterations": 0,
        "tools_used": [],
        "status": "planning",
    }
    async for event in compiled_graph.astream(initial_state, config):
        node_name = list(event.keys())[0]
        status = event[node_name].get("status", "")
        print(f"[{node_name}] status={status}")

    final = compiled_graph.get_state(config)
    print("\n--- BRIEFING ---")
    print(final.values.get("draft_briefing", ""))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m agent.runner '<topic>'")
        sys.exit(1)
    asyncio.run(run(sys.argv[1]))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it imports without errors**

```bash
.venv/bin/python -c "from agent.runner import run, main; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add agent/runner.py
git commit -m "feat: add agent CLI runner"
```

---

## Task 9: Output directories

**Files:**
- Create: `examples/.gitkeep`
- Create: `evals/week4.md`

- [ ] **Step 1: Create examples and evals directories**

```bash
mkdir -p examples evals
touch examples/.gitkeep
```

Create `evals/week4.md`:

```markdown
# Week 4 Eval Notes

Topic queries run, LangSmith trace links, and notes go here during the build week.
```

- [ ] **Step 2: Run the full test suite to confirm everything is green**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: 19 tests `PASSED`, 0 failed.

- [ ] **Step 3: Final commit**

```bash
git add examples/.gitkeep evals/week4.md
git commit -m "feat: add examples and evals directory stubs"
```

---

## Verification

After all tasks complete, confirm the full structure exists:

```bash
find agent/ tests/agent/ examples/ evals/ -type f | sort
```

Expected output:
```
agent/__init__.py
agent/edges.py
agent/graph.py
agent/llm.py
agent/nodes/__init__.py
agent/nodes/critique.py
agent/nodes/draft_briefing.py
agent/nodes/extract_findings.py
agent/nodes/plan_research.py
agent/nodes/revise.py
agent/nodes/search_papers.py
agent/nodes/select_and_fetch.py
agent/runner.py
agent/state.py
evals/week4.md
examples/.gitkeep
tests/agent/__init__.py
tests/agent/conftest.py
tests/agent/test_edges.py
tests/agent/test_graph.py
tests/agent/test_nodes.py
tests/agent/test_state.py
```

And all tests pass:

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: 19 tests `PASSED`.
