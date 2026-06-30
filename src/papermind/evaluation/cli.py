"""CLI for running RAGAS evaluation on collected PaperMind samples."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from papermind.config import settings
from papermind.evaluation.collect import load_eval_samples
from papermind.evaluation.ragas_eval import (
    analyze_faithfulness_by_finding,
    evaluate_papermind_run,
)
from papermind.evaluation.schemas import PaperMindEvalSample


def _ground_truth_from_dataset_case(case: dict) -> str:
    parts: list[str] = []
    if claims := case.get("key_claims"):
        parts.append("Key claims:\n- " + "\n- ".join(claims))
    if benchmarks := case.get("ground_truth_benchmarks"):
        benchmark_lines = [
            f"- {item.get('metric', 'metric')}: {item.get('value', '')}"
            for item in benchmarks
            if isinstance(item, dict)
        ]
        if benchmark_lines:
            parts.append("Benchmarks:\n" + "\n".join(benchmark_lines))
    return "\n\n".join(parts)


def enrich_samples_with_dataset(
    samples: list[PaperMindEvalSample],
    dataset_path: Path,
) -> list[PaperMindEvalSample]:
    if not dataset_path.exists():
        return samples

    cases_by_topic: dict[str, dict] = {}
    with dataset_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            case = json.loads(line)
            topic = case.get("topic_query", "").strip().lower()
            if topic:
                cases_by_topic[topic] = case

    enriched: list[PaperMindEvalSample] = []
    for sample in samples:
        topic = (sample.get("user_topic") or "").strip().lower()
        case = cases_by_topic.get(topic)
        if not case:
            enriched.append(sample)
            continue

        updated = dict(sample)
        if not updated.get("ground_truth"):
            updated["ground_truth"] = _ground_truth_from_dataset_case(case)
        enriched.append(updated)  # type: ignore[arg-type]
    return enriched


def _print_scores(scores: dict[str, float]) -> None:
    print("\nRAGAS Results")
    print("=" * 40)
    for metric in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
        if metric in scores:
            print(f"{metric:20s}: {scores[metric]:.3f}")
    print("-" * 40)
    print(f"{'overall':20s}: {scores['overall']:.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation on PaperMind samples")
    parser.add_argument(
        "--samples",
        default=settings.eval_samples_path,
        help="Path to eval_samples.jsonl collected from agent runs",
    )
    parser.add_argument(
        "--dataset",
        default="evals/dataset.jsonl",
        help="Optional benchmark dataset for ground-truth enrichment",
    )
    parser.add_argument(
        "--model",
        default=settings.eval_llm_model,
        help="OpenAI model for RAGAS LLM-as-judge metrics",
    )
    parser.add_argument(
        "--include-context-recall",
        action="store_true",
        help="Force context_recall even without reference_contexts",
    )
    parser.add_argument(
        "--finding-diagnostics",
        action="store_true",
        help="Run per-finding faithfulness diagnostics",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional path to write JSON results",
    )
    args = parser.parse_args()

    if not settings.openai_api_key:
        print("Error: OPENAI_API_KEY is required for RAGAS evaluation.", file=sys.stderr)
        sys.exit(1)

    samples = load_eval_samples(args.samples)
    if not samples:
        print(f"No samples found at {args.samples}", file=sys.stderr)
        print("Run a briefing first — samples are appended on graph completion.", file=sys.stderr)
        sys.exit(1)

    samples = enrich_samples_with_dataset(samples, Path(args.dataset))
    print(f"Evaluating {len(samples)} sample(s) from {args.samples}")

    scores = evaluate_papermind_run(
        samples,
        llm_model=args.model,
        include_context_recall=args.include_context_recall or None,
    )
    _print_scores(scores)

    if args.finding_diagnostics:
        flagged = analyze_faithfulness_by_finding(samples, llm_model=args.model)
        if flagged:
            print("\nLow-grounding findings")
            print("=" * 40)
            for item in flagged:
                print(f"- [{item['faithfulness']:.2f}] {item['finding']}")
                print(f"  topic: {item['user_topic']}")
        else:
            print("\nNo low-grounding findings detected.")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"scores": scores, "sample_count": len(samples)}
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote results to {output_path}")


if __name__ == "__main__":
    main()
