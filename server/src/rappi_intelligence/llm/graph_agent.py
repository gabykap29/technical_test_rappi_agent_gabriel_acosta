"""LangGraph-powered agent that uses a configurable LLM provider."""
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, Sequence
from typing import Any, TypedDict

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from plotly.utils import PlotlyJSONEncoder

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

            async def _get_report():
                chunks = []
                async for chunk in self.generate_executive_report_stream():
                    chunks.append(chunk)
                return "".join(chunks)

            try:
                report = asyncio.run(_get_report())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    report = loop.run_until_complete(_get_report())
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

    async def ask_stream(
        self,
        question: str,
        conversation_history: Sequence[object] | None = None,
    ) -> AsyncGenerator[str, None]:
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
        history_context = _format_conversation_history(conversation_history)

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
                    f"Conversation history:\n{history_context}\n\n"
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
                    f"Conversation history:\n{history_context}\n\n"
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

    async def generate_executive_report_stream(self) -> AsyncGenerator[str, None]:
        """Generate an executive report using the LLM with streaming."""
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from rappi_intelligence.analytics.insights import InsightGenerator

        generator = InsightGenerator(self.dataset)
        insights = generator.generate()

        generated_at = datetime.now(ZoneInfo("America/Buenos_Aires"))
        timestamp = generated_at.strftime("%Y-%m-%d %H:%M:%S")
        generated_at_label = generated_at.strftime("%Y-%m-%d %H:%M:%S %Z")

        wide = self.dataset.wide
        available_metrics = list(wide["METRIC"].unique()) if "METRIC" in wide.columns else []
        available_countries = list(wide["COUNTRY"].unique()) if "COUNTRY" in wide.columns else []
        week_columns = [col for col in wide.columns if col.startswith("L") and col.endswith("W")]
        technical_query = (
            "InsightGenerator.generate() sobre dataset.wide; "
            f"METRIC in {available_metrics}; "
            f"COUNTRY in {available_countries}; "
            f"WEEK columns in {week_columns}; "
            f"rows={len(wide)}"
        )

        query_info = {
            "metrics_analyzed": available_metrics[:10],
            "countries": available_countries,
            "time_period": f"{week_columns[-1] if week_columns else 'N/A'} to {week_columns[0] if week_columns else 'N/A'}",
            "total_zones": int(wide["ZONE"].nunique()) if "ZONE" in wide.columns else 0,
            "total_rows": len(wide),
            "technical_query": technical_query,
        }

        yield _json_dumps({
            "type": "metadata",
            "timestamp": timestamp,
            "insights_count": len(insights),
            "query_info": query_info,
        }) + "\n\n"

        yield "# Generando análisis de datos...\n\n"

        charts_data = self._generate_report_charts(insights)
        for chart in charts_data:
            yield _json_dumps({
                "type": "chart",
                "chart": chart,
            }) + "\n\n"

        report_prompt = [
            SystemMessage(
                content=(
                    "Eres un asistente de análisis ejecutivo senior. "
                    "Genera un reporte ejecutivo en formato MARKDOWN PURO "
                    "(solo markdown, sin HTML). "
                    "Usa: # para títulos, ## para subtítulos, **texto** para "
                    "negritas, - para listas, "
                    "| Tabla | syntax | para tablas. "
                    "NO uses tags HTML como <div>, <table>, <pre>, etc. "
                    "Sé detallado y accionable."
                )
            ),
            HumanMessage(
                content=(
                    f"Insights generados:\n{self._format_insights(insights)}\n"
                    f"Datos analizados:\n"
                    f"- Fecha y hora actual: {generated_at_label}\n"
                    f"- Métricas: {', '.join(available_metrics[:5])}\n"
                    f"- Países: {', '.join(available_countries)}\n"
                    f"- Período: {week_columns[-1] if week_columns else 'N/A'} a {week_columns[0] if week_columns else 'N/A'}\n"
                    "Genera el reporte ejecutivo en MARKDOWN PURO:\n"
                    "Incluye la fecha y hora de generación al inicio del reporte.\n"
                    "## Executive Summary\n"
                    "Top 5 insights críticos\n\n"
                    "## Análisis por Categoría\n"
                    "### Anomalías\n"
                    "| Métrica | UE | Cambio | Acción |\n"
                    "|--------|------|--------|--------|\n\n"
                    "## Recomendaciones\n"
                    "## Metodología\n"
                    "Usa solo markdown. No HTML."
                )
            ),
        ]

        async for chunk in self.llm.astream(report_prompt):
            if chunk.content:
                yield chunk.content

    def _generate_report_charts(self, insights: list) -> list[dict]:
        """Generate chart data for the executive report."""
        import plotly.express as px
        import plotly.graph_objects as go
        from rappi_intelligence.shared.models import Insight

        charts = []
        wide = self.dataset.wide

        severity_counts = {}
        for insight in insights:
            if isinstance(insight, Insight):
                severity_counts[insight.severity] = severity_counts.get(insight.severity, 0) + 1

        if severity_counts:
            fig = go.Figure(data=[go.Pie(
                labels=list(severity_counts.keys()),
                values=list(severity_counts.values()),
                marker_colors=['#ff3b30', '#ff7a1a', '#ffb15c', '#d82f19']
            )])
            fig.update_layout(
                title="Distribución por Severidad",
                template="plotly_white",
            )
            charts.append({
                "type": "pie",
                "title": "Distribución por Severidad",
                "data": _json_safe(fig.to_dict()),
            })

        metric_data = wide[wide["METRIC"].isin(["Gross Profit UE", "Perfect Orders", "Orders"])].groupby(
            ["COUNTRY", "METRIC"]
        )["L0W"].sum().reset_index()
        if not metric_data.empty:
            fig = px.bar(
                metric_data,
                x="COUNTRY",
                y="L0W",
                color="METRIC",
                title="Métricas Clave por País",
                barmode="group"
            )
            fig.update_layout(template="plotly_white")
            charts.append({
                "type": "bar",
                "title": "Métricas Clave por País",
                "data": _json_safe(fig.to_dict()),
            })

        country_zones = wide.groupby("COUNTRY")["ZONE"].nunique().reset_index()
        if not country_zones.empty:
            fig = px.bar(
                country_zones,
                x="COUNTRY",
                y="ZONE",
                title="Zonas por País"
            )
            fig.update_layout(template="plotly_white")
            charts.append({
                "type": "bar",
                "title": "Zonas por País",
                "data": _json_safe(fig.to_dict()),
            })

        return charts

    def _generate_report(self, state: AgentState) -> AgentState:
        return {"executive_report": "Reporte generado"}

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


def _format_conversation_history(messages: Sequence[object] | None) -> str:
    if not messages:
        return "No previous conversation."

    lines = []
    for message in messages[-12:]:
        role = getattr(message, "role", "")
        content = getattr(message, "content", "")
        if not role or not content:
            continue
        clean_content = " ".join(str(content).split())
        if len(clean_content) > 800:
            clean_content = f"{clean_content[:800]}..."
        lines.append(f"{role}: {clean_content}")
    return "\n".join(lines) if lines else "No previous conversation."


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, cls=PlotlyJSONEncoder)


def _json_safe(payload: Any) -> Any:
    return json.loads(_json_dumps(payload))
