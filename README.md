# Premier League Football Agent

A LangChain/LangGraph multi-agent assistant for Premier League 2024/25 standings, player statistics, fixtures, recent form, and head-to-head results. `notebook.ipynb` remains the development and experimentation reference; `agent/` contains the reusable implementation and reads datasets relative to the repository, regardless of the working directory.

## Setup

1. Create and activate a Python virtual environment.
2. Install the dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project folder and add your Groq API key:

   ```text
   GROQ_API_KEY=your_api_key_here
   ```

4. Open `notebook.ipynb` in Jupyter to review the implementation and experiments.

## Streamlit app

Launch the interface from the repository root with:

```powershell
streamlit run app.py
```

The sidebar provides **Chat**, **Player Comparison**, **Team Form**, **Head-to-Head**, and **League Table** pages. Chat calls the existing `agent.ask()` workflow; the analysis pages call its deterministic package functions. Chat messages are retained in the UI for display, while each `ask()` call is independent and does not carry agent memory between questions. Chat requires `GROQ_API_KEY`; dataset pages use the local files without an LLM call.

The bundled match reports cover only 2024-08-18 through 2024-12-22. Team form and head-to-head results are partial historical data, not current results or complete-season coverage.

## Package use

The `agent/` package separates configuration and data loading from deterministic player, match, and league tools. The existing supervisor, statistics and fixtures subagents, guardrail, routing, and LangGraph workflow are in `agent/workflow.py`.

Configure `GROQ_API_KEY` in the project `.env` file (or the process environment) before calling the LLM-backed workflow. Importing the package does not initialize models or make network requests. The project `.env` is loaded when `ask()` first initializes the graph.

```python
from agent import ask

print(ask("Compare Mohamed Salah and Erling Haaland"))
print(ask("What is Arsenal's form in the last five matches?"))
```

The deterministic tools are also directly importable, for example `agent.player_tools.compare_players`, `agent.match_tools.team_form`, `agent.match_tools.head_to_head`, and `agent.league_tools.get_league_table`. The match reports cover only 2024-08-18 through 2024-12-22, so those results are partial historical data, not current or complete-season results.

## Tests

From the repository root, run:

```powershell
python -m pytest -q
```

The `.env` file and local virtual environments are excluded from Git.
