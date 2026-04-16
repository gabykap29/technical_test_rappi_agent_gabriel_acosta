"""HTTP API for the Next.js frontend."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rappi_intelligence.agent import RappiOperationsAgent
from rappi_intelligence.config import DEFAULT_PROVIDER_MODELS
from rappi_intelligence.credentials import CredentialStore
from rappi_intelligence.llm_providers import SUPPORTED_PROVIDERS, LLMConfigurationError
from rappi_intelligence.reporting import render_markdown_report

app = FastAPI(title="Rappi Operations Intelligence API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProviderRequest(BaseModel):
    """Provider configuration payload."""

    provider: str
    model: str
    api_key: str | None = None
    base_url: str | None = None
    preserve_existing_key: bool = True


class ChatRequest(BaseModel):
    """Chat request payload."""

    question: str = Field(min_length=1)
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    require_llm: bool = True


class ReportRequest(BaseModel):
    """Report request payload."""

    provider: str | None = None
    model: str | None = None
    base_url: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    """Return API health."""

    return {"status": "ok"}


@app.get("/dataset/overview")
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


@app.get("/providers")
def list_providers() -> dict[str, Any]:
    """Return supported providers and saved credential status."""

    saved = CredentialStore().list_providers()
    return {
        "supported": list(SUPPORTED_PROVIDERS),
        "defaultModels": DEFAULT_PROVIDER_MODELS,
        "saved": [credential.__dict__ for credential in saved],
    }


@app.post("/providers")
def save_provider(payload: ProviderRequest) -> dict[str, str]:
    """Save provider settings and encrypted API key."""

    if payload.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    CredentialStore().save_provider(
        provider=payload.provider,
        model=payload.model,
        api_key=payload.api_key,
        base_url=payload.base_url,
        preserve_existing_key=payload.preserve_existing_key,
    )
    return {"status": "saved"}


@app.post("/chat")
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


@app.post("/report")
def report(_: ReportRequest) -> dict[str, str]:
    """Generate the executive report markdown."""

    agent = RappiOperationsAgent()
    return {"markdown": render_markdown_report(agent.dataset)}


def _table_records(table) -> list[dict[str, Any]]:
    if table is None or table.empty:
        return []
    return table.head(100).where(table.notna(), None).to_dict(orient="records")
