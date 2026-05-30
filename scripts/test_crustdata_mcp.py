#!/usr/bin/env python3
"""Unit tests for Crustdata MCP normalizers (no live API calls)."""

from __future__ import annotations

import sys

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from src.utils.crustdata_mcp import (
    normalize_job_search_response,
    normalize_person_enrich_response,
    person_fields_for_mcp,
)


def test_person_fields_mapping():
    fields = person_fields_for_mcp(["basic_profile", "experience", "skills"])
    assert "name" in fields
    assert "past_employers" in fields
    assert "skills" in fields


def test_normalize_person_ok():
    data = {
        "profiles": [
            {
                "linkedin_flagship_url": "https://linkedin.com/in/jane",
                "name": "Jane Doe",
                "headline": "Engineer",
                "summary": "Builder",
                "past_employers": [{"employer_name": "Acme"}],
                "current_employers": [],
                "education_background": [{"institute_name": "MIT"}],
                "skills": ["Python"],
            }
        ]
    }
    result = normalize_person_enrich_response(
        data,
        identifier="https://linkedin.com/in/jane",
        identifier_type="professional_network_profile_url",
        live=False,
    )
    assert result["status"] == "ok"
    assert result["person_data"]["basic_profile"]["name"] == "Jane Doe"
    assert result["person_data"]["experience"]["past_employers"][0]["employer_name"] == "Acme"


def test_normalize_person_no_match():
    result = normalize_person_enrich_response(
        {"profiles": []},
        identifier="x",
        identifier_type="professional_network_profile_url",
        live=False,
    )
    assert result["status"] == "no_match"


def test_normalize_job_search():
    data = {
        "job_listings": [
            {
                "title": "Backend Engineer",
                "company_name": "Acme",
                "location": "India",
                "url": "https://example.com/job",
                "description": "Build APIs " * 500,
            }
        ]
    }
    jobs = normalize_job_search_response(data)
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Backend Engineer"
    assert len(jobs[0]["description"]) <= 1501


if __name__ == "__main__":
    test_person_fields_mapping()
    test_normalize_person_ok()
    test_normalize_person_no_match()
    test_normalize_job_search()
    print("All crustdata MCP normalizer tests passed.")
