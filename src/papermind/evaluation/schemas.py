from typing import TypedDict


class PaperMindEvalSample(TypedDict, total=False):
    """Single evaluation sample collected from a PaperMind agent run."""

    run_id: str
    user_topic: str
    research_questions: list[str]
    retrieved_papers: list[str]
    extracted_findings: list[str]
    final_briefing: str
    paper_abstracts: list[str]
    ground_truth: str
    reference_contexts: list[str]
