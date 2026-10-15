from pathlib import Path
import os
import subprocess
import sys
from unittest.mock import Mock

import pytest

import app


def test_app_import_and_chat_adapter_do_not_call_llm(monkeypatch):
    ask = Mock(return_value="grounded result")
    monkeypatch.setattr(app, "ask", ask)
    assert app.run_chat_query("What is Arsenal's form?") == "grounded result"
    ask.assert_called_once_with("What is Arsenal's form?")


def test_importing_app_does_not_initialize_the_agent():
    project = str(Path(__file__).resolve().parents[1])
    env = os.environ.copy()
    env["PYTHONPATH"] = project + os.pathsep + env.get("PYTHONPATH", "")
    script = (
        "import agent.workflow as workflow; "
        "workflow._runtime=lambda: (_ for _ in ()).throw(AssertionError('runtime called')); "
        "import app"
    )
    result = subprocess.run([sys.executable, "-c", script], cwd=Path(project).parent,
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_chat_request_sanitizes_missing_configuration_and_provider_errors(monkeypatch):
    monkeypatch.setattr(app, "ask", Mock(side_effect=RuntimeError("GROQ_API_KEY missing")))
    answer, error = app.request_chat_answer("Compare players")
    assert answer is None and "not configured" in error

    class APIError(Exception):
        pass

    monkeypatch.setattr(app, "ask", Mock(side_effect=APIError("private response body")))
    answer, error = app.request_chat_answer("Compare players")
    assert answer is None
    assert "model provider" in error
    assert "private response body" not in error


def test_page_adapters_delegate_to_package_functions(monkeypatch):
    compare = Mock(return_value={"status": "ok"})
    form = Mock(return_value={"status": "ok"})
    h2h = Mock(return_value={"status": "ok"})
    table = Mock(return_value="[]")
    monkeypatch.setattr(app, "compare_players", compare)
    monkeypatch.setattr(app, "team_form", form)
    monkeypatch.setattr(app, "head_to_head", h2h)
    monkeypatch.setattr(app, "get_league_table", table)

    assert app.compare_players_for_ui([], "A", "B", "Arsenal", "Chelsea") == {"status": "ok"}
    assert app.get_team_form_for_ui([], "Arsenal") == {"status": "ok"}
    assert app.get_head_to_head_for_ui([], "Arsenal", "Chelsea") == {"status": "ok"}
    assert app.get_league_table_for_ui([]) == []
    compare.assert_called_once_with([], "A", "B", "Arsenal", "Chelsea")
    form.assert_called_once_with([], "Arsenal", None)
    h2h.assert_called_once_with([], "Arsenal", "Chelsea")
    table.assert_called_once_with([])


@pytest.mark.parametrize(
    "error, expected",
    [
        (RuntimeError("Set GROQ_API_KEY; secret=do-not-show"), "not configured"),
        (TimeoutError("request timed out"), "timed out"),
        (RuntimeError("unexpected internal secret"), "could not complete"),
    ],
)
def test_chat_errors_are_friendly_and_do_not_expose_exception(error, expected):
    message = app.friendly_agent_error(error)
    assert expected in message
    assert "do-not-show" not in message
    assert "internal secret" not in message


def test_ui_coverage_disclosures_use_package_period_and_notes():
    result = {
        "data_period": {"start": "2024-08-18", "end": "2024-12-22"},
        "coverage_note": "Partial reports only; not current results.",
        "history_note": "Head-to-head history is incomplete.",
    }
    form_notice = app.coverage_message(result)
    h2h_notice = app.coverage_message(result, head_to_head_page=True)
    assert "2024-08-18 through 2024-12-22" in form_notice
    assert "not current results" in form_notice
    assert "history is incomplete" in h2h_notice


def test_streamlit_pages_render_without_agent_calls(monkeypatch):
    from streamlit.testing.v1 import AppTest

    ask = Mock(side_effect=AssertionError("Agent must not run while rendering pages"))
    monkeypatch.setattr(app, "ask", ask)
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    for page in ("Home", "Chat", "Player Comparison", "Team Form", "Head-to-Head", "League Table"):
        test_app = AppTest.from_file(str(app_path)).run(timeout=12)
        assert not test_app.exception
        test_app.radio[0].set_value(page).run(timeout=12)
        assert not test_app.exception
    ask.assert_not_called()


def test_player_comparison_page_displays_existing_comparison():
    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).resolve().parents[1] / "app.py"
    test_app = AppTest.from_file(str(app_path)).run(timeout=12)
    test_app.radio[0].set_value("Player Comparison").run(timeout=12)
    test_app.selectbox(key="player_a_select").set_value("Mohamed Salah")
    test_app.selectbox(key="player_b_select").set_value("Erling Haaland")
    test_app.run(timeout=12)
    test_app.button[0].click().run(timeout=12)
    assert not test_app.exception
    assert any("Mohamed Salah" in element.value for element in test_app.subheader)
    assert len(test_app.dataframe) == 1


def test_team_pages_display_period_and_incomplete_coverage():
    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).resolve().parents[1] / "app.py"
    team_app = AppTest.from_file(str(app_path)).run(timeout=12)
    team_app.radio[0].set_value("Team Form").run(timeout=12)
    team_app.selectbox(key="form_team_select").set_value("Arsenal").run(timeout=12)
    team_app.button[0].click().run(timeout=12)
    assert not team_app.exception
    team_notice = " ".join(element.value for element in team_app.warning)
    assert "2024-08-18 through 2024-12-22" in team_notice
    assert "not current real-world results" in team_notice

    h2h_app = AppTest.from_file(str(app_path)).run(timeout=12)
    h2h_app.radio[0].set_value("Head-to-Head").run(timeout=12)
    h2h_app.selectbox(key="h2h_a_select").set_value("Chelsea")
    h2h_app.selectbox(key="h2h_b_select").set_value("Arsenal")
    h2h_app.run(timeout=12)
    h2h_app.button[0].click().run(timeout=12)
    assert not h2h_app.exception
    h2h_notice = " ".join(element.value for element in h2h_app.warning)
    assert "2024-08-18 through 2024-12-22" in h2h_notice
    assert "history is incomplete" in h2h_notice

def test_featured_players_uses_numeric_goals_and_player_team_identity():
    rows = [
        {"Player": "Nine", "Squad": "A", "Performance_Gls": "9", "Performance_Ast": "2"},
        {"Player": "Ten", "Squad": "B", "Performance_Gls": "10", "Performance_Ast": "4"},
        {"Player": "Ten", "Squad": "B", "Performance_Gls": "10", "Performance_Ast": "4"},
        {"Player": "Ten", "Squad": "C", "Performance_Gls": "11", "Performance_Ast": "1"},
    ]
    result = app.get_featured_players_for_ui(rows)
    assert [(r["player"], r["team"], r["goals"], r["assists"]) for r in result] == [
        ("Ten", "C", 11, 1), ("Ten", "B", 10, 4), ("Nine", "A", 9, 2)]
    assert app.get_featured_players_for_ui([]) == []


def test_featured_players_matches_raw_repository_top_five():
    _, players, _, _ = app.load_page_data()
    expected = sorted(players, key=lambda row: int(row["Performance_Gls"]), reverse=True)[:5]
    result = app.get_featured_players_for_ui(players)
    assert [(r["player"], r["team"], r["goals"], r["assists"]) for r in result] == [
        (r["Player"], r["Squad"], int(r["Performance_Gls"]), int(r["Performance_Ast"])) for r in expected]


@pytest.fixture
def dashboard_ui(monkeypatch):
    """Render Home natively; capture tables only when testing legacy pages."""
    import agent
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    table = Mock()
    ask = Mock(return_value="Grounded test response")
    monkeypatch.setattr(st, "dataframe", table)
    monkeypatch.setattr(agent, "ask", ask)
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    test_app = AppTest.from_file(str(app_path)).run(timeout=12)
    assert not test_app.exception
    return test_app, table, ask


def test_home_has_top_statistics_and_full_width_bounded_chat(dashboard_ui):
    test_app, table, ask = dashboard_ui
    assert test_app.radio[0].value == "Home"
    assert list(test_app.radio[0].options) == [
        "Home", "Chat", "Player Comparison", "Team Form", "Head-to-Head", "League Table"]
    left, right = test_app.get("column")
    assert left.weight == right.weight == 0.5
    assert left.gap == right.gap == "medium"
    assert not left.chat_input and not right.chat_input
    assert left.subheader[0].value == "Featured Players"
    assert right.subheader[0].value == "Top 5 League Teams"
    assert len(left.markdown[0].value.split("  \n")) == 4
    assert len(right.markdown[0].value.split("  \n")) == 5
    assert not test_app.expander and not test_app.dataframe
    source, players, _, _ = app.load_page_data()
    for card, row in zip(left.markdown[0].value.split("  \n"), app.get_featured_players_for_ui(players)[:4]):
        assert row["player"] in card and row["team"] in card
        assert f"{row['goals']} goals · {row['assists']} assists" in card
    teams = sorted(source, key=lambda row: int(row["Rk"]))[:5]
    for card, row in zip(right.markdown[0].value.split("  \n"), teams):
        assert f"{row['Rk']}. {row['Squad']}" in card
        assert f"{row['Pts']} points" in card
        assert f"GD {int(row['GD']):+d}" in card
    # Chat is a full-width sibling after the top row and divider, not inside a column.
    blocks = list(test_app.main.children.values())
    chat = next(block for block in blocks if block.type == "flex_container" and block.chat_input)
    history = next(block for block in chat.get("flex_container") if block.proto.height_config.pixel_height == 350)
    assert history.proto.autoscroll is True and not history.chat_input
    assert list(chat.children.values())[-1].type == "chat_input"
    assert any(block.type == "divider" for block in blocks[:blocks.index(chat)])
    table.assert_not_called()
    ask.assert_not_called()


def test_home_chat_submission_and_shared_history_across_navigation(dashboard_ui):
    test_app, _, ask = dashboard_ui
    test_app.chat_input[0].set_value("Who scored the most goals?").run(timeout=12)
    assert not test_app.exception
    ask.assert_called_once_with("Who scored the most goals?")
    history = [{"role": "user", "content": "Who scored the most goals?"},
               {"role": "assistant", "content": "Grounded test response"}]
    assert test_app.session_state["football_chat_messages"] == history
    test_app.radio[0].set_value("Chat").run(timeout=12)
    assert not test_app.exception and len(test_app.chat_message) == 2
    assert test_app.session_state["football_chat_messages"] == history
    test_app.chat_input[0].set_value("And the second?").run(timeout=12)
    assert not test_app.exception
    ask.assert_called_with("And the second?", history=history)
    test_app.radio[0].set_value("Home").run(timeout=12)
    assert not test_app.exception and len(test_app.chat_message) == 4
    assert len(test_app.session_state["football_chat_messages"]) == 4
    assert ask.call_count == 2


def test_dashboard_updates_from_supplied_data(monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    rows = [{"Rk": "2", "Squad": "Second", "MP": "3", "Pts": "4"},
            {"Rk": "1", "Squad": "First", "MP": "3", "Pts": "7"}]
    players = [{"Player": "Changed", "Squad": "First", "Performance_Gls": "17", "Performance_Ast": "6"}]
    table = Mock()
    monkeypatch.setattr(st, "dataframe", table)
    monkeypatch.setattr(app, "load_page_data", lambda: (rows, players, [], {}))
    def render_supplied_data():
        import app
        table_rows, player_rows, _, _ = app.load_page_data()
        app._render_home(table_rows, player_rows)
    test_app = AppTest.from_function(render_supplied_data).run(timeout=12)
    assert not test_app.exception
    assert any("Changed" in item.value for item in test_app.markdown)
    assert any("17 goals · 6 assists" in item.value for item in test_app.markdown)
    right = test_app.get("column")[1]
    assert "1. First" in right.markdown[0].value and "7 points" in right.markdown[0].value
    assert "2. Second" in right.markdown[0].value and "4 points" in right.markdown[0].value
    assert "GD" not in right.markdown[0].value
    table.assert_not_called()


def test_all_navigation_pages_render_without_inference_with_table_capture(dashboard_ui):
    test_app, _, ask = dashboard_ui
    for page in ("Home", "Chat", "Player Comparison", "Team Form", "Head-to-Head", "League Table"):
        test_app.radio[0].set_value(page).run(timeout=12)
        assert not test_app.exception
    ask.assert_not_called()

def test_home_renders_with_pyarrow_unavailable(monkeypatch):
    import agent
    from streamlit.testing.v1 import AppTest
    monkeypatch.setitem(sys.modules, "pyarrow", None)
    ask = Mock(side_effect=AssertionError("Opening Home must not invoke the model"))
    monkeypatch.setattr(agent, "ask", ask)
    test_app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=12)
    assert not test_app.exception and len(test_app.chat_input) == 1
    assert len(test_app.get("column")[0].markdown[0].value.split("  \n")) == 4
    assert len(test_app.get("column")[1].markdown[0].value.split("  \n")) == 5
    ask.assert_not_called()


def test_forty_submissions_stay_inside_fixed_history_with_composer_below(dashboard_ui):
    test_app, _, ask = dashboard_ui
    outer_count = len(test_app.main.children)
    for index in range(40):
        test_app.chat_input[0].set_value(f"Question {index}").run(timeout=12)
        assert not test_app.exception
        assert len(test_app.main.children) == outer_count
        history = next(block for block in test_app.get("flex_container")
                       if block.proto.height_config.pixel_height == 350)
        assert len(history.chat_message) == (index + 1) * 2
        assert not history.chat_input
        assert len(test_app.chat_input) == 1
    assert ask.call_count == 40
    messages = test_app.session_state["football_chat_messages"]
    assert [(m["role"],m["content"]) for m in messages] == [
        pair for index in range(40) for pair in (("user",f"Question {index}"),
                                                ("assistant","Grounded test response"))]
    test_app.run(timeout=12)
    assert len(test_app.chat_message) == 80 and ask.call_count == 40


def test_embedded_chat_errors_remain_in_history_and_are_not_sent_as_context(dashboard_ui):
    test_app, _, ask = dashboard_ui
    ask.side_effect = TimeoutError("request timed out")
    test_app.chat_input[0].set_value("First question").run(timeout=12)
    assert not test_app.exception
    history = test_app.session_state["football_chat_messages"]
    assert history[1]["error"] is True and "timed out" in history[1]["content"]
    window = next(block for block in test_app.get("flex_container")
                  if block.proto.height_config.pixel_height == 350)
    assert len(window.chat_message) == 2 and window.error
    ask.side_effect = None
    test_app.chat_input[0].set_value("Try again").run(timeout=12)
    assert not test_app.exception
    ask.assert_called_with("Try again", history=[{"role":"user","content":"First question"}])
