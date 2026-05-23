#!/usr/bin/env python3
"""Resume agent CLI — collect sources, synthesize, review, render."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from src.config import load_config
from src.graph import run_pipeline
from src.renderer import write_outputs
from src.reviewer import review_resume
from src.schema import Resume
from src.utils.pdf import extract_text

app = typer.Typer(
    name="resume-agent",
    help="Multi-agent resume updater: GitHub, LinkedIn paste, URLs, manual context -> LaTeX/PDF.",
)
console = Console()


@app.command()
def update(
    pdf: Path = typer.Option(
        Path("inputs/resume.pdf"),
        "--pdf",
        help="Path to your current resume PDF.",
    ),
    config: Path = typer.Option(
        Path("config.yaml"),
        "--config",
        help="Path to config.yaml.",
    ),
    skip_review: bool = typer.Option(
        False,
        "--skip-review",
        help="Accept all synthesizer changes without interactive review.",
    ),
    no_compile: bool = typer.Option(
        False,
        "--no-compile",
        help="Write .tex and .json only; skip PDF compilation.",
    ),
):
    """Run the full pipeline: collect -> synthesize -> review -> render."""
    cfg = load_config(config)

    if not pdf.exists():
        console.print(
            f"[red]Resume PDF not found at {pdf}[/red]\n"
            "Place your current resume at inputs/resume.pdf or pass --pdf."
        )
        raise typer.Exit(code=1)

    console.print(f"[bold]Extracting text from[/bold] {pdf}")
    existing_text = extract_text(pdf)
    if not existing_text.strip():
        console.print("[yellow]Warning: PDF extraction returned little/no text.[/yellow]")

    profile = cfg.get("profile", {})
    if not profile.get("name") or not profile.get("email"):
        console.print(
            "[yellow]Tip: set profile.name and profile.email in config.yaml "
            "so contact info is always correct.[/yellow]"
        )

    console.print("[bold cyan]Running collectors + synthesizer...[/bold cyan]")
    state = run_pipeline(
        config=cfg,
        existing_resume_text=existing_text,
        profile=profile,
    )

    proposed: Resume | None = state.get("synthesized")
    if not proposed:
        console.print("[red]Synthesizer did not return a resume.[/red]")
        raise typer.Exit(code=1)

    # Save raw synthesizer output for inspection.
    out_cfg = cfg.get("output", {})
    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    draft_path = out_dir / "resume.draft.json"
    draft_path.write_text(
        json.dumps(proposed.model_dump(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    console.print(f"Draft saved to [green]{draft_path}[/green]")

    if skip_review:
        final = proposed
    else:
        final = review_resume(proposed, config=cfg, console=console)

    paths = write_outputs(
        final,
        output_dir=out_dir,
        basename=out_cfg.get("resume_basename", "resume"),
        compile=not no_compile and bool(out_cfg.get("compile_pdf", True)),
    )

    console.print("\n[bold green]Done![/bold green]")
    for kind, path in paths.items():
        console.print(f"  {kind}: {path}")


@app.command()
def init_inputs():
    """Create starter input files under inputs/."""
    inputs = Path("inputs")
    inputs.mkdir(exist_ok=True)

    templates = {
        "linkedin_profile.txt": (
            "# Paste your LinkedIn profile text here.\n"
            "# Open LinkedIn -> your profile -> select all -> copy.\n"
            "# Include Experience, Education, About, and Featured sections.\n"
        ),
        "twitter_profile.txt": (
            "# Paste your Twitter/X bio and pinned tweets here.\n"
            "# Include links to notable threads or project announcements.\n"
        ),
        "manual_context.md": (
            "# Free-form context the agents should know about\n"
            "# Links below are auto-fetched (GitHub README, Devpost, etc.)\n\n"
            "## Recent work\n"
            "- \n\n"
            "## Hackathon wins\n"
            "- Event name, prize, project — repo: https://github.com/you/project\n"
            "- Or markdown: [project](https://github.com/you/project) — Devpost: https://devpost.com/software/example\n\n"
            "## Achievements / awards\n"
            "- \n\n"
            "## Anything else\n"
            "- \n"
        ),
        "urls.txt": (
            "# One URL per line — project pages, Devpost wins, blog posts, certificates\n"
            "# https://devpost.com/software/example\n"
        ),
    }

    for name, content in templates.items():
        path = inputs / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            console.print(f"Created {path}")
        else:
            console.print(f"[dim]Already exists: {path}[/dim]")

    console.print(
        "\nNext steps:\n"
        "1. Copy .env.example -> .env and set ANTHROPIC_API_KEY\n"
        "2. Fill in config.yaml (profile + github_username)\n"
        "3. Put your current resume PDF at inputs/resume.pdf\n"
        "4. Run: python -m src.main update"
    )


def main():
    app()


if __name__ == "__main__":
    main()
