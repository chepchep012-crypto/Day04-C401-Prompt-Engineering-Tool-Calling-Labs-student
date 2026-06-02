from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

# Domains considered editorially reliable for news / research
_TRUSTED_DOMAINS: frozenset[str] = frozenset({
    # Major newspapers / wire services
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "theguardian.com",
    "nytimes.com", "washingtonpost.com", "ft.com", "economist.com",
    "bloomberg.com", "wsj.com", "forbes.com", "time.com",
    # Tech / science media
    "nature.com", "science.org", "technologyreview.com", "wired.com",
    "arstechnica.com", "techcrunch.com", "theverge.com", "venturebeat.com",
    "spectrum.ieee.org", "sciencedirect.com", "springer.com",
    # Academic / preprint
    "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "scholar.google.com",
    "semanticscholar.org", "openreview.net", "acm.org", "ieee.org",
    # Vietnamese reputable
    "vnexpress.net", "tuoitre.vn", "thanhnien.vn", "nhandan.vn",
    "dantri.com.vn", "vtv.vn",
    # Business
    "pitchbook.com", "crunchbase.com", "marketingweek.com",
    "insurancejournal.com", "skift.com",
})

_CLICKBAIT_PATTERNS = re.compile(
    r"(you won'?t believe|shocking|must see|click here|free money|"
    r"doctors hate|this one weird|number \d+ will|what happens next)",
    re.IGNORECASE,
)


def _domain(url: str) -> str:
    try:
        return urlparse(url.lower()).netloc.replace("www.", "").split(":")[0]
    except Exception:
        return ""


def _score_item(item: dict[str, Any]) -> dict[str, Any]:
    """Score a single item on 0–1 credibility scale using heuristic signals."""
    signals: dict[str, bool] = {}
    url = item.get("url", "") or ""
    title = item.get("title", "") or ""
    summary = item.get("summary", "") or ""
    authors = item.get("authors") or item.get("author") or ""
    published = item.get("published") or item.get("date") or ""
    source = item.get("source", "") or _domain(url)

    # Signal: HTTPS
    signals["https"] = url.startswith("https://")

    # Signal: trusted domain
    dom = _domain(url) or source.lower()
    signals["trusted_domain"] = any(dom.endswith(td) for td in _TRUSTED_DOMAINS)

    # Signal: has author info
    signals["has_author"] = bool(authors)

    # Signal: has publication date
    signals["has_date"] = bool(published)

    # Signal: meaningful summary (> 80 chars)
    signals["has_summary"] = len(summary.strip()) > 80

    # Signal: title not ALL CAPS
    signals["title_not_shouting"] = not (title.isupper() and len(title) > 10)

    # Signal: no clickbait patterns in title
    signals["no_clickbait"] = not bool(_CLICKBAIT_PATTERNS.search(title))

    # Signal: title not excessively punctuated (≤ 3 ! or ?)
    signals["no_excessive_punctuation"] = (title.count("!") + title.count("?")) <= 3

    # Weighted sum (trusted_domain and no_clickbait weigh more)
    weights = {
        "https": 1,
        "trusted_domain": 3,
        "has_author": 1,
        "has_date": 1,
        "has_summary": 1,
        "title_not_shouting": 1,
        "no_clickbait": 2,
        "no_excessive_punctuation": 1,
    }
    total_weight = sum(weights.values())
    earned = sum(weights[k] for k, v in signals.items() if v)
    score = round(earned / total_weight, 3)

    label = "high" if score >= 0.75 else ("medium" if score >= 0.40 else "low")

    return {
        "title": title or url,
        "url": url,
        "source": source,
        "score": score,
        "label": label,
        "signals": signals,
    }


def assess_credibility(
    items: list[dict[str, Any]] | None = None,
    text: str = "",
    url: str = "",
) -> dict[str, Any]:
    """Assess the credibility of content items using heuristic signals.

    Signals checked per item:
    - HTTPS URL
    - Domain in curated trusted-source list
    - Has author information
    - Has publication date
    - Has substantive summary (> 80 chars)
    - Title not all-caps shouting
    - No clickbait phrases in title
    - No excessive ! / ? in title

    When `items` is empty and `text`/`url` are provided, wraps them as a
    single synthetic item for scoring.
    """
    if not items and (text or url):
        items = [{"title": text[:120] if text else url, "url": url, "summary": text}]

    items = items or []
    scored = [_score_item(item) for item in items]

    overall = round(sum(s["score"] for s in scored) / len(scored), 3) if scored else 0.0
    overall_label = "high" if overall >= 0.75 else ("medium" if overall >= 0.40 else "low")

    return {
        "tool": "credibility",
        "overall_score": overall,
        "overall_label": overall_label,
        "item_count": len(scored),
        "items": scored,
    }
