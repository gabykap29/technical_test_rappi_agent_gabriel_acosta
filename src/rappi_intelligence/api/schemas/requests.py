"""HTTP request schemas."""

from pydantic import BaseModel, Field


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
