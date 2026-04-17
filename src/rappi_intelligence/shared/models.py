"""Domain models used by the agent and insight engine."""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class AnalyticsDataset:
    """Normalized analytical tables."""

    wide: pd.DataFrame
    long: pd.DataFrame
    metric_dictionary: pd.DataFrame | None = None


@dataclass
class AgentResponse:
    """Response returned by the conversational agent."""

    answer: str
    table: pd.DataFrame | None = None
    chart: Any | None = None
    suggestions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    query: str = ""


@dataclass
class Insight:
    """Structured business insight."""

    category: str
    title: str
    detail: str
    recommendation: str
    severity: str = "medium"
    evidence: dict[str, Any] = field(default_factory=dict)
