"""LangGraph state shared across all nodes."""

from __future__ import annotations

from typing import Annotated, TypedDict

from .schema import Resume


def _merge_dict(left: dict | None, right: dict | None) -> dict:
    """Reducer that merges per-source payloads from parallel collector nodes."""
    out: dict = dict(left or {})
    out.update(right or {})
    return out


class GraphState(TypedDict, total=False):
    """Shared state across the LangGraph run."""

    # --- inputs ---
    config: dict
    existing_resume_text: str         # raw text extracted from the user's PDF
    profile: dict                     # static contact info from config.yaml

    # --- collected, in parallel ---
    # Each collector writes into `sources[<name>] = {...}` via the merge reducer.
    sources: Annotated[dict, _merge_dict]

    # --- synthesizer output ---
    synthesized: Resume | None

    # --- post-review (filled by CLI, not by a graph node) ---
    approved: Resume | None
