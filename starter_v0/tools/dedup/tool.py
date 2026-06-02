from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from tools._shared import fold_text, terms


def _norm_url(url: str) -> str:
    """Normalize URL: lowercase, strip scheme, strip trailing slash."""
    try:
        p = urlparse(url.lower().strip())
        return (p.netloc + p.path).rstrip("/")
    except Exception:
        return url.lower().strip()


def _title_key(title: str) -> str:
    """Fold and strip whitespace for title comparison."""
    return " ".join(fold_text(title).split())


def _similar(a: str, b: str, threshold: float = 0.80) -> bool:
    """Return True if two strings share ≥ threshold of their terms."""
    ta, tb = terms(a), terms(b)
    if not ta or not tb:
        return a == b
    overlap = len(ta & tb) / max(len(ta), len(tb))
    return overlap >= threshold


def dedup_items(
    items: list[dict[str, Any]] | None = None,
    key: str = "url",
    title_threshold: float = 0.80,
) -> dict[str, Any]:
    """Remove duplicate items from a result list.

    Deduplication strategy:
    - key='url'   : exact URL match (normalized) — fastest
    - key='title' : fuzzy title match using term-overlap ≥ title_threshold
    - key='both'  : remove if EITHER url OR title already seen
    """
    items = items or []
    seen_urls: set[str] = set()
    seen_titles: list[str] = []
    kept: list[dict[str, Any]] = []

    for item in items:
        url = _norm_url(item.get("url", ""))
        title = item.get("title", "") or item.get("summary", "")[:120]

        if key in ("url", "both"):
            if url and url in seen_urls:
                continue

        if key in ("title", "both"):
            if any(_similar(title, t, title_threshold) for t in seen_titles):
                continue

        seen_urls.add(url)
        if title:
            seen_titles.append(title)
        kept.append(item)

    return {
        "tool": "dedup",
        "key": key,
        "original_count": len(items),
        "removed": len(items) - len(kept),
        "items": kept,
    }
