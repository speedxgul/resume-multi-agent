"""Helpers for reordering resume body sections in the PDF."""

from __future__ import annotations

from ..schema import DEFAULT_SECTION_ORDER, normalize_section_order

# CLI aliases → canonical section keys
SECTION_ALIASES: dict[str, str] = {
    "summary": "summary",
    "experience": "experience",
    "exp": "experience",
    "projects": "projects",
    "project": "projects",
    "skills": "skills",
    "skill": "skills",
    "education": "education",
    "edu": "education",
    "achievements": "achievements",
    "achievement": "achievements",
}


def resolve_section(name: str) -> str:
    key = name.strip().lower()
    if key in SECTION_ALIASES:
        return SECTION_ALIASES[key]
    if key in DEFAULT_SECTION_ORDER:
        return key
    raise ValueError(
        f"Unknown section {name!r}. "
        f"Use: {', '.join(DEFAULT_SECTION_ORDER)}"
    )


def move_section(
    order: list[str],
    block: str,
    *,
    before: str | None = None,
    after: str | None = None,
) -> list[str]:
    """Move one section block before or after another in the PDF layout."""
    block_key = resolve_section(block)
    normalized = normalize_section_order(order)
    new_order = [s for s in normalized if s != block_key]

    if before:
        anchor = resolve_section(before)
        if anchor not in new_order:
            raise ValueError(f"Anchor section {before!r} not in current order")
        new_order.insert(new_order.index(anchor), block_key)
    elif after:
        anchor = resolve_section(after)
        if anchor not in new_order:
            raise ValueError(f"Anchor section {after!r} not in current order")
        new_order.insert(new_order.index(anchor) + 1, block_key)
    else:
        raise ValueError("Specify before/above or after/below an anchor section")

    return normalize_section_order(new_order)


def format_section_order(order: list[str]) -> str:
    normalized = normalize_section_order(order)
    lines = []
    for idx, name in enumerate(normalized, start=1):
        lines.append(f"  {idx}. {name}")
    return "\n".join(lines)
