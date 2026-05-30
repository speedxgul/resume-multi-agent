"""Crustdata collector — structured LinkedIn profile via Person Enrich API."""

from __future__ import annotations

from typing import Any

import httpx

from ..utils.crustdata import DEFAULT_PERSON_FIELDS, _api_key, enrich_person


def _profile_url(config: dict) -> str:
    sources = config.get("sources", {})
    override = (sources.get("crustdata_profile_url") or "").strip()
    if override:
        return override
    return (config.get("profile", {}).get("linkedin") or "").strip()


def _resolve_fields(config: dict) -> list[str]:
    sources = config.get("sources", {})
    configured = sources.get("crustdata_fields")
    if configured:
        return list(configured)
    return list(DEFAULT_PERSON_FIELDS)


def collect_crustdata(config: dict) -> dict[str, Any]:
    """Fetch structured person profile from Crustdata for the synthesizer."""
    sources = config.get("sources", {})
    if not sources.get("crustdata_enabled", False):
        return {
            "crustdata_person": {
                "status": "skipped",
                "reason": "crustdata_enabled is false in config.yaml",
            }
        }

    if not _api_key():
        return {
            "crustdata_person": {
                "status": "skipped",
                "reason": "CRUSTDATA_API_KEY not set in .env",
            }
        }

    profile_url = _profile_url(config)
    use_email = bool(sources.get("crustdata_use_email", False))
    email = (config.get("profile", {}).get("email") or "").strip()

    if not profile_url and not (use_email and email):
        return {
            "crustdata_person": {
                "status": "skipped",
                "reason": (
                    "no profile URL — set profile.linkedin or "
                    "sources.crustdata_profile_url (or enable crustdata_use_email "
                    "with profile.email)"
                ),
            }
        }

    use_live = bool(sources.get("crustdata_use_live", False))
    fields = _resolve_fields(config)
    min_score = sources.get("crustdata_min_similarity_score")
    identifier = profile_url or email
    identifier_type = (
        "professional_network_profile_url" if profile_url else "business_email"
    )

    try:
        if profile_url:
            results = enrich_person(
                profile_urls=[profile_url],
                fields=fields,
                use_live=use_live,
            )
        else:
            kwargs: dict[str, Any] = {
                "business_emails": [email],
                "fields": fields,
                "use_live": use_live,
            }
            if min_score is not None:
                kwargs["min_similarity_score"] = float(min_score)
            results = enrich_person(**kwargs)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        detail = exc.response.text[:500]
        return {
            "crustdata_person": {
                "status": "error",
                "reason": f"HTTP {status}: {detail}",
                "identifier": identifier,
            }
        }
    except Exception as exc:
        return {
            "crustdata_person": {
                "status": "error",
                "reason": str(exc),
                "identifier": identifier,
            }
        }

    if not results:
        return {
            "crustdata_person": {
                "status": "no_match",
                "reason": "empty response from Crustdata",
                "identifier": identifier,
            }
        }

    entry = results[0]
    matches = entry.get("matches") or []
    if not matches:
        return {
            "crustdata_person": {
                "status": "no_match",
                "reason": "no matching profile in Crustdata dataset",
                "identifier": entry.get("matched_on", identifier),
                "match_type": entry.get("match_type", identifier_type),
            }
        }

    best = max(matches, key=lambda m: m.get("confidence_score", 0))
    return {
        "crustdata_person": {
            "status": "ok",
            "matched_on": entry.get("matched_on", identifier),
            "match_type": entry.get("match_type", identifier_type),
            "confidence_score": best.get("confidence_score"),
            "live": use_live,
            "person_data": best.get("person_data", {}),
        }
    }
