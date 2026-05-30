"""Crustdata API client — person enrichment."""

from __future__ import annotations

import os
from typing import Any

import httpx

CRUSTDATA_API = "https://api.crustdata.com"
API_VERSION = "2025-11-01"

DEFAULT_PERSON_FIELDS = [
    "basic_profile",
    "experience",
    "education",
    "skills",
    "honors",
    "certifications",
    "social_handles",
]


def _api_key() -> str | None:
    key = os.environ.get("CRUSTDATA_API_KEY", "").strip()
    return key or None


def _headers() -> dict[str, str]:
    key = _api_key()
    if not key:
        raise RuntimeError("CRUSTDATA_API_KEY not set")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "x-api-version": API_VERSION,
    }


def enrich_person(
    *,
    profile_urls: list[str] | None = None,
    business_emails: list[str] | None = None,
    fields: list[str] | None = None,
    use_live: bool = False,
    min_similarity_score: float | None = None,
) -> list[dict[str, Any]]:
    """Call Crustdata Person Enrich (cached or live). Returns the top-level response array."""
    if profile_urls and business_emails:
        raise ValueError("Provide profile_urls or business_emails, not both")
    if not profile_urls and not business_emails:
        raise ValueError("Provide profile_urls or business_emails")

    body: dict[str, Any] = {}
    if profile_urls:
        body["professional_network_profile_urls"] = profile_urls[:25]
    else:
        body["business_emails"] = business_emails[:25]  # type: ignore[index]

    if fields:
        body["fields"] = fields
    if min_similarity_score is not None:
        body["min_similarity_score"] = min_similarity_score

    path = (
        "/person/professional_network/enrich/live"
        if use_live
        else "/person/enrich"
    )

    with httpx.Client(base_url=CRUSTDATA_API, timeout=60.0) as client:
        resp = client.post(path, headers=_headers(), json=body)
        resp.raise_for_status()
        data = resp.json()

    if not isinstance(data, list):
        raise ValueError(f"Unexpected Crustdata response type: {type(data).__name__}")
    return data
