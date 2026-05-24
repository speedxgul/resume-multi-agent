"""TTY-safe prompts with proper arrow-key / line editing support."""

from __future__ import annotations

import re

from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import confirm as pt_confirm
from rich.console import Console

# Arrow keys and other escape sequences that leak into naive stdin reads.
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[0-9;]*[A-Za-z]|\x1b\].*?\x07")


def clean_tty_input(text: str) -> str:
    return _ANSI_ESCAPE.sub("", text).strip()


def ask_ynf(console: Console, section: str, *, default: str = "y") -> str:
    """Ask accept (y), reject (n), or feedback (f). Single-letter choice only."""
    console.print(
        f"[bold]{section}[/bold] — [green]y[/green]=accept  "
        f"[red]n[/red]=reject  [yellow]f[/yellow]=give feedback"
    )
    console.print(
        "[dim]Type y, n, or f then Enter. "
        "For longer edits, type [bold]f[/bold] first, then enter your feedback.[/dim]"
    )

    while True:
        raw = prompt(
            f"{section} [y/n/f] ",
            default=default,
        ).strip().lower()
        raw = clean_tty_input(raw)

        if raw in ("y", "n", "f"):
            return raw

        if len(raw) > 1:
            console.print(
                "[yellow]That looks like feedback text. "
                "Press [bold]f[/bold] then Enter, then paste your feedback on the next line.[/yellow]"
            )
            continue

        console.print("[yellow]Please enter y, n, or f.[/yellow]")


def ask_feedback(console: Console) -> str:
    """Free-form feedback with readline-style editing (arrow keys work)."""
    console.print("[cyan]Your feedback[/cyan] (what should change?)")
    text = prompt("> ", multiline=False)
    return clean_tty_input(text)


def ask_confirm(console: Console, message: str, *, default: bool = True) -> bool:
    console.print(message)
    return pt_confirm("", default=default)
