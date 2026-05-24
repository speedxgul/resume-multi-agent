"""Human-in-the-loop section review before writing LaTeX."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel

from .revision import apply_section, apply_section_edit_with_confirm
from .schema import REVIEWABLE_SECTIONS, Resume
from .utils.diff import render_full_section, render_section_diff
from .utils.prompts import ask_confirm, ask_feedback, ask_ynf


def _empty_resume_from_contact(resume: Resume) -> Resume:
    """Baseline for diffing when we only have synthesized output."""
    return Resume(contact=resume.contact)


def _review_one_section(
    *,
    section: str,
    baseline_value: Any,
    proposed_value: Any,
    approved: Resume,
    config: dict,
    console: Console,
) -> tuple[Resume, Any]:
    """Review a single section with accept / reject / feedback loop."""
    candidate = proposed_value

    while True:
        render_section_diff(console, section, baseline_value, candidate)

        choice = ask_ynf(console, section, default="y")

        if choice == "y":
            approved = apply_section(approved, section, candidate)
            return approved, candidate

        if choice == "n":
            approved = apply_section(approved, section, baseline_value)
            console.print(f"[dim]Kept previous {section}.[/dim]")
            return approved, baseline_value

        feedback = ask_feedback(console)
        if not feedback:
            console.print("[yellow]Empty feedback — try again.[/yellow]")
            continue

        updated = apply_section_edit_with_confirm(
            console=console,
            resume=approved,
            section=section,
            feedback=feedback,
            config=config,
            current_value=candidate,
            confirm_message="Apply this revision to the draft?",
        )
        if updated is None:
            continue

        candidate = updated.section_payload(section)
        approved = updated
        console.print("[green]Updated — review the diff below.[/green]")
        render_full_section(console, f"{section} (revised)", candidate)


def review_resume(
    proposed: Resume,
    *,
    baseline: Resume | None = None,
    config: dict | None = None,
    console: Console | None = None,
) -> Resume:
    """Walk through sections; accept, reject, or iteratively refine via LLM feedback."""
    console = console or Console()
    config = config or {}
    baseline = baseline or _empty_resume_from_contact(proposed)
    approved = proposed

    console.print("\n[bold cyan]Review proposed resume updates[/bold cyan]")
    console.print(
        "For each section:\n"
        "  [green]y[/green] — accept as shown\n"
        "  [red]n[/red] — keep the previous/current version\n"
        "  [yellow]f[/yellow] — describe changes; Claude revises this section (repeat until you accept)\n"
    )

    for section in REVIEWABLE_SECTIONS:
        console.rule(f"[bold]{section}[/bold]")
        baseline_value = baseline.section_payload(section)
        proposed_value = proposed.section_payload(section)

        approved, _ = _review_one_section(
            section=section,
            baseline_value=baseline_value,
            proposed_value=proposed_value,
            approved=approved,
            config=config,
            console=console,
        )
        proposed = apply_section(proposed, section, approved.section_payload(section))

    if ask_confirm(console, "\nWrite final resume files?", default=True):
        return approved

    raise SystemExit("Review cancelled — no files written.")
