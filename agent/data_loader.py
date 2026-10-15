"""Loading and validation for the repository's CSV and JSONL data."""

from __future__ import annotations

import csv
import json
from datetime import date
from typing import Any

from .config import MATCHES_JSONL, PLAYER_CSV, TABLE_CSV

TABLE_COLUMNS = {"Rk", "Squad", "MP", "Pts"}
PLAYER_COLUMNS = {
    "Player", "Squad", "Playing Time_Min", "Playing Time_MP",
    "Performance_Gls", "Performance_Ast", "Per 90 Minutes_Gls",
    "Per 90 Minutes_Ast", "Per 90 Minutes_G+A",
}


def load_csv(path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV as rows of source-named columns."""
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def load_table() -> list[dict[str, str]]:
    return load_csv(TABLE_CSV)


def load_players() -> list[dict[str, str]]:
    return load_csv(PLAYER_CSV)


def load_matches() -> list[dict[str, Any]]:
    """Unwrap each match_reports.jsonl record while retaining its match report."""
    reports = []
    with MATCHES_JSONL.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on {MATCHES_JSONL}:{line_number}") from exc
            reports.append(record.get("match_report", record))
    return reports


def validate_datasets(
    table_rows: list[dict[str, Any]],
    player_rows: list[dict[str, Any]],
    match_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    if not table_rows or not player_rows or not match_reports:
        raise ValueError("A required dataset is empty")
    missing_table = TABLE_COLUMNS - set(table_rows[0])
    missing_players = PLAYER_COLUMNS - set(player_rows[0])
    if missing_table or missing_players:
        raise ValueError(
            f"Missing dataset columns: table={sorted(missing_table)}, "
            f"players={sorted(missing_players)}"
        )
    parsed_dates = []
    for report in match_reports:
        try:
            match_date = date.fromisoformat(report["date"])
            teams = report["teams"]
            for side in ("home", "away"):
                if not teams[side].get("name") or teams[side].get("score") is None:
                    raise ValueError("missing team name or score")
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid match report: {report!r}") from exc
        parsed_dates.append(match_date)
    return {
        "table_rows": len(table_rows),
        "player_rows": len(player_rows),
        "match_reports": len(match_reports),
        "match_start": min(parsed_dates).isoformat(),
        "match_end": max(parsed_dates).isoformat(),
    }


def load_datasets() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, Any]], dict[str, Any]]:
    table, players, matches = load_table(), load_players(), load_matches()
    metadata = validate_datasets(table, players, matches)
    return table, players, matches, metadata
