"""Revise a single resume section from natural-language user feedback."""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter

from ..schema import Achievement, Education, Experience, Project, Resume
from ..utils.llm import complete_json

SECTION_SCHEMA_HINTS: dict[str, str] = {
    "summary": 'string or null, e.g. "Software engineer focused on ..."',
    "experience": (
        "array of objects: "
        '{company, role, location?, start_date, end_date?, bullets: string[]}'
    ),
    "projects": (
        "array of objects: "
        '{name, description, tech: string[], link?, bullets: string[]}'
    ),
    "skills": 'object mapping category -> string[], e.g. {"Languages": ["Python"]}',
    "education": (
        "array of objects: "
        '{institution, degree, field?, start_date?, end_date?, gpa?, coursework?}'
    ),
    "achievements": (
        "array of objects: {title, description?, date?, link?}"
    ),
}

_SECTION_VALIDATORS: dict[str, TypeAdapter[Any]] = {
    "summary": TypeAdapter(str | None),
    "experience": TypeAdapter(list[Experience]),
    "projects": TypeAdapter(list[Project]),
    "skills": TypeAdapter(dict[str, list[str]]),
    "education": TypeAdapter(list[Education]),
    "achievements": TypeAdapter(list[Achievement]),
}

SYSTEM_PROMPT = """You revise one section of a resume based on user feedback.

Rules:
- Apply the user's feedback precisely. Do not ignore requests.
- Do not invent employers, dates, metrics, or awards not supported by the current content or feedback.
- If feedback asks to remove something, remove it. If it asks to reword, reword. If it asks to add detail the user provided, add it.
- Keep bullets concise and ATS-friendly unless the user asks otherwise.
- Return ONLY valid JSON in this exact shape: {"value": <revised section value>}
- The "value" must match the section schema described in the user message.
- No markdown fences, no commentary outside JSON.
"""


def _validate_section(section: str, value: Any) -> Any:
    adapter = _SECTION_VALIDATORS.get(section)
    if adapter is None:
        raise ValueError(f"Unknown section: {section}")
    return adapter.validate_python(value)


def revise_section(
    *,
    section: str,
    current_value: Any,
    feedback: str,
    config: dict,
    resume_context: Resume | None = None,
    prior_feedback: list[str] | None = None,
) -> Any:
    """Call Claude to revise one section from user feedback."""
    models = config.get("models", {})
    model = models.get("extractor", models.get("synthesizer", "claude-sonnet-4-5"))
    max_tokens = int(models.get("revise_max_tokens", 4096))

    context_block = ""
    if resume_context:
        context_block = f"""
## Full resume context (for consistency; do not rewrite other sections)
{json.dumps(resume_context.model_dump(), indent=2, default=str)}
"""

    prior_block = ""
    if prior_feedback:
        prior_block = (
            "## Prior feedback already applied in this review round\n"
            + "\n".join(f"- {f}" for f in prior_feedback)
        )

    user_prompt = f"""## Section to revise
{section}

## Expected schema for "value"
{SECTION_SCHEMA_HINTS[section]}

## Current value
{json.dumps(current_value, indent=2, default=str)}

{context_block}
{prior_block}

## User feedback (apply this now)
{feedback.strip()}

Return JSON: {{"value": <revised {section}>}}
"""

    payload = complete_json(
        model=model,
        system=SYSTEM_PROMPT,
        user=user_prompt,
        max_tokens=max_tokens,
    )

    if "value" not in payload:
        raise ValueError('Model response missing "value" key')

    return _validate_section(section, payload["value"])
