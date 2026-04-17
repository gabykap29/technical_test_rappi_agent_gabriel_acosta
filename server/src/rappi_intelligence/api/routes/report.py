"""Executive report routes."""

from fastapi import APIRouter

from rappi_intelligence.agents.operations_agent import RappiOperationsAgent
from rappi_intelligence.api.schemas.requests import ReportRequest
from rappi_intelligence.reports.rendering import render_markdown_report

router = APIRouter(tags=["report"])


@router.post("/report")
def report(_: ReportRequest) -> dict[str, str]:
    """Generate the executive report markdown."""

    agent = RappiOperationsAgent()
    return {"markdown": render_markdown_report(agent.dataset)}
