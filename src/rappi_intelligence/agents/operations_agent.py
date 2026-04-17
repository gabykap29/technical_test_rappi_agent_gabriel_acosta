"""High-level conversational agent facade."""

from typing import AsyncGenerator

from rappi_intelligence.analytics.query_engine import QueryEngine
from rappi_intelligence.data.loader import load_dataset
from rappi_intelligence.llm.graph_agent import LangGraphOperationsAgent
from rappi_intelligence.llm.providers import (
    LLMConfigurationError,
    build_chat_model,
    load_llm_config,
)
from rappi_intelligence.shared.models import AgentResponse


class RappiOperationsAgent:
    """Stateful agent for operational analytics questions."""

    def __init__(
        self,
        data_source: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        require_llm: bool = False,
    ) -> None:
        self.dataset = load_dataset(data_source)
        self.provider = provider
        self.model = model
        self.base_url = base_url
        self.require_llm = require_llm
        self.engine = self._build_engine(provider, model, base_url, require_llm)

    def ask(self, question: str) -> AgentResponse:
        """Answer a business question and keep conversational context."""

        return self.engine.ask(question)

    async def ask_stream(self, question: str) -> AsyncGenerator[str, None]:
        """Stream answer chunks when the selected engine supports it."""

        if hasattr(self.engine, "ask_stream"):
            async for chunk in self.engine.ask_stream(question):
                yield chunk
            return

        # Fallback for deterministic engine without streaming.
        response = self.engine.ask(question)
        if response.answer:
            yield response.answer

    def evidence(self, question: str) -> AgentResponse:
        """Return deterministic evidence table without forcing a full LLM response."""

        if hasattr(self.engine, "tools"):
            return self.engine.tools.ask(question)
        return self.engine.ask(question)

    def starter_questions(self) -> list[str]:
        """Useful questions for non-technical users."""

        return [
            "Cuales son las 5 zonas con mayor Lead Penetration esta semana?",
            "Compara Perfect Order entre zonas Wealthy y Non Wealthy en Mexico",
            "Muestra la evolucion de Gross Profit UE en Chapinero ultimas 8 semanas",
            "Cual es el promedio de Lead Penetration por pais?",
            "Que zonas tienen alto Lead Penetration pero bajo Perfect Order?",
            "Cuales zonas crecen mas en ordenes en las ultimas 5 semanas?",
        ]

    def _build_engine(
        self,
        provider: str | None,
        model: str | None,
        base_url: str | None,
        require_llm: bool,
    ):
        if not provider:
            return QueryEngine(self.dataset)
        try:
            config = load_llm_config(provider, model, base_url=base_url)
            llm = build_chat_model(config)
            return LangGraphOperationsAgent(
                dataset=self.dataset,
                llm=llm,
                provider=config.provider,
                model=config.model,
            )
        except LLMConfigurationError:
            if require_llm:
                raise
            return QueryEngine(self.dataset)
