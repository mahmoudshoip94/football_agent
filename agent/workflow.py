"""Lazy construction of the existing LangChain/LangGraph agent workflow."""

from __future__ import annotations

import time
from functools import lru_cache
from typing import Annotated, Literal, TypedDict

from .analytics import analyze_data, discover_data
from .data_loader import load_datasets
from .intent import classify_question_scope, is_premier_league_question, query_dataset_scope_limitation
from .league_tools import get_league_table as table_data_tool
from .match_tools import (
    get_match_fixtures as fixtures_data_tool,
    gethead_to_head as h2h_data_tool,
    getteam_form as form_data_tool,
)
from .milestone_tools import get_scoring_milestones as milestone_data_tool
from .player_tools import (
    compare_player_stats as compare_data_tool,
    get_player_stats as player_data_tool,
)
from .prompts import FIXTURES_PROMPT, GUARDRAIL_REJECTION, STATS_PROMPT, SUPERVISOR_PROMPT


@lru_cache(maxsize=1)
def _runtime():
    """Initialize provider-backed graph and load local data only on first ask()."""
    # Importing agent does not initialize models, contact providers, or discover models.
    from langchain.agents import create_agent
    from langchain_ollama import ChatOllama
    from langchain.tools import tool
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
    from langgraph.graph import END, START, StateGraph
    from langgraph.graph.message import add_messages

    table_rows, player_rows, match_reports, _ = load_datasets()

    def make_toolset():
        @tool
        def get_league_table(top_n: int | None = None) -> str:
            """Return the project-default Premier League 2024/25 table, including team goals for and against for standings and attack/defense questions. Leave top_n unset to compare all teams."""
            return table_data_tool(table_rows, top_n)

        @tool
        def get_player_stats(
            player_name: str | None = None, team: str | None = None,
            stat: str | None = None, limit: int = 10,
        ) -> str:
            """Return project-default Premier League 2024/25 player statistics. Supports goals, assists, appearances, minutes, and clean sheets if the CSV has that field; report missing fields instead of substituting another statistic."""
            return player_data_tool(player_rows, player_name, team, stat, limit)

        @tool
        def get_scoring_milestones(question: str) -> str:
            """Return all date-sorted hat-tricks with rank ranges for first, nth or latest queries, or goal thresholds; disclose partial report coverage and explain only relevant same-date ties."""
            return milestone_data_tool(match_reports, question)

        @tool
        def compare_player_stats(
            player_a: str, player_b: str, team_a: str | None = None, team_b: str | None = None,
        ) -> str:
            """Compare two players with deterministic CSV values and differences; use team qualifiers for duplicate names."""
            return compare_data_tool(player_rows, player_a, player_b, team_a, team_b)

        @tool
        def getteam_form(team_a: str, team_b: str | None = None) -> str:
            """Show each team's latest five available matches, results, aggregates, and data coverage."""
            return form_data_tool(match_reports, team_a, team_b)

        @tool
        def gethead_to_head(team_a: str, team_b: str) -> str:
            """Show available head-to-head matches and the record from team_a's perspective."""
            return h2h_data_tool(match_reports, team_a, team_b)

        @tool
        def get_match_fixtures(
            matchweek: int | None = None, team: str | None = None, limit: int = 20,
        ) -> str:
            """Return 2024/25 match fixtures/results filtered by matchweek or team."""
            return fixtures_data_tool(match_reports, matchweek, team, limit)

        return (get_league_table, get_player_stats, compare_player_stats, get_scoring_milestones,
                getteam_form, gethead_to_head, get_match_fixtures)

    (get_table_tool, get_stats_tool, get_compare_tool,
     get_milestone_tool, get_form_tool, get_h2h_tool, get_fixtures_tool) = make_toolset()
    @tool
    def inspect_data() -> dict:
        """Discover source datasets, columns, meanings, identities, and coverage."""
        return discover_data(table_rows, player_rows, match_reports)

    @tool
    def analyze(dataset: str, steps: list[dict]) -> dict:
        """Compose operations: filter(field,operator eq/contains/in/ge/gt/le/lt,value); derive(name,method add/subtract/per90,fields); group(by,metrics {output:{agg sum/mean/min/max/count/distinct/first,field}}); cumulative/difference(by identity keys,field,name), chronological by date; sort(by fields,descending); ordinal(field tie key,position 1-based or -1 last), retaining all ties. Call inspect_data first. No generated code. Return evidence for every claim."""
        return analyze_data(table_rows, player_rows, match_reports, dataset, steps)

    stats_subagent = create_agent(
        model=ChatOllama(model="gemma4:e4b", base_url="http://localhost:11434"),
        tools=[get_stats_tool, get_compare_tool, get_table_tool, get_milestone_tool, inspect_data, analyze],
        system_prompt=STATS_PROMPT,
    )
    fixtures_subagent = create_agent(
        model=ChatOllama(model="gemma4:e4b", base_url="http://localhost:11434"),
        tools=[get_fixtures_tool, get_form_tool, get_h2h_tool, inspect_data, analyze],
        system_prompt=FIXTURES_PROMPT,
    )

    @tool
    def call_stats_analyst(query: str) -> str:
        """Statistical analyst specialised in Premier League numbers and standings."""
        result = stats_subagent.invoke({"messages": [{"role": "user", "content": query}]})
        return result["messages"][-1].content

    @tool
    def call_fixtures_reporter(query: str) -> str:
        """Fixtures and results reporter for Premier League gameweeks."""
        result = fixtures_subagent.invoke({"messages": [{"role": "user", "content": query}]})
        return result["messages"][-1].content

    subagent_tools = {
        "call_stats_analyst": call_stats_analyst,
        "call_fixtures_reporter": call_fixtures_reporter,
    }

    def guardrail_node(state):
        last = state["messages"][-1]
        text = last.content if hasattr(last, "content") else str(last)
        if classify_question_scope(text) == "out_of_scope":
            return {"blocked": True, "messages": [AIMessage(content=GUARDRAIL_REJECTION)]}
        # Uncertain wording reaches the existing supervisor for language understanding.
        return {"blocked": False}

    def route_after_guardrail(state) -> Literal["supervisor", "end"]:
        return "end" if state.get("blocked") else "supervisor"

    supervisor_model = ChatOllama(model="gemma4:e4b", base_url="http://localhost:11434").bind_tools(list(subagent_tools.values()))

    def supervisor_node(state):
        response = supervisor_model.invoke([SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"])
        return {"messages": [response]}

    def route_after_supervisor(state) -> Literal["tools", "end"]:
        return "tools" if getattr(state["messages"][-1], "tool_calls", None) else "end"

    def tools_node(state):
        tool_messages = []
        for tool_call in getattr(state["messages"][-1], "tool_calls", []) or []:
            name, args, call_id = tool_call["name"], tool_call["args"], tool_call["id"]
            if name not in subagent_tools:
                tool_messages.append(ToolMessage(content=f"⚠️ Unknown tool `{name}`.", tool_call_id=call_id))
                continue
            result = last_error = None
            for attempt in range(3):
                try:
                    result = subagent_tools[name].invoke(args)
                    break
                except Exception as exc:
                    last_error = exc
                    time.sleep(1.0 * (1.5 ** attempt))
            if result is None:
                result = f"⚠️ Tool `{name}` failed after retries: {last_error}"
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=call_id))
        return {"messages": tool_messages}

    WorkflowState = TypedDict("WorkflowState", {
        "messages": Annotated[list, add_messages],
        "blocked": bool,
    })

    builder = StateGraph(WorkflowState)
    builder.add_node("guardrail", guardrail_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("tools", tools_node)
    builder.add_edge(START, "guardrail")
    builder.add_conditional_edges("guardrail", route_after_guardrail,
                                  {"supervisor": "supervisor", "end": END})
    builder.add_conditional_edges("supervisor", route_after_supervisor,
                                  {"tools": "tools", "end": END})
    builder.add_edge("tools", "supervisor")
    return builder.compile(), player_rows, match_reports, table_rows


def ask(question: str, max_len: int = 1200, *, history: list[dict] | None = None) -> str:
    """Run the existing supervisor/subagent graph and return its grounded answer."""
    graph, player_rows, match_reports, table_rows = _runtime()
    from langchain_core.messages import HumanMessage

    messages = [{"role": m["role"], "content": m["content"]} for m in history or []
                if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)]
    messages.append(HumanMessage(content=question))
    limitation = query_dataset_scope_limitation(question)
    if limitation:
        return limitation
    result = graph.invoke({"messages": messages, "blocked": False})
    response = result["messages"][-1].content
    return response[:max_len] + "..." if len(response) > max_len else response


__all__ = ["ask", "is_premier_league_question"]
