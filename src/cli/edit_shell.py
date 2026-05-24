"""Post-render interactive shell: compile PDF and Claude-powered edits."""

from __future__ import annotations

import platform
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..agents.resume_reviser import revise_resume
from ..renderer import compile_resume_pdf, load_resume_json, write_outputs
from ..revision import apply_section_edit_with_confirm
from ..schema import REVIEWABLE_SECTIONS, Resume
from ..utils.diff import render_full_section, render_section_diff
from ..utils.prompts import ask_confirm, ask_feedback
from ..utils.section_order import format_section_order, move_section

HELP_TEXT = """
[bold]Commands[/bold]
  help              Show this help
  pdf, compile      Compile outputs/resume.tex → PDF
  open              Open the PDF in your default viewer
  show [section]    Show section JSON (reloads from disk first; try `show contact`, `show order`)
  show order        Show PDF section order (section_order)
  order             Same as `show order`
  move A above B    Move section block A above B (instant, no Claude)
  move A below B    Move section block A below B
  reload            Reload resume.json from disk into memory
  edit <section>    Revise one section with Claude (feedback prompt)
  edit order        Reorder PDF sections with natural-language feedback
  edit              Revise the full resume with Claude
  save              Reload resume.json from disk, then write .tex (+ .json)
  quit, exit        Leave edit mode

[dim]Section blocks:[/dim] summary, experience, projects, skills, education, achievements
[dim]Example:[/dim] move education above experience

[dim]Tip: edit outputs/resume.json in your editor, save the file, then run[/dim]
[dim]`save` and `pdf` here — no need to restart the shell.[/dim]
[dim]Inline links: ask Claude to use [visible text](https://url) in any text field.[/dim]
[dim]Reorder jobs/projects: ask Claude to move items in the array (2nd from bottom = index N-2).[/dim]
"""


@dataclass
class ShellState:
    resume: Resume
    config: dict
    output_dir: Path
    basename: str
    json_path: Path
    tex_path: Path
    pdf_path: Path

    @classmethod
    def from_config(cls, config: dict, *, json_path: Path | None = None) -> ShellState:
        out_cfg = config.get("output", {})
        output_dir = Path("outputs")
        basename = out_cfg.get("resume_basename", "resume")
        jp = json_path or (output_dir / f"{basename}.json")
        if not jp.exists():
            raise FileNotFoundError(f"Resume JSON not found: {jp}")

        return cls(
            resume=load_resume_json(jp),
            config=config,
            output_dir=output_dir,
            basename=basename,
            json_path=jp,
            tex_path=output_dir / f"{basename}.tex",
            pdf_path=output_dir / f"{basename}.pdf",
        )

    def auto_compile_after_edit(self) -> bool:
        return bool(self.config.get("output", {}).get("auto_compile_after_edit", False))


def _open_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", str(path)], check=False)
    elif system == "Windows":
        subprocess.run(f'start "" {shlex.quote(str(path))}', shell=True, check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def reload_from_disk(state: ShellState, console: Console) -> None:
    """Load resume.json from disk into shell memory (picks up manual editor changes)."""
    try:
        state.resume = load_resume_json(state.json_path)
    except Exception as exc:
        console.print(
            Panel(
                f"Could not load {state.json_path}:\n{exc}\n"
                "Fix the JSON file and try again.",
                title="Reload failed",
                border_style="red",
            )
        )
        raise


def _save_resume(
    state: ShellState,
    *,
    compile_pdf: bool = False,
    reload: bool = True,
    console: Console | None = None,
) -> dict[str, Path]:
    if reload:
        if console is None:
            state.resume = load_resume_json(state.json_path)
        else:
            reload_from_disk(state, console)
    return write_outputs(
        state.resume,
        output_dir=state.output_dir,
        basename=state.basename,
        compile=compile_pdf,
    )


def _show_overview(console: Console, resume: Resume) -> None:
    table = Table(title="Resume overview")
    table.add_column("Section")
    table.add_column("Summary")
    table.add_row("contact", resume.contact.name)
    table.add_row("summary", (resume.summary or "")[:80] or "(empty)")
    table.add_row("experience", str(len(resume.experience)))
    table.add_row("projects", str(len(resume.projects)))
    table.add_row("education", str(len(resume.education)))
    table.add_row("skills", str(len(resume.skills)))
    table.add_row("achievements", str(len(resume.achievements)))
    table.add_row("section_order", " → ".join(resume.section_order))
    console.print(table)


def _cmd_pdf(console: Console, state: ShellState) -> None:
    if not state.tex_path.exists():
        _save_resume(state, compile_pdf=False, console=console)
    try:
        pdf = compile_resume_pdf(state.tex_path, state.output_dir)
        state.pdf_path = pdf
        console.print(f"[green]Compiled:[/green] {pdf}")
    except Exception as exc:
        console.print(Panel(str(exc), title="Compile failed", border_style="red"))


def _cmd_edit_section(console: Console, state: ShellState, section: str) -> None:
    feedback = ask_feedback(console)
    if not feedback:
        console.print("[yellow]Empty feedback — cancelled.[/yellow]")
        return

    updated = apply_section_edit_with_confirm(
        console=console,
        resume=state.resume,
        section=section,
        feedback=feedback,
        config=state.config,
    )
    if updated is None:
        return

    state.resume = updated
    paths = _save_resume(
        state,
        compile_pdf=state.auto_compile_after_edit(),
        reload=False,
    )
    console.print(f"[green]Saved[/green] {paths['json']} and {paths['tex']}")
    if "pdf" in paths:
        console.print(f"[green]Compiled[/green] {paths['pdf']}")
    else:
        console.print("[dim]Run `pdf` to refresh the PDF.[/dim]")


def _cmd_order(console: Console, state: ShellState) -> None:
    console.print("[bold]PDF section order[/bold] (top → bottom):\n")
    console.print(format_section_order(state.resume.section_order))
    console.print(
        "\n[dim]Use `move education above experience` to reorder blocks instantly.[/dim]"
    )


def _cmd_move(console: Console, state: ShellState, parts: list[str]) -> None:
    """Parse: move <block> above|below|before|after <anchor>"""
    if len(parts) < 4:
        console.print(
            "[red]Usage:[/red] move <section> above|below <section>\n"
            "[dim]Example: move education above experience[/dim]"
        )
        return

    block = parts[1]
    direction = parts[2].lower()
    anchor = parts[3]

    before: str | None = None
    after: str | None = None
    if direction in ("above", "before"):
        before = anchor
    elif direction in ("below", "after"):
        after = anchor
    else:
        console.print(
            f"[red]Expected above/below/before/after, got {direction!r}.[/red]\n"
            "[dim]Example: move education above experience[/dim]"
        )
        return

    old_order = list(state.resume.section_order)
    try:
        new_order = move_section(old_order, block, before=before, after=after)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        return

    if new_order == old_order:
        console.print("[yellow]Section order unchanged.[/yellow]")
        return

    state.resume.section_order = new_order
    paths = _save_resume(
        state,
        compile_pdf=state.auto_compile_after_edit(),
        reload=False,
    )
    console.print("[green]Updated section order:[/green]")
    console.print(format_section_order(new_order))
    console.print(f"[green]Saved[/green] {paths['json']} and {paths['tex']}")
    if "pdf" in paths:
        console.print(f"[green]Compiled[/green] {paths['pdf']}")
    else:
        console.print("[dim]Run `pdf` to refresh the PDF.[/dim]")


def _cmd_edit_full(console: Console, state: ShellState) -> None:
    feedback = ask_feedback(console)
    if not feedback:
        console.print("[yellow]Empty feedback — cancelled.[/yellow]")
        return

    old = state.resume
    console.print("[dim]Sending feedback to Claude (full resume)...[/dim]")

    try:
        proposed = revise_resume(resume=old, feedback=feedback, config=state.config)
    except Exception as exc:
        console.print(
            Panel(str(exc), title="Revision failed", border_style="red"),
        )
        return

    for section in ["section_order", *REVIEWABLE_SECTIONS]:
        render_section_diff(
            console,
            section,
            old.section_payload(section),
            proposed.section_payload(section),
        )

    if not ask_confirm(console, "Apply full resume changes?", default=True):
        console.print("[dim]Discarded — resume unchanged.[/dim]")
        return

    state.resume = proposed
    paths = _save_resume(
        state,
        compile_pdf=state.auto_compile_after_edit(),
        reload=False,
    )
    console.print(f"[green]Saved[/green] {paths['json']} and {paths['tex']}")
    if "pdf" in paths:
        console.print(f"[green]Compiled[/green] {paths['pdf']}")
    else:
        console.print("[dim]Run `pdf` to refresh the PDF.[/dim]")


def _dispatch_line(console: Console, state: ShellState, line: str) -> bool:
    """Handle one command. Returns False to exit shell."""
    parts = line.strip().split()
    if not parts:
        return True

    cmd = parts[0].lower()
    arg = parts[1].lower() if len(parts) > 1 else ""

    if cmd in ("quit", "exit", "q"):
        return False

    if cmd == "help":
        console.print(HELP_TEXT)
        return True

    if cmd in ("pdf", "compile"):
        _cmd_pdf(console, state)
        return True

    if cmd == "open":
        if not state.pdf_path.exists():
            console.print("[yellow]PDF not found — run `pdf` first.[/yellow]")
            return True
        _open_path(state.pdf_path)
        console.print(f"[dim]Opened {state.pdf_path}[/dim]")
        return True

    if cmd == "reload":
        try:
            reload_from_disk(state, console)
            console.print(f"[green]Reloaded[/green] {state.json_path}")
            console.print(f"[dim]Contact location: {state.resume.contact.location or '(empty)'}[/dim]")
        except Exception:
            pass
        return True

    if cmd == "save":
        try:
            paths = _save_resume(state, compile_pdf=False, console=console)
            console.print(
                f"[green]Reloaded from disk and saved[/green] {paths['json']} and {paths['tex']}"
            )
        except Exception:
            pass
        return True

    if cmd == "order":
        try:
            reload_from_disk(state, console)
        except Exception:
            return True
        _cmd_order(console, state)
        return True

    if cmd == "move":
        _cmd_move(console, state, parts)
        return True

    if cmd == "show":
        try:
            reload_from_disk(state, console)
        except Exception:
            return True
        if arg in ("order", "section_order"):
            _cmd_order(console, state)
        elif arg == "contact":
            render_full_section(console, "contact", state.resume.contact.model_dump())
        elif arg and arg in REVIEWABLE_SECTIONS:
            render_full_section(console, arg, state.resume.section_payload(arg))
        elif arg:
            console.print(
                f"[red]Unknown section {arg!r}.[/red] "
                f"Valid: order, contact, {', '.join(REVIEWABLE_SECTIONS)}"
            )
        else:
            _show_overview(console, state.resume)
        return True

    if cmd == "edit":
        if arg in ("order", "section_order"):
            _cmd_edit_section(console, state, "section_order")
        elif arg:
            if arg not in REVIEWABLE_SECTIONS:
                console.print(
                    f"[red]Unknown section {arg!r}.[/red] "
                    f"Valid: order, {', '.join(REVIEWABLE_SECTIONS)}"
                )
                return True
            _cmd_edit_section(console, state, arg)
        else:
            _cmd_edit_full(console, state)
        return True

    console.print(f"[red]Unknown command {cmd!r}.[/red] Type `help`.")
    return True


def run_edit_shell(
    config: dict,
    *,
    json_path: Path | None = None,
    console: Console | None = None,
) -> None:
    """Interactive REPL for post-render PDF compile and Claude edits."""
    console = console or Console()

    try:
        state = ShellState.from_config(config, json_path=json_path)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise SystemExit(1) from exc

    console.print("\n[bold cyan]Edit mode[/bold cyan] — type [bold]help[/bold] for commands")
    console.print(f"Loaded [green]{state.json_path}[/green]\n")

    from prompt_toolkit import prompt

    while True:
        try:
            line = prompt("> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not _dispatch_line(console, state, line):
            console.print("[dim]Goodbye.[/dim]")
            break
