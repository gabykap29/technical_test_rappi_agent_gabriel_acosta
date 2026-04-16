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
    max_tokens: int | None = None
    top_p: float | None = None
    request_timeout: int | None = 120
    base_url: str | None = None


class LLMConfigurationError(ValueError):
    """Raised when an LLM provider cannot be configured."""


def load_llm_config(
    provider: str,
    model: str | None = None,
    store: CredentialStore | None = None,
    base_url: str | None = None,
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
    configured_base_url = base_url or credential_store.get_base_url(provider)
    return LLMConfig(
        provider=provider,
        model=configured_model,
        api_key=api_key,
        base_url=configured_base_url,
    )


def build_chat_model(config: LLMConfig) -> Any:
    """Build the LangChain chat model for the selected provider."""

    provider_name = config.provider.strip().upper()
    base_kwargs = {"temperature": config.temperature}

    if provider_name == "GEMINI":
        if not config.api_key:
            _raise_missing_key(config.provider)
        from langchain_google_genai import ChatGoogleGenerativeAI

        model_kwargs = _with_optional_params(
            base_kwargs,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            request_timeout=config.request_timeout,
        )
        return ChatGoogleGenerativeAI(
            google_api_key=config.api_key,
            model=config.model,
            **model_kwargs,
        )

    if provider_name == "OLLAMA":
        from langchain_ollama import ChatOllama

        base_url = config.base_url or "http://localhost:11434"
        kwargs: dict[str, Any] = {
            "base_url": base_url,
            "model": config.model,
            "temperature": config.temperature,
        }
        if config.api_key:
            kwargs["client_kwargs"] = {
                "headers": {"Authorization": f"Bearer {config.api_key}"}
            }
        return ChatOllama(**kwargs)

    if provider_name == "ANTHROPIC":
        if not config.api_key:
            _raise_missing_key(config.provider)
        from langchain_anthropic import ChatAnthropic

        model_kwargs = _with_optional_params(
            base_kwargs,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            request_timeout=config.request_timeout,
        )
        return ChatAnthropic(
            api_key=config.api_key,
            model=config.model,
            **model_kwargs,
        )

    if provider_name == "OPENAI":
        if not config.api_key:
            _raise_missing_key(config.provider)
        from langchain_openai import ChatOpenAI

        model_kwargs = _with_optional_params(
            base_kwargs,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            request_timeout=config.request_timeout,
        )
        return ChatOpenAI(
            api_key=config.api_key,
            model=config.model,
            **model_kwargs,
        )

    raise LLMConfigurationError(f"Unsupported provider: {config.provider}")


def _with_optional_params(
    model_kwargs: dict[str, Any],
    max_tokens: int | None,
    top_p: float | None,
    request_timeout: int | None,
) -> dict[str, Any]:
    params = model_kwargs.copy()
    if max_tokens is not None:
        params["max_tokens"] = max_tokens
    if top_p is not None:
        params["top_p"] = top_p
    if request_timeout is not None:
        params["request_timeout"] = request_timeout
    return params


def _raise_missing_key(provider: str) -> None:
    raise LLMConfigurationError(
        f"No encrypted API key configured for {provider}. "
        "Add it from the Streamlit sidebar or CLI before asking the LLM agent."
    )
