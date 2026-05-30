"""LangGraph node wrappers for collectors and synthesizer."""

from __future__ import annotations

from typing import Any

from .crustdata import collect_crustdata
from .github import collect_github
from .manual import collect_linkedin, collect_manual_context, collect_twitter
from .synthesizer import synthesize_resume
from .urls import collect_urls


def node_collect_crustdata(state: dict[str, Any]) -> dict[str, Any]:
    return {"sources": collect_crustdata(state["config"])}


def node_collect_github(state: dict[str, Any]) -> dict[str, Any]:
    return {"sources": collect_github(state["config"])}


def node_collect_linkedin(state: dict[str, Any]) -> dict[str, Any]:
    return {"sources": collect_linkedin(state["config"])}


def node_collect_twitter(state: dict[str, Any]) -> dict[str, Any]:
    return {"sources": collect_twitter(state["config"])}


def node_collect_manual(state: dict[str, Any]) -> dict[str, Any]:
    return {"sources": collect_manual_context(state["config"])}


def node_collect_urls(state: dict[str, Any]) -> dict[str, Any]:
    return {"sources": collect_urls(state["config"])}


def node_synthesize(state: dict[str, Any]) -> dict[str, Any]:
    resume = synthesize_resume(
        config=state["config"],
        existing_resume_text=state.get("existing_resume_text", ""),
        profile=state.get("profile", {}),
        sources=state.get("sources", {}),
    )
    return {"synthesized": resume}
