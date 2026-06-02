from __future__ import annotations

from collections import Counter
from typing import Any

from tools._shared import terms


def extract_keywords(items: list[dict[str, Any]] | None = None, text: str = "", top_k: int = 10) -> dict[str, Any]:
    items = items or []
    counter: Counter[str] = Counter()
    for item in items:
        blob = f"{item.get('title', '')} {item.get('summary', '')}"
        counter.update(terms(blob))
    if text:
        counter.update(terms(text))
    top = [{"term": term, "count": count} for term, count in counter.most_common(max(0, top_k))]
    return {"tool": "extract_keywords", "keywords": top, "unique_terms": len(counter)}
