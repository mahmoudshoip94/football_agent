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

The sidebar provides **Chat**, **Player Comparison**, **Team Form**, **Head-to-Head**, and **League Table** pages. Chat calls the existing `agent.ask()` workflow; the analysis pages call its deterministic package functions. Chat messages are explicitly passed into `ask()` to support follow-up questions. Chat requires `GROQ_API_KEY`; dataset pages use the local files without an LLM call.

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

## Data-driven analysis

The supervisor and two existing subagents now have `inspect_data` and `analyze` tools. The model plans and combines operations; Python validates columns and performs calculations. `ask()` returns the graph answer without phrase-based answer replacements. Existing lookup, comparison, form, fixtures and table tools remain available.

`agent.analytics.discover_data` exposes six relations: aggregate players and teams, matches, team matches, player matches, and keeper matches. Source columns are retained alongside explicit player/team identities, opponents, scores, dates and stable match keys. `analyze_data` accepts an ordered list of operations:

- `filter`: field, operator (`eq`, `contains`, `in`, `ge`, `gt`, `le`, `lt`), value.
- `derive`: output name, method (`add`, `subtract`, `per90`), source fields.
- `group`: grouping keys and named metrics (`sum`, `mean`, `min`, `max`, `count`, `distinct`, earliest `first`).
- `cumulative` / `difference`: identity keys, field, output name; chronological by match date. Cumulative output includes the previous total and observed match count.
- `sort`: fields and descending flag.
- `ordinal`: tie field and one-based position (or -1 for last). Every row tied at the requested position is returned.

For example, hat-tricks use player-match goals >=3, followed by sorting and ordinal selection. The same set can be grouped by player or opponent and counted. `scoring_events(reports, threshold=None, position=None)` provides a deterministic convenience interface for all hat-tricks or configurable cumulative goal crossings. It includes match evidence and observed matches, which are not complete-season appearances.

Supported analysis includes second/third/last hat-tricks, counts by scorer or conceding team, configurable goal thresholds, player/team rankings, per-90 metrics, goal contributions, highest-scoring matches, home/away points, and changes between observed player appearances. These are compositions of operations, not individual question handlers.

Chat now passes conversation history explicitly. Programmatic callers may use `ask(question, history=[{'role':'user','content':'...'}, {'role':'assistant','content':'...'}])`. There is no hidden cross-session memory.

Coverage: 574 aggregate player rows, 20 table teams (38 matches each), and 158 reports dated 2024-08-18 through 2024-12-22. CSV snapshot dates are not recorded. Reports omit season matches, and player identities have no global IDs. Names are qualified by team rather than silently merging transfers or duplicates. There are no individual goal timestamps; same-date ordinals retain ties. True season milestone dates and fastest season appearance counts need complete reports. Conservative keeper clean sheets require a sole 90-minute keeper, zero goals allowed and agreement with the team score; partial keeper appearances need substitution timing. No all-time or other-season dataset is included.

Offline tests exercise deterministic analysis, source reconciliation, mocked graph calls, and Streamlit pages. Mocked orchestration does not establish the quality of a live model's planning. Live model validation requires configured Groq credentials.
