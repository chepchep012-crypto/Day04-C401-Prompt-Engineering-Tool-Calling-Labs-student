from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err


def translate_text(
    text: str = "",
    source_lang: str = "en",
    target_lang: str = "vi",
) -> dict[str, Any]:
    """Translate text using MyMemory free API (no API key required)."""
    try:
        if not text:
            raise ValueError("text is required")
        # MyMemory does not support 'auto' — default to 'en' if not specified
        src = source_lang if source_lang and source_lang != "auto" else "en"
        langpair = f"{src}|{target_lang}"
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": langpair},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        translated = data.get("responseData", {}).get("translatedText", "")
        match_quality = data.get("responseData", {}).get("match", 0)
        return {
            "tool": "translate",
            "original": text,
            "translated": translated,
            "source_lang": src,
            "target_lang": target_lang,
            "match_quality": match_quality,
        }
    except Exception as exc:
        return err("translate", exc)
