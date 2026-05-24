"""Shared Claude section revision + apply helpers for review and post-render shell."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel

from .agents.section_reviser import revise_section
from .schema import REVIEWABLE_SECTIONS, Resume

# Sections + PDF layout order editable via `edit <name>` / `edit order`
EDITABLE_SECTIONS: list[str] = REVIEWABLE_SECTIONS + ["section_order"]
from .utils.diff import render_full_section, render_section_diff
from .utils.prompts import ask_confirm


def apply_section(resume: Resume, section: str, value: Any) -> Resume:
    data = resume.model_dump()
    data[section] = value
    return Resume.model_validate(data)


def revise_section_from_feedback(
    *,
    section: str,
    current_value: Any,
    feedback: str,
    config: dict,
    resume_context: Resume,
    prior_feedback: list[str] | None = None,
) -> Any:
    """Call Claude to revise a section; propagates API/validation errors."""
    return revise_section(
        section=section,
        current_value=current_value,
        feedback=feedback,
        config=config,
        resume_context=resume_context,
        prior_feedback=prior_feedback,
    )


def apply_section_edit_with_confirm(
    *,
    console: Console,
    resume: Resume,
    section: str,
    feedback: str,
    config: dict,
    current_value: Any | None = None,
    confirm_message: str = "Apply changes?",
) -> Resume | None:
    """Revise one section from feedback; show diff; return updated resume if user confirms."""
    if section not in EDITABLE_SECTIONS:
        raise ValueError(
            f"Unknown section {section!r}. Valid: {', '.join(EDITABLE_SECTIONS)}, or use `edit order`"
        )

    old_value = (
        current_value if current_value is not None else resume.section_payload(section)
    )
    console.print("[dim]Sending feedback to Claude...[/dim]")

    try:
        new_value = revise_section_from_feedback(
            section=section,
            current_value=old_value,
            feedback=feedback,
            config=config,
            resume_context=resume,
        )
    except Exception as exc:
        console.print(
            Panel(
                f"Could not apply feedback: {exc}",
                title="Revision failed",
                border_style="red",
            )
        )
        return None

    render_section_diff(console, section, old_value, new_value)
    render_full_section(console, f"{section} (proposed)", new_value)

    if not ask_confirm(console, confirm_message, default=True):
        console.print("[dim]Discarded — resume unchanged.[/dim]")
        return None

    return apply_section(resume, section, new_value)
