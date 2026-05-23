#!/usr/bin/env python3
"""Quick test for URL extraction from manual context text."""

from src.utils.url_fetch import extract_urls, normalize_url

sample = """
## Hackathon wins
- EthVietnam 2025 — [leadpool](https://github.com/octocat/Hello-World)
- Devpost: https://devpost.com/software/example.
- Tweet: https://x.com/someuser/status/1234567890
"""

urls = extract_urls(sample)
assert len(urls) == 3
assert normalize_url(urls[0]) == "https://github.com/octocat/Hello-World"
print("extract_urls ok:", urls)
