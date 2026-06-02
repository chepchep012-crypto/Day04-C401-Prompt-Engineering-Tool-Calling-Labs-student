from __future__ import annotations

import re
from collections import Counter
from typing import Any

from tools._shared import fold_text, terms


def _bigrams(word_list: list[str]) -> list[str]:
    """Return adjacent word pairs as 'w1 w2' strings."""
    return [f"{word_list[i]} {word_list[i + 1]}" for i in range(len(word_list) - 1)]


def extract_keywords(
    text: str = "",
    items: list[dict[str, Any]] | None = None,
    top_k: int = 10,
    include_bigrams: bool = True,
) -> dict[str, Any]:
    """Extract the most prominent keywords from text or a list of items.

    When `items` is provided, concatenates title + summary of each item.
    Unigrams and optional bigrams are counted; stopwords are removed via
    the shared `terms()` helper. Returns the top_k by frequency.
    """
    if items:
        combined = " ".join(
            " ".join(filter(None, [item.get("title", ""), item.get("summary", "")]))
            for item in items
        )
        text = combined + " " + text

    if not text.strip():
        return {"tool": "keywords", "keywords": [], "top_k": top_k, "source_length": 0}

    folded = fold_text(text)
    raw_words = re.findall(r"[a-z0-9]+", folded)

    unigrams = [w for w in raw_words if len(w) > 2 and w in terms(text)]
    counts: Counter[str] = Counter(unigrams)

    if include_bigrams:
        bg = _bigrams(raw_words)
        # Only keep bigrams where both words are non-stopword
        valid_unigram_set = set(unigrams)
        for pair in bg:
            w1, w2 = pair.split()
            if w1 in valid_unigram_set and w2 in valid_unigram_set:
                counts[pair] += 1

    top = counts.most_common(top_k)
    keywords = [{"keyword": kw, "count": cnt} for kw, cnt in top]

    return {
        "tool": "keywords",
        "top_k": top_k,
        "source_length": len(text),
        "keywords": keywords,
    }
