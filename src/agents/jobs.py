"""Crustdata job search collector — target role postings via MCP."""

from __future__ import annotations

from typing import Any

from ..utils.crustdata_mcp import (
    api_key,
    call_crustdata_tool_sync,
    mcp_url,
    normalize_job_search_response,
)


def _target_config(config: dict) -> dict[str, Any]:
    return config.get("target") or {}


def _build_filters(target: dict[str, Any]) -> dict[str, Any] | None:
    titles = [t.strip() for t in (target.get("titles") or []) if str(t).strip()]
    if not titles:
        return None

    conditions: list[dict[str, Any]] = [
        {
            "op": "or",
            "conditions": [
                {"field": "job_details.title", "type": "(.)", "value": title}
                for title in titles
            ],
        }
    ]

    category = (target.get("category") or "").strip()
    if category:
        conditions.append({"field": "job_details.category", "type": "=", "value": category})

    workplace = (target.get("workplace_type") or "").strip()
    if workplace:
        conditions.append({"field": "job_details.workplace_type", "type": "=", "value": workplace})

    country = (target.get("location_country") or "").strip()
    if country:
        conditions.append({"field": "location.country", "type": "=", "value": country})

    industries = [i.strip() for i in (target.get("industries") or []) if str(i).strip()]
    if industries:
        conditions.append(
            {"field": "company.basic_info.industries", "type": "in", "value": industries}
        )

    domains = [d.strip() for d in (target.get("company_domains") or []) if str(d).strip()]
    if domains:
        conditions.append(
            {"field": "company.basic_info.primary_domain", "type": "in", "value": domains}
        )

    if len(conditions) == 1:
        return conditions[0]
    return {"op": "and", "conditions": conditions}


def collect_jobs(config: dict) -> dict[str, Any]:
    """Fetch target job postings from Crustdata MCP for resume tailoring."""
    target = _target_config(config)
    if not target.get("enabled", False):
        return {
            "target_jobs": {
                "status": "skipped",
                "reason": "target.enabled is false in config.yaml",
            }
        }

    if not api_key():
        return {
            "target_jobs": {
                "status": "skipped",
                "reason": "CRUSTDATA_API_KEY not set in .env",
            }
        }

    filters = _build_filters(target)
    if not filters:
        return {
            "target_jobs": {
                "status": "skipped",
                "reason": "no target titles — set target.titles in config.yaml",
            }
        }

    max_jobs = int(target.get("max_jobs") or 15)
    params: dict[str, Any] = {
        "filters": filters,
        "limit": max(1, min(max_jobs, 100)),
        "format": "json",
        "compact": False,
        "sorts": [{"field": "metadata.date_added", "order": "desc"}],
    }

    try:
        data = call_crustdata_tool_sync(
            "crustdata_job_search",
            arguments={"params": params},
            url=mcp_url(config),
        )
    except Exception as exc:
        return {
            "target_jobs": {
                "status": "error",
                "reason": str(exc),
            }
        }

    if isinstance(data, dict) and data.get("error"):
        return {
            "target_jobs": {
                "status": "error",
                "reason": str(data["error"]),
            }
        }

    jobs = normalize_job_search_response(data)
    if not jobs:
        return {
            "target_jobs": {
                "status": "no_match",
                "reason": "no jobs matched the target filters",
            }
        }

    return {
        "target_jobs": {
            "status": "ok",
            "count": len(jobs),
            "jobs": jobs,
        }
    }
