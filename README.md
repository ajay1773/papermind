# PaperMind

Autonomous research briefing agent for AI/ML papers. Give it a topic — e.g. "LLM evaluation methods" or "Graph RAG" — and it plans a research strategy, searches OpenAlex, fetches and reads papers, extracts structured findings, drafts a cited technical briefing, and self-critiques the result.

Built with **LangGraph** (multi-agent supervisor pattern), **MCP** (OpenAlex + Semantic Scholar + paper store tools), **Qdrant** (section-aware PDF chunks), and **RAGAS** (quality measurement).

## Evaluation Results

Measured on **7 live agent runs** collected in `evals/eval_samples.jsonl` (June 2026). Ground-truth key claims from `evals/dataset.jsonl` are merged by topic before scoring.

| Metric | Score | Notes |
|--------|------:|-------|
| **Faithfulness** | **0.76** | Claims mostly grounded in retrieved abstracts/TLDRs |
| Answer relevancy | 0.29 | Low — briefing format is long-form synthesis, not a direct Q&A answer |
| Context precision | 0.53 | ~half of retrieved context is relevant to the question |
| Context recall | 0.11 | Low — eval uses abstract-only contexts vs full key-claim ground truth |
| **Overall (weighted)** | **0.51** | 40% faithfulness + 30% relevancy + 20% precision + 10% recall |

Full output: [`evals/ragas_final.json`](evals/ragas_final.json)

**Topics evaluated:** LLM evaluation (×3), LoRA, small language models in healthcare, Graph RAG, LLM quantization.

**Improvements applied before final eval:**
- OpenAlex **concept ID filters** to stop off-topic retrieval (e.g. automotive papers on LLM queries)
- Query prompt fix: quote the **subject** (`"large language models"`), not the task (`"evaluation methods"`)
- Extraction **chunk cap** (head 6 + tail 4, 8k chars) and **TLDR quality gate** (skip papers with &lt;80 chars of text)
- Draft prompt: mandatory inline `(openalex_id: W…)` citations

Re-run eval after collecting new samples:

```bash
uv run papermind-eval-ragas --output evals/ragas_final.json --include-context-recall
```

Benchmark spec (20 hand-curated cases with ground-truth papers and claims): [`evals/dataset.jsonl`](evals/dataset.jsonl)

Production incidents and mitigations: [`docs/post-mortem.md`](docs/post-mortem.md)

## Architecture

```
User topic
    │
    ▼
Supervisor ──► Planner (research plan, OpenAlex query, concept IDs)
    │              │
    │              ▼
    │          Search papers (OpenAlex MCP)
    │              │
    │              ▼
    └──► Reader ──► Select & fetch (PDF / TLDR / abstract)
                   Extract findings (structured JSON per paper)
    │              │
    │              ▼
    └──► Critic ──► Draft briefing → Critique → Revise (max 2)
                   │
                   ▼
              Final briefing + eval sample → evals/eval_samples.jsonl
```

**MCP servers:**
- **Papers** (`papermind-mcp-papers`) — OpenAlex search, Semantic Scholar TLDRs, PDF fetch
- **Store** (`papermind-mcp-store`) — hybrid search over indexed paper chunks in Qdrant

## Setup

```bash
cp .env.example .env   # OPENAI_API_KEY, OPENALEX_MAILTO, optional QDRANT_* / SEMANTIC_SCHOLAR_API_KEY
uv sync
```

## Run

**1. Start MCP servers** (required for agent runs):

```bash
uv run papermind-mcp-papers   # papers discovery
uv run papermind-mcp-store    # paper store (separate terminal)
# or: ./scripts/start_mcp_servers.sh
```

**2. Run a briefing** (CLI):

```bash
uv run papermind-agent "Recent advances in retrieval-augmented generation"
```

**3. Web UI:**

```bash
uv run python -m papermind.app
```

Open [http://localhost:8000/briefing](http://localhost:8000/briefing) for the research briefing form.

**4. Collect eval samples** — set `EVAL_COLLECT_ENABLED=true` in `.env`. Each completed briefing appends one line to `evals/eval_samples.jsonl`. Turn off when done benchmarking.

## Docker (local + Oracle Cloud)

The Docker image runs **FastAPI + papers MCP in one container** — no separate MCP terminals needed in production.

```bash
cp .env.example .env   # set OPENAI_API_KEY, OPENALEX_MAILTO
docker compose up --build
```

Open [http://localhost:8000/briefing](http://localhost:8000/briefing).

**Oracle Cloud (Always Free ARM):** create an `VM.Standard.A1.Flex` instance (Ubuntu 22.04 aarch64), install Docker, clone the repo, copy `.env`, then:

```bash
docker compose up -d --build
```

Open port **8000** in the OCI security list (or use Cloudflare Tunnel and keep ports closed). SQLite memory and uploads persist in the `papermind-data` Docker volume (`DATA_DIR=/app/data`).

Full step-by-step: **[docs/deploy-oracle-cloudflare.md](docs/deploy-oracle-cloudflare.md)**

### Deployment-related env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` / `APP_PORT` | `8000` | Web server port |
| `MCP_PAPERS_URL` | `http://127.0.0.1:8009/mcp` | Agent → papers MCP (same container) |
| `MCP_PAPERS_PORT` | `8009` | Papers MCP listen port |
| `DATA_DIR` | `./data` | SQLite memory DB directory |
| `UPLOAD_DIR` | `./data/uploads` | Document uploads |
| `APP_DEBUG` | `false` | Disable uvicorn reload in production |
| `EVAL_COLLECT_ENABLED` | `false` | Disable eval sample writes in production |
| `BRIEFING_RATE_LIMIT` | `5/hour` | Max briefing requests per IP (slowapi format) |
| `BRIEFING_RATE_LIMIT_ENABLED` | `true` | Set `false` for unlimited local dev |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/ingest` | Upload and ingest a document |
| POST | `/api/v1/query` | RAG query against ingested documents |
| GET | `/briefing` | Research briefing web UI |
| POST | `/briefing` | Run multi-agent briefing for a topic |

## Project Structure

```
src/papermind/
├── agent/           # LangGraph multi-agent graph (planner, reader, critic)
├── mcp/             # MCP servers (papers + store)
├── evaluation/      # RAGAS eval CLI + sample collection
├── ingestion/       # PDF parsing, section-aware chunking
├── retrieval/       # RAG query pipeline
├── vectorstore/     # Qdrant client
├── memory/          # Cross-session paper/briefing memory
└── web/             # FastAPI routes + templates

evals/
├── dataset.jsonl        # 20 benchmark cases (ground truth)
├── eval_samples.jsonl   # Auto-collected agent run outputs
└── ragas_final.json     # Latest RAGAS scores
```

## Tech Stack

| Layer | Tool |
|-------|------|
| Agent | LangGraph, supervisor + planner / reader / critic |
| Tools | MCP (OpenAlex, Semantic Scholar) |
| LLM | GPT-4o (agent), gpt-4o-mini (RAGAS judge) |
| Vector DB | Qdrant Cloud (prod), in-session fallback when unavailable |
| Embeddings | text-embedding-3-small |
| Eval | RAGAS (faithfulness, answer_relevancy, context precision/recall) |
| Backend | FastAPI + Jinja2 |

## License

Private / portfolio project.
