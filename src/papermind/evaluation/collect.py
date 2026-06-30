from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from papermind.agent.state import PaperMindState
from papermind.evaluation.schemas import PaperMindEvalSample

logger = logging.getLogger(__name__)

DEFAULT_SAMPLES_PATH = Path("evals/eval_samples.jsonl")


def _paper_context_text(paper: dict) -> str:
    title = paper.get("title", "Unknown title")
    openalex_id = paper.get("openalex_id", "")
    abstract = paper.get("abstract") or ""
    tldr = paper.get("tldr") or {}
    tldr_text = tldr.get("tldr") if isinstance(tldr, dict) else ""
    body = abstract.strip() or (tldr_text or "").strip() or "No abstract or TLDR available."
    header = f"{title} ({openalex_id})" if openalex_id else title
    return f"{header}\n{body}"


def briefing_to_text(briefing: dict | str | None) -> str:
    if briefing is None:
        return ""
    if isinstance(briefing, str):
        return briefing
    if hasattr(briefing, "model_dump"):
        briefing = briefing.model_dump()

    sections: list[str] = []
    if summary := briefing.get("executive_summary"):
        sections.append(f"Executive Summary: {summary}")
    if breakdowns := briefing.get("paper_breakdowns"):
        sections.append("Paper Breakdowns:")
        for paper in breakdowns:
            if not isinstance(paper, dict):
                continue
            sections.append(
                f"- {paper.get('title', 'Unknown')} ({paper.get('openalex_id', '')}): "
                f"{paper.get('contribution', paper.get('key_result', ''))}"
            )
    if synthesis := briefing.get("synthesis"):
        sections.append(f"Synthesis: {synthesis}")
    if gaps := briefing.get("gaps"):
        sections.append(f"Gaps: {gaps}")
    if recommended := briefing.get("recommended_reading"):
        sections.append(f"Recommended Reading: {recommended}")
    if quality := briefing.get("data_quality_note"):
        sections.append(f"Data Quality Note: {quality}")
    return "\n\n".join(sections)


def build_eval_sample_from_state(
    state: PaperMindState,
    *,
    run_id: str | None = None,
    ground_truth: str = "",
) -> PaperMindEvalSample | None:
    briefing_text = briefing_to_text(state.get("draft_briefing"))
    fetched_papers = [
        paper for paper in state.get("fetched_papers", []) if isinstance(paper, dict)
    ]
    extracted_findings = state.get("extracted_findings", [])

    if not briefing_text or not fetched_papers:
        logger.info(
            "Skipping eval sample collection: briefing=%s papers=%d",
            bool(briefing_text),
            len(fetched_papers),
        )
        return None

    finding_summaries = []
    for finding in extracted_findings:
        if not isinstance(finding, dict):
            continue
        finding_summaries.append(
            f"{finding.get('title', 'Unknown')} ({finding.get('openalex_id', '')}): "
            f"{finding.get('main_claim', finding.get('key_results', ''))}"
        )

    return PaperMindEvalSample(
        run_id=run_id or str(uuid.uuid4()),
        user_topic=state.get("user_topic", ""),
        research_questions=list(state.get("research_questions", [])),
        retrieved_papers=[
            paper.get("openalex_id") or paper.get("title", "")
            for paper in fetched_papers
        ],
        extracted_findings=finding_summaries,
        final_briefing=briefing_text,
        paper_abstracts=[_paper_context_text(paper) for paper in fetched_papers],
        ground_truth=ground_truth,
    )


def save_eval_sample(
    sample: PaperMindEvalSample,
    path: Path | str = DEFAULT_SAMPLES_PATH,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(sample, ensure_ascii=False) + "\n")
    logger.info("Saved eval sample for topic '%s' to %s", sample.get("user_topic"), target)


def load_eval_samples(path: Path | str = DEFAULT_SAMPLES_PATH) -> list[PaperMindEvalSample]:
    target = Path(path)
    if not target.exists():
        return []

    samples: list[PaperMindEvalSample] = []
    with target.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            samples.append(json.loads(line))
    return samples
