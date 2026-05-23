"""LangGraph workflow: parallel collectors -> synthesizer."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .agents.nodes import (
    node_collect_github,
    node_collect_linkedin,
    node_collect_manual,
    node_collect_twitter,
    node_collect_urls,
    node_synthesize,
)
from .state import GraphState


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("collect_github", node_collect_github)
    graph.add_node("collect_linkedin", node_collect_linkedin)
    graph.add_node("collect_twitter", node_collect_twitter)
    graph.add_node("collect_manual", node_collect_manual)
    graph.add_node("collect_urls", node_collect_urls)
    graph.add_node("synthesize", node_synthesize)

    # Fan-out from START to all collectors in parallel.
    for node in (
        "collect_github",
        "collect_linkedin",
        "collect_twitter",
        "collect_manual",
        "collect_urls",
    ):
        graph.add_edge(START, node)
        graph.add_edge(node, "synthesize")

    graph.add_edge("synthesize", END)
    return graph.compile()


def run_pipeline(
    *,
    config: dict,
    existing_resume_text: str,
    profile: dict,
) -> dict:
    app = build_graph()
    return app.invoke(
        {
            "config": config,
            "existing_resume_text": existing_resume_text,
            "profile": profile,
            "sources": {},
        }
    )
