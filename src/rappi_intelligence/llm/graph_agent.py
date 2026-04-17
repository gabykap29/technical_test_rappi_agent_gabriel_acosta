"""LangGraph-powered agent that uses a configurable LLM provider."""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator, TypedDict

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
    executive_report: str


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

        normalized = question.lower()
        is_report_request = any(
            keyword in normalized
            for keyword in [
                "reporte",
                "reporte ejecutivo",
                "executive report",
                "informe",
                "reporte de operaciones",
            ]
        )

        if is_report_request:
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                chunks = []
                async for chunk in self.generate_executive_report_stream():
                    chunks.append(chunk)
                report = "".join(chunks)
            finally:
                loop.close()
            return AgentResponse(
                answer=report,
                metadata={
                    "provider": self.provider,
                    "model": self.model,
                    "type": "executive_report",
                },
            )

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

    async def ask_stream(self, question: str) -> AsyncGenerator[str, None]:
        """Answer a question with streaming response."""

        normalized = question.lower()
        is_report_request = any(
            keyword in normalized
            for keyword in [
                "reporte",
                "reporte ejecutivo",
                "executive report",
                "informe",
                "reporte de operaciones",
            ]
        )

        if is_report_request:
            async for chunk in self.generate_executive_report_stream():
                yield chunk
            return

        # 1. PLAN - Get the plan
        metrics = ", ".join(sorted(self.dataset.wide["METRIC"].unique()))
        countries = ", ".join(sorted(self.dataset.wide["COUNTRY"].unique()))

        plan_prompt = [
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
                    'JSON schema: {"intent": string, "metric": string|null, '
                    '"country": string|null, "zone": string|null, '
                    '"limit": number|null, "rationale": string}'
                )
            ),
        ]

        plan_message = self.llm.invoke(plan_prompt)
        plan = _parse_json(str(plan_message.content))

        # 2. EXECUTE - Get the data
        enriched_question = _enrich_question(question, plan)
        tool_response = self.tools.ask(enriched_question)

        # 3. RESPOND - Stream the response
        table_sample = _table_sample(tool_response.table)

        respond_prompt = [
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
                    f"User question: {question}\n"
                    "Planner JSON: "
                    f"{json.dumps(plan, ensure_ascii=False)}\n"
                    f"Base analytical answer: {tool_response.answer}\n"
                    f"Evidence table sample:\n{table_sample}\n"
                    "Write the final answer and include one practical next step."
                )
            ),
        ]

        # Stream the LLM response
        async for chunk in self.llm.astream(respond_prompt):
            if chunk.content:
                yield chunk.content

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("plan", self._plan)
        graph.add_node("execute", self._execute)
        graph.add_node("respond", self._respond)
        graph.add_node("report", self._generate_report)
        graph.set_entry_point("plan")

        def should_run_report(state: AgentState) -> str:
            plan = state.get("plan", {})
            intent = plan.get("intent", "")
            question = state.get("question", "").lower()
            is_report = any(
                keyword in question
                for keyword in [
                    "reporte",
                    "executive report",
                    "informe",
                    "reporte de operaciones",
                ]
            )
            if is_report or intent == "executive_report":
                return "report"
            return "execute"

        graph.add_conditional_edges(
            "plan", should_run_report, {"report": "report", "execute": "execute"}
        )
        graph.add_edge("execute", "respond")
        graph.add_edge("respond", END)
        graph.add_edge("report", END)
        return graph.compile()

async def generate_executive_report_stream(
        self,
    ) -> AsyncGenerator[str, None]:
        """Generate an executive report using the LLM with streaming."""
        from rappi_intelligence.analytics.insights import InsightGenerator

        generator = InsightGenerator(self.dataset)
        insights = generator.generate()

        yield "# Generando análisis de datos...\n\n"

        report_prompt = [
            SystemMessage(
                content=(
                    "Eres un asistente de análisis executives senior. "
                    "Genera un reporte ejecutivo en formato Markdown en español. "
                    "Usa los insights proporcionados y agrega contexto de negocio. "
                    "Sé detallado y accionable."
                )
            ),
            HumanMessage(
                content=(
                    f"Insights generados:\n{self._format_insights(insights)}\n"
                    "Genera el reporte ejecutivo con:\n"
                    "## Executive Summary (top 5 insights más importantes)\n"
                    "## Análisis por categoría (Anomalías, Tendencias, Benchmarks, Correlaciones, Oportunidades)\n"
                    "## Recomendaciones\n"
                    "## Metodología"
                )
            ),
        ]

        async for chunk in self.llm.astream(report_prompt):
            if chunk.content:
                yield chunk.content

    def _generate_report(self, state: AgentState) -> AgentState:
        return {"executive_report": "Reporte generado"}
        return {"executive_report": self.generate_executive_report()}

    def _format_insights(self, insights: list) -> str:
        from rappi_intelligence.shared.models import Insight

        lines = []
        for insight in insights[:15]:
            if isinstance(insight, Insight):
                lines.append(
                    f"- [{insight.severity}] {insight.title}: {insight.detail}"
                )
        return "\n".join(lines)

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
                    'JSON schema: {"intent": string, "metric": string|null, '
                    '"country": string|null, "zone": string|null, '
                    '"limit": number|null, "rationale": string}'
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
