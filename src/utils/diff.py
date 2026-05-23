"""Pretty diff rendering for the review step."""

from __future__ import annotations

import difflib
import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text


def _serialize(value: Any) -> str:
    """Render a section payload as deterministic JSON text for diffing."""
    return json.dumps(value, indent=2, default=lambda o: o.model_dump() if hasattr(o, "model_dump") else str(o), sort_keys=False)


def render_section_diff(
    console: Console,
    section_name: str,
    old_value: Any,
    new_value: Any,
) -> None:
    """Print a colored unified diff for a single resume section."""
    old_text = _serialize(old_value).splitlines(keepends=False)
    new_text = _serialize(new_value).splitlines(keepends=False)

    diff = list(
        difflib.unified_diff(
            old_text,
            new_text,
            fromfile=f"current/{section_name}",
            tofile=f"proposed/{section_name}",
            lineterm="",
        )
    )

    if not diff:
        console.print(
            Panel.fit(
                Text(f"{section_name}: no changes proposed", style="dim"),
                border_style="dim",
            )
        )
        return

    body = Text()
    for line in diff:
        if line.startswith("+++") or line.startswith("---"):
            body.append(line + "\n", style="bold")
        elif line.startswith("@@"):
            body.append(line + "\n", style="cyan")
        elif line.startswith("+"):
            body.append(line + "\n", style="green")
        elif line.startswith("-"):
            body.append(line + "\n", style="red")
        else:
            body.append(line + "\n", style="dim")

    console.print(Panel(body, title=f"[bold]{section_name}[/bold]", border_style="yellow"))


def render_full_section(console: Console, section_name: str, value: Any) -> None:
    """Pretty-print a single section as JSON (used when editing)."""
    payload = _serialize(value)
    console.print(Panel(Syntax(payload, "json", theme="ansi_dark", word_wrap=True), title=section_name))
