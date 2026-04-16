"""Rule-based natural language analytics for the required use cases."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import pandas as pd
import plotly.express as px

from rappi_intelligence.config import (
    CANONICAL_WEEK_COLUMNS,
    IDENTIFIER_COLUMNS,
    METRIC_ALIASES,
    NEGATIVE_METRICS,
    POSITIVE_METRICS,
)
from rappi_intelligence.models import AgentResponse, AnalyticsDataset


@dataclass
class ConversationMemory:
    """Small conversation memory for follow-up questions."""

    last_metric: str | None = None
    last_country: str | None = None
    last_zone: str | None = None
    last_intent: str | None = None


class QueryEngine:
    """Translate business questions into deterministic pandas analyses."""

    def __init__(self, dataset: AnalyticsDataset) -> None:
        self.dataset = dataset
        self.memory = ConversationMemory()
        self.metrics = sorted(dataset.wide["METRIC"].dropna().unique())
        self.countries = sorted(dataset.wide["COUNTRY"].dropna().unique())
        self.zones = sorted(dataset.wide["ZONE"].dropna().unique())

    def ask(self, question: str) -> AgentResponse:
        """Answer a natural-language question using the available dataset."""

        normalized = _normalize(question)
        metric = self._extract_metric(normalized)
        country = self._extract_country(normalized)
        zone = self._extract_zone(normalized)

        if metric:
            self.memory.last_metric = metric
        if country:
            self.memory.last_country = country
        if zone:
            self.memory.last_zone = zone

        if self._is_growth_question(normalized):
            return self._orders_growth(country)
        if "alto" in normalized and "bajo" in normalized:
            return self._high_low_analysis(country)
        if _contains_any(normalized, ["evolucion", "tendencia", "ultimas"]):
            return self._trend(metric, zone, country, normalized)
        if _contains_any(normalized, ["compara", "comparacion", "versus", "vs"]):
            return self._comparison(metric, country)
        if _contains_any(normalized, ["promedio", "media", "average"]):
            return self._average(metric, normalized)
        if _contains_any(normalized, ["problematic", "problema", "deterior"]):
            return self._problematic_zones(country)
        if _contains_any(normalized, ["top", "mayor", "mejor", "5 zonas"]):
            return self._top_zones(metric, country, normalized)

        return self._fallback(metric, country, zone)

    def _top_zones(
        self,
        metric: str | None,
        country: str | None,
        normalized: str,
    ) -> AgentResponse:
        metric = metric or self.memory.last_metric or "Lead Penetration"
        ascending = _contains_any(normalized, ["menor", "peor", "bajo"])
        rows = self._metric_rows(metric, country)
        table = (
            rows[IDENTIFIER_COLUMNS + ["ZONE_TYPE", "METRIC", "L0W"]]
            .sort_values("L0W", ascending=ascending)
            .head(_extract_limit(normalized, default=5))
            .reset_index(drop=True)
        )
        chart = px.bar(table, x="ZONE", y="L0W", color="COUNTRY", title=metric)
        adjective = "menor" if ascending else "mayor"
        return AgentResponse(
            answer=f"Estas son las zonas con {adjective} {metric} en la semana actual.",
            table=table,
            chart=chart,
            suggestions=[
                f"Compara {metric} entre Wealthy y Non Wealthy",
                f"Muestra la evolucion de {metric} para la primera zona",
            ],
        )

    def _comparison(
        self,
        metric: str | None,
        country: str | None,
    ) -> AgentResponse:
        metric = metric or self.memory.last_metric or "Perfect Orders"
        rows = self._metric_rows(metric, country)
        table = (
            rows.groupby(["COUNTRY", "ZONE_TYPE"], dropna=False)["L0W"]
            .mean()
            .reset_index()
            .sort_values(["COUNTRY", "L0W"], ascending=[True, False])
        )
        chart = px.bar(table, x="ZONE_TYPE", y="L0W", color="COUNTRY", barmode="group")
        return AgentResponse(
            answer=(
                f"Comparacion de {metric} por tipo de zona"
                + (f" en {country}." if country else ".")
            ),
            table=table,
            chart=chart,
            suggestions=[
                f"Que zonas explican la brecha de {metric}?",
                "Muestra zonas problematicas por pais",
            ],
        )

    def _trend(
        self,
        metric: str | None,
        zone: str | None,
        country: str | None,
        normalized: str,
    ) -> AgentResponse:
        metric = metric or self.memory.last_metric or "Gross Profit UE"
        zone = zone or self.memory.last_zone
        weeks = min(_extract_limit(normalized, default=8), 9)
        rows = self._metric_rows(metric, country)
        if zone:
            rows = rows[rows["ZONE"].map(_normalize) == _normalize(zone)]
        if rows.empty:
            return AgentResponse(answer="No encontre datos para esa tendencia.")

        week_columns = CANONICAL_WEEK_COLUMNS[-weeks:]
        id_columns = IDENTIFIER_COLUMNS + ["METRIC"]
        table = rows[id_columns + week_columns].head(10)
        long = table.melt(id_vars=id_columns, var_name="WEEK", value_name="VALUE")
        chart = px.line(long, x="WEEK", y="VALUE", color="ZONE", markers=True)
        target = f" en {zone}" if zone else ""
        return AgentResponse(
            answer=f"Evolucion de {metric}{target} durante las ultimas {weeks} semanas.",
            table=table.reset_index(drop=True),
            chart=chart,
            suggestions=[
                f"Compara {metric} por pais",
                "Que cambio semana a semana fue mas fuerte?",
            ],
        )

    def _average(self, metric: str | None, normalized: str) -> AgentResponse:
        metric = metric or self.memory.last_metric or "Lead Penetration"
        rows = self._metric_rows(metric)
        group_columns = ["COUNTRY"] if "pais" in normalized else ["COUNTRY", "CITY"]
        table = (
            rows.groupby(group_columns)["L0W"]
            .mean()
            .reset_index()
            .sort_values("L0W", ascending=False)
        )
        chart = px.bar(table.head(20), x=group_columns[-1], y="L0W", color="COUNTRY")
        return AgentResponse(
            answer=f"Promedio actual de {metric} por {', '.join(group_columns)}.",
            table=table,
            chart=chart,
            suggestions=[
                f"Top 5 zonas con mayor {metric}",
                f"Zonas con deterioro de {metric}",
            ],
        )

    def _high_low_analysis(self, country: str | None) -> AgentResponse:
        lead = self._metric_rows("Lead Penetration", country)
        perfect = self._metric_rows("Perfect Orders", country)
        table = lead[IDENTIFIER_COLUMNS + ["L0W"]].merge(
            perfect[IDENTIFIER_COLUMNS + ["L0W"]],
            on=IDENTIFIER_COLUMNS,
            suffixes=("_LEAD", "_PERFECT"),
        )
        lead_threshold = table["L0W_LEAD"].quantile(0.75)
        perfect_threshold = table["L0W_PERFECT"].quantile(0.25)
        table = table[
            (table["L0W_LEAD"] >= lead_threshold)
            & (table["L0W_PERFECT"] <= perfect_threshold)
        ].sort_values(["L0W_LEAD", "L0W_PERFECT"], ascending=[False, True])
        chart = px.scatter(
            table,
            x="L0W_LEAD",
            y="L0W_PERFECT",
            color="COUNTRY",
            hover_data=["CITY", "ZONE"],
        )
        return AgentResponse(
            answer=(
                "Zonas con Lead Penetration alto y Perfect Orders bajo. "
                "Use percentil 75 para lead y percentil 25 para perfect orders."
            ),
            table=table.head(20).reset_index(drop=True),
            chart=chart,
            suggestions=[
                "Genera recomendaciones para estas zonas",
                "Compara estas zonas contra benchmarks del mismo pais",
            ],
        )

    def _orders_growth(self, country: str | None) -> AgentResponse:
        rows = self._metric_rows("Orders", country)
        table = rows[IDENTIFIER_COLUMNS + ["L5W", "L0W"]].copy()
        table["ABS_GROWTH"] = table["L0W"] - table["L5W"]
        table["PCT_GROWTH"] = _safe_divide(table["ABS_GROWTH"], table["L5W"])
        table = table.sort_values("PCT_GROWTH", ascending=False).head(10)
        explanation = self._growth_explanation(table)
        chart = px.bar(table, x="ZONE", y="PCT_GROWTH", color="COUNTRY")
        return AgentResponse(
            answer=(
                "Estas zonas tuvieron mayor crecimiento de ordenes en las ultimas "
                f"5 semanas. Posibles drivers: {explanation}"
            ),
            table=table.reset_index(drop=True),
            chart=chart,
            suggestions=[
                "Muestra Gross Profit UE para estas zonas",
                "Busca deterioros de Perfect Orders en las zonas que crecieron",
            ],
        )

    def _problematic_zones(self, country: str | None) -> AgentResponse:
        current = self.dataset.wide.copy()
        if country:
            current = current[current["COUNTRY"] == country]
        current["DELTA"] = current["L0W"] - current["L1W"]
        current["PCT_DELTA"] = _safe_divide(current["DELTA"], current["L1W"])
        current["IS_NEGATIVE_METRIC"] = current["METRIC"].isin(NEGATIVE_METRICS)
        current["BAD_MOVE"] = (
            (current["PCT_DELTA"] < -0.10) & ~current["IS_NEGATIVE_METRIC"]
        ) | ((current["PCT_DELTA"] > 0.10) & current["IS_NEGATIVE_METRIC"])
        table = current[current["BAD_MOVE"]].sort_values("PCT_DELTA").head(15)
        cols = IDENTIFIER_COLUMNS + ["METRIC", "L1W", "L0W", "PCT_DELTA"]
        return AgentResponse(
            answer=(
                "Interpreto zonas problematicas como zonas con deterioro semanal "
                "mayor al 10% en metricas de negocio."
            ),
            table=table[cols].reset_index(drop=True),
            suggestions=[
                "Genera el reporte ejecutivo",
                "Compara estas zonas con zonas similares",
            ],
        )

    def _fallback(
        self,
        metric: str | None,
        country: str | None,
        zone: str | None,
    ) -> AgentResponse:
        metric = metric or self.memory.last_metric or "Lead Penetration"
        rows = self._metric_rows(metric, country)
        if zone:
            rows = rows[rows["ZONE"].map(_normalize) == _normalize(zone)]
        table = rows[IDENTIFIER_COLUMNS + ["ZONE_TYPE", "METRIC", "L0W"]].head(10)
        return AgentResponse(
            answer=(
                "No identifique una intencion especifica. Te dejo una vista "
                f"rapida de {metric} y algunas preguntas sugeridas."
            ),
            table=table.reset_index(drop=True),
            suggestions=[
                f"Top 5 zonas con mayor {metric}",
                f"Promedio de {metric} por pais",
                "Que zonas tienen alto Lead Penetration pero bajo Perfect Order?",
            ],
        )

    def _metric_rows(self, metric: str, country: str | None = None) -> pd.DataFrame:
        rows = self.dataset.wide[self.dataset.wide["METRIC"] == metric].copy()
        if country:
            rows = rows[rows["COUNTRY"] == country]
        return rows

    def _extract_metric(self, normalized: str) -> str | None:
        for alias, metric in METRIC_ALIASES.items():
            if alias in normalized and metric in self.metrics:
                return metric
        for metric in self.metrics:
            if _normalize(metric) in normalized:
                return metric
        return None

    def _extract_country(self, normalized: str) -> str | None:
        country_names = {
            "argentina": "AR",
            "brasil": "BR",
            "chile": "CL",
            "colombia": "CO",
            "costa rica": "CR",
            "ecuador": "EC",
            "mexico": "MX",
            "peru": "PE",
            "uruguay": "UY",
        }
        for name, code in country_names.items():
            if name in normalized and code in self.countries:
                return code
        for country in self.countries:
            if re.search(rf"\b{country.lower()}\b", normalized):
                return country
        return None

    def _extract_zone(self, normalized: str) -> str | None:
        for zone in self.zones:
            if _normalize(zone) in normalized:
                return zone
        return None

    def _is_growth_question(self, normalized: str) -> bool:
        return _contains_any(normalized, ["crecen", "crecimiento", "growth"]) and (
            "orden" in normalized or "orders" in normalized
        )

    def _growth_explanation(self, table: pd.DataFrame) -> str:
        if table.empty:
            return "no hay zonas con crecimiento suficiente para explicar."

        zones = table["ZONE"].head(5).tolist()
        peers = self.dataset.wide[self.dataset.wide["ZONE"].isin(zones)]
        metric_changes = peers.copy()
        metric_changes["PCT_DELTA"] = _safe_divide(
            metric_changes["L0W"] - metric_changes["L5W"],
            metric_changes["L5W"],
        )
        drivers = (
            metric_changes[metric_changes["METRIC"].isin(POSITIVE_METRICS)]
            .groupby("METRIC")["PCT_DELTA"]
            .mean()
            .sort_values(ascending=False)
            .head(3)
        )
        if drivers.empty:
            return "no se detectaron drivers claros en metricas relacionadas."
        return ", ".join(f"{metric} ({value:.1%})" for metric, value in drivers.items())


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).lower())
    plain = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", plain).strip()


def _contains_any(value: str, options: list[str]) -> bool:
    return any(option in value for option in options)


def _extract_limit(value: str, default: int) -> int:
    match = re.search(r"\b(\d+)\b", value)
    return int(match.group(1)) if match else default


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.div(denominator.replace({0: pd.NA})).fillna(0)
