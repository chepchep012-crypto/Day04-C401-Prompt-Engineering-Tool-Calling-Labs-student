from __future__ import annotations

from typing import Any

from tools._shared import terms


def _score(query_terms: set[str], item: dict[str, Any]) -> float:
    """Compute relevance score: term overlap between query and item text."""
    if not query_terms:
        return 0.0
    item_text = " ".join(filter(None, [
        item.get("title", ""),
        item.get("summary", ""),
        item.get("source", ""),
    ]))
    item_terms = terms(item_text)
    if not item_terms:
        return 0.0
    # Jaccard-like: intersection over query size (recall-oriented)
    overlap = len(query_terms & item_terms)
    return round(overlap / len(query_terms), 4)


def rank_items(
    query: str = "",
    items: list[dict[str, Any]] | None = None,
    top_k: int = 0,
) -> dict[str, Any]:
    """Rank a list of items by relevance to a query using term-overlap scoring.

    Each item gets a `_relevance` field (0.0–1.0). Items with the same score
    keep their original order (stable sort). Set top_k=0 to return all items.
    """
    items = items or []
    query_terms = terms(query)

    scored = [
        {**item, "_relevance": _score(query_terms, item)}
        for item in items
    ]
    scored.sort(key=lambda x: x["_relevance"], reverse=True)

    result = scored[:top_k] if top_k and top_k > 0 else scored
    return {
        "tool": "rank",
        "query": query,
        "top_k": top_k or len(result),
        "items": result,
    }
