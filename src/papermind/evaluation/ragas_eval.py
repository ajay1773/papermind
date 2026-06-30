from __future__ import annotations

import logging
from typing import Any

from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from papermind.config import settings
from papermind.evaluation.collect import briefing_to_text
from papermind.evaluation.ragas_compat import apply_ragas_compat
from papermind.evaluation.schemas import PaperMindEvalSample

logger = logging.getLogger(__name__)

apply_ragas_compat()
from ragas import evaluate  # noqa: E402
from ragas.dataset_schema import EvaluationResult  # noqa: E402
from ragas.embeddings.base import LangchainEmbeddingsWrapper  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402
from ragas.metrics import (  # noqa: E402
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)


def _metric_score(result: EvaluationResult, metric: str) -> float:
    value = result[metric]
    if isinstance(value, list):
        return sum(float(item) for item in value) / len(value)
    return float(value)


def _get_ragas_llm(model: str | None = None) -> LangchainLLMWrapper:
    model_name = model or settings.eval_llm_model
    return LangchainLLMWrapper(
        ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=settings.openai_api_key,
        )
    )


def _get_ragas_embeddings() -> LangchainEmbeddingsWrapper:
    return LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(
            model=settings.eval_embedding_model,
            api_key=settings.openai_api_key,
        )
    )


def _expand_samples_to_rows(samples: list[PaperMindEvalSample]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sample in samples:
        questions = sample.get("research_questions") or [sample.get("user_topic", "")]
        answer = sample.get("final_briefing") or briefing_to_text(sample.get("final_briefing"))
        contexts = sample.get("paper_abstracts") or []
        ground_truth = sample.get("ground_truth") or ""
        answer_text = answer
        has_ground_truth = bool(ground_truth.strip()) and ground_truth.strip() != answer_text.strip()

        for question in questions:
            if not question:
                continue
            rows.append(
                {
                    "question": question,
                    "answer": answer_text,
                    "contexts": contexts,
                    "ground_truth": ground_truth or answer_text,
                    "reference": ground_truth or answer_text,
                    "retrieved_paper_ids": sample.get("retrieved_papers") or [],
                    "run_id": sample.get("run_id"),
                    "user_topic": sample.get("user_topic"),
                    "has_ground_truth": has_ground_truth,
                }
            )
    return rows


def create_eval_dataset(samples: list[PaperMindEvalSample]) -> Dataset:
    rows = _expand_samples_to_rows(samples)
    if not rows:
        raise ValueError("No evaluation rows could be built from the provided samples")

    return Dataset.from_dict(
        {
            "question": [row["question"] for row in rows],
            "answer": [row["answer"] for row in rows],
            "contexts": [row["contexts"] for row in rows],
            "ground_truth": [row["ground_truth"] for row in rows],
            "reference": [row["reference"] for row in rows],
        }
    )


def evaluate_papermind_run(
    samples: list[PaperMindEvalSample],
    *,
    llm_model: str | None = None,
    include_context_recall: bool | None = None,
) -> dict[str, float]:
    if not samples:
        raise ValueError("At least one eval sample is required")

    rows = _expand_samples_to_rows(samples)
    use_context_recall = (
        include_context_recall
        if include_context_recall is not None
        else any(row["has_ground_truth"] for row in rows)
    )

    dataset = create_eval_dataset(samples)
    metrics = [faithfulness, answer_relevancy, context_precision]
    if use_context_recall:
        metrics.append(context_recall)

    llm = _get_ragas_llm(llm_model)
    embeddings = _get_ragas_embeddings()
    result = evaluate(dataset=dataset, metrics=metrics, llm=llm, embeddings=embeddings)

    scores = {
        "faithfulness": _metric_score(result, "faithfulness"),
        "answer_relevancy": _metric_score(result, "answer_relevancy"),
        "context_precision": _metric_score(result, "context_precision"),
    }
    if use_context_recall:
        try:
            scores["context_recall"] = _metric_score(result, "context_recall")
        except KeyError:
            pass

    scores["overall"] = (
        scores["faithfulness"] * 0.4
        + scores["answer_relevancy"] * 0.3
        + scores["context_precision"] * 0.2
        + scores.get("context_recall", scores["context_precision"]) * 0.1
    )
    return scores


def analyze_faithfulness_by_finding(
    samples: list[PaperMindEvalSample],
    *,
    llm_model: str | None = None,
    threshold: float = 0.7,
) -> list[dict[str, Any]]:
    """Flag extracted findings that appear weakly grounded in retrieved paper contexts."""
    llm = _get_ragas_llm(llm_model)
    embeddings = _get_ragas_embeddings()
    flagged: list[dict[str, Any]] = []

    for sample in samples:
        question = sample.get("user_topic", "")
        contexts = sample.get("paper_abstracts") or []
        for finding in sample.get("extracted_findings") or []:
            row = Dataset.from_dict(
                {
                    "question": [question],
                    "contexts": [contexts],
                    "answer": [finding],
                }
            )
            result = evaluate(
                dataset=row,
                metrics=[faithfulness],
                llm=llm,
                embeddings=embeddings,
            )
            score = _metric_score(result, "faithfulness")
            if score < threshold:
                flagged.append(
                    {
                        "run_id": sample.get("run_id"),
                        "user_topic": sample.get("user_topic"),
                        "finding": finding,
                        "faithfulness": score,
                        "retrieved_papers": sample.get("retrieved_papers") or [],
                    }
                )
    return flagged
