from __future__ import annotations

from typing import Any

from tools._shared import terms


def _score(item: dict[str, Any], query_terms: set[str]) -> int:
    text = f"{item.get('title', '')} {item.get('summary', '')}"
    return len(query_terms & terms(text))


def rank_items(items: list[dict[str, Any]] | None = None, query: str = "", top_k: int = 5) -> dict[str, Any]:
    items = items or []
    query_terms = terms(query)
    scored = [{**item, "relevance": _score(item, query_terms)} for item in items]
    # Sắp xếp giảm dần theo điểm; giữ nguyên thứ tự gốc cho các item bằng điểm (stable sort).
    ranked = sorted(scored, key=lambda item: item["relevance"], reverse=True)[: max(0, top_k)]
    return {"tool": "rank_items", "query": query, "ranked": ranked, "item_count": len(ranked)}
