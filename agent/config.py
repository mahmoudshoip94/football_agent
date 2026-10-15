"""Environment and model configuration for the football agent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "Data"
TABLE_CSV = DATA_DIR / "Table.csv"
PLAYER_CSV = DATA_DIR / "Player_Stats.csv"
MATCHES_JSONL = DATA_DIR / "match_reports.jsonl"
MAIN_MODEL = "groq:openai/gpt-oss-20b"
STRONG_MODEL = "groq:openai/gpt-oss-120b"


@dataclass(frozen=True)
class Settings:
    main_model: str = MAIN_MODEL
    strong_model: str = STRONG_MODEL
    groq_api_key: str | None = None


def get_settings(*, require_api_key: bool = False) -> Settings:
    """Load the project .env file and return settings without network access."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None
    if load_dotenv is not None:
        load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.environ.get("GROQ_API_KEY")
    if require_api_key and not api_key:
        raise RuntimeError("Set GROQ_API_KEY in the project .env file or environment.")
    return Settings(groq_api_key=api_key)
