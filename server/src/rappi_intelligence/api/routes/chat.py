"""Agent chat routes."""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from rappi_intelligence.agents.operations_agent import RappiOperationsAgent
from rappi_intelligence.api.schemas.requests import ChatRequest
from rappi_intelligence.llm.providers import LLMConfigurationError
from rappi_intelligence.memory.conversations import ConversationStore
from rappi_intelligence.security.credentials import CredentialStore

router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat(payload: ChatRequest) -> dict[str, Any]:
    """Ask the operations agent and return serializable evidence."""

    memory = ConversationStore()
    history_id = memory.ensure_conversation(payload.history_id)
    try:
        agent = RappiOperationsAgent(
            provider=payload.provider,
            model=payload.model,
            base_url=payload.base_url,
            require_llm=payload.require_llm,
        )
        response = agent.ask(payload.question)
        memory.append_message(history_id, "user", payload.question)
        memory.append_message(history_id, "assistant", response.answer)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response.metadata["history_id"] = history_id
    return {
        "answer": response.answer,
        "table": _table_records(response.table),
        "columns": [] if response.table is None else list(response.table.columns),
        "suggestions": response.suggestions,
        "metadata": response.metadata,
        "query": response.query,
        "history_id": history_id,
    }


@router.post("/chat/stream")
async def chat_stream(payload: ChatRequest, request: Request):
    """Ask the operations agent and stream the LLM response."""

    async def generate() -> AsyncGenerator[str, None]:
        memory = ConversationStore()
        history_id = memory.ensure_conversation(payload.history_id)
        conversation_history = memory.get_messages(history_id)
        assistant_chunks: list[str] = []
        try:
            yield f"data: {json.dumps({'type': 'history', 'history_id': history_id})}\n\n"
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
                "query": tool_response.query,
            }
            yield f"data: {json.dumps(table_data, default=str)}\n\n"

            # Then stream structured report events or regular LLM text chunks.
            async for chunk in agent.ask_stream(
                payload.question,
                conversation_history=conversation_history,
            ):
                stream_event = _stream_event(chunk)
                if stream_event.get("type") == "chunk":
                    assistant_chunks.append(str(stream_event.get("content", "")))
                yield f"data: {json.dumps(stream_event, default=str)}\n\n"

            memory.append_message(history_id, "user", payload.question)
            memory.append_message(history_id, "assistant", "".join(assistant_chunks))

        except asyncio.CancelledError:
            CredentialStore().clear_api_keys()
            raise
        except LLMConfigurationError as exc:
            yield f"data: {json.dumps({'type': 'error', 'error': str(exc)})}\n\n"
        except Exception as exc:
            error_payload = {"type": "error", "error": f"Unexpected error: {exc}"}
            yield f"data: {json.dumps(error_payload)}\n\n"
        finally:
            if await request.is_disconnected():
                CredentialStore().clear_api_keys()

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


def _stream_event(chunk: str) -> dict[str, Any]:
    """Keep structured report chunks separate from streamed markdown text."""

    stripped = chunk.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and payload.get("type") in {"metadata", "chart"}:
            return payload
    return {"type": "chunk", "content": chunk}
