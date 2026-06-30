import json
from typing import Any


def parse_candidate_paper(paper: dict) -> dict | None:
    if paper.get("openalex_id"):
        return paper

    try:
        raw = paper.get("text", "{}")
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        return parsed if isinstance(parsed, dict) else None
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None


def get_formatted_candidate_papers(papers: list[dict]) -> str:
    paper_string = ""
    for paper in papers:
        parsed = parse_candidate_paper(paper)
        if parsed is None:
            continue

        abstract = parsed.get("abstract", "") or ""
        truncated_abstract = abstract[:300] + "..." if len(abstract) > 300 else abstract

        paper_string += f"""
---
ID: {parsed.get('openalex_id', '')}
Title: {parsed.get('title', '')}
Abstract: {truncated_abstract}
Citation count: {parsed.get('citation_count', 0)}
Publication date: {parsed.get('publication_date', '')}
Fetchable: {parsed.get('is_fetchable', False)}
---
"""
    return paper_string


def enrich_selected_papers(relevant_papers: list[dict], candidate_papers: list[dict]) -> list[dict]:
    candidate_paper_lookup: dict[str, Any] = {}
    for candidate_paper in candidate_papers:
        parsed = parse_candidate_paper(candidate_paper)
        if parsed and parsed.get("openalex_id"):
            candidate_paper_lookup[parsed["openalex_id"]] = parsed

    complete_papers: list[dict] = []
    for relevant_paper in relevant_papers:
        openalex_id = relevant_paper.get("openalex_id")
        if not openalex_id or openalex_id not in candidate_paper_lookup:
            continue

        complete_paper = candidate_paper_lookup[openalex_id].copy()
        complete_paper["relevance_reason"] = relevant_paper.get("relevance_reason", "")
        complete_paper["fetch_priority"] = relevant_paper.get("fetch_priority", "low")
        complete_papers.append(complete_paper)
    return complete_papers
