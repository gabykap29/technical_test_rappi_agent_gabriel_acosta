"""Dataset metadata routes."""

from fastapi import APIRouter

from rappi_intelligence.agents.operations_agent import RappiOperationsAgent

router = APIRouter(prefix="/dataset", tags=["dataset"])


@router.get("/overview")
def dataset_overview() -> dict[str, int]:
    """Return dataset coverage metrics for the UI."""

    agent = RappiOperationsAgent()
    wide = agent.dataset.wide
    return {
        "countries": int(wide["COUNTRY"].nunique()),
        "zones": int(wide["ZONE"].nunique()),
        "metrics": int(wide["METRIC"].nunique()),
        "analyticalRows": int(len(wide)),
    }
