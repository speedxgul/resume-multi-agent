"""Human-in-the-loop section review before writing LaTeX."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.prompt import Confirm, Prompt

from .schema import REVIEWABLE_SECTIONS, Resume
from .utils.diff import render_full_section, render_section_diff


def _empty_resume_from_contact(resume: Resume) -> Resume:
    """Baseline for diffing when we only have synthesized output."""
    return Resume(contact=resume.contact)


def _apply_section(resume: Resume, section: str, value: Any) -> Resume:
    data = resume.model_dump()
    data[section] = value
    return Resume.model_validate(data)


def review_resume(
    proposed: Resume,
    *,
    baseline: Resume | None = None,
    console: Console | None = None,
) -> Resume:
    """Walk through proposed sections; user accepts, rejects, or edits each one."""
    console = console or Console()
    baseline = baseline or _empty_resume_from_contact(proposed)
    approved = proposed

    console.print("\n[bold cyan]Review proposed resume updates[/bold cyan]")
    console.print(
        "For each section: [green]y[/green]=accept, [red]n[/red]=keep current, "
        "[yellow]e[/yellow]=edit JSON manually.\n"
    )

    for section in REVIEWABLE_SECTIONS:
        old_value = baseline.section_payload(section)
        new_value = proposed.section_payload(section)
        render_section_diff(console, section, old_value, new_value)

        choice = Prompt.ask(
            f"Accept changes to [bold]{section}[/bold]?",
            choices=["y", "n", "e"],
            default="y",
        )

        if choice == "n":
            approved = _apply_section(approved, section, old_value)
        elif choice == "e":
            render_full_section(console, section, new_value)
            raw = Prompt.ask("Paste edited JSON for this section")
            try:
                parsed = json.loads(raw)
                approved = _apply_section(approved, section, parsed)
            except json.JSONDecodeError as exc:
                console.print(f"[red]Invalid JSON ({exc}); keeping proposed version.[/red]")
        # choice == "y" keeps proposed section as-is

    if Confirm.ask("\nWrite final resume files?", default=True):
        return approved

    raise SystemExit("Review cancelled — no files written.")
