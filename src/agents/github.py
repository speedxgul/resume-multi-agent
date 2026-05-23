"""GitHub collector — repos, languages, READMEs, profile."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx


GITHUB_API = "https://api.github.com"


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(client: httpx.Client, url: str) -> Any:
    resp = client.get(url, headers=_headers(), timeout=30.0)
    resp.raise_for_status()
    return resp.json()


def _repo_score(repo: dict) -> float:
    pushed = repo.get("pushed_at") or repo.get("updated_at") or ""
    recency = 0.0
    if pushed:
        try:
            dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - dt).days
            recency = max(0.0, 365.0 - age_days) / 365.0
        except ValueError:
            pass
    return float(repo.get("stargazers_count", 0)) + recency * 10.0


def collect_github(config: dict) -> dict[str, Any]:
    """Fetch GitHub profile + top repos for the synthesizer."""
    username = config.get("sources", {}).get("github_username", "").strip()
    if not username:
        return {
            "github": {
                "status": "skipped",
                "reason": "github_username not set in config.yaml",
            }
        }

    max_repos = int(config.get("sources", {}).get("github_max_repos", 30))
    readme_limit = int(config.get("sources", {}).get("github_include_readmes", 5))

    with httpx.Client(base_url=GITHUB_API) as client:
        profile = _get(client, f"/users/{username}")
        repos = _get(
            client,
            f"/users/{username}/repos?per_page=100&sort=updated&type=owner",
        )

    repos = sorted(repos, key=_repo_score, reverse=True)[:max_repos]

    enriched: list[dict[str, Any]] = []
    with httpx.Client(base_url=GITHUB_API) as client:
        for idx, repo in enumerate(repos):
            entry: dict[str, Any] = {
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "html_url": repo.get("html_url"),
                "homepage": repo.get("homepage"),
                "language": repo.get("language"),
                "topics": repo.get("topics", []),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "pushed_at": repo.get("pushed_at"),
                "created_at": repo.get("created_at"),
            }

            if idx < readme_limit:
                try:
                    readme = _get(client, f"/repos/{repo['full_name']}/readme")
                    import base64

                    content = base64.b64decode(readme.get("content", "")).decode(
                        "utf-8", errors="replace"
                    )
                    entry["readme_excerpt"] = content[:4000]
                except Exception as exc:
                    entry["readme_error"] = str(exc)

            try:
                langs = _get(client, f"/repos/{repo['full_name']}/languages")
                entry["languages"] = langs
            except Exception:
                entry["languages"] = {}

            enriched.append(entry)

    return {
        "github": {
            "status": "ok",
            "username": username,
            "profile": {
                "name": profile.get("name"),
                "bio": profile.get("bio"),
                "company": profile.get("company"),
                "location": profile.get("location"),
                "blog": profile.get("blog"),
                "twitter_username": profile.get("twitter_username"),
                "public_repos": profile.get("public_repos"),
                "followers": profile.get("followers"),
                "html_url": profile.get("html_url"),
            },
            "repos": enriched,
        }
    }
