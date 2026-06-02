"""
knowledge tool — lưu và tìm kiếm knowledge base cục bộ.

Actions:
  save   — lưu một đoạn nội dung vào KB
  search — tìm kiếm trong KB để trả lời câu hỏi
  list   — liệt kê toàn bộ entries
  delete — xóa entry theo id
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from tools._shared import ROOT, err, fold_text, terms

KB_PATH = ROOT / "knowledge" / "kb.json"


# ── Storage helpers ───────────────────────────────────────────────────────────

def _load() -> list[dict[str, Any]]:
    if KB_PATH.exists():
        try:
            return json.loads(KB_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_db(entries: list[dict[str, Any]]) -> None:
    KB_PATH.parent.mkdir(parents=True, exist_ok=True)
    KB_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def _next_id(entries: list[dict]) -> str:
    nums = [int(e["id"].replace("kb", "")) for e in entries if re.match(r"kb\d+", e.get("id", ""))]
    return f"kb{(max(nums) + 1) if nums else 1:04d}"


# ── Score function ────────────────────────────────────────────────────────────

def _score(entry: dict, query_terms: set[str]) -> float:
    title_terms   = terms(entry.get("title", ""))
    content_terms = terms(entry.get("content", ""))
    tag_terms     = terms(" ".join(entry.get("tags", [])))

    title_hits   = len(query_terms & title_terms)
    content_hits = len(query_terms & content_terms)
    tag_hits     = len(query_terms & tag_terms)

    # Weight: title 3×, tags 2×, content 1×
    return title_hits * 3 + tag_hits * 2 + content_hits


# ── Public API ────────────────────────────────────────────────────────────────

def manage_knowledge(
    action: str = "search",
    query: str = "",
    content: str = "",
    title: str = "",
    url: str = "",
    tags: list[str] | None = None,
    top_k: int = 3,
    entry_id: str = "",
) -> dict[str, Any]:
    """
    Quản lý knowledge base cục bộ.

    action="save"   → lưu content vào KB. Cần content, title khuyến khích.
    action="search" → tìm kiếm KB theo query, trả về top_k kết quả.
    action="list"   → liệt kê tất cả entries (id, title, url, tags, saved_at).
    action="delete" → xóa entry theo entry_id.
    """
    try:
        action = (action or "search").strip().lower()
        entries = _load()

        # ── SAVE ─────────────────────────────────────────────────────────────
        if action == "save":
            if not content:
                return err("knowledge", ValueError("content is required for action=save"))

            # Try to merge with an existing entry on the same topic
            MERGE_THRESHOLD = 5
            merged_entry: dict[str, Any] | None = None
            if title or tags:
                query_str = (title or "") + " " + " ".join(tags or [])
                query_t = terms(query_str)
                if query_t:
                    candidates = [(e, _score(e, query_t)) for e in entries]
                    candidates = [(e, s) for e, s in candidates if s >= MERGE_THRESHOLD]
                    if candidates:
                        best_entry, best_score = max(candidates, key=lambda x: x[1])
                        # Append new content under a separator
                        best_entry["content"] = best_entry["content"] + "\n\n---\n\n" + content
                        best_entry["char_count"] = len(best_entry["content"])
                        best_entry["updated_at"] = datetime.now().isoformat(timespec="seconds")
                        # Merge tags (union)
                        existing_tags: set[str] = set(best_entry.get("tags") or [])
                        best_entry["tags"] = sorted(existing_tags | set(tags or []))
                        if url:
                            best_entry["url"] = url
                        merged_entry = best_entry
                        _save_db(entries)

            if merged_entry:
                return {
                    "tool": "knowledge",
                    "action": "merge",
                    "id": merged_entry["id"],
                    "title": merged_entry["title"],
                    "char_count": merged_entry["char_count"],
                    "status": "merged",
                    "total_entries": len(entries),
                }

            entry: dict[str, Any] = {
                "id": _next_id(entries),
                "title": title or (content[:80] + ("…" if len(content) > 80 else "")),
                "url": url or "",
                "content": content,
                "tags": tags or [],
                "saved_at": datetime.now().isoformat(timespec="seconds"),
                "char_count": len(content),
            }
            entries.append(entry)
            _save_db(entries)
            return {
                "tool": "knowledge",
                "action": "save",
                "id": entry["id"],
                "title": entry["title"],
                "char_count": entry["char_count"],
                "status": "saved",
                "total_entries": len(entries),
            }

        # ── SEARCH ────────────────────────────────────────────────────────────
        if action == "search":
            if not query:
                return err("knowledge", ValueError("query is required for action=search"))
            query_terms = terms(query)
            if not query_terms:
                return {"tool": "knowledge", "action": "search", "query": query, "results": []}

            scored = [(e, _score(e, query_terms)) for e in entries]
            scored = [(e, s) for e, s in scored if s > 0]
            scored.sort(key=lambda x: x[1], reverse=True)

            results = []
            for entry, score in scored[:top_k]:
                # Return up to 1200 chars of content to keep context small
                snippet = entry["content"]
                if len(snippet) > 1200:
                    # Try to find a paragraph containing a query term
                    paragraphs = [p.strip() for p in snippet.split("\n\n") if p.strip()]
                    relevant = [p for p in paragraphs if any(t in fold_text(p) for t in query_terms)]
                    snippet = "\n\n".join(relevant[:3]) if relevant else snippet[:1200] + "…"

                results.append({
                    "id": entry["id"],
                    "title": entry["title"],
                    "url": entry.get("url", ""),
                    "tags": entry.get("tags", []),
                    "saved_at": entry.get("saved_at", ""),
                    "score": score,
                    "snippet": snippet,
                })
            return {
                "tool": "knowledge",
                "action": "search",
                "query": query,
                "total_entries": len(entries),
                "results": results,
            }

        # ── LIST ──────────────────────────────────────────────────────────────
        if action == "list":
            return {
                "tool": "knowledge",
                "action": "list",
                "total_entries": len(entries),
                "entries": [
                    {
                        "id": e["id"],
                        "title": e["title"],
                        "url": e.get("url", ""),
                        "tags": e.get("tags", []),
                        "saved_at": e.get("saved_at", ""),
                        "char_count": e.get("char_count", len(e.get("content", ""))),
                    }
                    for e in entries
                ],
            }

        # ── DELETE ────────────────────────────────────────────────────────────
        if action == "delete":
            if not entry_id:
                return err("knowledge", ValueError("entry_id is required for action=delete"))
            before = len(entries)
            entries = [e for e in entries if e["id"] != entry_id]
            if len(entries) == before:
                return {"tool": "knowledge", "action": "delete", "status": "not_found", "entry_id": entry_id}
            _save_db(entries)
            return {"tool": "knowledge", "action": "delete", "status": "deleted", "entry_id": entry_id}

        return err("knowledge", ValueError(f"Unknown action: {action}. Use save/search/list/delete."))

    except Exception as exc:
        return err("knowledge", exc)
