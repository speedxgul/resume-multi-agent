"""Fetch and extract readable text from user-supplied URLs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

from ..config import read_text_file


def _extract_main_text(html: str) -> str:
    """Best-effort main-content extraction without heavy dependencies."""
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


def _fetch_url(client: httpx.Client, url: str) -> dict[str, Any]:
    try:
        resp = client.get(url, follow_redirects=True, timeout=30.0)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return {
                "url": url,
                "status": "skipped",
                "reason": f"unsupported content-type: {content_type}",
            }

        text = _extract_main_text(resp.text)
        return {
            "url": url,
            "status": "ok",
            "title": BeautifulSoup(resp.text, "html.parser").title.string
            if resp.text
            else None,
            "text": text[:8000],
        }
    except Exception as exc:
        return {"url": url, "status": "error", "reason": str(exc)}


def collect_urls(config: dict) -> dict[str, Any]:
    rel = config.get("sources", {}).get("urls_file", "inputs/urls.txt")
    raw = read_text_file(rel)
    if not raw:
        return {
            "urls": {
                "status": "skipped",
                "reason": f"file missing or empty: {rel}",
            }
        }

    urls = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)

    if not urls:
        return {"urls": {"status": "skipped", "reason": "no URLs listed"}}

    pages: list[dict[str, Any]] = []
    with httpx.Client(
        headers={"User-Agent": "resume-agent/0.1 (+https://github.com/local)"}
    ) as client:
        for url in urls:
            pages.append(_fetch_url(client, url))

    return {
        "urls": {
            "status": "ok",
            "path": str(Path(rel)),
            "pages": pages,
        }
    }
