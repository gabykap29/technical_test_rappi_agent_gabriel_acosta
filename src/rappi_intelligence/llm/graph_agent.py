"""LangGraph-powered agent that uses a configurable LLM provider."""

from __future__ import annotations

import json
from typing import Any, TypedDict

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from rappi_intelligence.analytics.query_engine import QueryEngine
from rappi_intelligence.shared.models import AgentResponse, AnalyticsDataset


class AgentState(TypedDict, total=False):
    """State passed between LangGraph nodes."""

    question: str
    plan: dict[str, Any]
    tool_response: AgentResponse
    final_answer: str


class LangGraphOperationsAgent:
    """LLM orchestration layer over deterministic analytics tools."""

    def __init__(
        self,
        dataset: AnalyticsDataset,
        llm: Any,
        provider: str,
        model: str,
    ) -> None:
        self.dataset = dataset
        self.llm = llm
        self.provider = provider
        self.model = model
        self.tools = QueryEngine(dataset)
        self.graph = self._build_graph()

    def ask(self, question: str) -> AgentResponse:
        """Answer a question through the LangGraph workflow."""

        state = self.graph.invoke({"question": question})
        response = state["tool_response"]
        response.answer = state.get("final_answer") or response.answer
        response.metadata.update(
            {
                "provider": self.provider,
                "model": self.model,
                "plan": state.get("plan", {}),
            }
        )
        return response

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("plan", self._plan)
        graph.add_node("execute", self._execute)
        graph.add_node("respond", self._respond)
        graph.set_entry_point("plan")
        graph.add_edge("plan", "execute")
        graph.add_edge("execute", "respond")
        graph.add_edge("respond", END)
        return graph.compile()

    def _plan(self, state: AgentState) -> AgentState:
        question = state["question"]
        metrics = ", ".join(sorted(self.dataset.wide["METRIC"].unique()))
        countries = ", ".join(sorted(self.dataset.wide["COUNTRY"].unique()))
        prompt = [
            SystemMessage(
                content=(
                    "You are an analytics planner for Rappi operations data. "
                    "Return only valid JSON. Choose one intent among: ranking, "
                    "comparison, trend, average, high_low, growth, problematic, "
                    "fallback. Include metric, country, zone, limit and rationale "
                    "when available. Do not calculate results."
                )
            ),
            HumanMessage(
                content=(
                    f"Question: {question}\n"
                    f"Available metrics: {metrics}\n"
                    f"Available countries: {countries}\n"
                    "JSON schema: {\"intent\": string, \"metric\": string|null, "
                    "\"country\": string|null, \"zone\": string|null, "
                    "\"limit\": number|null, \"rationale\": string}"
                )
            ),
        ]
        message = self.llm.invoke(prompt)
        plan = _parse_json(str(message.content))
        return {"plan": plan}

    def _execute(self, state: AgentState) -> AgentState:
        question = state["question"]
        plan = state.get("plan", {})
        enriched_question = _enrich_question(question, plan)
        return {"tool_response": self.tools.ask(enriched_question)}

    def _respond(self, state: AgentState) -> AgentState:
        response = state["tool_response"]
        table_sample = _table_sample(response.table)
        prompt = [
            SystemMessage(
                content=(
                    "You are a senior operations analytics assistant. Answer in "
                    "Spanish. Be concise, business-oriented and explicit about "
                    "what the evidence says. Do not invent numbers outside the "
                    "provided table or base answer."
                )
            ),
            HumanMessage(
                content=(
                    f"User question: {state['question']}\n"
                    "Planner JSON: "
                    f"{json.dumps(state.get('plan', {}), ensure_ascii=False)}\n"
                    f"Base analytical answer: {response.answer}\n"
                    f"Evidence table sample:\n{table_sample}\n"
                    "Write the final answer and include one practical next step."
                )
            ),
        ]
        message = self.llm.invoke(prompt)
        return {"final_answer": str(message.content)}


def _parse_json(content: str) -> dict[str, Any]:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        return {"intent": "fallback", "rationale": content[:300]}
    try:
        return json.loads(content[start : end + 1])
    except json.JSONDecodeError:
        return {"intent": "fallback", "rationale": content[:300]}


def _enrich_question(question: str, plan: dict[str, Any]) -> str:
    hints = []
    for key in ("intent", "metric", "country", "zone", "limit"):
        value = plan.get(key)
        if value:
            hints.append(f"{key}: {value}")
    if not hints:
        return question
    return f"{question}\nContexto interpretado por LLM: {', '.join(hints)}"


def _table_sample(table: pd.DataFrame | None) -> str:
    if table is None or table.empty:
        return "No table returned."
    return table.head(12).to_string(index=False)
