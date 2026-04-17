"""LLM provider configuration routes."""

from typing import Any

from fastapi import APIRouter, HTTPException

from rappi_intelligence.api.schemas.requests import ProviderRequest
from rappi_intelligence.llm.providers import SUPPORTED_PROVIDERS
from rappi_intelligence.security.credentials import CredentialStore
from rappi_intelligence.shared.config import DEFAULT_PROVIDER_MODELS

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
def list_providers() -> dict[str, Any]:
    """Return supported providers and saved credential status."""

    saved = CredentialStore().list_providers()
    return {
        "supported": list(SUPPORTED_PROVIDERS),
        "defaultModels": DEFAULT_PROVIDER_MODELS,
        "saved": [credential.__dict__ for credential in saved],
    }


@router.post("")
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
