"""Premier League table data tool."""

from __future__ import annotations

import json
from typing import Any

from .player_tools import _to_float, _to_int


def get_league_table(table_rows: list[dict[str, Any]], top_n: int | None = None) -> str:
    rows = sorted(table_rows, key=lambda row: _to_int(row.get("Rk"), 999))
    if top_n:
        rows = rows[:int(top_n)]
    output = [{
        "position": _to_int(row.get("Rk")), "team": row.get("Squad"),
        "played": _to_int(row.get("MP")), "wins": _to_int(row.get("W")),
        "draws": _to_int(row.get("D")), "losses": _to_int(row.get("L")),
        "goals_for": _to_int(row.get("GF")), "goals_against": _to_int(row.get("GA")),
        "goal_diff": _to_int(row.get("GD")), "points": _to_int(row.get("Pts")),
        "points_per_match": _to_float(row.get("Pts/MP")),
        "xG": _to_float(row.get("xG")), "xGA": _to_float(row.get("xGA")),
        "xGD": _to_float(row.get("xGD")), "xGD_per_90": _to_float(row.get("xGD/90")),
        "top_team_scorer": row.get("Top Team Scorer"),
        "goalkeeper": row.get("Goalkeeper"), "notes": row.get("Notes"),
    } for row in rows]
    return json.dumps(output, ensure_ascii=False)


def query_team_table_leader(table_rows: list[dict[str, Any]], query: str) -> str | None:
    """Answer simple team goal/defense leader questions from the existing table tool."""
    text = (query or "").casefold()
    if not any(term in text for term in ("team", "club", "defense", "defence", "goals conceded")):
        return None
    if any(term in text for term in ("best defense", "best defence", "fewest goals conceded", "least goals conceded")):
        key, label, choose = "goals_against", "fewest goals conceded", min
    elif "goal" in text and any(term in text for term in ("most", "highest", "scored", "attack")):
        key, label, choose = "goals_for", "most goals scored", max
    else:
        return None
    rows = json.loads(get_league_table(table_rows))
    if not rows:
        return "The league table dataset contains no rows to rank."
    value = choose(row[key] for row in rows)
    leaders = [row["team"] for row in rows if row[key] == value]
    return (f"In the project's Premier League 2024/25 league table, {', '.join(leaders)} "
            f"have the {label} ({value}).")
