"""Revise the full resume from natural-language user feedback."""

from __future__ import annotations

import json

from ..schema import Resume
from ..utils.llm import complete_json
from .prompt_snippets import LINK_GUIDANCE, REORDER_GUIDANCE

SYSTEM_PROMPT = f"""You revise a resume JSON document based on user feedback.

Rules:
- Apply the user's feedback precisely across any sections that need to change.
- Do not invent employers, degrees, dates, metrics, or awards not supported by the current resume or feedback.
- Keep contact fields unchanged unless the user explicitly asks to change contact info.
- Keep bullets concise and ATS-friendly unless the user asks otherwise.
{LINK_GUIDANCE}
{REORDER_GUIDANCE}
- Return ONLY valid JSON matching the full resume schema.
- Shape: {{"value": {{contact, section_order, summary, experience, projects, education, skills, achievements}}}}
- No markdown fences, no commentary outside JSON.
"""


def revise_resume(
    *,
    resume: Resume,
    feedback: str,
    config: dict,
) -> Resume:
    """Call Claude to revise the entire resume from user feedback."""
    models = config.get("models", {})
    model = models.get("extractor", models.get("synthesizer", "claude-sonnet-4-5"))
    max_tokens = int(
        models.get("max_tokens", models.get("revise_max_tokens", 8192))
    )

    user_prompt = f"""## Current resume
{json.dumps(resume.model_dump(), indent=2, default=str)}

## User feedback (apply now)
{feedback.strip()}

Return JSON: {{"value": <full updated resume object>}}
"""

    payload = complete_json(
        model=model,
        system=SYSTEM_PROMPT,
        user=user_prompt,
        max_tokens=max_tokens,
    )

    if "value" not in payload:
        raise ValueError('Model response missing "value" key')

    return Resume.model_validate(payload["value"])
