"""Deterministic fixture, recent-form, and head-to-head analysis."""

from __future__ import annotations

import json
from datetime import date
from typing import Any, Iterable

ALIASES = {
    "wolves": "Wolverhampton Wanderers", "man city": "Manchester City",
    "man utd": "Manchester United", "man united": "Manchester United",
    "spurs": "Tottenham Hotspur",
}
PERIOD_NOTE = (
    "Repository coverage is partial for the 2024/25 season; these are only the "
    "matches present in the available reports, which end on 2024-12-22. "
    "They are not current real-world results."
)
H2H_NOTE = (
    "Head-to-head history is incomplete: this includes only meetings present in "
    "the repository's partial 2024/25 match reports, ending on 2024-12-22. "
    "It does not establish the complete earlier or later history between these teams."
)


def _score(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() and number >= 0 else None


def _team_name(data: dict[str, Any]) -> str | None:
    name = data.get("name") or data.get("team") or data.get("title")
    return str(name).strip() if name else None


def normalise_matches(match_reports: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    matches = []
    for report in match_reports:
        teams = report.get("teams") or {}
        home, away = teams.get("home") or {}, teams.get("away") or {}
        home_name, away_name = _team_name(home), _team_name(away)
        home_score = _score(home.get("score", report.get("home_score")))
        away_score = _score(away.get("score", report.get("away_score")))
        try:
            match_date = date.fromisoformat(str(report.get("date")))
        except (TypeError, ValueError):
            continue
        if not home_name or not away_name or home_score is None or away_score is None:
            continue
        matches.append({
            "date": match_date.isoformat(), "_date": match_date,
            "home_team": home_name, "away_team": away_name,
            "home_score": home_score, "away_score": away_score,
            "venue": report.get("venue"),
        })
    return matches


def resolve_team(query: str, matches: list[dict[str, Any]]) -> dict[str, Any]:
    known = sorted({match[side] for match in matches for side in ("home_team", "away_team")})
    value = (query or "").strip().casefold()
    alias = ALIASES.get(value)
    if alias:
        exact_alias = [name for name in known if name.casefold() == alias.casefold()]
        if exact_alias:
            return {"status": "ok", "team": exact_alias[0]}
    exact = [name for name in known if name.casefold() == value]
    candidates = exact or [name for name in known if value and value in name.casefold()]
    if len(candidates) == 1:
        return {"status": "ok", "team": candidates[0]}
    return {"status": "clarification_required", "reason": "ambiguous" if candidates else "missing",
            "requested": query, "candidates": candidates}


def _coverage(matches: list[dict[str, Any]]) -> dict[str, Any]:
    dates = [match["date"] for match in matches]
    return {"data_period": {"start": min(dates) if dates else None,
                            "end": max(dates) if dates else None},
            "coverage_note": PERIOD_NOTE}


def _outcome(goals_for: int, goals_against: int) -> str:
    return "W" if goals_for > goals_against else "D" if goals_for == goals_against else "L"


def _summarize(team: str, matches: list[dict[str, Any]]) -> dict[str, Any]:
    recent = [m for m in matches if team in (m["home_team"], m["away_team"])]
    recent.sort(key=lambda m: (m["_date"], m["home_team"], m["away_team"]), reverse=True)
    selected = recent[:5]
    results = []
    wins = draws = losses = goals_for_total = goals_against_total = points = 0
    for match in selected:
        is_home = match["home_team"] == team
        opponent = match["away_team"] if is_home else match["home_team"]
        goals_for = match["home_score"] if is_home else match["away_score"]
        goals_against = match["away_score"] if is_home else match["home_score"]
        result = _outcome(goals_for, goals_against)
        wins += result == "W"
        draws += result == "D"
        losses += result == "L"
        goals_for_total += goals_for
        goals_against_total += goals_against
        points += 3 if result == "W" else 1 if result == "D" else 0
        results.append({
            "date": match["date"], "opponent": opponent,
            "score": f"{goals_for}-{goals_against}",
            "goals_for": goals_for, "goals_against": goals_against,
            "venue_status": "home" if is_home else "away", "result": result,
        })
    return {
        "team": team, "matches_available": len(recent), "matches_in_form": len(selected),
        "most_recent_available_match_date": recent[0]["date"] if recent else None,
        "matches": results,
        "summary": {"wins": wins, "draws": draws, "losses": losses,
                    "goals_scored": goals_for_total, "goals_conceded": goals_against_total,
                    "goal_difference": goals_for_total - goals_against_total, "points": points},
    }


def team_form(match_reports: Iterable[dict[str, Any]], team_a: str,
              team_b: str | None = None) -> dict[str, Any]:
    reports = list(match_reports)
    matches = normalise_matches(reports)
    resolved_a = resolve_team(team_a, matches)
    resolved_b = resolve_team(team_b, matches) if team_b else None
    unresolved = [r for r in (resolved_a, resolved_b) if r is not None and r["status"] != "ok"]
    result: dict[str, Any] = {"status": "clarification_required" if unresolved else "ok",
                              **_coverage(matches)}
    if unresolved:
        result["teams"] = unresolved
        return result
    result["teams"] = [_summarize(resolved_a["team"], matches)]
    if resolved_b:
        if resolved_a["team"] == resolved_b["team"]:
            return {"status": "clarification_required", "reason":
                    "The same team was resolved for both comparison inputs.", **_coverage(matches)}
        result["teams"].append(_summarize(resolved_b["team"], matches))
    return result


def head_to_head(match_reports: Iterable[dict[str, Any]], team_a: str,
                 team_b: str) -> dict[str, Any]:
    matches = normalise_matches(match_reports)
    resolved_a, resolved_b = resolve_team(team_a, matches), resolve_team(team_b, matches)
    unresolved = [r for r in (resolved_a, resolved_b) if r["status"] != "ok"]
    if unresolved:
        return {"status": "clarification_required", "teams": unresolved, **_coverage(matches)}
    first, second = resolved_a["team"], resolved_b["team"]
    if first == second:
        return {"status": "clarification_required", "reason":
                "The same team was resolved for both inputs.", **_coverage(matches)}
    meetings = [m for m in matches if {m["home_team"], m["away_team"]} == {first, second}]
    meetings.sort(key=lambda m: (m["_date"], m["home_team"], m["away_team"]))
    wins = draws = losses = goals_for_total = goals_against_total = 0
    output = []
    for match in meetings:
        is_home = match["home_team"] == first
        goals_for = match["home_score"] if is_home else match["away_score"]
        goals_against = match["away_score"] if is_home else match["home_score"]
        result = _outcome(goals_for, goals_against)
        wins += result == "W"
        draws += result == "D"
        losses += result == "L"
        goals_for_total += goals_for
        goals_against_total += goals_against
        output.append({
            "date": match["date"], "home_team": match["home_team"],
            "away_team": match["away_team"],
            "score": f"{match['home_score']}-{match['away_score']}",
            "home_score": match["home_score"], "away_score": match["away_score"],
            "venue": match["venue"], "result_for_first_team": result,
        })
    return {
        "status": "ok", "team_a": first, "team_b": second, "matches": output,
        "summary_for_team_a": {"total_matches": len(meetings), "wins": wins, "draws": draws,
                               "losses": losses, "goals_scored": goals_for_total,
                               "goals_conceded": goals_against_total},
        "history_note": H2H_NOTE, **_coverage(matches),
    }


def getteam_form(match_reports: Iterable[dict[str, Any]], team_a: str,
                 team_b: str | None = None) -> str:
    return json.dumps(team_form(match_reports, team_a, team_b), ensure_ascii=False)


def gethead_to_head(match_reports: Iterable[dict[str, Any]], team_a: str, team_b: str) -> str:
    return json.dumps(head_to_head(match_reports, team_a, team_b), ensure_ascii=False)


def get_match_fixtures(match_reports: Iterable[dict[str, Any]], matchweek: int | None = None,
                       team: str | None = None, limit: int = 20) -> str:
    fixtures = []
    for report in match_reports:
        try:
            current_week = int(float(report.get("matchweek") or 0))
        except (TypeError, ValueError):
            current_week = 0
        if matchweek is not None and current_week != int(matchweek):
            continue
        teams = report.get("teams", {}) or {}
        home, away = teams.get("home", {}) or {}, teams.get("away", {}) or {}
        home_name, away_name = _team_name(home), _team_name(away)
        if team and team.casefold() not in (home_name or "").casefold() and team.casefold() not in (away_name or "").casefold():
            continue
        home_score = home.get("score", report.get("home_score"))
        away_score = away.get("score", report.get("away_score"))
        hs, aws = _int_or_none(home_score), _int_or_none(away_score)
        result = None if hs is None or aws is None else (
            "Home Win" if hs > aws else "Away Win" if aws > hs else "Draw"
        )
        fixtures.append({
            "matchweek": current_week, "date": report.get("date"),
            "home_team": home_name, "away_team": away_name,
            "home_score": hs, "away_score": aws, "result": result,
            "venue": report.get("venue"), "attendance": _int_or_none(report.get("attendance")) or 0,
            "competition": report.get("competition"),
        })
    fixtures.sort(key=lambda item: (item["matchweek"] or 0, item["date"] or ""))
    return json.dumps(fixtures[:max(0, int(limit))], ensure_ascii=False)


def _int_or_none(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def query_match_analysis(match_reports: Iterable[dict[str, Any]], query: str) -> str | None:
    """Return deterministic natural-language answers for recognized form/H2H asks."""
    reports = list(match_reports)
    matches = normalise_matches(reports)
    text = (query or "").casefold()
    h2h_intent = any(term in text for term in ("head-to-head", "head to head", "h2h"))
    if not h2h_intent and "how many times" in text and any(
        word in text for word in (" beat ", "beat ", " defeated", "defeat")
    ):
        h2h_intent = True
    form_intent = any(term in text for term in (
        "last five", "last 5", "recent form", "team form", "recent results",
    )) or ("form" in text and not h2h_intent)
    if not (h2h_intent or form_intent):
        return None
    known = sorted({match[side] for match in matches for side in ("home_team", "away_team")})
    phrases = [(name.casefold(), name) for name in known]
    phrases.extend((alias, canonical) for alias, canonical in ALIASES.items())
    mentions = [(text.find(phrase), -len(phrase), canonical)
                for phrase, canonical in phrases if phrase in text and canonical in known]
    found = []
    for _, _, canonical in sorted(mentions):
        if canonical not in found:
            found.append(canonical)

    def clarification(message: str) -> str:
        return message + " Available team names: " + ", ".join(known) + "."

    if h2h_intent:
        if len(found) < 2:
            return clarification("Please identify both teams for the head-to-head comparison.")
        result = head_to_head(reports, found[0], found[1])
        if result["status"] != "ok":
            return clarification("I could not resolve both teams reliably.")
        summary = result["summary_for_team_a"]
        lines = [f"## Head-to-head: {result['team_a']} vs {result['team_b']}", ""]
        if result["matches"]:
            for match in result["matches"]:
                venue = f" — {match['venue']}" if match["venue"] else ""
                lines.append(f"- {match['date']}: {match['home_team']} {match['score']} {match['away_team']}"
                             f"{venue} ({match['result_for_first_team']} for {result['team_a']})")
        else:
            lines.append("- No meetings are present in the available reports.")
        lines.extend(["", f"Record for {result['team_a']}: {summary['total_matches']} matches; "
                      f"{summary['wins']} wins, {summary['draws']} draws, {summary['losses']} losses; "
                      f"{summary['goals_scored']} goals scored, {summary['goals_conceded']} conceded.",
                      f"Data period: {result['data_period']['start']} to {result['data_period']['end']}.",
                      result["history_note"]])
        return "\n".join(lines)
    if not found:
        return clarification("Please identify the team whose form or results you want.")
    result = team_form(reports, found[0], found[1] if len(found) > 1 else None)
    if result["status"] != "ok":
        return clarification("I could not resolve the requested team names reliably.")
    lines = []
    for summary in result["teams"]:
        lines.extend([f"## {summary['team']} — latest five available matches", "",
                      f"Matches available in reports: {summary['matches_available']}. Most recent available match: "
                      f"{summary['most_recent_available_match_date'] or 'none'}."])
        if summary["matches"]:
            for match in summary["matches"]:
                lines.append(f"- {match['date']}: vs {match['opponent']} ({match['venue_status']}) "
                             f"{match['score']} — {match['result']}")
        else:
            lines.append("- No matches are present for this team in the available reports.")
        totals = summary["summary"]
        lines.extend([f"- Record: {totals['wins']} W, {totals['draws']} D, {totals['losses']} L; "
                      f"{totals['goals_scored']} goals for, {totals['goals_conceded']} against; "
                      f"goal difference {totals['goal_difference']:+}; {totals['points']} points.", ""])
    lines.extend([f"Data period: {result['data_period']['start']} to {result['data_period']['end']}.",
                  result["coverage_note"]])
    return "\n".join(lines)
