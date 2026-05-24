"""Render structured Resume to LaTeX and optionally compile PDF."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .schema import Resume
from .utils.latex import compile_pdf, escape, escape_url


def _env() -> Environment:
    templates_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["e"] = escape
    env.filters["url"] = escape_url
    return env


def render_latex(resume: Resume) -> str:
    template = _env().get_template("resume.tex.j2")
    return template.render(
        contact=resume.contact,
        summary=resume.summary,
        experience=resume.experience,
        projects=resume.projects,
        education=resume.education,
        skills=resume.skills,
        achievements=resume.achievements,
    )


def load_resume_json(path: str | Path) -> Resume:
    """Load a resume from a JSON file written by write_outputs."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Resume.model_validate(data)


def compile_resume_pdf(tex_path: Path, output_dir: Path | None = None) -> Path:
    """Compile .tex to PDF; raises if no compiler or compilation fails."""
    out = output_dir or tex_path.parent
    pdf = compile_pdf(tex_path.resolve(), out.resolve())
    if pdf is None:
        raise RuntimeError(
            "No LaTeX compiler found. Install tectonic or TeX Live (pdflatex)."
        )
    return pdf


def write_outputs(
    resume: Resume,
    *,
    output_dir: str | Path = "outputs",
    basename: str = "resume",
    compile: bool = True,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / f"{basename}.json"
    tex_path = out / f"{basename}.tex"

    json_path.write_text(
        json.dumps(resume.model_dump(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tex_path.write_text(render_latex(resume), encoding="utf-8")

    result = {"json": json_path, "tex": tex_path}
    if compile:
        pdf = compile_pdf(tex_path, out)
        if pdf:
            result["pdf"] = pdf
    return result
