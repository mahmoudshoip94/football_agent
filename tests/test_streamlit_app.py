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
    for page in ("Chat", "Player Comparison", "Team Form", "Head-to-Head", "League Table"):
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
