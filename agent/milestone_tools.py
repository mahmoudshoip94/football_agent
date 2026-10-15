"""Chronological scoring milestones supported by match-level player statistics."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date
from typing import Any, Iterable

from .intent import normalize_question
from .match_tools import PERIOD_NOTE

TEAM_TOTAL_PATTERN = re.compile(r"\d+\s+players", re.IGNORECASE)
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
}
SCOPE_NOTE = (
    "Milestone totals use only individual player goal rows in the available 2024/25 "
    "match reports. Reports cover only part of the season through 2024-12-22; they do "
    "not establish Premier League all-time records or the complete season."
)
PRECISION_NOTE = (
    "The reports give player goals per match and match dates, not individual goal timestamps. "
    "A result is ordered by match date; the exact scoring order within a match or on the same "
    "date cannot be established."
)


def _int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _period(reports: list[dict[str, Any]]) -> dict[str, str | None]:
    dates = []
    for report in reports:
        try:
            dates.append(date.fromisoformat(str(report.get("date"))))
        except (TypeError, ValueError):
            continue
    return {"start": min(dates).isoformat() if dates else None,
            "end": max(dates).isoformat() if dates else None}


def _goal_events(match_reports: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str | None]]:
    """Legacy event view over the same validated relation used by general analysis."""
    from .analytics import relations, number
    reports = list(match_reports)
    events = []
    for row in relations([], [], reports)['player_matches']:
        goals = number(row.get('Performance_Gls'))
        if goals is None or goals <= 0:
            continue
        events.append({**{key: row[key] for key in (
            'date', 'player', 'team', 'opponent', 'home_team', 'away_team', 'home_score', 'away_score')},
            'home_score': _int(row['home_score']), 'away_score': _int(row['away_score']),
            '_date': date.fromisoformat(row['date']), 'matchweek': row.get('matchweek'),
            'venue_status': row['side'], 'goals_in_match': int(goals), 'venue_time': row.get('venue_time')})
    events.sort(key=lambda r: (r['_date'], r['home_team'], r['away_team'], r['player']))
    return events, _period(reports)


def first_hat_tricks(match_reports: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Find the earliest date with an individual player scoring at least three goals."""
    events, period = _goal_events(match_reports)
    hat_tricks = [event for event in events if event["goals_in_match"] >= 3]
    if not hat_tricks:
        return {"status": "not_found", "milestone": "first_hat_trick", "candidates": [],
                "data_period": period, "coverage_note": PERIOD_NOTE, "precision_note": PRECISION_NOTE}
    earliest = min(event["_date"] for event in hat_tricks)
    candidates = [{key: event[key] for key in (
        "date", "matchweek", "player", "team", "opponent", "venue_status",
        "goals_in_match", "home_team", "away_team", "home_score", "away_score", "venue_time",
    )} for event in hat_tricks if event["_date"] == earliest]
    return {"status": "ok", "milestone": "first_hat_trick", "candidates": candidates,
            "data_period": period, "coverage_note": PERIOD_NOTE, "scope_note": SCOPE_NOTE,
            "precision_note": PRECISION_NOTE}


def first_to_goal_threshold(
    match_reports: Iterable[dict[str, Any]], threshold: int,
) -> dict[str, Any]:
    """Find who first crossed a season-goal threshold by available match date."""
    if threshold <= 0:
        raise ValueError("Goal threshold must be a positive integer")
    events, period = _goal_events(match_reports)
    if not events:
        return {"status": "unavailable", "milestone": "goal_threshold", "threshold": threshold,
                "candidates": [], "data_period": period, "coverage_note": PERIOD_NOTE}
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_date[event["date"]].append(event)
    totals: dict[tuple[str, str], int] = defaultdict(int)
    date_crossings = []
    for day in sorted(by_date):
        daily: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for event in by_date[day]:
            daily[(event["player"], event["team"] or "")].append(event)
        crossings = []
        for identity, player_events in daily.items():
            goals = sum(event["goals_in_match"] for event in player_events)
            before = totals[identity]
            after = before + goals
            if before < threshold <= after:
                matches = [{key: event[key] for key in (
                    "date", "matchweek", "opponent", "venue_status", "goals_in_match",
                    "home_team", "away_team", "home_score", "away_score", "venue_time",
                )} for event in player_events]
                crossings.append({"player": identity[0], "team": identity[1], "date": day,
                                  "goal_total_before": before, "goals_in_matches_on_date": goals,
                                  "goal_total_after": after, "matches": matches})
            totals[identity] = after
        if crossings:
            date_crossings = crossings
            break
    return {
        "status": "ok" if date_crossings else "not_reached",
        "milestone": "goal_threshold", "threshold": threshold,
        "candidates": date_crossings, "data_period": period,
        "coverage_note": PERIOD_NOTE, "scope_note": SCOPE_NOTE,
        "precision_note": PRECISION_NOTE,
    }


def _unsupported_milestone_scope(question: str) -> str | None:
    """Return an explicit unsupported scope; omitted scope uses the project default."""
    text = normalize_question(question)
    if any(term in text for term in ("all-time", "all time", "ever", "in history", "career record")):
        return "all-time"
    seasons = re.findall(r"\b(20\d{2})\s*(?:/|-)\s*(\d{2,4})\b", text)
    for start, end in seasons:
        normalized_end = end if len(end) == 4 else start[:2] + end
        if (start, normalized_end) != ("2024", "2025"):
            return f"{start}/{end}"
    if any(term in text for term in ("last season", "previous season", "prior season")):
        return "another season"
    return None


def _scope_limitation(scope: str) -> str:
    return (
        f"I can't verify that {scope} milestone from this project's datasets. "
        "They contain 2024/25 season statistics and partial match reports dated "
        "2024-08-18 through 2024-12-22, not complete historical coverage."
    )

def _threshold_from_question(question: str) -> int | None:
    text = normalize_question(question)
    words = "|".join(sorted(NUMBER_WORDS, key=len, reverse=True))
    match = re.search(
        rf"\b(\d{{1,3}}|{words})\b\s*(?:-\s*)?(?:(?:premier\s+)?league\s+)?goals?\b",
        text,
    )
    if not match:
        match = re.search(rf"\b(?:reach(?:ed)?|hit|get\s+to)\s+(?:the\s+)?(?:\b(\d{{1,3}}|{words})\b)\s*(?:-\s*)?(?:goal\s+)?mark\b", text)
    if not match:
        return None
    value = match.group(1)
    return int(value) if value and value.isdigit() else NUMBER_WORDS.get(value)


def analyze_milestone_query(
    match_reports: Iterable[dict[str, Any]], question: str,
) -> dict[str, Any] | None:
    """Classify and answer supported milestone questions, or request scope clarification."""
    text = normalize_question(question)
    hat_trick_intent = "hat trick" in text and any(term in text for term in ("first", "earliest"))
    threshold = _threshold_from_question(text)
    threshold_intent = threshold is not None and any(
        term in text for term in ("first", "quickest", "fastest", "reach", "reached", "who hit", "who got")
    )
    if not (hat_trick_intent or threshold_intent):
        return None
    milestone = "first_hat_trick" if hat_trick_intent else "goal_threshold"
    requested_scope = _unsupported_milestone_scope(text)
    if requested_scope:
        return {
            "status": "unsupported_scope", "milestone": milestone,
            "limitation": _scope_limitation(requested_scope),
            "data_period": _period(list(match_reports)),
            "coverage_note": SCOPE_NOTE,
        }
    if hat_trick_intent:
        return first_hat_tricks(match_reports)
    return first_to_goal_threshold(match_reports, threshold)


def format_milestone_answer(result: dict[str, Any]) -> str:
    """Format deterministic milestone output without adding unsupported facts."""
    if result["status"] == "unsupported_scope":
        return result["limitation"]
    if result["status"] == "clarification_required":
        return result["clarification"]
    period = result.get("data_period") or {}
    if result["status"] == "not_reached":
        message = f"No player reached {result['threshold']} goals in the available match reports."
    elif result["status"] == "unavailable":
        message = "The available match reports do not contain usable player-level goal records for this milestone."
    elif result["status"] == "not_found":
        message = "No individual player hat-trick was recorded in the available match reports."
    elif result["milestone"] == "first_hat_trick":
        candidates = result["candidates"]
        names = ", ".join(f"{item['player']} ({item['team']})" for item in candidates)
        message = f"Earliest hat-trick date in the available reports: {candidates[0]['date']} - {names}."
    else:
        candidates = result["candidates"]
        names = ", ".join(
            f"{item['player']} ({item['team']}, {item['goal_total_before']} to "
            f"{item['goal_total_after']} goals)" for item in candidates
        )
        message = f"First recorded match date to reach {result['threshold']} goals: {candidates[0]['date']} - {names}."
    details = []
    for candidate in result.get("candidates", []):
        matches = candidate.get("matches") or [candidate]
        for match in matches:
            if "matches" in candidate:
                details.append(f"{candidate['player']}: {match['date']}, Matchweek {match['matchweek']}, "
                               f"{match['home_team']} {match['home_score']}-{match['away_score']} {match['away_team']}; "
                               f"{match['goals_in_match']} goal{'s' if match['goals_in_match'] != 1 else ''} in match.")
            else:
                details.append(f"{candidate['player']}: {match['date']}, Matchweek {match['matchweek']}, "
                               f"{match['home_team']} {match['home_score']}-{match['away_score']} {match['away_team']}.")
    if details:
        message += " Supporting match: " + " ".join(details)
    message += f" Data period: {period.get('start')} to {period.get('end')}. {result.get('scope_note', SCOPE_NOTE)}"
    if result.get("precision_note"):
        message += " " + result["precision_note"]
    return message


def query_scoring_milestone(match_reports: Iterable[dict[str, Any]], question: str) -> str | None:
    result = analyze_milestone_query(match_reports, question)
    return format_milestone_answer(result) if result is not None else None


def get_scoring_milestones(match_reports: Iterable[dict[str, Any]], question: str) -> str:
    if "hat trick" in normalize_question(question) and not _unsupported_milestone_scope(question):
        result = scoring_events(match_reports)
        result.pop("precision_note", None)
        by_date = defaultdict(list)
        for position, event in enumerate(result.get("rows", []), start=1):
            by_date[event["date"]].append((position, event))
        for events in by_date.values():
            for _, event in events:
                event["rank_start"], event["rank_end"] = events[0][0], events[-1][0]
                if len(events) > 1:
                    event["precision_note"] = (
                        "Multiple hat-tricks share this date; missing goal timestamps "
                        "prevent ordering these tied events, not events on different dates."
                    )
        result["coverage_note"] = (
            "Repository match reports cover only 2024-08-18 through 2024-12-22. "
            "Ranks identify events in the available reports; the latest recorded event "
            "cannot establish the final hat-trick of the entire 2024/25 season."
        )
    else:
        result = analyze_milestone_query(match_reports, question)
        if result is None:
            result = {"status": "unsupported", "message": "The query does not specify a supported chronological scoring milestone."}
    return json.dumps(result, ensure_ascii=False)


def scoring_events(match_reports, threshold=None, position=None):
    """All qualifying player-match events or first threshold crossings per identity."""
    from .analytics import analyze_data
    reports = list(match_reports)
    if threshold is not None and (not isinstance(threshold, int) or threshold <= 0):
        raise ValueError('Goal threshold must be a positive integer')
    steps = []
    if threshold is None:
        steps.append({'op':'filter', 'field':'Performance_Gls', 'operator':'ge', 'value':3})
    else:
        steps.extend([
            {'op':'cumulative', 'by':['player','team'], 'field':'Performance_Gls', 'name':'total_goals'},
            {'op':'filter', 'field':'total_goals', 'operator':'ge', 'value':threshold},
            {'op':'filter', 'field':'total_goals_before', 'operator':'lt', 'value':threshold}])
    steps.append({'op':'sort','by':['date']})
    complete = analyze_data([], [], reports, 'player_matches', steps)
    if position is not None:
        selected = analyze_data([], [], reports, 'player_matches', steps + [{'op':'ordinal','field':'date','position':position}])
    else:
        selected = complete
    selected['qualifying_events'] = complete.get('row_count', 0)
    selected['requested_position'] = position
    selected['threshold'] = threshold
    selected['ambiguous_order'] = len(selected.get('rows', []))>1 if position is not None else False
    if selected['ambiguous_order']: selected['status'] = 'ambiguous'
    return selected
