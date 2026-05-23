"""Extract URLs from text and fetch readable page content."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

# Bare URLs in markdown or plain text.
_BARE_URL = re.compile(r"https?://[^\s\)\]\>\"\'<>]+", re.IGNORECASE)
# Markdown links: [label](https://...)
_MARKDOWN_URL = re.compile(r"\]\((https?://[^\)]+)\)", re.IGNORECASE)

_TRAILING_PUNCT = ".,;:!?)'\"}"

# Hosts where generic HTML fetch rarely yields useful content.
_LOW_VALUE_FETCH_HOSTS = frozenset(
    {
        "twitter.com",
        "www.twitter.com",
        "x.com",
        "www.x.com",
        "mobile.twitter.com",
        "mobile.x.com",
    }
)

_USER_AGENT = "resume-agent/0.1 (+https://github.com/local)"


def normalize_url(url: str) -> str:
    """Normalize for deduplication (scheme, host, strip trailing slash)."""
    url = url.strip().rstrip(_TRAILING_PUNCT)
    parsed = urlparse(url)
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or ""
    # Drop fragment; keep query (Devpost etc. may use it).
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def extract_urls(text: str) -> list[str]:
    """Pull unique http(s) URLs from markdown or plain text, in document order."""
    seen: set[str] = set()
    ordered: list[str] = []

    def add(raw: str) -> None:
        cleaned = raw.strip().rstrip(_TRAILING_PUNCT)
        if not cleaned.startswith(("http://", "https://")):
            return
        key = normalize_url(cleaned)
        if key not in seen:
            seen.add(key)
            ordered.append(cleaned)

    for match in _MARKDOWN_URL.finditer(text):
        add(match.group(1))
    for match in _BARE_URL.finditer(text):
        add(match.group(0))

    return ordered


def _extract_main_text(html: str) -> str:
    try:
        from readabilipy import simple_json_from_html_string

        article = simple_json_from_html_string(html, use_readability=True)
        text = article.get("plain_text") or article.get("text") or ""
        if text.strip():
            return text.strip()
    except Exception:
        pass

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body
    if not main:
        return soup.get_text("\n", strip=True)
    return main.get_text("\n", strip=True)


def _github_readme_via_api(url: str) -> dict[str, Any] | None:
    """Fetch README for github.com/owner/repo links via the REST API."""
    parsed = urlparse(url)
    if parsed.netloc.lower() not in ("github.com", "www.github.com"):
        return None

    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None

    owner, repo = parts[0], parts[1].removesuffix(".git")
    api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"

    import base64
    import os

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = httpx.get(api_url, headers=headers, timeout=30.0, follow_redirects=True)
        resp.raise_for_status()
        payload = resp.json()
        content = base64.b64decode(payload.get("content", "")).decode(
            "utf-8", errors="replace"
        )
        return {
            "url": url,
            "status": "ok",
            "title": f"{owner}/{repo} README",
            "text": content[:8000],
            "fetch_method": "github_readme_api",
        }
    except Exception:
        return None


def fetch_page(client: httpx.Client, url: str) -> dict[str, Any]:
    """Fetch one URL; GitHub repos prefer README API, X/Twitter are skipped."""
    parsed = urlparse(normalize_url(url))
    host = parsed.netloc.lower()

    if host in _LOW_VALUE_FETCH_HOSTS:
        return {
            "url": url,
            "status": "skipped",
            "reason": "Twitter/X links are kept as references only (not fetched)",
            "fetch_method": "skipped_social",
        }

    readme = _github_readme_via_api(url)
    if readme:
        return readme

    try:
        resp = client.get(url, follow_redirects=True, timeout=30.0)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return {
                "url": url,
                "status": "skipped",
                "reason": f"unsupported content-type: {content_type}",
                "fetch_method": "http",
            }

        text = _extract_main_text(resp.text)
        title = None
        if resp.text:
            title_tag = BeautifulSoup(resp.text, "html.parser").title
            title = title_tag.string if title_tag else None

        return {
            "url": url,
            "status": "ok",
            "title": title,
            "text": text[:8000],
            "fetch_method": "http",
        }
    except Exception as exc:
        return {
            "url": url,
            "status": "error",
            "reason": str(exc),
            "fetch_method": "http",
        }


def fetch_pages(
    urls: list[str],
    *,
    skip_normalized: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Fetch many URLs, optionally skipping already-fetched normalized URLs."""
    skip = skip_normalized or set()
    pages: list[dict[str, Any]] = []

    with httpx.Client(headers={"User-Agent": _USER_AGENT}) as client:
        for url in urls:
            if normalize_url(url) in skip:
                pages.append(
                    {
                        "url": url,
                        "status": "skipped",
                        "reason": "already listed in urls.txt",
                        "fetch_method": "dedupe",
                    }
                )
                continue
            pages.append(fetch_page(client, url))

    return pages
