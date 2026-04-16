"""Markdown and HTML report rendering."""

from __future__ import annotations

from html import escape
from pathlib import Path

from rappi_intelligence.config import REPORTS_DIR
from rappi_intelligence.insights import InsightGenerator
from rappi_intelligence.models import AnalyticsDataset, Insight


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


def render_html_report(markdown_report: str) -> str:
    """Render a simple standalone HTML report from Markdown text."""

    body = []
    for line in markdown_report.splitlines():
        if line.startswith("# "):
            body.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("### "):
            body.append(f"<h3>{escape(line[4:])}</h3>")
        elif line.startswith("#### "):
            body.append(f"<h4>{escape(line[5:])}</h4>")
        elif line.startswith("- "):
            body.append(f"<p>{escape(line)}</p>")
        elif line.strip():
            body.append(f"<p>{escape(line)}</p>")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Rappi Operations Intelligence Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.5; }}
    h1, h2, h3 {{ color: #222; }}
    h4 {{ margin-bottom: 4px; }}
    p {{ max-width: 980px; }}
  </style>
</head>
<body>
{chr(10).join(body)}
</body>
</html>
"""


def write_reports(
    dataset: AnalyticsDataset,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Write Markdown and HTML reports to disk."""

    target = output_dir or REPORTS_DIR
    target.mkdir(parents=True, exist_ok=True)
    markdown = render_markdown_report(dataset)
    html = render_html_report(markdown)
    markdown_path = target / "executive_report.md"
    html_path = target / "executive_report.html"
    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    return markdown_path, html_path


def _categories(insights: list[Insight]) -> list[str]:
    return list(dict.fromkeys(insight.category for insight in insights))
