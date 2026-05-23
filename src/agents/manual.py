"""Load pasted LinkedIn, Twitter, and manual context files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import read_text_file


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
    return _load_named_file(config, "manual_context_file", "manual_context")
