"""Markdown-style inline links → LaTeX \\href for resume text fields."""

from __future__ import annotations

import re

from .latex import escape, escape_url

# [label](https://example.com) — label must not contain ]
_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")


def render_richtext(text: str | None) -> str:
    """Convert plain text + [label](url) markdown links to safe LaTeX."""
    if not text:
        return ""

    parts: list[str] = []
    last = 0
    for match in _LINK.finditer(text):
        if match.start() > last:
            parts.append(escape(text[last : match.start()]))
        label = escape(match.group(1))
        url = escape_url(match.group(2))
        parts.append(f"\\href{{{url}}}{{{label}}}")
        last = match.end()

    if last < len(text):
        parts.append(escape(text[last:]))

    return "".join(parts)
