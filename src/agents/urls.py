"""Fetch and extract readable text from user-supplied URLs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import read_text_file
from ..utils.url_fetch import extract_urls, fetch_pages, normalize_url


def _urls_from_file(config: dict) -> tuple[list[str], str | None]:
    rel = config.get("sources", {}).get("urls_file", "inputs/urls.txt")
    raw = read_text_file(rel)
    if not raw:
        return [], rel

    urls: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls, rel


def collect_urls(config: dict) -> dict[str, Any]:
    urls, rel = _urls_from_file(config)
    if not urls:
        return {
            "urls": {
                "status": "skipped",
                "reason": f"file missing or empty: {rel}",
            }
        }

    pages = fetch_pages(urls)
    return {
        "urls": {
            "status": "ok",
            "path": str(Path(rel or "inputs/urls.txt")),
            "pages": pages,
        }
    }


def listed_url_keys(config: dict) -> set[str]:
    """Normalized URLs already listed in urls.txt (for deduping embedded fetches)."""
    urls, _ = _urls_from_file(config)
    return {normalize_url(u) for u in urls}


def collect_urls_from_text(
    text: str,
    *,
    skip_normalized: set[str] | None = None,
    source_label: str = "embedded",
) -> dict[str, Any]:
    """Extract and fetch URLs found inside arbitrary text (e.g. manual_context.md)."""
    found = extract_urls(text)
    if not found:
        return {
            "extracted_urls": [],
            "pages": [],
            "status": "ok",
            "source": source_label,
        }

    pages = fetch_pages(found, skip_normalized=skip_normalized)
    return {
        "extracted_urls": found,
        "pages": pages,
        "status": "ok",
        "source": source_label,
    }
