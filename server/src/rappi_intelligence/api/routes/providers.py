"""LLM provider configuration routes."""

from typing import Any

from fastapi import APIRouter, HTTPException

from rappi_intelligence.api.schemas.requests import ProviderRequest
from rappi_intelligence.llm.providers import SUPPORTED_PROVIDERS
from rappi_intelligence.security.credentials import CredentialStore
from rappi_intelligence.shared.config import CLOUD_MODE, DEFAULT_PROVIDER_MODELS

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
def list_providers() -> dict[str, Any]:
    """Return supported providers and saved credential status."""

    saved = CredentialStore().list_providers()
    supported = [
        provider
        for provider in SUPPORTED_PROVIDERS
        if not (CLOUD_MODE and provider == "ollama")
    ]
    default_models = {
        provider: model
        for provider, model in DEFAULT_PROVIDER_MODELS.items()
        if provider in supported
    }
    return {
        "supported": supported,
        "defaultModels": default_models,
        "saved": [
            credential.__dict__
            for credential in saved
            if credential.provider in supported
        ],
    }


@router.post("")
def save_provider(payload: ProviderRequest) -> dict[str, str]:
    """Save provider settings and encrypted API key."""

    if payload.provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=400, detail="Unsupported provider")
    if CLOUD_MODE and payload.provider == "ollama":
        raise HTTPException(
            status_code=400,
            detail="Ollama is disabled when CLOUD=true",
        )
    CredentialStore().save_provider(
        provider=payload.provider,
        model=payload.model,
        api_key=payload.api_key,
        base_url=payload.base_url,
        preserve_existing_key=payload.preserve_existing_key,
    )
    return {"status": "saved"}


@router.post("/clear")
def clear_provider_api_keys() -> dict[str, int | str]:
    """Remove encrypted provider API keys from local storage."""

    cleared = CredentialStore().clear_api_keys()
    return {"status": "cleared", "cleared": cleared}
