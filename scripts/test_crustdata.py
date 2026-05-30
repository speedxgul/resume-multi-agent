#!/usr/bin/env python3
"""Unit tests for Crustdata collector skip/fallback logic (no live API calls)."""

from __future__ import annotations

import os
import sys
from unittest.mock import patch

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from src.agents.crustdata import collect_crustdata


def test_skipped_when_disabled():
    result = collect_crustdata({"sources": {"crustdata_enabled": False}})
    assert result["crustdata_person"]["status"] == "skipped"


def test_skipped_without_api_key():
    config = {
        "sources": {"crustdata_enabled": True},
        "profile": {"linkedin": "https://linkedin.com/in/test"},
    }
    with patch.dict(os.environ, {"CRUSTDATA_API_KEY": ""}, clear=False):
        result = collect_crustdata(config)
    assert result["crustdata_person"]["status"] == "skipped"
    assert "CRUSTDATA_API_KEY" in result["crustdata_person"]["reason"]


def test_skipped_without_identifier():
    config = {
        "sources": {"crustdata_enabled": True},
        "profile": {},
    }
    with patch.dict(os.environ, {"CRUSTDATA_API_KEY": "test-key"}, clear=False):
        result = collect_crustdata(config)
    assert result["crustdata_person"]["status"] == "skipped"


def test_ok_with_mocked_api():
    config = {
        "sources": {"crustdata_enabled": True},
        "profile": {"linkedin": "https://linkedin.com/in/jane"},
    }
    mock_response = [
        {
            "matched_on": "https://linkedin.com/in/jane",
            "match_type": "professional_network_profile_url",
            "matches": [
                {
                    "confidence_score": 1.0,
                    "person_data": {
                        "basic_profile": {"name": "Jane Doe", "headline": "Engineer"},
                    },
                }
            ],
        }
    ]
    with patch.dict(os.environ, {"CRUSTDATA_API_KEY": "test-key"}, clear=False):
        with patch("src.agents.crustdata.enrich_person", return_value=mock_response):
            result = collect_crustdata(config)
    assert result["crustdata_person"]["status"] == "ok"
    assert result["crustdata_person"]["person_data"]["basic_profile"]["name"] == "Jane Doe"


def test_no_match():
    config = {
        "sources": {"crustdata_enabled": True},
        "profile": {"linkedin": "https://linkedin.com/in/nobody"},
    }
    mock_response = [
        {
            "matched_on": "https://linkedin.com/in/nobody",
            "match_type": "professional_network_profile_url",
            "matches": [],
        }
    ]
    with patch.dict(os.environ, {"CRUSTDATA_API_KEY": "test-key"}, clear=False):
        with patch("src.agents.crustdata.enrich_person", return_value=mock_response):
            result = collect_crustdata(config)
    assert result["crustdata_person"]["status"] == "no_match"


if __name__ == "__main__":
    test_skipped_when_disabled()
    test_skipped_without_api_key()
    test_skipped_without_identifier()
    test_ok_with_mocked_api()
    test_no_match()
    print("All crustdata collector tests passed.")
