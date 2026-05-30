"""Crustdata MCP client — streamable HTTP transport for pipeline collectors."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

DEFAULT_MCP_URL = "https://mcp.crustdata.com/mcp"

# REST field names (config) -> MCP people_enrich field names
_PERSON_FIELD_MAP: dict[str, str] = {
    "basic_profile": "name,headline,summary,location,languages,last_updated",
    "experience": "past_employers,current_employers,all_employers,title",
    "education": "education_background",
    "skills": "skills",
    # honors/certifications may be plan-gated on MCP — omitted from default map
    "social_handles": "twitter_handle,linkedin_flagship_url",
}

# MCP fields that may fail on some plans — skipped when building field list
_SKIP_MCP_FIELDS = {"honors", "certifications"}


def api_key() -> str | None:
    key = os.environ.get("CRUSTDATA_API_KEY", "").strip()
    return key or None


def mcp_url(config: dict) -> str:
    crustdata = config.get("crustdata") or {}
    return (crustdata.get("mcp_url") or DEFAULT_MCP_URL).strip()


def person_fields_for_mcp(configured: list[str] | None) -> str | None:
    """Map config crustdata_fields to comma-separated MCP field names."""
    if not configured:
        return None
    parts: list[str] = []
    for field in configured:
        if field in _SKIP_MCP_FIELDS:
            continue
        mapped = _PERSON_FIELD_MAP.get(field)
        if mapped:
            parts.extend(mapped.split(","))
        else:
            parts.append(field)
    seen: set[str] = set()
    ordered: list[str] = []
    for part in parts:
        if part not in seen:
            seen.add(part)
            ordered.append(part)
    return ",".join(ordered) if ordered else None


def parse_tool_result(result: Any) -> Any:
    """Extract JSON payload from an MCP CallToolResult."""
    if result.isError:
        text = ""
        if result.content:
            text = getattr(result.content[0], "text", "") or str(result.content[0])
        raise RuntimeError(text or "MCP tool returned an error")

    if not result.content:
        return None

    text = getattr(result.content[0], "text", None)
    if text is None:
        return result.content

    text = text.strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


async def call_crustdata_tool(
    tool_name: str,
    *,
    arguments: dict[str, Any],
    url: str = DEFAULT_MCP_URL,
) -> Any:
    key = api_key()
    if not key:
        raise RuntimeError("CRUSTDATA_API_KEY not set")

    headers = {"Authorization": f"Bearer {key}"}
    async with streamablehttp_client(url, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return parse_tool_result(result)


def call_crustdata_tool_sync(
    tool_name: str,
    *,
    arguments: dict[str, Any],
    url: str = DEFAULT_MCP_URL,
) -> Any:
    return asyncio.run(call_crustdata_tool(tool_name, arguments=arguments, url=url))


def normalize_person_enrich_response(
    data: Any,
    *,
    identifier: str,
    identifier_type: str,
    live: bool,
) -> dict[str, Any]:
    """Normalize crustdata_people_enrich MCP JSON to crustdata_person collector shape."""
    if isinstance(data, dict) and data.get("error"):
        return {
            "status": "error",
            "reason": str(data["error"]),
            "identifier": identifier,
        }

    profiles: list[dict[str, Any]] = []
    if isinstance(data, dict):
        raw = data.get("profiles")
        if isinstance(raw, list):
            profiles = raw

    if not profiles:
        return {
            "status": "no_match",
            "reason": "no matching profile in Crustdata dataset",
            "identifier": identifier,
            "match_type": identifier_type,
        }

    profile = profiles[0]
    person_data = {
        "basic_profile": {
            "name": profile.get("name"),
            "headline": profile.get("headline"),
            "summary": profile.get("summary"),
            "location": profile.get("location"),
            "languages": profile.get("languages"),
            "last_updated": profile.get("last_updated"),
        },
        "experience": {
            "current_employers": profile.get("current_employers") or [],
            "past_employers": profile.get("past_employers") or [],
            "all_employers": profile.get("all_employers") or [],
        },
        "education": profile.get("education_background") or [],
        "skills": profile.get("skills") or [],
        "honors": profile.get("honors") or [],
        "social_handles": {
            "linkedin": profile.get("linkedin_flagship_url") or profile.get("linkedin_profile_url"),
            "twitter": profile.get("twitter_handle"),
        },
        "raw_profile": profile,
    }

    return {
        "status": "ok",
        "matched_on": profile.get("linkedin_flagship_url") or identifier,
        "match_type": identifier_type,
        "confidence_score": 1.0,
        "live": live,
        "person_data": person_data,
    }


def normalize_job_listing(entry: dict[str, Any]) -> dict[str, Any]:
    description = entry.get("description") or entry.get("content", {}).get("description") or ""
    if len(description) > 1500:
        description = description[:1500] + "…"
    return {
        "title": entry.get("title") or entry.get("job_details", {}).get("title"),
        "company": entry.get("company_name") or entry.get("company", {}).get("basic_info", {}).get("name"),
        "location": entry.get("location") or entry.get("location", {}).get("raw"),
        "url": entry.get("url") or entry.get("job_details", {}).get("url"),
        "description": description,
        "category": entry.get("category") or entry.get("job_details", {}).get("category"),
        "workplace_type": entry.get("workplace_type") or entry.get("job_details", {}).get("workplace_type"),
    }


def normalize_job_search_response(data: Any) -> list[dict[str, Any]]:
    """Extract normalized job dicts from crustdata_job_search MCP JSON."""
    if isinstance(data, dict):
        listings = data.get("job_listings") or data.get("jobs") or []
    elif isinstance(data, list):
        listings = data
    else:
        listings = []

    return [normalize_job_listing(entry) for entry in listings if isinstance(entry, dict)]
