from __future__ import annotations

from agent.data_loader import load_datasets, load_matches
from agent.intent import classify_question_scope, normalize_question, query_dataset_scope_limitation
from agent.milestone_tools import (
    analyze_milestone_query,
    first_hat_tricks,
    first_to_goal_threshold,
    query_scoring_milestone,
)


def test_obvious_typos_and_paraphrased_football_intents_reach_supervisor():
    assert normalize_question("who reatched 10 goles first") == "who reached 10 goals first"
    for question in (
        "who scored first hat trick",
        "who reatched 10 goles first",
        "Who was the first player to reach 10 Premier League goals?",
        "Who made the quickest scoring milestone?",
    ):
        assert classify_question_scope(question) == "in_scope"
    assert classify_question_scope("What is the weather today?") == "out_of_scope"
    assert classify_question_scope("Who won La Liga?") == "out_of_scope"
    assert classify_question_scope("Can you explain xG chain involvement?") != "out_of_scope"


def test_default_context_answers_milestones_without_scope_clarification():
    matches = load_matches()
    hat_trick = analyze_milestone_query(matches, "Who scored the first hat-trick?")
    threshold = analyze_milestone_query(matches, "Who reached 10 goals first?")
    typo_threshold = analyze_milestone_query(matches, "Who reatched 10 goles first?")
    assert hat_trick["status"] == "ok"
    assert hat_trick["candidates"][0]["player"] == "Erling Haaland"
    assert threshold["status"] == typo_threshold["status"] == "ok"
    assert threshold["candidates"][0]["player"] == "Erling Haaland"
    assert typo_threshold["candidates"][0]["player"] == "Erling Haaland"


def test_repository_first_hat_trick_and_coverage():
    result = first_hat_tricks(load_matches())
    assert result["status"] == "ok"
    assert result["candidates"][0]["player"] == "Erling Haaland"
    assert result["candidates"][0]["date"] == "2024-08-24"
    assert result["candidates"][0]["goals_in_match"] == 3
    assert result["data_period"] == {"start": "2024-08-18", "end": "2024-12-22"}
    assert "timestamps" in result["precision_note"]


def test_repository_first_ten_goal_threshold_and_format_disclosure():
    matches = load_matches()
    result = first_to_goal_threshold(matches, 10)
    assert result["status"] == "ok"
    assert result["candidates"][0]["player"] == "Erling Haaland"
    assert result["candidates"][0]["date"] == "2024-09-22"
    assert (result["candidates"][0]["goal_total_before"],
            result["candidates"][0]["goal_total_after"]) == (9, 10)
    answer = query_scoring_milestone(matches, "Who reached 10 goals first?")
    assert "Erling Haaland" in answer
    assert "2024-08-18 to 2024-12-22" in answer
    assert "only part of the season" in answer
    assert "exact scoring order" in answer


def _report(day, player, goals):
    return {"date": f"2024-08-{day:02d}", "matchweek": day,
            "teams": {"home": {"name": "A", "score": 3},
                      "away": {"name": "B", "score": 0}},
            "player_stats": {"home": [{"Player": player, "Performance_Gls": str(goals)},
                                        {"Player": "16 Players", "Performance_Gls": "3"}],
                             "away": []}}


def test_synthetic_threshold_tie_and_excludes_aggregate_team_rows():
    reports = [_report(1, "P1", 2), _report(2, "P1", 1),
               _report(2, "P2", 3)]
    result = first_to_goal_threshold(reports, 3)
    assert result["status"] == "ok"
    assert {row["player"] for row in result["candidates"]} == {"P1", "P2"}
    assert all(row["goal_total_after"] == 3 for row in result["candidates"])


def test_top_scorer_remains_a_player_statistics_question():
    import json
    from agent.player_tools import get_player_stats
    _, players, _, _ = load_datasets()
    assert query_scoring_milestone(load_matches(), "Who scored the most goals?") is None
    top = json.loads(get_player_stats(players, stat="goals", limit=1))[0]
    assert top["player"] == "Mohamed Salah"
    assert top["goals"] == 29


def test_unknown_football_entity_is_not_blocked_as_unrelated():
    assert classify_question_scope("What did River Plate do in its last match?") != "out_of_scope"


def test_ask_runs_graph_then_uses_deterministic_milestone_result(monkeypatch):
    from types import SimpleNamespace
    import agent.workflow as workflow

    reports = load_matches()
    calls = []

    class FakeGraph:
        def invoke(self, state):
            calls.append(state)
            return {"messages": [SimpleNamespace(content="model fallback")]}

    monkeypatch.setattr(workflow, "_runtime", lambda: (FakeGraph(), [], reports, []))
    answer = workflow.ask("Who reached 10 goals first?")
    assert len(calls) == 1
    assert "Erling Haaland" in answer
    assert "model fallback" not in answer
    assert "Do you mean" not in answer



def test_empty_match_level_goal_data_returns_honest_limitations():
    from agent.milestone_tools import format_milestone_answer

    no_player_goal_data = [{"date": "2024-08-18", "teams": {
        "home": {"name": "A", "score": 0}, "away": {"name": "B", "score": 0}},
        "player_stats": {"home": [{"Player": "A Team", "Performance_Gls": "0"}],
                         "away": []}}]
    hat_result = first_hat_tricks(no_player_goal_data)
    threshold_result = first_to_goal_threshold(no_player_goal_data, 10)
    assert "No individual player hat-trick" in format_milestone_answer(hat_result)
    assert threshold_result["status"] == "unavailable"
    assert "do not contain usable player-level goal records" in format_milestone_answer(threshold_result)


def test_explicit_all_time_milestone_gets_data_limitation():
    matches = load_matches()
    answer = query_scoring_milestone(matches, "Who scored the first hat-trick ever?")
    assert "can't verify" in answer
    assert "2024-08-18 through 2024-12-22" in answer
    assert "Do you mean" not in answer
    assert query_dataset_scope_limitation("Who scored the most goals of all time?") is not None
    other_season = query_scoring_milestone(matches, "Who reached 10 goals first in 2023/24?")
    assert "can't verify" in other_season
    assert "2024/25" in other_season


def test_clean_sheets_are_reported_unsupported_for_actual_csv():
    import json
    from agent.data_loader import load_datasets
    from agent.player_tools import get_player_stats, query_player_stat_limitation

    _, players, _, _ = load_datasets()
    assert "Goalkeeping_CS" not in players[0]
    limitation = query_player_stat_limitation(players, "Who had the most clean sheets?")
    assert limitation and "no goalkeeper clean-sheets column" in limitation
    result = json.loads(get_player_stats(players, stat="clean_sheets"))
    assert result["status"] == "unsupported"


def test_player_stat_limitation_flows_through_ask_without_scope_question(monkeypatch):
    from types import SimpleNamespace
    from agent.data_loader import load_datasets
    import agent.workflow as workflow

    _, players, reports, _ = load_datasets()
    table, _, _, _ = load_datasets()
    class FakeGraph:
        def invoke(self, state):
            return {"messages": [SimpleNamespace(content="model answer must be overridden")]}
    monkeypatch.setattr(workflow, "_runtime", lambda: (FakeGraph(), players, reports, table))
    answer = workflow.ask("Who had the most clean sheets?")
    assert "can't identify a clean-sheets leader" in answer
    assert "Which league" not in answer and "Which season" not in answer


def test_default_player_and_team_leaders_reuse_existing_tools():
    from agent.league_tools import query_team_table_leader
    from agent.player_tools import query_player_leader
    table, players, _, _ = load_datasets()
    goals = query_player_leader(players, "Who scored the most goals?")
    assists = query_player_leader(players, "Which player had the most assists?")
    appearances = query_player_leader(players, "Who had the most appearances?")
    team_goals = query_team_table_leader(table, "Which team scored the most goals?")
    defense = query_team_table_leader(table, "Which team had the best defense?")
    assert "Mohamed Salah" in goals and "29 goals" in goals
    assert "assists" in assists and "appearances" in appearances
    assert "Liverpool" in team_goals
    assert "fewest goals conceded" in defense


def test_ask_answers_default_leader_queries_from_existing_datasets(monkeypatch):
    from types import SimpleNamespace
    import agent.workflow as workflow

    table, players, reports, _ = load_datasets()
    class FakeGraph:
        def invoke(self, state):
            return {"messages": [SimpleNamespace(content="model response")]}
    monkeypatch.setattr(workflow, "_runtime", lambda: (FakeGraph(), players, reports, table))
    top_scorer = workflow.ask("Who scored the most goals?")
    clean_sheets = workflow.ask("Who had the most clean sheets?")
    assert "Mohamed Salah" in top_scorer and "29 goals" in top_scorer
    assert "can't identify a clean-sheets leader" in clean_sheets
    assert "model response" not in top_scorer + clean_sheets
