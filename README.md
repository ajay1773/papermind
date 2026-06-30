# PaperMind

**Give it an AI/ML topic. Get a structured research briefing in 5 minutes.**

PaperMind is an autonomous research agent that reads recent arXiv papers so you don't have to. Type a topic — it plans a search strategy, pulls up to 20 papers from OpenAlex, extracts what's genuinely new, translates benchmarks into plain English, and returns a cited technical briefing with an executive summary, paper-by-paper breakdowns, synthesis, and open questions.

Built as a personal tool for staying current with fast-moving AI research without drowning in papers.

---

## Run it yourself

**Requirements:** Docker, an OpenAI API key, and your email address (for OpenAlex's polite pool — no key needed).

```bash
git clone https://github.com/ajay1773/papermind.git
cd papermind
cp .env.example .env
```

Open `.env` and set two values:

```bash
OPENAI_API_KEY=sk-...          # your OpenAI key
OPENALEX_MAILTO=you@email.com  # your email — required by OpenAlex, no signup
```

Then:

```bash
docker compose up --build
```

Open [http://localhost:8000/briefing](http://localhost:8000/briefing), type a topic, hit **Run**.

**Cost:** ~$0.15–$1.50 per briefing depending on how many papers the agent reads. No other paid services required — Qdrant and LlamaParse are optional enhancements.

---

## What you get

Type *"retrieval augmented generation"* and the agent returns:

- **Executive summary** — 2–3 sentences on the current state of the field
- **Paper breakdowns** — per-paper: main claim, key benchmark result, confidence level (full text vs abstract)
- **Synthesis** — what the papers collectively tell us
- **Open questions** — what's still unanswered
- **Recommended reading** — which paper to read first and why
- **Full citations** — linked to DOI

---

## How it works

```
Your topic
    │
    ▼
Planner — research strategy, OpenAlex query, concept IDs
    │
    ▼
Reader — search → select → fetch PDFs/TLDRs → extract findings
    │
    ▼
Critic — draft briefing → critique → revise (max 2 iterations)
    │
    ▼
Structured briefing
```

Multi-agent graph built with **LangGraph** (supervisor pattern). Tools served over **MCP** — OpenAlex search, Semantic Scholar TLDRs, PDF fetch and chunk. Section-aware PDF indexing with **Qdrant** (falls back to in-session memory if Qdrant isn't configured).

---

## Evaluation

Measured on 7 live agent runs against hand-curated ground-truth claims.

| Metric | Score |
|--------|------:|
| **Faithfulness** | **0.76** |
| Context precision | 0.53 |
| Answer relevancy | 0.29 |
| Context recall | 0.11 |
| **Weighted overall** | **0.51** |

Faithfulness (claims grounded in retrieved sources) is the metric that matters most here — 0.76 means the agent rarely hallucinates. Relevancy and recall are lower because the briefing format is long-form synthesis, not direct Q&A.

---

## Tech stack

| Layer | Tool |
|-------|------|
| Agent orchestration | LangGraph, supervisor + planner / reader / critic |
| Tools | MCP (OpenAlex, Semantic Scholar) |
| LLM | GPT-4o |
| Vector store | Qdrant Cloud (optional) |
| Embeddings | text-embedding-3-small |
| Eval | RAGAS |
| Backend | FastAPI + Jinja2 + HTMX |

---

## Optional enhancements

| Service | What it adds | Required? |
|---------|-------------|-----------|
| `QDRANT_URL` + `QDRANT_API_KEY` | Persistent PDF chunks across sessions | No — falls back to in-session memory |
| `SEMANTIC_SCHOLAR_API_KEY` | Higher rate limits for TLDR enrichment | No — works without it |
| `LLAMA_CLOUD_API_KEY` | Structured PDF parsing (better extraction) | No — falls back to pypdf |
| `LANGSMITH_API_KEY` | Agent run tracing | No |

---

## Project structure

```
src/papermind/
├── agent/       # LangGraph multi-agent graph
├── mcp/         # MCP servers — papers + store tools
├── ingestion/   # PDF parsing, section-aware chunking
├── retrieval/   # RAG query pipeline
├── vectorstore/ # Qdrant client
├── memory/      # Cross-session memory
└── web/         # FastAPI routes + Jinja2 templates
```

---

## License

MIT
