"""Regression tests for required business questions."""

import json

from rappi_intelligence.agents.operations_agent import RappiOperationsAgent
from rappi_intelligence.analytics.insights import InsightGenerator
from rappi_intelligence.llm.graph_agent import LangGraphOperationsAgent


def test_agent_answers_top_zones() -> None:
    agent = RappiOperationsAgent()

    response = agent.ask("Cuales son las 5 zonas con mayor Lead Penetration?")

    assert "mayor Lead Penetration" in response.answer
    assert response.table is not None
    assert len(response.table) == 5


def test_agent_compares_zone_types_in_mexico() -> None:
    agent = RappiOperationsAgent()

    response = agent.ask("Compara Perfect Order entre Wealthy y Non Wealthy en Mexico")

    assert response.table is not None
    assert set(response.table["COUNTRY"]) == {"MX"}
    assert {"Wealthy", "Non Wealthy"}.issubset(set(response.table["ZONE_TYPE"]))


def test_agent_returns_trend_for_chapinero() -> None:
    agent = RappiOperationsAgent()

    response = agent.ask("Muestra Gross Profit UE en Chapinero ultimas 8 semanas")

    assert response.table is not None
    assert response.table.iloc[0]["ZONE"] == "Chapinero"
    assert "L0W" in response.table.columns


def test_insights_cover_required_categories() -> None:
    agent = RappiOperationsAgent()
    insights = InsightGenerator(agent.dataset).generate()

    categories = {insight.category for insight in insights}

    assert "Anomalias" in categories
    assert "Tendencias preocupantes" in categories
    assert "Benchmarking" in categories
    assert "Correlaciones" in categories
    assert "Oportunidades" in categories


def test_executive_report_charts_are_standard_json_serializable() -> None:
    agent = RappiOperationsAgent()
    graph_agent = LangGraphOperationsAgent(
        dataset=agent.dataset,
        llm=object(),
        provider="test",
        model="test",
    )
    insights = InsightGenerator(agent.dataset).generate()

    charts = graph_agent._generate_report_charts(insights)

    json.dumps(charts)
    assert charts
