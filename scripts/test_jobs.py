#!/usr/bin/env python3
"""Unit tests for job collector skip/fallback logic (no live API calls)."""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from src.agents.jobs import collect_jobs


def test_skipped_when_disabled():
    result = collect_jobs({"target": {"enabled": False}})
    assert result["target_jobs"]["status"] == "skipped"


def test_skipped_without_api_key():
    config = {"target": {"enabled": True, "titles": ["Engineer"]}}
    with patch.dict(os.environ, {"CRUSTDATA_API_KEY": ""}, clear=False):
        result = collect_jobs(config)
    assert result["target_jobs"]["status"] == "skipped"


def test_skipped_without_titles():
    config = {"target": {"enabled": True, "titles": []}}
    with patch.dict(os.environ, {"CRUSTDATA_API_KEY": "test-key"}, clear=False):
        result = collect_jobs(config)
    assert result["target_jobs"]["status"] == "skipped"


def test_ok_with_mocked_mcp():
    config = {
        "target": {
            "enabled": True,
            "titles": ["Backend Engineer"],
            "location_country": "India",
            "max_jobs": 5,
        }
    }
    mock_response = {
        "job_listings": [
            {
                "title": "Backend Engineer",
                "company_name": "Acme",
                "location": "Bengaluru, India",
                "url": "https://example.com/job/1",
                "description": "Python, Go, distributed systems.",
            }
        ]
    }
    with patch.dict(os.environ, {"CRUSTDATA_API_KEY": "test-key"}, clear=False):
        with patch(
            "src.agents.jobs.call_crustdata_tool_sync",
            return_value=mock_response,
        ) as mock_call:
            result = collect_jobs(config)
    assert result["target_jobs"]["status"] == "ok"
    assert result["target_jobs"]["count"] == 1
    assert result["target_jobs"]["jobs"][0]["title"] == "Backend Engineer"
    args = mock_call.call_args
    assert args[0][0] == "crustdata_job_search"
    params = args[1]["arguments"]["params"]
    assert params["format"] == "json"
    assert params["compact"] is False


def test_no_match():
    config = {"target": {"enabled": True, "titles": ["Rare Role XYZ"]}}
    with patch.dict(os.environ, {"CRUSTDATA_API_KEY": "test-key"}, clear=False):
        with patch(
            "src.agents.jobs.call_crustdata_tool_sync",
            return_value={"job_listings": []},
        ):
            result = collect_jobs(config)
    assert result["target_jobs"]["status"] == "no_match"


if __name__ == "__main__":
    test_skipped_when_disabled()
    test_skipped_without_api_key()
    test_skipped_without_titles()
    test_ok_with_mocked_mcp()
    test_no_match()
    print("All job collector tests passed.")
