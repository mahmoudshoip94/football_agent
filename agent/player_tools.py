"""Deterministic player lookup and comparison functions."""

from __future__ import annotations

import json
import re
from typing import Any, Iterable

PER_90_COLUMNS = {
    "goals": "Per 90 Minutes_Gls",
    "assists": "Per 90 Minutes_Ast",
    "goals_assists": "Per 90 Minutes_G+A",
    "non_penalty_goals": "Per 90 Minutes_G-PK",
    "non_penalty_goals_assists": "Per 90 Minutes_G+A-PK",
}


def _number(value: Any, *, integer: bool = False) -> int | float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if integer else number


def _resolve_player(
    rows: Iterable[dict[str, Any]], player_name: str, team: str | None
) -> tuple[str, dict[str, Any] | None, list[dict[str, str]]]:
    query = (player_name or "").strip().casefold()
    team_query = (team or "").strip().casefold()
    all_rows = list(rows)
    exact = [r for r in all_rows if str(r.get("Player", "")).strip().casefold() == query]
    candidates = exact or [
        r for r in all_rows if query and query in str(r.get("Player", "")).casefold()
    ]
    if team_query:
        candidates = [
            r for r in candidates if str(r.get("Squad", "")).strip().casefold() == team_query
        ]
    choices = [
        {"player": str(r.get("Player", "")), "team": str(r.get("Squad", ""))}
        for r in candidates
    ]
    if len(candidates) > 1:
        keys = (
            "Player", "Squad", "Playing Time_Min", "Playing Time_MP",
            "Performance_Gls", "Performance_Ast", *PER_90_COLUMNS.values(),
        )
        unique: dict[tuple[Any, ...], dict[str, Any]] = {}
        for row in candidates:
            unique.setdefault(tuple(row.get(key) for key in keys), row)
        candidates = list(unique.values())
        choices = [
            {"player": str(r.get("Player", "")), "team": str(r.get("Squad", ""))}
            for r in candidates
        ]
    if not candidates:
        return "missing", None, []
    if len(candidates) > 1:
        return "ambiguous", None, choices
    return "ok", candidates[0], choices


def _player_values(row: dict[str, Any]) -> dict[str, Any]:
    minutes = _number(row.get("Playing Time_Min"), integer=True)
    per_90 = {
        label: None if minutes in (None, 0) else _number(row.get(column))
        for label, column in PER_90_COLUMNS.items()
    }
    return {
        "player": row.get("Player"),
        "team": row.get("Squad"),
        "goals": _number(row.get("Performance_Gls"), integer=True),
        "assists": _number(row.get("Performance_Ast"), integer=True),
        "minutes": minutes,
        "appearances": _number(row.get("Playing Time_MP"), integer=True),
        "per_90": per_90,
    }


def compare_players(
    rows: Iterable[dict[str, Any]], player_a: str, player_b: str,
    team_a: str | None = None, team_b: str | None = None,
) -> dict[str, Any]:
    status_a, row_a, choices_a = _resolve_player(rows, player_a, team_a)
    status_b, row_b, choices_b = _resolve_player(rows, player_b, team_b)
    unresolved = []
    if status_a != "ok":
        unresolved.append({"requested": player_a, "team": team_a, "status": status_a, "candidates": choices_a})
    if status_b != "ok":
        unresolved.append({"requested": player_b, "team": team_b, "status": status_b, "candidates": choices_b})
    if unresolved:
        return {"status": "clarification_required", "players": unresolved}
    a, b = _player_values(row_a), _player_values(row_b)
    if row_a is row_b:
        return {"status": "clarification_required", "reason":
                "The same player row was selected twice; identify two different players."}
    comparable = ("goals", "assists", "minutes", "appearances")
    differences = {
        key: a[key] - b[key] if a[key] is not None and b[key] is not None else None
        for key in comparable
    }
    differences["per_90"] = {
        key: round(a["per_90"][key] - b["per_90"][key], 2)
        if a["per_90"][key] is not None and b["per_90"][key] is not None else None
        for key in PER_90_COLUMNS
    }
    return {
        "status": "ok", "players": [a, b],
        "difference_player_a_minus_player_b": differences,
        "difference_order": [a["player"], b["player"]],
    }


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_player_stats(
    player_rows: Iterable[dict[str, Any]], player_name: str | None = None,
    team: str | None = None, stat: str | None = None, limit: int = 10,
) -> str:
    """Return notebook-compatible player rows as JSON using CSV source columns."""
    rows = list(player_rows)
    if player_name:
        name = player_name.casefold()
        rows = [r for r in rows if name in str(r.get("Player", "")).casefold()]
    if team:
        squad = team.casefold()
        rows = [r for r in rows if squad in str(r.get("Squad", "")).casefold()]
    requested_stat = (stat or "goals").strip().casefold().replace("-", "_").replace(" ", "_")
    stat_columns = {
        "goals": "Performance_Gls", "assists": "Performance_Ast",
        "g+a": "Performance_G+A", "minutes": "Playing Time_Min",
        "starts": "Playing Time_Starts", "appearances": "Playing Time_MP",
        "clean_sheet": "Goalkeeping_CS", "clean_sheets": "Goalkeeping_CS",
    }
    stat_key = stat_columns.get(requested_stat, "Performance_Gls")
    if requested_stat in {"clean_sheet", "clean_sheets"} and not any(
        stat_key in row for row in rows
    ):
        return json.dumps({
            "status": "unsupported", "stat": "clean_sheets",
            "message": "The Player_Stats.csv dataset has no goalkeeper clean-sheets column, so a clean-sheets leader cannot be determined from the available data.",
        }, ensure_ascii=False)
    rows.sort(key=lambda row: _to_float(row.get(stat_key)), reverse=True)
    output = [{
        "player": row.get("Player"), "nation": row.get("Nation"),
        "position": row.get("Pos"), "team": row.get("Squad"),
        "age": _to_int(row.get("Age")), "appearances": _to_int(row.get("Playing Time_MP")),
        "starts": _to_int(row.get("Playing Time_Starts")),
        "minutes": _to_int(row.get("Playing Time_Min")),
        "nineties": _to_float(row.get("Playing Time_90s")),
        "goals": _to_int(row.get("Performance_Gls")),
        "assists": _to_int(row.get("Performance_Ast")),
        "goals_assists": _to_int(row.get("Performance_G+A")),
        "non_pen_goals": _to_int(row.get("Performance_G-PK")),
        "penalties": _to_int(row.get("Performance_PK")),
        "penalties_att": _to_int(row.get("Performance_PKatt")),
        "yellow_cards": _to_int(row.get("Performance_CrdY")),
        "red_cards": _to_int(row.get("Performance_CrdR")),
        "goals_per_90": _to_float(row.get("Per 90 Minutes_Gls")),
        "assists_per_90": _to_float(row.get("Per 90 Minutes_Ast")),
        "ga_pk_per_90": _to_float(row.get("Per 90 Minutes_G+A-PK")),
        **({"clean_sheets": _to_int(row.get("Goalkeeping_CS"))}
           if "Goalkeeping_CS" in row else {}),
    } for row in rows[:max(0, int(limit))]]
    return json.dumps(output, ensure_ascii=False)


def compare_player_stats(
    player_rows: Iterable[dict[str, Any]], player_a: str, player_b: str,
    team_a: str | None = None, team_b: str | None = None,
) -> str:
    return json.dumps(compare_players(player_rows, player_a, player_b, team_a, team_b), ensure_ascii=False)


def query_player_comparison(rows: Iterable[dict[str, Any]], query: str) -> str | None:
    """Deterministically format a comparison query, preserving notebook labels."""
    rows = list(rows)
    text = (query or "").casefold()
    if not re.search(r"\b(compare|comparison|versus|vs)\b", text):
        return None
    names = sorted({str(row.get("Player", "")).strip() for row in rows if row.get("Player")})
    mentions = []
    for name in names:
        match = re.search(r"(?<!\w)" + re.escape(name.casefold()) + r"(?!\w)", text)
        if match:
            mentions.append((match.start(), -len(name), name))
    if len({item[2] for item in mentions}) < 2:
        tokens = {m.group().casefold(): m.start() for m in re.finditer(r"[\w]+", text)}
        present = {item[2] for item in mentions}
        for name in names:
            surname = name.split()[-1].casefold()
            if len(surname) >= 4 and surname in tokens and name not in present:
                mentions.append((tokens[surname], -len(name), name))
    ordered = []
    for _, _, name in sorted(mentions):
        if name not in ordered:
            ordered.append(name)
    if len(ordered) != 2:
        return None

    def team_qualifier(name: str) -> str | None:
        squads = {str(row.get("Squad", "")) for row in rows
                  if str(row.get("Player", "")).casefold() == name.casefold()}
        found = [squad for squad in squads if squad and squad.casefold() in text]
        aliases = {"wolves": "Wolverhampton Wanderers", "man city": "Manchester City",
                   "man utd": "Manchester United", "man united": "Manchester United",
                   "spurs": "Tottenham Hotspur"}
        if not found:
            found = [canonical for alias, canonical in aliases.items()
                     if alias in text and canonical in squads]
        return found[0] if len(found) == 1 else None

    result = compare_players(rows, ordered[0], ordered[1],
                             team_qualifier(ordered[0]), team_qualifier(ordered[1]))
    if result["status"] != "ok":
        lines = ["Please clarify the player comparison:"]
        for item in result.get("players", []):
            teams = ", ".join(candidate["team"] for candidate in item.get("candidates", []))
            lines.append(f"- {item['requested']}: {item['status']}" + (f" (teams: {teams})" if teams else ""))
        if result.get("reason"):
            lines.append(f"- {result['reason']}")
        return "\n".join(lines)
    a, b = result["players"]
    delta = result["difference_player_a_minus_player_b"]
    show = lambda value: "N/A" if value is None else str(value)
    lines = [f"## {a['player']} ({a['team']}) vs {b['player']} ({b['team']})", "",
             "| Statistic | Player A | Player B | A - B |", "|---|---:|---:|---:|"]
    for key, label in (("goals", "Goals"), ("assists", "Assists"),
                       ("minutes", "Minutes"), ("appearances", "Appearances")):
        lines.append(f"| {label} | {show(a[key])} | {show(b[key])} | {show(delta[key])} |")
    for key, label in (("goals", "Goals per 90"), ("assists", "Assists per 90"),
                       ("goals_assists", "G+A per 90 (Per 90 Minutes_G+A)"),
                       ("non_penalty_goals", "Non-penalty goals per 90"),
                       ("non_penalty_goals_assists", "Non-penalty G+A per 90 (Per 90 Minutes_G+A-PK)")):
        lines.append(f"| {label} | {show(a['per_90'][key])} | {show(b['per_90'][key])} | {show(delta['per_90'][key])} |")
    return "\n".join(lines)


def query_player_stat_limitation(player_rows: Iterable[dict[str, Any]], query: str) -> str | None:
    """Explain recognized player statistics that the supplied CSV cannot answer."""
    if not re.search(r"\bclean[ -]?sheets?\b", (query or "").casefold()):
        return None
    rows = list(player_rows)
    if any("Goalkeeping_CS" in row for row in rows):
        return None
    return (
        "I can't identify a clean-sheets leader from the project data: "
        "Player_Stats.csv has no goalkeeper clean-sheets column. The available "
        "statistics are for the 2024/25 season."
    )


def query_player_leader(player_rows: Iterable[dict[str, Any]], query: str) -> str | None:
    """Answer common default-season player leader questions through get_player_stats."""
    text = (query or "").casefold()
    if re.search(r"\b(compare|comparison|versus|vs)\b", text):
        return None
    if any(term in text for term in ("team", "club")):
        return None
    if any(term in text for term in ("clean sheet", "clean sheets")):
        return None
    if any(term in text for term in ("assist", "assists", "assister")) and any(
        term in text for term in ("most", "top", "highest", "leader")
    ):
        stat, label = "assists", "assists"
    elif any(term in text for term in ("appearance", "appearances", "matches played", "games played")) and any(
        term in text for term in ("most", "top", "highest", "leader")
    ):
        stat, label = "appearances", "appearances"
    elif (any(term in text for term in ("goal", "goals", "top scorer", "top-scorer")) and any(
        term in text for term in ("most", "top", "highest", "leader")
    )) or "who scored the most" in text:
        stat, label = "goals", "goals"
    else:
        return None
    rows = list(player_rows)
    result = json.loads(get_player_stats(rows, stat=stat, limit=len(rows)))
    if not result:
        return "The player statistics dataset contains no rows to rank."
    value = result[0][stat]
    leaders = [row for row in result if row[stat] == value]
    names = ", ".join(f"{row['player']} ({row['team']})" for row in leaders)
    return (f"Most {label} in the project's Premier League 2024/25 player statistics: "
            f"{names} - {value} {label}.")
