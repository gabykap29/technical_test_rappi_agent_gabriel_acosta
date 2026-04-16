"""High-level conversational agent facade."""

from rappi_intelligence.data_loader import load_dataset
from rappi_intelligence.models import AgentResponse
from rappi_intelligence.query_engine import QueryEngine


class RappiOperationsAgent:
    """Stateful agent for operational analytics questions."""

    def __init__(self, data_source: str | None = None) -> None:
        self.dataset = load_dataset(data_source)
        self.engine = QueryEngine(self.dataset)

    def ask(self, question: str) -> AgentResponse:
        """Answer a business question and keep conversational context."""

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
