"""Lightweight scope recognition with an LLM fallback for uncertain wording."""

from __future__ import annotations

import re
from typing import Literal

from .prompts import PREMIER_KEYWORDS

TYPO_CORRECTIONS = {
    "reatched": "reached",
    "goles": "goals",
    "hatrick": "hat trick",
    "hattrick": "hat trick",
    "premire": "premier",
}
OUT_OF_SCOPE_TERMS = (
    "la liga", "serie a", "bundesliga", "ligue 1", "champions league",
    "europa league", "nba", "nfl", "nhl", "mlb", "weather", "forecast",
    "recipe", "cooking", "movie", "film", "politics", "stock price", "bitcoin",
)
FOOTBALL_TERMS = (
    "football", "soccer", "score", "scored", "scoring", "goal", "goals",
    "hat trick", "milestone", "record", "player", "players", "team", "teams",
    "club", "league", "match", "matches", "result", "results", "fixture",
    "standings", "table", "points", "assists", "top scorer", "reached", "reach",
    "quickest", "fastest", "first", "form", "performance", "performed",
    "clean sheet", "clean sheets", "goalkeeper", "appearances", "defense", "defence",
)


def normalize_question(question: str) -> str:
    """Correct a small set of obvious football-query misspellings and aliases."""
    normalized = (question or "").casefold().replace("hat-trick", "hat trick")
    for misspelling, correction in TYPO_CORRECTIONS.items():
        normalized = re.sub(rf"\b{re.escape(misspelling)}\b", correction, normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def classify_question_scope(question: str) -> Literal["in_scope", "out_of_scope", "uncertain"]:
    """Reject clear non-PL requests, allow football questions, defer uncertain wording."""
    normalized = normalize_question(question)
    if any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in OUT_OF_SCOPE_TERMS):
        return "out_of_scope"
    if any(term in normalized for term in PREMIER_KEYWORDS) or any(
        re.search(rf"\b{re.escape(term)}\b", normalized) for term in FOOTBALL_TERMS
    ):
        return "in_scope"
    return "uncertain"


def is_premier_league_question(question: str) -> bool:
    """Whether a question may proceed to the supervisor for language understanding."""
    return classify_question_scope(question) != "out_of_scope"


def query_dataset_scope_limitation(question: str) -> str | None:
    """Explain explicit history/season requests that exceed this project's datasets."""
    text = normalize_question(question)
    football_context = any(term in text for term in (
        "football", "soccer", "premier league", "goal", "goals", "player", "team",
        "match", "assists", "standings", "table", "clean sheet", "appearance",
    ))
    if not football_context:
        return None
    if any(term in text for term in ("all-time", "all time", "ever", "in history", "career record")):
        scope = "all-time or career football statistics"
    else:
        seasons = re.findall(r"\b(20\d{2})\s*(?:/|-)\s*(\d{2,4})\b", text)
        requested_other_season = False
        for start, end in seasons:
            normalized_end = end if len(end) == 4 else start[:2] + end
            if (start, normalized_end) != ("2024", "2025"):
                requested_other_season = True
                break
        if not requested_other_season and not any(
            term in text for term in ("last season", "previous season", "prior season")
        ):
            return None
        scope = "that season's statistics"
    return (
        f"I can't verify {scope} from this project. Its aggregate datasets cover the "
        "2024/25 Premier League season, and match reports are partial, dated "
        "2024-08-18 through 2024-12-22."
    )
