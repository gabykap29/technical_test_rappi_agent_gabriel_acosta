"""Agent chat routes."""

import json
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

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


@router.post("/chat/stream")
async def chat_stream(payload: ChatRequest):
    """Ask the operations agent and stream the LLM response."""

    async def generate() -> AsyncGenerator[str, None]:
        try:
            agent = RappiOperationsAgent(
                provider=payload.provider,
                model=payload.model,
                base_url=payload.base_url,
                require_llm=payload.require_llm,
            )

            # First, get deterministic evidence table
            tool_response = agent.evidence(payload.question)

            table_data = {
                "type": "table",
                "table": _table_records(tool_response.table),
                "columns": (
                    list(tool_response.table.columns)
                    if tool_response.table is not None
                    else []
                ),
                "suggestions": tool_response.suggestions,
            }
            yield f"data: {json.dumps(table_data, default=str)}\n\n"

            # Then stream the LLM response
            async for chunk in agent.ask_stream(payload.question):
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

        except LLMConfigurationError as exc:
            yield f"data: {json.dumps({'type': 'error', 'error': str(exc)})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'error': f'Unexpected error: {str(exc)}'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _table_records(table) -> list[dict[str, Any]]:
    if table is None or table.empty:
        return []
    return table.head(100).where(table.notna(), None).to_dict(orient="records")
