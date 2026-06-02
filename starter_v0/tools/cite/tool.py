from __future__ import annotations

from typing import Any

from tools._shared import domain


def _one_line(item: dict[str, Any]) -> str:
    title = (item.get("title") or "Không tiêu đề").strip()
    url = (item.get("url") or "").strip()
    source = (item.get("source") or domain(url)).strip()
    parts = [title] + ([source] if source else [])
    line = ". ".join(parts)
    return f"{line}. {url}" if url else f"{line}."


def build_citations(items: list[dict[str, Any]] | None = None, style: str = "numbered") -> dict[str, Any]:
    items = items or []
    if style == "markdown":
        lines = [
            f"- [{(item.get('title') or 'link').strip()}]({(item.get('url') or '').strip()})"
            for item in items
        ]
    else:
        lines = [f"[{index + 1}] {_one_line(item)}" for index, item in enumerate(items)]
    return {
        "tool": "build_citations",
        "style": style,
        "citations": "\n".join(lines),
        "item_count": len(items),
    }
