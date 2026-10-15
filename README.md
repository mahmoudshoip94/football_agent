Football Agent — AI-Powered Premier League Analytics
An intelligent, multi-agent football analytics system built using Python, LangChain, LangGraph, Ollama, and Streamlit.
Football Agent allows users to explore English Premier League statistics, compare players, analyze team performances, investigate historical match results, and ask natural-language questions through an AI-powered conversational interface.
The project combines LLM-based reasoning and orchestration with deterministic statistical tools, ensuring that football statistics are retrieved and calculated from structured datasets rather than generated from the language model's general knowledge.
1. Project Overview
Football Agent is designed to make football analytics more accessible through natural-language interaction.
Instead of manually searching through league tables, player statistics, and match reports, users can ask questions such as:
- Who scored the most goals in the 2024/25 Premier League dataset?
- Compare Mohamed Salah and Erling Haaland.
- Which team has the best defense?
- What were Arsenal's last five available results?
- Show the head-to-head results between Liverpool and Manchester City.
- Who scored the first hat-trick in the available match reports?
- Which player first reached ten goals?
The system interprets the user's request, delegates tasks to specialized agents when appropriate, executes statistical tools, and generates a readable response.
Project scope
Property	Description
Competition	English Premier League
Season	2024/25
Application	Streamlit
Programming language	Python
Agent framework	LangChain and LangGraph
LLM integration	Ollama
Configured model	gemma4:e4b
Data sources	Local CSV and JSONL files
Analytical engine	Deterministic Python functions
Interaction	Dashboard and conversational AI
Important: The project analyzes a historical dataset. It does not currently provide live football scores, continuously updated standings, or real-time match information.
The match-report logic describes partial coverage from August 18, 2024, through December 22, 2024. The aggregate CSV files may represent different snapshots of the season.
2. Key Features
2.1 AI Football Chat
The conversational assistant supports natural-language questions about Premier League football.
The chat system can:
- Interpret questions about football statistics.
- Delegate queries to specialized agents.
- Use football datasets as the factual source.
- Support follow-up questions using conversation history.
- Identify unsupported questions.
- Request clarification when player or team names are ambiguous.
- Explain limitations caused by incomplete data.
2.2 Player Statistics
Retrieve statistics including goals, assists, appearances, minutes played, starts, and available per-90 metrics.
Player data is read from Player_Stats.csv.
2.3 Player Comparison
Compare two football players across multiple metrics.
The comparison engine calculates differences between players and handles ambiguous player identities using their team information.
2.4 League Table Analysis
Explore Premier League standings, including points, wins, draws, losses, goal difference, and expected-goal statistics where available.
2.5 Team Form Analysis
Analyze the latest five available matches for a team, including wins, draws, losses, goals scored, goals conceded, and points earned.
2.6 Head-to-Head Analysis
Compare two teams using their meetings in the available match reports.
The system reports match results and an aggregate record from the perspective of the first selected team.
2.7 Chronological Scoring Milestones
Analyze questions involving hat-tricks and scoring thresholds.
The system supports chronological analysis using match dates and player-level goal statistics.
2.8 General-Purpose Analytical Operations
The project includes a reusable analytical engine supporting:
Operation	Purpose
filter	Select rows using conditions
derive	Calculate new statistical fields
group	Aggregate records
sort	Order analytical results
ordinal	Select ranked positions
cumulative	Calculate cumulative values
difference	Calculate changes between records
These operations allow the agent to perform more complex analyses without executing arbitrary model-generated Python code or SQL.
3. System Architecture
The system follows a multi-agent architecture with a central supervisor coordinating specialized agents.
#chatgpt-mermaid-_r_36m_{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;fill:rgb(255, 255, 255);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-_r_36m_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-_r_36m_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-_r_36m_ .error-icon{fill:rgba(255, 255, 255, 0.03);}#chatgpt-mermaid-_r_36m_ .error-text{fill:rgb(255, 255, 255);stroke:rgb(255, 255, 255);}#chatgpt-mermaid-_r_36m_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-_r_36m_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-_r_36m_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-_r_36m_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-_r_36m_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-_r_36m_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-_r_36m_ .marker{fill:rgba(255, 255, 255, 0.498);stroke:rgba(255, 255, 255, 0.498);}#chatgpt-mermaid-_r_36m_ .marker.cross{stroke:rgba(255, 255, 255, 0.498);}#chatgpt-mermaid-_r_36m_ svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;}#chatgpt-mermaid-_r_36m_ p{margin:0;}#chatgpt-mermaid-_r_36m_ .label{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:rgb(255, 255, 255);}#chatgpt-mermaid-_r_36m_ .cluster-label text{fill:rgb(255, 255, 255);}#chatgpt-mermaid-_r_36m_ .cluster-label span{color:rgb(255, 255, 255);}#chatgpt-mermaid-_r_36m_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-_r_36m_ .label text,#chatgpt-mermaid-_r_36m_ span{fill:rgb(255, 255, 255);color:rgb(255, 255, 255);}#chatgpt-mermaid-_r_36m_ .node rect,#chatgpt-mermaid-_r_36m_ .node circle,#chatgpt-mermaid-_r_36m_ .node ellipse,#chatgpt-mermaid-_r_36m_ .node polygon,#chatgpt-mermaid-_r_36m_ .node path{fill:rgb(26, 40, 61);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-_r_36m_ .rough-node .label text,#chatgpt-mermaid-_r_36m_ .node .label text,#chatgpt-mermaid-_r_36m_ .image-shape .label,#chatgpt-mermaid-_r_36m_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-_r_36m_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-_r_36m_ .rough-node .label,#chatgpt-mermaid-_r_36m_ .node .label,#chatgpt-mermaid-_r_36m_ .image-shape .label,#chatgpt-mermaid-_r_36m_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-_r_36m_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-_r_36m_ .root .anchor path{fill:rgba(255, 255, 255, 0.498)!important;stroke-width:0;stroke:rgba(255, 255, 255, 0.498);}#chatgpt-mermaid-_r_36m_ .arrowheadPath{fill:rgba(255, 255, 255, 0.498);}#chatgpt-mermaid-_r_36m_ .edgePath .path{stroke:rgba(255, 255, 255, 0.498);stroke-width:1px;}#chatgpt-mermaid-_r_36m_ .flowchart-link{stroke:rgba(255, 255, 255, 0.498);fill:none;}#chatgpt-mermaid-_r_36m_ .edgeLabel{background-color:rgb(24, 24, 24);text-align:center;}#chatgpt-mermaid-_r_36m_ .edgeLabel p{background-color:rgb(24, 24, 24);}#chatgpt-mermaid-_r_36m_ .edgeLabel rect{opacity:0.5;background-color:rgb(24, 24, 24);fill:rgb(24, 24, 24);}#chatgpt-mermaid-_r_36m_ .labelBkg{background-color:rgba(24, 24, 24, 0.5);}#chatgpt-mermaid-_r_36m_ .cluster rect{fill:rgba(255, 255, 255, 0.03);stroke:rgba(255, 255, 255, 0.082);stroke-width:1px;}#chatgpt-mermaid-_r_36m_ .cluster text{fill:rgb(255, 255, 255);}#chatgpt-mermaid-_r_36m_ .cluster span{color:rgb(255, 255, 255);}#chatgpt-mermaid-_r_36m_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:12px;background:rgba(255, 255, 255, 0.03);border:1px solid rgba(255, 255, 255, 0.082);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-_r_36m_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(255, 255, 255);}#chatgpt-mermaid-_r_36m_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-_r_36m_ .icon-shape,#chatgpt-mermaid-_r_36m_ .image-shape{background-color:rgb(24, 24, 24);text-align:center;}#chatgpt-mermaid-_r_36m_ .icon-shape p,#chatgpt-mermaid-_r_36m_ .image-shape p{background-color:rgb(24, 24, 24);padding:2px;}#chatgpt-mermaid-_r_36m_ .icon-shape .label rect,#chatgpt-mermaid-_r_36m_ .image-shape .label rect{opacity:0.5;background-color:rgb(24, 24, 24);fill:rgb(24, 24, 24);}#chatgpt-mermaid-_r_36m_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-_r_36m_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-_r_36m_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-_r_36m_ [data-look="neo"].node rect,#chatgpt-mermaid-_r_36m_ [data-look="neo"].cluster rect,#chatgpt-mermaid-_r_36m_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-_r_36m_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_36m_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-_r_36m_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-_r_36m_-gradient);stroke-width:1px;}#chatgpt-mermaid-_r_36m_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_36m_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-_r_36m_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-_r_36m_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_36m_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-_r_36m_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-_r_36m_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_36m_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-_r_36m_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_36m_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-_r_36m_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-_r_36m_ .node tspan[font-weight="normal"],#chatgpt-mermaid-_r_36m_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-_r_36m_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-_r_36m_ .node rect,#chatgpt-mermaid-_r_36m_ .node circle,#chatgpt-mermaid-_r_36m_ .node ellipse,#chatgpt-mermaid-_r_36m_ .node polygon,#chatgpt-mermaid-_r_36m_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-_r_36m_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-_r_36m_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-_r_36m_ .edgePaths .flowchart-link{stroke:rgba(255, 255, 255, 0.498);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-_r_36m_ .marker{fill:rgba(255, 255, 255, 0.498);stroke:rgba(255, 255, 255, 0.498);}#chatgpt-mermaid-_r_36m_ :root{--mermaid-font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}UserStreamlit DashboardScope GuardrailDeterministic Python ToolsLangGraph SupervisorScope RejectionStatistics AnalystFixtures ReporterStatistics and Analytics ToolsFixtures and Match ToolsLocal CSV and JSONLChatDashboard pagesIn scopeOut of scope





3.1 Supervisor Agent
The supervisor is the main coordinator of the conversational system.
Its responsibilities include understanding the user's question, selecting the appropriate specialist, delegating tasks, preserving relevant conversation context, and combining specialist responses.
The supervisor exposes two delegation tools:
- call_stats_analyst(query)
- call_fixtures_reporter(query)
3.2 Statistics Analyst Agent
The Statistics Analyst handles statistical and analytical questions about players, teams, league rankings, and scoring milestones.
Its tools include:
Tool	Responsibility
get_player_stats	Retrieve player statistics
compare_player_stats	Compare two players
get_league_table	Retrieve league standings
get_scoring_milestones	Analyze scoring milestones
inspect_data	Discover available datasets and columns
analyze	Execute structured analytical operations
3.3 Fixtures Reporter Agent
The Fixtures Reporter handles match-related questions.
Its tools include:
Tool	Responsibility
get_match_fixtures	Retrieve recorded fixtures and results
getteam_form	Analyze recent team form
gethead_to_head	Compare recorded meetings
inspect_data	Inspect available analytical data
analyze	Execute structured analysis
3.4 Deterministic Execution Layer
The project separates language-model reasoning from statistical calculations.
The LLM selects tools and analytical operations, while Python functions execute the calculations.
This architecture reduces dependence on LLM-generated numerical answers and avoids executing arbitrary model-generated Python or SQL.
It does not, however, guarantee that every model-selected tool or final interpretation will be correct.
4. Technology Stack
Technology	Purpose
Python	Core application and data processing
LangChain	Agent and tool integrations
LangGraph	Supervisor workflow orchestration
Ollama	Local language-model runtime
Streamlit	Interactive dashboard
CSV	Aggregate player and league data
JSONL	Match reports
pytest	Automated testing
Declared dependencies
The repository's requirements.txt contains:
langchain
langchain-ollama
python-dotenv
requests
pytest
streamlit


The source also imports langgraph and langchain_core, which are not separately pinned in the dependency file.
5. Repository Structure
football_agent/
├── app.py
├── README.md
├── VALIDATION.md
├── requirements.txt
├── pytest.ini
├── notebook.ipynb
├── test.ipynb
├── agent/
│   ├── __init__.py
│   ├── workflow.py
│   ├── config.py
│   ├── data_loader.py
│   ├── intent.py
│   ├── prompts.py
│   ├── analytics.py
│   ├── player_tools.py
│   ├── league_tools.py
│   ├── match_tools.py
│   └── milestone_tools.py
├── tests/
│   ├── test_agent_tools.py
│   ├── test_analytics.py
│   ├── test_hat_trick_chronology.py
│   ├── test_live_analytics.py
│   ├── test_milestone_intent.py
│   └── test_streamlit_app.py
└── Data/
    ├── Table.csv
    ├── Player_Stats.csv
    └── match_reports.jsonl


Note: Data/ is the expected runtime directory. It is excluded by .gitignore and is not included in the inspected GitHub revision.
6. Installation and Setup
Prerequisites
Install Python 3.10 or newer, Git, and Ollama. A modern Python 3.11+ environment is recommended, although the repository does not define a verified compatibility matrix.
Step 1 — Clone the repository
git clone https://github.com/mahmoudshoip94/football_agent.git
cd football_agent


Step 2 — Create a virtual environment
python -m venv .venv


Activate it on Linux or macOS:
source .venv/bin/activate


On Windows PowerShell:
.\.venv\Scripts\Activate.ps1


Step 3 — Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt


Step 4 — Provide the datasets
Create a Data/ directory in the repository root and supply:
Data/Table.csv
Data/Player_Stats.csv
Data/match_reports.jsonl


These files are required but not provided by the public repository.
Verify that they can be loaded:
python -c "from agent.data_loader import load_datasets; print(load_datasets()[3])"


Step 5 — Configure Ollama
The current workflow initializes Ollama using:
ChatOllama(    model="gemma4:e4b",    base_url="http://localhost:11434")



Start Ollama:
ollama serve


Check available models:
ollama list


The configured model tag must exist in your Ollama environment. If it is unavailable, install a supported compatible model and update the ChatOllama initializations in agent/workflow.py.
Configuration note: The repository still contains Groq configuration references, but the actual workflow uses Ollama. Adding GROQ_API_KEY does not switch the running agent to Groq.
7. Datasets and Data Coverage
The application relies on three local data sources.
7.1 League Table Dataset
File: Data/Table.csv
Contains team-level statistics such as ranking, matches played, wins, draws, losses, goals scored, goals conceded, goal difference, points, and available expected-goal metrics.
7.2 Player Statistics Dataset
File: Data/Player_Stats.csv
Contains player-level statistics such as:
- Player and squad names
- Appearances and starts
- Minutes played
- Goals and assists
- Penalty statistics
- Cards
- Per-90 performance metrics
Required source columns include:
Player
Squad
Playing Time_Min
Playing Time_MP
Performance_Gls
Performance_Ast
Per 90 Minutes_Gls
Per 90 Minutes_Ast
Per 90 Minutes_G+A


7.3 Match Reports Dataset
File: Data/match_reports.jsonl
Contains match-level information including dates, participating teams, scores, and optional player and goalkeeper statistics.
These reports support fixture lookups, recent form, head-to-head analysis, and scoring milestones.
Data coverage limitations
The project's recorded documentation describes:
Dataset	Recorded coverage
League table	20 teams
Player statistics	574 player rows
Match reports	158 reports
Report date range	August 18 – December 22, 2024
These counts come from repository documentation and could not be independently checked without the missing datasets.
The system must not interpret partial reports as complete-season or all-time historical coverage.
8. Running the Application
Launch the Streamlit dashboard:
streamlit run app.py


The application provides six navigation sections.
Page	Description
Home	Featured players, leading teams, embedded chat
Chat	Natural-language AI assistant
Player Comparison	Side-by-side player metrics and charts
Team Form	Recent available results and summary
Head-to-Head	Recorded meetings between two teams
League Table	Historical standings
The data-driven dashboard pages do not require LLM inference. The chat feature requires a working Ollama model.
9. Python API Usage
9.1 Ask the AI Agent
from agent import askanswer = ask(    "Compare Mohamed Salah and Erling Haaland",    max_len=4000)print(answer)



The ask() function supports explicit conversation history:
follow_up = ask(    "Who has more goals per 90?",    history=[        {            "role": "user",            "content": "Compare Mohamed Salah and Erling Haaland"        },        {            "role": "assistant",            "content": answer        }    ],    max_len=4000)print(follow_up)



The default max_len is 1,200 characters. Longer responses require a higher limit.
9.2 Use Deterministic Tools Directly
import jsonfrom agent.data_loader import load_datasetsfrom agent.player_tools import compare_players, get_player_statsfrom agent.match_tools import team_form, head_to_headfrom agent.league_tools import get_league_tableteams, players, reports, metadata = load_datasets()comparison = compare_players(    players,    "Mohamed Salah",    "Erling Haaland")print(comparison)top_assists = json.loads(    get_player_stats(players, stat="assists", limit=5))print(top_assists)print(team_form(reports, "Arsenal"))print(head_to_head(reports, "Arsenal", "Chelsea"))print(json.loads(get_league_table(teams, top_n=5)))



These functions can be used without the LLM.
10. Agent Workflow
The conversation workflow is implemented using LangGraph.
#chatgpt-mermaid-_r_3b3_{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;fill:rgb(255, 255, 255);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-_r_3b3_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-_r_3b3_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-_r_3b3_ .error-icon{fill:rgba(255, 255, 255, 0.03);}#chatgpt-mermaid-_r_3b3_ .error-text{fill:rgb(255, 255, 255);stroke:rgb(255, 255, 255);}#chatgpt-mermaid-_r_3b3_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-_r_3b3_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-_r_3b3_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-_r_3b3_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-_r_3b3_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-_r_3b3_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-_r_3b3_ .marker{fill:rgba(255, 255, 255, 0.498);stroke:rgba(255, 255, 255, 0.498);}#chatgpt-mermaid-_r_3b3_ .marker.cross{stroke:rgba(255, 255, 255, 0.498);}#chatgpt-mermaid-_r_3b3_ svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;}#chatgpt-mermaid-_r_3b3_ p{margin:0;}#chatgpt-mermaid-_r_3b3_ .label{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:rgb(255, 255, 255);}#chatgpt-mermaid-_r_3b3_ .cluster-label text{fill:rgb(255, 255, 255);}#chatgpt-mermaid-_r_3b3_ .cluster-label span{color:rgb(255, 255, 255);}#chatgpt-mermaid-_r_3b3_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-_r_3b3_ .label text,#chatgpt-mermaid-_r_3b3_ span{fill:rgb(255, 255, 255);color:rgb(255, 255, 255);}#chatgpt-mermaid-_r_3b3_ .node rect,#chatgpt-mermaid-_r_3b3_ .node circle,#chatgpt-mermaid-_r_3b3_ .node ellipse,#chatgpt-mermaid-_r_3b3_ .node polygon,#chatgpt-mermaid-_r_3b3_ .node path{fill:rgb(26, 40, 61);stroke:rgb(31, 78, 148);stroke-width:1px;}#chatgpt-mermaid-_r_3b3_ .rough-node .label text,#chatgpt-mermaid-_r_3b3_ .node .label text,#chatgpt-mermaid-_r_3b3_ .image-shape .label,#chatgpt-mermaid-_r_3b3_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-_r_3b3_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-_r_3b3_ .rough-node .label,#chatgpt-mermaid-_r_3b3_ .node .label,#chatgpt-mermaid-_r_3b3_ .image-shape .label,#chatgpt-mermaid-_r_3b3_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-_r_3b3_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-_r_3b3_ .root .anchor path{fill:rgba(255, 255, 255, 0.498)!important;stroke-width:0;stroke:rgba(255, 255, 255, 0.498);}#chatgpt-mermaid-_r_3b3_ .arrowheadPath{fill:rgba(255, 255, 255, 0.498);}#chatgpt-mermaid-_r_3b3_ .edgePath .path{stroke:rgba(255, 255, 255, 0.498);stroke-width:1px;}#chatgpt-mermaid-_r_3b3_ .flowchart-link{stroke:rgba(255, 255, 255, 0.498);fill:none;}#chatgpt-mermaid-_r_3b3_ .edgeLabel{background-color:rgb(24, 24, 24);text-align:center;}#chatgpt-mermaid-_r_3b3_ .edgeLabel p{background-color:rgb(24, 24, 24);}#chatgpt-mermaid-_r_3b3_ .edgeLabel rect{opacity:0.5;background-color:rgb(24, 24, 24);fill:rgb(24, 24, 24);}#chatgpt-mermaid-_r_3b3_ .labelBkg{background-color:rgba(24, 24, 24, 0.5);}#chatgpt-mermaid-_r_3b3_ .cluster rect{fill:rgba(255, 255, 255, 0.03);stroke:rgba(255, 255, 255, 0.082);stroke-width:1px;}#chatgpt-mermaid-_r_3b3_ .cluster text{fill:rgb(255, 255, 255);}#chatgpt-mermaid-_r_3b3_ .cluster span{color:rgb(255, 255, 255);}#chatgpt-mermaid-_r_3b3_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:12px;background:rgba(255, 255, 255, 0.03);border:1px solid rgba(255, 255, 255, 0.082);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-_r_3b3_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(255, 255, 255);}#chatgpt-mermaid-_r_3b3_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-_r_3b3_ .icon-shape,#chatgpt-mermaid-_r_3b3_ .image-shape{background-color:rgb(24, 24, 24);text-align:center;}#chatgpt-mermaid-_r_3b3_ .icon-shape p,#chatgpt-mermaid-_r_3b3_ .image-shape p{background-color:rgb(24, 24, 24);padding:2px;}#chatgpt-mermaid-_r_3b3_ .icon-shape .label rect,#chatgpt-mermaid-_r_3b3_ .image-shape .label rect{opacity:0.5;background-color:rgb(24, 24, 24);fill:rgb(24, 24, 24);}#chatgpt-mermaid-_r_3b3_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-_r_3b3_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-_r_3b3_ .node .neo-node{stroke:rgb(31, 78, 148);}#chatgpt-mermaid-_r_3b3_ [data-look="neo"].node rect,#chatgpt-mermaid-_r_3b3_ [data-look="neo"].cluster rect,#chatgpt-mermaid-_r_3b3_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-_r_3b3_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_3b3_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-_r_3b3_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-_r_3b3_-gradient);stroke-width:1px;}#chatgpt-mermaid-_r_3b3_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_3b3_ [data-look="neo"].node .neo-line path{stroke:rgb(31, 78, 148);filter:none;}#chatgpt-mermaid-_r_3b3_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-_r_3b3_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_3b3_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-_r_3b3_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-_r_3b3_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_3b3_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-_r_3b3_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_3b3_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(153, 206, 255);}#chatgpt-mermaid-_r_3b3_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(153, 206, 255);}#chatgpt-mermaid-_r_3b3_ .node tspan[font-weight="normal"],#chatgpt-mermaid-_r_3b3_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-_r_3b3_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-width:1px;}#chatgpt-mermaid-_r_3b3_ .node rect,#chatgpt-mermaid-_r_3b3_ .node circle,#chatgpt-mermaid-_r_3b3_ .node ellipse,#chatgpt-mermaid-_r_3b3_ .node polygon,#chatgpt-mermaid-_r_3b3_ .node path{fill:rgb(0, 40, 77);stroke:rgba(255, 255, 255, 0.1);stroke-width:1px;}#chatgpt-mermaid-_r_3b3_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-_r_3b3_ .node.mermaid-decision .label-container{fill:rgb(0, 14, 26);stroke:rgb(26, 62, 95);stroke-dasharray:2,2;}#chatgpt-mermaid-_r_3b3_ .edgePaths .flowchart-link{stroke:rgba(255, 255, 255, 0.498);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-_r_3b3_ .marker{fill:rgba(255, 255, 255, 0.498);stroke:rgba(255, 255, 255, 0.498);}#chatgpt-mermaid-_r_3b3_ :root{--mermaid-font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}STARTGuardrailENDSupervisorTool ExecutorOut of scopeIn scopeDelegateFinal response





The supervisor can delegate to the Statistics Analyst and Fixtures Reporter. Each specialist can invoke its own analytical tools.
The graph is initialized lazily on the first ask() call.
The guardrail uses keyword and pattern matching to identify clearly unrelated requests. It is not a comprehensive security or prompt-injection defense.
11. Analytics Engine
The project includes six analytical relations.
Relation	Description
players	Aggregate player records
teams	Aggregate club records
matches	Unique match records
team_matches	Team-level match performance
player_matches	Individual match appearances
keeper_matches	Goalkeeper match records
The analyze_data() function accepts a structured sequence of operations.
Example: Find the earliest recorded hat-trick
from agent.analytics import analyze_datafrom agent.data_loader import load_datasetsteams, players, reports, _ = load_datasets()result = analyze_data(    teams,    players,    reports,    "player_matches",    [        {            "op": "filter",            "field": "Performance_Gls",            "operator": "ge",            "value": 3        },        {            "op": "sort",            "by": ["date"]        },        {            "op": "ordinal",            "field": "date",            "position": 1        }    ])print(result["rows"])



Example: Rank players by recorded hat-tricks
result = analyze_data(    teams,    players,    reports,    "player_matches",    [        {            "op": "filter",            "field": "Performance_Gls",            "operator": "ge",            "value": 3        },        {            "op": "group",            "by": ["player", "team"],            "metrics": {                "hat_tricks": {                    "agg": "count"                }            }        },        {            "op": "sort",            "by": ["hat_tricks"],            "descending": True        }    ])print(result["rows"])



The engine supports up to 30 operations per analysis request.
It validates operation names, available fields, and arguments rather than executing unrestricted generated code.
12. Testing and Validation
The project uses pytest for automated testing.
Run the full test suite:
python -m pytest -q


Exclude optional integration tests:
python -m pytest -q -m "not integration"


Tests cover player statistics, match analysis, chronological milestones, analytical operations, mocked agent orchestration, and Streamlit interface behavior.
Previously recorded results
The repository's VALIDATION.md reports:
Result	Count
Passed	51
Skipped	7
Failed	3
The three recorded failures were attributed to Windows Application Control blocking a PyArrow native library during Streamlit table-rendering tests.
A separate focused run reported 43 passed and 7 skipped.
These are historical results from the repository documentation, not independently reproduced test results.
13. Known Limitations
Limitation	Description
Missing datasets	Required Data/ files are not committed
Provider mismatch	Groq references remain, while the workflow uses Ollama
Partial match coverage	Match reports do not cover the complete season
Historical-only data	No live scores or current standings
Missing goal timestamps	Exact intra-match goal chronology cannot be established
Player identity	No globally stable player IDs
Dependency versions	Requirements are not version-pinned
Persistent memory	Chat history is held in the Streamlit session
Deployment	No verified production deployment configuration
Licensing	No tracked license file
14. Troubleshooting
Missing dataset error
Check that the Data/ directory exists and contains all three required files with valid schemas.
Ollama connection error
Verify the model runtime:
ollama list


Ensure the server is running and the configured model tag matches an installed model.
Groq API key does not work
The active workflow uses Ollama. Groq environment variables do not automatically configure the running agent.
Incomplete match results
Match reports cover only part of the historical season. Missing reports may affect rankings, form, head-to-head results, and scoring milestones.
Ambiguous player names
Specify the player's team when multiple records match the same name.
15. Future Improvements
Recommended development priorities:
1. Reproducible data setup: Provide sample datasets, documented data acquisition, and schema validation.
2. Unified model configuration: Make provider, model name, and endpoint configurable.
3. Dependency management: Pin compatible versions and add automated CI checks.
4. Data coverage tracking: Record dataset timestamps and completeness.
5. Agent evaluation: Measure tool selection, factual correctness, and analytical accuracy.
6. Production readiness: Add deployment configuration, observability, and error monitoring.
7. Advanced analytics: Expand player and team analysis after improving data completeness.
These are recommendations, not features currently implemented in the repository.
16. Contributing and License
Contributions should preserve the separation between LLM reasoning and deterministic statistical execution.
New features should include appropriate tests, clear data provenance, and explicit limitations where source coverage is incomplete.
The repository does not currently include a tracked LICENSE file. Reuse and redistribution permissions should be confirmed with the repository owner.