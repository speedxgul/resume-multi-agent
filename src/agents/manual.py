"""Load pasted LinkedIn, Twitter, and manual context files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import read_text_file
from .urls import collect_urls_from_text, listed_url_keys


def _load_named_file(config: dict, key: str, label: str) -> dict[str, Any]:
    rel = config.get("sources", {}).get(key, "")
    if not rel:
        return {label: {"status": "skipped", "reason": f"{key} not configured"}}

    text = read_text_file(rel)
    if not text:
        return {
            label: {
                "status": "skipped",
                "reason": f"file missing or empty: {rel}",
            }
        }

    return {
        label: {
            "status": "ok",
            "path": str(Path(rel)),
            "text": text,
        }
    }


def collect_linkedin(config: dict) -> dict[str, Any]:
    return _load_named_file(config, "linkedin_profile_file", "linkedin")


def collect_twitter(config: dict) -> dict[str, Any]:
    return _load_named_file(config, "twitter_profile_file", "twitter")


def collect_manual_context(config: dict) -> dict[str, Any]:
    rel = config.get("sources", {}).get("manual_context_file", "")
    if not rel:
        return {
            "manual_context": {
                "status": "skipped",
                "reason": "manual_context_file not configured",
            }
        }

    text = read_text_file(rel)
    if not text:
        return {
            "manual_context": {
                "status": "skipped",
                "reason": f"file missing or empty: {rel}",
            }
        }

    skip = listed_url_keys(config)
    embedded = collect_urls_from_text(
        text,
        skip_normalized=skip,
        source_label="manual_context.md",
    )

    return {
        "manual_context": {
            "status": "ok",
            "path": str(Path(rel)),
            "text": text,
            "embedded_links": embedded,
        }
    }
