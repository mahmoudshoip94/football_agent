import json
import os
from pathlib import Path

import pytest

from agent.data_loader import load_datasets
from agent.league_tools import get_league_table, query_team_table_leader
from agent.match_tools import (
    H2H_NOTE,
    PERIOD_NOTE,
    get_match_fixtures,
    head_to_head,
    query_match_analysis,
    team_form,
)
from agent.milestone_tools import first_hat_tricks, first_to_goal_threshold, query_scoring_milestone
from agent.player_tools import (
    compare_players,
    compare_player_stats,
    get_player_stats,
    query_player_comparison,
    query_player_leader,
    query_player_stat_limitation,
)


@pytest.fixture(scope="module")
def datasets():
    return load_datasets()


def match(day, home, away, hs, aws, venue=None):
    return {
        "date": day,
        "teams": {"home": {"name": home, "score": hs},
                  "away": {"name": away, "score": aws}},
        "venue": venue,
    }


def test_real_player_comparison_and_per_90(datasets):
    _, players, _, _ = datasets
    result = compare_players(players, "Mohamed Salah", "Erling Haaland")
    assert result["status"] == "ok"
    salah, haaland = result["players"]
    assert (salah["team"], salah["goals"], salah["assists"], salah["minutes"], salah["appearances"]) == (
        "Liverpool", 29, 18, 3371, 38
    )
    assert salah["per_90"]["goals_assists"] == 1.25
    assert salah["per_90"]["non_penalty_goals_assists"] == 1.01
    assert result["difference_player_a_minus_player_b"]["goals"] == 7
    assert result["difference_player_a_minus_player_b"]["per_90"]["goals_assists"] == 0.43
    assert haaland["appearances"] == 31
    assert "G+A per 90 (Per 90 Minutes_G+A)" in query_player_comparison(
        players, "Compare Mohamed Salah vs Erling Haaland"
    )


def test_duplicate_and_missing_player_resolution(datasets):
    _, players, _, _ = datasets
    ambiguous = compare_players(players, "Carlos Alcaraz", "Erling Haaland")
    assert ambiguous["status"] == "clarification_required"
    assert {c["team"] for c in ambiguous["players"][0]["candidates"]} == {"Southampton", "Everton"}
    resolved = compare_players(players, "Carlos Alcaraz", "Erling Haaland", "Everton")
    assert resolved["status"] == "ok"
    assert resolved["players"][0]["team"] == "Everton"
    missing = compare_players(players, "Not A Real Player", "Erling Haaland")
    assert missing["status"] == "clarification_required"
    assert missing["players"][0]["status"] == "missing"


def test_player_stats_uses_appearance_source_and_per90_fields(datasets):
    _, players, _, _ = datasets
    result = json.loads(get_player_stats(players, "Mohamed Salah", limit=1))[0]
    raw = next(row for row in players if row["Player"] == "Mohamed Salah")
    assert result["appearances"] == int(raw["Playing Time_MP"]) == 38
    assert result["goals_per_90"] == float(raw["Per 90 Minutes_Gls"])
    assert result["ga_pk_per_90"] == float(raw["Per 90 Minutes_G+A-PK"])


def test_zero_minutes_do_not_return_per90_rates():
    rows = [{"Player": "Zero", "Squad": "Arsenal", "Playing Time_Min": "0",
             "Playing Time_MP": "1", "Performance_Gls": "0", "Performance_Ast": "0",
             **{column: "0.00" for column in (
                 "Per 90 Minutes_Gls", "Per 90 Minutes_Ast", "Per 90 Minutes_G+A",
                 "Per 90 Minutes_G-PK", "Per 90 Minutes_G+A-PK",
             )}},
            {"Player": "Other", "Squad": "Chelsea", "Playing Time_Min": "90",
             "Playing Time_MP": "1", "Performance_Gls": "1", "Performance_Ast": "0"}]
    result = compare_players(rows, "Zero", "Other")
    assert result["players"][0]["per_90"]["goals"] is None
    assert result["difference_player_a_minus_player_b"]["per_90"]["goals"] is None


def test_latest_five_form_order_venue_draw_and_aggregates(datasets):
    _, _, reports, _ = datasets
    result = team_form(reports, "Arsenal")
    arsenal = result["teams"][0]
    assert [row["date"] for row in arsenal["matches"]] == sorted(
        (row["date"] for row in arsenal["matches"]), reverse=True
    )
    assert arsenal["matches_in_form"] == 5
    assert arsenal["matches"][0]["date"] == "2024-12-21"
    assert arsenal["summary"] == {
        "wins": 3, "draws": 2, "losses": 0, "goals_scored": 13,
        "goals_conceded": 4, "goal_difference": 9, "points": 11,
    }
    assert result["data_period"] == {"start": "2024-08-18", "end": "2024-12-22"}
    assert result["coverage_note"] == PERIOD_NOTE


def test_form_home_away_and_short_history():
    reports = [match("2024-08-01", "Arsenal", "Chelsea", 2, 1),
               match("2024-08-08", "Chelsea", "Arsenal", 0, 1),
               match("2024-08-15", "Arsenal", "Chelsea", 1, 1)]
    result = team_form(reports, "Arsenal")
    team = result["teams"][0]
    assert [row["venue_status"] for row in team["matches"]] == ["home", "away", "home"]
    assert [row["result"] for row in team["matches"]] == ["D", "W", "W"]
    assert team["matches_available"] == team["matches_in_form"] == 3
    assert team["summary"] == {
        "wins": 2, "draws": 1, "losses": 0, "goals_scored": 4,
        "goals_conceded": 2, "goal_difference": 2, "points": 7,
    }


def test_two_team_form_and_team_clarifications(datasets):
    _, _, reports, _ = datasets
    both = team_form(reports, "Arsenal", "Chelsea")
    assert [team["team"] for team in both["teams"]] == ["Arsenal", "Chelsea"]
    assert both["teams"][0]["matches_available"] != 0
    short = team_form([match("2024-08-01", "Arsenal", "Chelsea", 1, 0)], "Arsenal")
    assert short["teams"][0]["matches_in_form"] == 1
    unknown = team_form(reports, "Barcelona")
    assert unknown["status"] == "clarification_required"
    ambiguous = team_form([match("2024-08-01", "Manchester United", "Chelsea", 1, 0),
                           match("2024-08-02", "Sheffield United", "Arsenal", 0, 1)], "United")
    assert ambiguous["teams"][0]["reason"] == "ambiguous"


def test_head_to_head_orientations_and_coverage(datasets):
    reports = [match("2024-08-01", "Arsenal", "Chelsea", 2, 1, "Emirates"),
               match("2024-08-08", "Chelsea", "Arsenal", 0, 1, "Stamford Bridge"),
               match("2024-08-15", "Arsenal", "Chelsea", 1, 1, "Emirates")]
    result = head_to_head(reports, "Arsenal", "Chelsea")
    assert [m["result_for_first_team"] for m in result["matches"]] == ["W", "W", "D"]
    assert result["summary_for_team_a"] == {
        "total_matches": 3, "wins": 2, "draws": 1, "losses": 0,
        "goals_scored": 4, "goals_conceded": 2,
    }
    reverse = head_to_head(reports, "Chelsea", "Arsenal")
    assert reverse["summary_for_team_a"]["losses"] == 2
    assert result["matches"][0]["venue"] == "Emirates"
    assert result["history_note"] == H2H_NOTE
    assert "incomplete" in result["history_note"].lower()
    real = head_to_head(datasets[2], "Chelsea", "Arsenal")
    assert real["data_period"] == {"start": "2024-08-18", "end": "2024-12-22"}


def test_match_tools_and_natural_language_formatters(datasets):
    table, players, matches, _ = datasets
    league = json.loads(get_league_table(table, top_n=4))
    assert len(league) == 4
    fixture = json.loads(get_match_fixtures(matches, team="Arsenal", limit=2))
    assert len(fixture) == 2 and fixture[0]["home_team"]
    form_text = query_match_analysis(matches, "What is Arsenal's form in the last five matches?")
    assert "Data period: 2024-08-18 to 2024-12-22" in form_text
    pair_text = query_match_analysis(matches, "Compare recent form of Arsenal and Chelsea")
    assert "## Arsenal" in pair_text and "## Chelsea" in pair_text
    h2h_text = query_match_analysis(matches, "Chelsea vs Arsenal head-to-head")
    assert "Head-to-head" in h2h_text and "history is incomplete" in h2h_text
    assert "Please identify both teams" in query_match_analysis(matches, "head-to-head history")
    assert query_player_comparison(players, "Compare Mohamed Salah and Erling Haaland")


def test_imports_do_not_require_or_call_langchain(monkeypatch, tmp_path):
    import subprocess
    import sys

    script = (
        "import builtins; original=builtins.__import__; "
        "blocked=('langchain','langgraph'); "
        "builtins.__import__=lambda name,*a,**k: (_ for _ in ()).throw(AssertionError(name)) "
        "if name.split('.')[0] in blocked else original(name,*a,**k); "
        "import agent; assert callable(agent.ask)"
    )
    env = os.environ.copy()
    project = str(Path(__file__).resolve().parents[1])
    env["PYTHONPATH"] = project + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path,
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_import_paths_load_data_outside_repository(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    table, players, matches, metadata = load_datasets()
    assert len(table) == 20 and len(players) == 574 and len(matches) == 158
    assert metadata["match_start"] == "2024-08-18"
    assert metadata["match_end"] == "2024-12-22"


def test_notebook_and_package_behavioral_parity(datasets):
    import re
    import typing
    from datetime import date as date_type

    table, players, matches, _ = datasets
    notebook = json.loads((Path(__file__).resolve().parents[1] / "notebook.ipynb").read_text(encoding="utf-8"))
    tools_cell = "".join(notebook["cells"][9]["source"])
    namespace = {
        "Any": typing.Any, "Iterable": typing.Iterable, "Optional": typing.Optional,
        "date": date_type, "json": json, "re": re, "tool": lambda function: function,
        "TABLE_ROWS": table, "PLAYER_ROWS": players, "MATCH_REPORTS": matches,
    }
    exec(compile(tools_cell, "notebook tools cell", "exec"), namespace)

    assert compare_players(players, "Mohamed Salah", "Erling Haaland") == namespace[
        "compare_players"
    ](players, "Mohamed Salah", "Erling Haaland")
    assert compare_players(players, "Carlos Alcaraz", "Erling Haaland", "Everton") == namespace[
        "compare_players"
    ](players, "Carlos Alcaraz", "Erling Haaland", "Everton")
    assert compare_players(players, "Not A Real Player", "Erling Haaland") == namespace[
        "compare_players"
    ](players, "Not A Real Player", "Erling Haaland")
    assert team_form(matches, "Arsenal", "Chelsea") == namespace["team_form"](
        matches, "Arsenal", "Chelsea"
    )
    assert team_form(matches, "Barcelona") == namespace["team_form"](matches, "Barcelona")
    assert head_to_head(matches, "Chelsea", "Arsenal") == namespace["head_to_head"](
        matches, "Chelsea", "Arsenal"
    )
    assert get_league_table(table, top_n=5) == namespace["get_league_table"](5)
    assert json.loads(get_player_stats(players, "Mohamed Salah", limit=1)) == json.loads(
        namespace["get_player_stats"]("Mohamed Salah", limit=1)
    )
    assert json.loads(get_player_stats(players, stat="clean_sheets")) == json.loads(
        namespace["get_player_stats"](stat="clean_sheets")
    )
    assert query_player_stat_limitation(players, "Who had the most clean sheets?") == namespace[
        "query_player_stat_limitation"
    ](players, "Who had the most clean sheets?")
    assert json.loads(get_match_fixtures(matches, team="Arsenal", limit=4)) == json.loads(
        namespace["get_match_fixtures"](team="Arsenal", limit=4)
    )
    assert query_player_leader(players, "Who scored the most goals?") == namespace["query_player_leader"](players, "Who scored the most goals?")
    assert query_team_table_leader(table, "Which team scored the most goals?") == namespace["query_team_table_leader"](table, "Which team scored the most goals?")
    assert first_hat_tricks(matches) == namespace["first_hat_tricks"](matches)
    assert first_to_goal_threshold(matches, 10) == namespace["first_to_goal_threshold"](matches, 10)
    for milestone_query in ("who scored first hat trick", "who reatched 10 goles first",
                            "Who reached 10 goals first this season?"):
        assert query_scoring_milestone(matches, milestone_query) == namespace["query_scoring_milestone"](
            matches, milestone_query
        )

    query = "Compare Mohamed Salah vs Erling Haaland"
    assert query_player_comparison(players, query) == namespace["_query_player_comparison"](
        players, query
    )
    query = "What is Arsenal's form in the last five matches?"
    assert query_match_analysis(matches, query) == namespace["query_match_analysis"](
        matches, query
    )
    query = "Compare the recent form of Arsenal and Chelsea"
    assert query_match_analysis(matches, query) == namespace["query_match_analysis"](
        matches, query
    )
    query = "Show the head-to-head record between Chelsea and Arsenal"
    assert query_match_analysis(matches, query) == namespace["query_match_analysis"](
        matches, query
    )
