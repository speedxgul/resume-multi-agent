"""Human-in-the-loop section review before writing LaTeX."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from .agents.section_reviser import revise_section
from .schema import REVIEWABLE_SECTIONS, Resume
from .utils.diff import render_full_section, render_section_diff


def _empty_resume_from_contact(resume: Resume) -> Resume:
    """Baseline for diffing when we only have synthesized output."""
    return Resume(contact=resume.contact)


def _apply_section(resume: Resume, section: str, value: Any) -> Resume:
    data = resume.model_dump()
    data[section] = value
    return Resume.model_validate(data)


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
    feedback_history: list[str] = []

    while True:
        render_section_diff(console, section, baseline_value, candidate)

        choice = Prompt.ask(
            f"[bold]{section}[/bold] — [green]y[/green]=accept  "
            f"[red]n[/red]=reject  [yellow]f[/yellow]=give feedback",
            choices=["y", "n", "f"],
            default="y",
        )

        if choice == "y":
            approved = _apply_section(approved, section, candidate)
            return approved, candidate

        if choice == "n":
            approved = _apply_section(approved, section, baseline_value)
            console.print(f"[dim]Kept previous {section}.[/dim]")
            return approved, baseline_value

        feedback = Prompt.ask(
            "[cyan]Your feedback[/cyan] (what should change?)",
        ).strip()
        if not feedback:
            console.print("[yellow]Empty feedback — try again.[/yellow]")
            continue

        feedback_history.append(feedback)
        console.print("[dim]Sending feedback to Claude...[/dim]")

        try:
            revised = revise_section(
                section=section,
                current_value=candidate,
                feedback=feedback,
                config=config,
                resume_context=approved,
                prior_feedback=feedback_history[:-1] or None,
            )
        except Exception as exc:
            console.print(
                Panel(
                    f"Could not apply feedback: {exc}\nTry rephrasing or accept/reject.",
                    title="Revision failed",
                    border_style="red",
                )
            )
            continue

        candidate = revised
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
        # Keep proposed in sync for downstream sections that read approved context
        proposed = _apply_section(proposed, section, approved.section_payload(section))

    if Confirm.ask("\nWrite final resume files?", default=True):
        return approved

    raise SystemExit("Review cancelled — no files written.")
