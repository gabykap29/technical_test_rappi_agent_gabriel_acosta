"""Agent chat routes."""

from typing import Any

from fastapi import APIRouter, HTTPException

from rappi_intelligence.agents.operations_agent import RappiOperationsAgent
from rappi_intelligence.api.schemas.requests import ChatRequest
from rappi_intelligence.llm.providers import LLMConfigurationError

router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat(payload: ChatRequest) -> dict[str, Any]:
    """Ask the operations agent and return serializable evidence."""

    try:
        agent = RappiOperationsAgent(
            provider=payload.provider,
            model=payload.model,
            base_url=payload.base_url,
            require_llm=payload.require_llm,
        )
        response = agent.ask(payload.question)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "answer": response.answer,
        "table": _table_records(response.table),
        "columns": [] if response.table is None else list(response.table.columns),
        "suggestions": response.suggestions,
        "metadata": response.metadata,
    }


def _table_records(table) -> list[dict[str, Any]]:
    if table is None or table.empty:
        return []
    return table.head(100).where(table.notna(), None).to_dict(orient="records")
