"""Synthesizer agent — merge existing resume + collected sources into structured Resume."""

from __future__ import annotations

import json
from typing import Any

from ..schema import Contact, Resume
from ..utils.llm import complete_structured
from .prompt_snippets import LINK_GUIDANCE, REORDER_GUIDANCE, TARGET_JOBS_GUIDANCE


SYSTEM_PROMPT = f"""You are a senior resume writer and career coach.

Given:
1) the user's existing resume text (may be outdated),
2) static contact/profile info,
3) fresh data from GitHub, LinkedIn paste, Twitter paste, manual notes (including fetched pages for links embedded in manual_context.md), and fetched URLs,

produce an updated resume as JSON matching the provided schema.

Rules:
- Preserve factual accuracy. Do not invent employers, degrees, dates, or metrics.
- Prefer newer information from sources over stale resume text when they conflict.
- When `crustdata_person.status` is `ok`, treat its `person_data` as the authoritative source for employment, education, skills, certifications, and honors (over pasted LinkedIn text).
{TARGET_JOBS_GUIDANCE}
- Keep bullets concise, impact-oriented, and ATS-friendly (strong verbs, quantified outcomes when available).
- Merge duplicate projects/experience entries instead of repeating them.
- Use static profile contact fields exactly for contact info (name, email, links).
- If a section has no supported data, return an empty list or null rather than guessing.
- Skills should be grouped logically (Languages, Frameworks, Tools, etc.).
- Achievements should include hackathon wins, awards, publications, notable posts when supported by sources. Use embedded link page content (Devpost, GitHub README) to enrich achievement and project bullets; keep X/Twitter URLs as reference links when fetch was skipped.
{LINK_GUIDANCE}
{REORDER_GUIDANCE}
- Set section_order to control PDF section sequence (default: summary, experience, projects, skills, education, achievements).
- Return ONLY valid JSON matching the schema. No markdown fences, no commentary.
"""


def _build_user_prompt(
    *,
    existing_resume_text: str,
    profile: dict[str, Any],
    sources: dict[str, Any],
) -> str:
    return f"""## Static profile (use for contact block)
{json.dumps(profile, indent=2)}

## Existing resume text (extracted from PDF)
{existing_resume_text or "(empty)"}

## Collected sources
{json.dumps(sources, indent=2, default=str)}

Return the full updated resume JSON.
Schema fields:
- contact: name, email, phone?, location?, linkedin?, github?, twitter?, website?
- section_order: string[] — PDF section order (summary, experience, projects, skills, education, achievements)
- summary: string or null
- experience: list of {{company, role, location?, start_date, end_date?, bullets[]}}
- projects: list of {{name, description, tech[], link?, bullets[]}}
- education: list of {{institution, degree, field?, start_date?, end_date?, gpa?, coursework[]}}
- skills: dict[str, list[str]]
- achievements: list of {{title, description?, date?, link?}}
Use [label](https://...) in any text field for inline clickable links in the PDF.
"""


def _contact_from_profile(profile: dict[str, Any]) -> Contact:
    github = profile.get("github", "") or ""
    if github and "github.com" not in github:
        github = f"https://github.com/{github.lstrip('@')}"

    twitter = profile.get("twitter", "") or ""
    if twitter and not twitter.startswith("http"):
        twitter = f"https://twitter.com/{twitter.lstrip('@')}"

    return Contact(
        name=profile.get("name", ""),
        email=profile.get("email", ""),
        phone=profile.get("phone") or None,
        location=profile.get("location") or None,
        linkedin=profile.get("linkedin") or None,
        github=github or None,
        twitter=twitter or None,
        website=profile.get("website") or None,
    )


def synthesize_resume(
    *,
    config: dict,
    existing_resume_text: str,
    profile: dict[str, Any],
    sources: dict[str, Any],
) -> Resume:
    """Call Claude to produce an updated structured resume."""
    models = config.get("models", {})
    model = models.get("synthesizer", "claude-opus-4-7")
    max_tokens = int(models.get("max_tokens", 8192))

    user_prompt = _build_user_prompt(
        existing_resume_text=existing_resume_text,
        profile=profile,
        sources=sources,
    )

    try:
        return complete_structured(
            model=model,
            system=SYSTEM_PROMPT,
            user=user_prompt,
            schema=Resume,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        raise RuntimeError(
            "Synthesizer failed to produce valid resume JSON. "
            "Check ANTHROPIC_API_KEY, model name, and source payload size."
        ) from exc
