from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class SourceInfo(BaseModel):
    heading: str
    page: int
    type: str
    source: str
    text: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]


class IngestResponse(BaseModel):
    filename: str
    doc_id: str = ""
    chunks: int
    status: str


class HealthResponse(BaseModel):
    status: str
    collection_count: int


class ResearchRequest(BaseModel):
    topic: str


class ResearchResponse(BaseModel):
    topic: str
    briefing: str
    papers_fetched: list[str]
    tools_used: list[str]
    critique_score: int
    iterations: int


class BenchmarkResult(BaseModel):
    benchmark: str
    score: str
    vs_prior_best: str


class PaperExtraction(BaseModel):
    paper_id: str
    section: str
    main_claim: str
    novelty_vs_prior_work: str
    benchmark_results: list[BenchmarkResult]
    methods_used: list[str]
    limitations_mentioned: list[str]
    key_citations: list[str]
