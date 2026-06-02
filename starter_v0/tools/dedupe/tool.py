from __future__ import annotations

from typing import Any

from tools._shared import fold_text


def _key(item: dict[str, Any], key: str) -> str:
    if key == "title":
        return fold_text((item.get("title") or "").strip())
    return (item.get("url") or "").strip().lower().rstrip("/")


def dedupe_items(items: list[dict[str, Any]] | None = None, key: str = "url") -> dict[str, Any]:
    items = items or []
    seen: set[str] = set()
    kept: list[dict[str, Any]] = []
    for item in items:
        identity = _key(item, key)
        if identity and identity in seen:
            continue
        if identity:
            seen.add(identity)
        kept.append(item)
    return {
        "tool": "dedupe_items",
        "key": key,
        "items": kept,
        "kept_count": len(kept),
        "removed_count": len(items) - len(kept),
    }
