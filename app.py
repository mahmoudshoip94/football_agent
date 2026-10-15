"""Streamlit presentation layer for the existing football agent package."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

from agent import ask
from agent.data_loader import load_datasets
from agent.league_tools import get_league_table
from agent.match_tools import H2H_NOTE, PERIOD_NOTE, head_to_head, team_form
from agent.player_tools import compare_players, get_player_stats

ENTER_MANUALLY = "Enter a name…"
SELECT_PROMPT = "Choose from available data…"


@st.cache_data(show_spinner=False)
def load_page_data():
    """Cache only local, deterministic dataset loading for the current process."""
    return load_datasets()


def run_chat_query(question: str, history: list[dict] | None = None) -> str:
    """Delegate conversational questions to the existing agent entry point."""
    return ask(question, history=history) if history else ask(question)


def request_chat_answer(question: str, history: list[dict] | None = None) -> tuple[str | None, str | None]:
    """Return either a successful answer or a sanitized, user-facing error."""
    try:
        return (run_chat_query(question, history) if history else run_chat_query(question)), None
    except Exception as error:  # Provider errors vary by LangChain/provider version.
        return None, friendly_agent_error(error)


def compare_players_for_ui(rows, player_a: str, player_b: str,
                           team_a: str | None = None, team_b: str | None = None):
    return compare_players(rows, player_a, player_b, team_a, team_b)


def get_team_form_for_ui(match_reports, team_a: str, team_b: str | None = None):
    return team_form(match_reports, team_a, team_b)


def get_head_to_head_for_ui(match_reports, team_a: str, team_b: str):
    return head_to_head(match_reports, team_a, team_b)


def get_league_table_for_ui(table_rows):
    return json.loads(get_league_table(table_rows))


def friendly_agent_error(error: Exception) -> str:
    """Translate runtime failures to useful messages without exposing exception details."""
    message = str(error)
    error_name = type(error).__name__.casefold()
    if isinstance(error, RuntimeError) and "GROQ_API_KEY" in message:
        return "The agent is not configured yet. Add GROQ_API_KEY to the project .env file or environment, then restart the app."
    if "timeout" in error_name or "timed out" in message.casefold():
        return "The agent request timed out. Please try again in a moment."
    if any(term in error_name for term in ("authentication", "ratelimit", "apierror", "connection")):
        return "The model provider could not complete this request. Check provider availability and configuration, then retry."
    return "The agent could not complete this request. Please try again."


def coverage_message(result: dict[str, Any], *, head_to_head_page: bool = False) -> str:
    period = result.get("data_period") or {}
    start, end = period.get("start"), period.get("end")
    disclosure = result.get("history_note") if head_to_head_page else result.get("coverage_note")
    date_text = f"Available reports cover {start} through {end}." if start and end else "The available reporting period could not be determined."
    return f"{date_text} {disclosure or (H2H_NOTE if head_to_head_page else PERIOD_NOTE)}"


def _select_or_enter(label: str, values: list[str], key: str) -> str:
    choices = [SELECT_PROMPT, *values, ENTER_MANUALLY]
    selected = st.selectbox(label, choices, key=f"{key}_select")
    if selected == ENTER_MANUALLY:
        return st.text_input(f"Enter {label.lower()}", key=f"{key}_manual").strip()
    return "" if selected == SELECT_PROMPT else selected


def _team_names(table_rows, match_reports) -> list[str]:
    names = {str(row.get("Squad", "")).strip() for row in table_rows if row.get("Squad")}
    for report in match_reports:
        for side in (report.get("teams") or {}).values():
            name = side.get("name") or side.get("team") or side.get("title")
            if name:
                names.add(str(name).strip())
    return sorted(names, key=str.casefold)


def _player_teams(player_rows, player: str) -> list[str]:
    return sorted({str(row.get("Squad", "")).strip() for row in player_rows
                   if str(row.get("Player", "")).strip().casefold() == player.casefold()
                   and row.get("Squad")}, key=str.casefold)


def _player_team_selector(label: str, player_rows, player: str, key: str) -> str | None:
    teams = _player_teams(player_rows, player) if player else []
    if len(teams) > 1:
        selected = st.selectbox(f"{label} team (resolve duplicate name)",
                                ["Select a team…", *teams], key=f"{key}_team")
        return None if selected == "Select a team…" else selected
    return teams[0] if len(teams) == 1 else None


def _render_clarification(result: dict[str, Any], entity: str) -> None:
    st.warning("The request could not be resolved reliably. Please clarify the selection.")
    for item in result.get(entity, []):
        candidates = item.get("candidates", [])
        if candidates:
            labels = []
            for candidate in candidates:
                if isinstance(candidate, dict):
                    label = candidate.get("player") or candidate.get("team", "")
                    if candidate.get("player") and candidate.get("team"):
                        label += f" ({candidate['team']})"
                else:
                    label = str(candidate)
                labels.append(label)
            choices = ", ".join(labels)
            st.caption(f"{item.get('requested', 'Selection')}: {choices}")
    if result.get("reason"):
        st.caption(result["reason"])


def _render_chat(*, embedded: bool = False) -> None:
    if embedded:
        st.subheader("AI Football Chat")
    else:
        st.header("Chat")
        st.caption("Ask natural-language questions about the bundled Premier League dataset.")
        st.info("Conversation context is passed to the agent for follow-up questions.")
    messages = st.session_state.setdefault("football_chat_messages", [])
    history = st.container(
        height=350 if embedded else "content", border=False,
        key="home_chat_history" if embedded else None,
        autoscroll=True if embedded else None,
    )
    with history:
        for message in messages:
            with st.chat_message(message["role"]):
                if message.get("error"):
                    st.error(message["content"])
                else:
                    st.markdown(message["content"])
    question = st.chat_input(
        "Ask about players, fixtures, form, head-to-head, or standings…",
        key="home_chat_input" if embedded else None,
    )
    if not question:
        return
    messages.append({"role": "user", "content": question})
    with history:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Checking the football data…"):
                answer, error_message = request_chat_answer(question, [m for m in messages[:-1] if not m.get("error")])
            if error_message:
                st.error(error_message)
                messages.append({"role": "assistant", "content": error_message, "error": True})
            else:
                st.markdown(answer)
                messages.append({"role": "assistant", "content": answer})


def get_featured_players_for_ui(player_rows) -> list[dict[str, Any]]:
    """Rank distinct player/team identities using the existing numeric stats helper."""
    unique = {}
    for row in player_rows:
        player = str(row.get("Player") or "").strip()
        team = str(row.get("Squad") or "").strip()
        if player:
            unique.setdefault((player.casefold(), team.casefold()), row)
    return json.loads(get_player_stats(unique.values(), stat="goals", limit=5))


def _render_home(table_rows, player_rows) -> None:
    top_left, top_right = st.columns([1, 1], gap="medium")
    with top_left, st.container(border=True, height="stretch"):
        st.subheader("Featured Players")
        players = get_featured_players_for_ui(player_rows)[:4]
        if not players:
            st.info("No player statistics are available.")
        st.markdown("  \n".join(
            f"**{rank}. {player['player']}** · {player['team'] or 'Team not recorded'} "
            f"— {player['goals']} goals · {player['assists']} assists"
            for rank, player in enumerate(players, start=1)
        ))
    with top_right, st.container(border=True, height="stretch"):
        st.subheader("Top 5 League Teams")
        rows = sorted(get_league_table_for_ui(table_rows), key=lambda row: row["position"])[:5]
        gd_teams = {row.get("Squad") for row in table_rows if row.get("GD") not in (None, "")}
        if not rows:
            st.info("No standings are available.")
        leaderboard = []
        for row in rows:
            goal_diff = f" · GD {row['goal_diff']:+d}" if row["team"] in gd_teams else ""
            leaderboard.append(f"**{row['position']}. {row['team']}** · {row['points']} points{goal_diff}")
        st.markdown("  \n".join(leaderboard))
    st.divider()
    with st.container(border=True):
        _render_chat(embedded=True)


def _render_player_comparison(player_rows) -> None:
    st.header("Player Comparison")
    st.caption("Compare two players using the season statistics in Player_Stats.csv.")
    names = sorted({str(row.get("Player", "")).strip() for row in player_rows if row.get("Player")}, key=str.casefold)
    left, right = st.columns(2)
    with left:
        player_a = _select_or_enter("Player A", names, "player_a")
        team_a = _player_team_selector("Player A", player_rows, player_a, "player_a")
    with right:
        player_b = _select_or_enter("Player B", names, "player_b")
        team_b = _player_team_selector("Player B", player_rows, player_b, "player_b")
    submitted = st.button("Compare players", type="primary")
    if not submitted:
        return
    if not player_a or not player_b:
        st.warning("Choose or enter both player names.")
        return
    result = compare_players_for_ui(player_rows, player_a, player_b, team_a, team_b)
    if result.get("status") != "ok":
        _render_clarification(result, "players")
        return
    player_a_data, player_b_data = result["players"]
    difference = result["difference_player_a_minus_player_b"]
    stats = [
        ("Goals", "goals", None), ("Assists", "assists", None),
        ("Minutes", "minutes", None), ("Appearances", "appearances", None),
        ("Goals per 90", "per_90", "goals"), ("Assists per 90", "per_90", "assists"),
        ("G+A per 90 (overall)", "per_90", "goals_assists"),
        ("Non-penalty goals per 90", "per_90", "non_penalty_goals"),
        ("Non-penalty G+A per 90", "per_90", "non_penalty_goals_assists"),
    ]
    display_rows = []
    for label, field, nested in stats:
        value_a = player_a_data[field][nested] if nested else player_a_data[field]
        value_b = player_b_data[field][nested] if nested else player_b_data[field]
        delta = difference[field][nested] if nested else difference[field]
        display_rows.append({"Statistic": label, player_a_data["player"]: value_a,
                             player_b_data["player"]: value_b, "A − B": delta})
    st.subheader(f"{player_a_data['player']} ({player_a_data['team']}) vs {player_b_data['player']} ({player_b_data['team']})")
    st.dataframe(display_rows, hide_index=True, width="stretch")
    st.caption("Per-90 values are shown only when available in the source data. Differences are supplied by the deterministic comparison function.")
    st.bar_chart([
        {"Player": player_a_data["player"], "Goals": player_a_data["goals"], "Assists": player_a_data["assists"]},
        {"Player": player_b_data["player"], "Goals": player_b_data["goals"], "Assists": player_b_data["assists"]},
    ], x="Player", y=["Goals", "Assists"])


def _render_form(match_reports, teams: list[str]) -> None:
    st.header("Team Form")
    st.caption("Latest available matches in the repository, newest first.")
    team = _select_or_enter("Team", teams, "form_team")
    submitted = st.button("Show recent form", type="primary")
    if not submitted:
        return
    if not team:
        st.warning("Choose or enter a team name.")
        return
    result = get_team_form_for_ui(match_reports, team)
    if result.get("status") != "ok":
        _render_clarification(result, "teams")
        return
    summary = result["teams"][0]
    st.subheader(summary["team"])
    st.write(f"**Matches available:** {summary['matches_available']} · **Most recent:** {summary['most_recent_available_match_date'] or 'None'} · **Shown:** {summary['matches_in_form']}")
    st.dataframe([{
        "Date": item["date"], "Opponent": item["opponent"], "Score (team view)": item["score"],
        "Home/Away": item["venue_status"].title(), "Result": item["result"],
    } for item in summary["matches"]], hide_index=True, width="stretch")
    totals = summary["summary"]
    metric_rows = [
        ("Wins", totals["wins"]), ("Draws", totals["draws"]), ("Losses", totals["losses"]),
        ("Goals scored", totals["goals_scored"]), ("Goals conceded", totals["goals_conceded"]),
        ("Goal difference", totals["goal_difference"]), ("Points", totals["points"]),
    ]
    columns = st.columns(4)
    for index, (label, value) in enumerate(metric_rows):
        with columns[index % len(columns)]:
            st.metric(label, value)
    st.warning(coverage_message(result))


def _render_head_to_head(match_reports, teams: list[str]) -> None:
    st.header("Head-to-Head")
    st.caption("Meetings present in the repository's match reports, viewed from Team A's perspective.")
    left, right = st.columns(2)
    with left:
        team_a = _select_or_enter("Team A", teams, "h2h_a")
    with right:
        team_b = _select_or_enter("Team B", teams, "h2h_b")
    submitted = st.button("Compare teams", type="primary")
    if not submitted:
        return
    if not team_a or not team_b:
        st.warning("Choose or enter both team names.")
        return
    result = get_head_to_head_for_ui(match_reports, team_a, team_b)
    if result.get("status") != "ok":
        _render_clarification(result, "teams")
        return
    st.subheader(f"{result['team_a']} vs {result['team_b']}")
    st.dataframe([{
        "Date": item["date"], "Home": item["home_team"], "Away": item["away_team"],
        "Score": item["score"], "Venue": item.get("venue") or "Not recorded",
        f"Result for {result['team_a']}": item["result_for_first_team"],
    } for item in result["matches"]], hide_index=True, width="stretch")
    summary = result["summary_for_team_a"]
    metrics = [
        ("Matches", summary["total_matches"]), ("Wins", summary["wins"]),
        ("Draws", summary["draws"]), ("Losses", summary["losses"]),
        ("Goals scored", summary["goals_scored"]), ("Goals conceded", summary["goals_conceded"]),
    ]
    columns = st.columns(3)
    for index, (label, value) in enumerate(metrics):
        with columns[index % len(columns)]:
            st.metric(label, value)
    st.warning(coverage_message(result, head_to_head_page=True))


def _render_league_table(table_rows) -> None:
    st.header("League Table")
    st.caption("Standings from the repository's existing season table; no live standings are fetched.")
    rows = get_league_table_for_ui(table_rows)
    columns = {
        "position": "Position", "team": "Club", "played": "MP", "wins": "W",
        "draws": "D", "losses": "L", "goals_for": "GF", "goals_against": "GA",
        "goal_diff": "GD", "points": "Pts",
    }
    st.dataframe([{label: row[key] for key, label in columns.items()} for row in rows],
                 hide_index=True, width="stretch", height=720)


def main() -> None:
    st.set_page_config(page_title="Football Analytics", page_icon="⚽", layout="wide")
    with st.sidebar:
        st.header("Navigate")
        section = st.radio("Section", ["Home", "Chat", "Player Comparison", "Team Form", "Head-to-Head", "League Table"], label_visibility="collapsed")
    if section == "Home":
        st.subheader("⚽ Football Analytics · Premier League 2024/25")
    else:
        st.title("⚽ Football Analytics")
        st.caption("Premier League 2024/25 dataset tools")
    try:
        table_rows, player_rows, match_reports, metadata = load_page_data()
    except Exception:
        st.error("The football datasets could not be loaded. Check that the repository Data files are present and valid.")
        return
    teams = _team_names(table_rows, match_reports)
    if section == "Home":
        _render_home(table_rows, player_rows)
    elif section == "Chat":
        _render_chat()
    elif section == "Player Comparison":
        _render_player_comparison(player_rows)
    elif section == "Team Form":
        _render_form(match_reports, teams)
    elif section == "Head-to-Head":
        _render_head_to_head(match_reports, teams)
    else:
        _render_league_table(table_rows)
    st.caption(f"Available match report period: {metadata['match_start']} to {metadata['match_end']} · partial historical coverage.")


if __name__ == "__main__":
    main()
