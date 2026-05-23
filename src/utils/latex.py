"""LaTeX helpers: safe escaping + compilation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# Order matters: backslash first so we don't double-escape.
_LATEX_REPLACEMENTS: list[tuple[str, str]] = [
    ("\\", r"\textbackslash{}"),
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
]


def escape(text: str | None) -> str:
    """Escape arbitrary text for safe inclusion in LaTeX body."""
    if not text:
        return ""
    out = text
    for src, dst in _LATEX_REPLACEMENTS:
        out = out.replace(src, dst)
    return out


def escape_url(url: str | None) -> str:
    """URLs go inside \\href{...}{...}; only `%`, `#`, `\\` need escaping."""
    if not url:
        return ""
    return (
        url.replace("\\", r"\\")
        .replace("%", r"\%")
        .replace("#", r"\#")
    )


def compile_pdf(tex_path: Path, workdir: Path) -> Path | None:
    """Compile a .tex file to PDF, trying tectonic first, then pdflatex.

    Returns the path to the produced PDF, or None if no compiler was found.
    Raises RuntimeError on compilation failure when a compiler IS available.
    """
    tex_path = tex_path.resolve()
    workdir = workdir.resolve()

    if shutil.which("tectonic"):
        proc = subprocess.run(
            [
                "tectonic",
                "--keep-logs",
                "--outdir",
                str(workdir),
                str(tex_path),
            ],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"tectonic failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )
        return workdir / (tex_path.stem + ".pdf")

    if shutil.which("pdflatex"):
        # Run twice for references; -interaction=nonstopmode to avoid hanging.
        for _ in range(2):
            proc = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory",
                    str(workdir),
                    str(tex_path),
                ],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"pdflatex failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
                )
        return workdir / (tex_path.stem + ".pdf")

    return None
