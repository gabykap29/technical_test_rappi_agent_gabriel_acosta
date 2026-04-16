"""Automatic insight generation for executive reporting."""

from __future__ import annotations

import pandas as pd

from rappi_intelligence.config import (
    CANONICAL_WEEK_COLUMNS,
    IDENTIFIER_COLUMNS,
    NEGATIVE_METRICS,
    POSITIVE_METRICS,
)
from rappi_intelligence.models import AnalyticsDataset, Insight


class InsightGenerator:
    """Generate business insights from normalized operational metrics."""

    def __init__(self, dataset: AnalyticsDataset) -> None:
        self.dataset = dataset
        self.wide = dataset.wide.copy()

    def generate(self) -> list[Insight]:
        """Generate all insight categories requested in the case."""

        insights: list[Insight] = []
        insights.extend(self.anomalies())
        insights.extend(self.worrying_trends())
        insights.extend(self.benchmarking())
        insights.extend(self.correlations())
        insights.extend(self.opportunities())
        return sorted(insights, key=_severity_rank)

    def executive_summary(self, limit: int = 5) -> list[Insight]:
        """Return the top critical insights for the executive summary."""

        return self.generate()[:limit]

    def anomalies(self, limit: int = 8) -> list[Insight]:
        """Find zones with week-over-week movement greater than 10%."""

        data = self.wide.copy()
        data["DELTA"] = data["L0W"] - data["L1W"]
        data["PCT_DELTA"] = _safe_divide(data["DELTA"], data["L1W"])
        data["IS_NEGATIVE"] = data["METRIC"].isin(NEGATIVE_METRICS)
        data["BAD_MOVE"] = (
            (data["PCT_DELTA"] <= -0.10) & ~data["IS_NEGATIVE"]
        ) | ((data["PCT_DELTA"] >= 0.10) & data["IS_NEGATIVE"])
        data["GOOD_MOVE"] = (
            (data["PCT_DELTA"] >= 0.10) & ~data["IS_NEGATIVE"]
        ) | ((data["PCT_DELTA"] <= -0.10) & data["IS_NEGATIVE"])

        selected = data[data["BAD_MOVE"] | data["GOOD_MOVE"]].copy()
        selected["MAGNITUDE"] = selected["PCT_DELTA"].abs()
        selected = selected.sort_values("MAGNITUDE", ascending=False).head(limit)

        insights = []
        for _, row in selected.iterrows():
            direction = "deterioro" if row["BAD_MOVE"] else "mejora"
            insights.append(
                Insight(
                    category="Anomalias",
                    title=f"{row['ZONE']} tuvo {direction} abrupto en {row['METRIC']}",
                    detail=(
                        f"{row['COUNTRY']} / {row['CITY']}: {row['METRIC']} cambio "
                        f"{row['PCT_DELTA']:.1%} vs la semana anterior."
                    ),
                    recommendation=(
                        "Revisar eventos operativos locales, cambios de oferta, "
                        "promociones y capacidad de cumplimiento de la zona."
                    ),
                    severity="high" if row["BAD_MOVE"] else "medium",
                    evidence=row.to_dict(),
                )
            )
        return insights

    def worrying_trends(self, limit: int = 8) -> list[Insight]:
        """Find metrics deteriorating for at least three consecutive weeks."""

        insights = []
        for _, row in self.wide.iterrows():
            values = row[CANONICAL_WEEK_COLUMNS].astype(float).tolist()
            recent = values[-4:]
            if len(recent) < 4:
                continue
            diffs = [recent[index] - recent[index - 1] for index in range(1, 4)]
            is_negative_metric = row["METRIC"] in NEGATIVE_METRICS
            deteriorating = all(diff < 0 for diff in diffs)
            if is_negative_metric:
                deteriorating = all(diff > 0 for diff in diffs)
            if not deteriorating:
                continue

            total_change = _safe_scalar_divide(recent[-1] - recent[0], recent[0])
            insights.append(
                Insight(
                    category="Tendencias preocupantes",
                    title=(
                        f"{row['METRIC']} se deteriora 3 semanas seguidas "
                        f"en {row['ZONE']}"
                    ),
                    detail=(
                        f"{row['COUNTRY']} / {row['CITY']} acumula un cambio de "
                        f"{total_change:.1%} desde L3W hasta L0W."
                    ),
                    recommendation=(
                        "Priorizar diagnostico semanal: validar si el deterioro "
                        "viene de demanda, oferta, conversion o calidad operativa."
                    ),
                    severity="high",
                    evidence=row.to_dict(),
                )
            )
        return insights[:limit]

    def benchmarking(self, limit: int = 8) -> list[Insight]:
        """Compare similar zones by country and wealth segment."""

        data = self.wide.copy()
        group_columns = ["COUNTRY", "ZONE_TYPE", "METRIC"]
        data["PEER_MEDIAN"] = data.groupby(group_columns)["L0W"].transform("median")
        data["GAP"] = data["L0W"] - data["PEER_MEDIAN"]
        data["PCT_GAP"] = _safe_divide(data["GAP"], data["PEER_MEDIAN"])
        data["IS_NEGATIVE"] = data["METRIC"].isin(NEGATIVE_METRICS)
        data["UNDERPERFORMING"] = (
            (data["PCT_GAP"] < -0.20) & ~data["IS_NEGATIVE"]
        ) | ((data["PCT_GAP"] > 0.20) & data["IS_NEGATIVE"])
        selected = data[data["UNDERPERFORMING"]].copy()
        selected["MAGNITUDE"] = selected["PCT_GAP"].abs()
        selected = selected.sort_values("MAGNITUDE", ascending=False).head(limit)

        insights = []
        for _, row in selected.iterrows():
            insights.append(
                Insight(
                    category="Benchmarking",
                    title=f"{row['ZONE']} queda lejos de sus pares en {row['METRIC']}",
                    detail=(
                        f"Vs zonas {row['ZONE_TYPE']} de {row['COUNTRY']}, "
                        f"la brecha es {row['PCT_GAP']:.1%}."
                    ),
                    recommendation=(
                        "Usar las mejores zonas pares como benchmark operativo y "
                        "replicar acciones de surtido, cobertura o conversion."
                    ),
                    severity="medium",
                    evidence=row.to_dict(),
                )
            )
        return insights

    def correlations(self, limit: int = 5) -> list[Insight]:
        """Find relevant correlations between current metrics."""

        pivot = self.wide.pivot_table(
            index=IDENTIFIER_COLUMNS,
            columns="METRIC",
            values="L0W",
            aggfunc="mean",
        )
        corr = pivot.corr(numeric_only=True)
        insights = []
        seen: set[tuple[str, str]] = set()
        for metric_a in corr.columns:
            for metric_b in corr.columns:
                if metric_a == metric_b:
                    continue
                key = tuple(sorted((metric_a, metric_b)))
                if key in seen:
                    continue
                seen.add(key)
                value = corr.loc[metric_a, metric_b]
                if pd.isna(value) or abs(value) < 0.45:
                    continue
                relation = "positiva" if value > 0 else "negativa"
                insights.append(
                    Insight(
                        category="Correlaciones",
                        title=f"{metric_a} y {metric_b} tienen correlacion {relation}",
                        detail=(
                            f"La correlacion actual entre ambas metricas es "
                            f"{value:.2f} a nivel zona."
                        ),
                        recommendation=(
                            "Usar esta relacion como hipotesis de diagnostico, "
                            "no como causalidad. Validar con segmentacion por pais."
                        ),
                        severity="medium",
                        evidence={"metric_a": metric_a, "metric_b": metric_b, "r": value},
                    )
                )
        return sorted(
            insights,
            key=lambda insight: abs(insight.evidence["r"]),
            reverse=True,
        )[:limit]

    def opportunities(self, limit: int = 8) -> list[Insight]:
        """Identify high-impact improvement opportunities."""

        lead = _metric(self.wide, "Lead Penetration")
        orders = _metric(self.wide, "Orders")
        perfect = _metric(self.wide, "Perfect Orders")
        if lead.empty or orders.empty:
            return []

        table = lead[IDENTIFIER_COLUMNS + ["L0W"]].merge(
            orders[IDENTIFIER_COLUMNS + ["L0W"]],
            on=IDENTIFIER_COLUMNS,
            suffixes=("_LEAD", "_ORDERS"),
        )
        if not perfect.empty:
            table = table.merge(
                perfect[IDENTIFIER_COLUMNS + ["L0W"]],
                on=IDENTIFIER_COLUMNS,
                how="left",
            ).rename(columns={"L0W": "L0W_PERFECT"})

        low_lead = table["L0W_LEAD"] <= table["L0W_LEAD"].quantile(0.25)
        high_orders = table["L0W_ORDERS"] >= table["L0W_ORDERS"].quantile(0.75)
        selected = table[low_lead & high_orders].sort_values(
            "L0W_ORDERS",
            ascending=False,
        )

        insights = []
        for _, row in selected.head(limit).iterrows():
            insights.append(
                Insight(
                    category="Oportunidades",
                    title=f"{row['ZONE']} combina alto volumen con bajo Lead Penetration",
                    detail=(
                        f"{row['COUNTRY']} / {row['CITY']} tiene "
                        f"{row['L0W_ORDERS']:.0f} ordenes actuales y "
                        f"{row['L0W_LEAD']:.2f} de Lead Penetration."
                    ),
                    recommendation=(
                        "Priorizar adquisicion de tiendas prospecto: el volumen "
                        "sugiere mayor retorno potencial por mejora de cobertura."
                    ),
                    severity="medium",
                    evidence=row.to_dict(),
                )
            )
        return insights


def _metric(data: pd.DataFrame, metric: str) -> pd.DataFrame:
    return data[data["METRIC"] == metric].copy()


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.div(denominator.replace({0: pd.NA})).fillna(0)


def _safe_scalar_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _severity_rank(insight: Insight) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(insight.severity, 3)
