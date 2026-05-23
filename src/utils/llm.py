"""Anthropic client helpers."""

from __future__ import annotations

import json
import os
import re
from typing import Any, TypeVar

from anthropic import Anthropic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return Anthropic(api_key=api_key)


def _extract_json(text: str) -> dict[str, Any]:
    """Pull a JSON object out of a model response."""
    text = text.strip()
    if text.startswith("{"):
        return json.loads(text)

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("Model response did not contain JSON")


def complete_json(
    *,
    model: str,
    system: str,
    user: str,
    max_tokens: int = 8192,
) -> dict[str, Any]:
    """Ask Claude for a JSON object and parse it."""
    client = get_client()
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    return _extract_json(text)


def complete_structured(
    *,
    model: str,
    system: str,
    user: str,
    schema: type[T],
    max_tokens: int = 8192,
) -> T:
    """Ask Claude for JSON matching a Pydantic schema."""
    payload = complete_json(
        model=model,
        system=system,
        user=user,
        max_tokens=max_tokens,
    )
    return schema.model_validate(payload)
