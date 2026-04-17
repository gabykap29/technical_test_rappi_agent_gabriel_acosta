"""Markdown report rendering."""

from __future__ import annotations

from rappi_intelligence.analytics.insights import InsightGenerator
from rappi_intelligence.shared.models import AnalyticsDataset, Insight


def render_markdown_report(dataset: AnalyticsDataset) -> str:
    """Render an executive insight report in Markdown."""

    generator = InsightGenerator(dataset)
    insights = generator.generate()
    summary = insights[:5]

    lines = [
        "# Rappi Operations Intelligence Report",
        "",
        "## Executive Summary",
        "",
    ]
    for index, insight in enumerate(summary, start=1):
        lines.append(f"{index}. **{insight.title}** - {insight.detail}")
    lines.extend(["", "## Insight Detail", ""])

    for category in _categories(insights):
        lines.extend([f"### {category}", ""])
        for insight in [item for item in insights if item.category == category]:
            lines.extend(
                [
                    f"#### {insight.title}",
                    "",
                    f"- Severity: {insight.severity}",
                    f"- Detail: {insight.detail}",
                    f"- Recommendation: {insight.recommendation}",
                    "",
                ]
            )

    lines.extend(
        [
            "## Methodology",
            "",
            "- Anomalies: week-over-week movement above 10%.",
            "- Worrying trends: three consecutive deteriorating weekly movements.",
            "- Benchmarking: current gap above 20% vs same country and zone type.",
            "- Correlations: absolute Pearson correlation above 0.45 by zone.",
            "- Opportunities: high orders with low Lead Penetration.",
            "",
        ]
    )
    return "\n".join(lines)


def _categories(insights: list[Insight]) -> list[str]:
    return list(dict.fromkeys(insight.category for insight in insights))
