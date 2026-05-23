"""Load config.yaml and merge env overrides."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_config(config_path: str | Path = "config.yaml") -> dict:
    load_dotenv()
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")

    with path.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    models = config.setdefault("models", {})
    if os.getenv("RESUME_AGENT_SYNTHESIZER_MODEL"):
        models["synthesizer"] = os.environ["RESUME_AGENT_SYNTHESIZER_MODEL"]
    if os.getenv("RESUME_AGENT_EXTRACTOR_MODEL"):
        models["extractor"] = os.environ["RESUME_AGENT_EXTRACTOR_MODEL"]

    return config


def read_text_file(path: str | Path) -> str | None:
    """Read a text file if it exists and has content."""
    p = Path(path)
    if not p.exists():
        return None
    text = p.read_text(encoding="utf-8").strip()
    return text or None
