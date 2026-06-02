from __future__ import annotations

import re
from typing import Any


def _authors_str(item: dict[str, Any]) -> str:
    authors = item.get("authors") or item.get("author") or ""
    if isinstance(authors, list):
        if len(authors) > 3:
            return ", ".join(str(a) for a in authors[:3]) + " et al."
        return ", ".join(str(a) for a in authors)
    return str(authors) if authors else ""


def _year(item: dict[str, Any]) -> str:
    for field in ("published", "updated", "date"):
        val = item.get(field, "")
        if val:
            m = re.search(r"\b(20\d{2})\b", str(val))
            if m:
                return m.group(1)
    return "n.d."


def _title(item: dict[str, Any]) -> str:
    return (item.get("title") or "Untitled").strip().rstrip(".")


def _source(item: dict[str, Any]) -> str:
    return item.get("source") or item.get("journal") or item.get("publisher") or ""


def _url(item: dict[str, Any]) -> str:
    return item.get("url") or item.get("pdf_url") or ""


def _apa(item: dict[str, Any], n: int) -> str:
    authors = _authors_str(item)
    year = _year(item)
    title = _title(item)
    source = _source(item)
    url = _url(item)
    parts = []
    if authors:
        parts.append(f"{authors}.")
    parts.append(f"({year}).")
    parts.append(f"{title}.")
    if source:
        parts.append(f"*{source}*.")
    if url:
        parts.append(url)
    return f"[{n}] " + " ".join(parts)


def _mla(item: dict[str, Any], n: int) -> str:
    authors = _authors_str(item)
    title = _title(item)
    source = _source(item)
    year = _year(item)
    url = _url(item)
    parts = []
    if authors:
        parts.append(f"{authors}.")
    parts.append(f'"{title}."')
    if source:
        parts.append(f"*{source}*,")
    parts.append(f"{year}.")
    if url:
        parts.append(url)
    return f"[{n}] " + " ".join(parts)


def _plain(item: dict[str, Any], n: int) -> str:
    title = _title(item)
    source = _source(item)
    year = _year(item)
    url = _url(item)
    line = f"[{n}] {title}"
    if source:
        line += f" — {source}"
    if year and year != "n.d.":
        line += f" ({year})"
    if url:
        line += f" — {url}"
    return line


_FORMATTERS = {"apa": _apa, "mla": _mla, "plain": _plain}


def build_citations(
    items: list[dict[str, Any]] | None = None,
    style: str = "plain",
    numbered: bool = True,
) -> dict[str, Any]:
    """Build a formatted citation list from a list of items.

    Supports APA, MLA, and plain styles. Items should have at minimum
    a 'title' and 'url'; 'authors', 'published', and 'source' are used
    when available.
    """
    items = items or []
    fmt = _formatters = _FORMATTERS.get(style, _plain)
    citations = []
    for i, item in enumerate(items, start=1):
        entry = fmt(item, i) if numbered else fmt(item, i).split("] ", 1)[-1]
        citations.append(entry)

    markdown = "\n".join(citations)
    return {
        "tool": "cite",
        "style": style,
        "count": len(citations),
        "citations": citations,
        "markdown": markdown,
    }
