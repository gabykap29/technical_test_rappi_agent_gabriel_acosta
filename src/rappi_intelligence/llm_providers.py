"""LangChain chat model factory for supported providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rappi_intelligence.config import DEFAULT_PROVIDER_MODELS
from rappi_intelligence.credentials import CredentialStore

SUPPORTED_PROVIDERS = ("openai", "anthropic", "gemini", "ollama")


@dataclass(frozen=True)
class LLMConfig:
    """Runtime LLM provider configuration."""

    provider: str
    model: str
    api_key: str | None = None
    temperature: float = 0.1


class LLMConfigurationError(ValueError):
    """Raised when an LLM provider cannot be configured."""


def load_llm_config(
    provider: str,
    model: str | None = None,
    store: CredentialStore | None = None,
) -> LLMConfig:
    """Load provider model and API key from encrypted storage."""

    provider = provider.lower().strip()
    if provider not in SUPPORTED_PROVIDERS:
        raise LLMConfigurationError(
            f"Unsupported provider '{provider}'. Use one of: "
            f"{', '.join(SUPPORTED_PROVIDERS)}."
        )

    credential_store = store or CredentialStore()
    configured_model = model or credential_store.get_model(provider)
    configured_model = configured_model or DEFAULT_PROVIDER_MODELS[provider]
    api_key = credential_store.get_api_key(provider)
    return LLMConfig(provider=provider, model=configured_model, api_key=api_key)


def build_chat_model(config: LLMConfig) -> Any:
    """Build the LangChain chat model for the selected provider."""

    provider = config.provider.lower().strip()
    if provider == "openai":
        if not config.api_key:
            _raise_missing_key(provider)
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
        )

    if provider == "anthropic":
        if not config.api_key:
            _raise_missing_key(provider)
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
        )

    if provider == "gemini":
        if not config.api_key:
            _raise_missing_key(provider)
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=config.model,
            google_api_key=config.api_key,
            temperature=config.temperature,
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=config.model, temperature=config.temperature)

    raise LLMConfigurationError(f"Unsupported provider: {provider}")


def _raise_missing_key(provider: str) -> None:
    raise LLMConfigurationError(
        f"No encrypted API key configured for {provider}. "
        "Add it from the Streamlit sidebar or CLI before asking the LLM agent."
    )
