"""Project configuration and shared constants."""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
SECRETS_DIR = ROOT_DIR / ".secrets"
FERNET_KEY_PATH = SECRETS_DIR / "fernet.key"
SECRETS_DB_PATH = SECRETS_DIR / "credentials.sqlite"
CONVERSATIONS_DB_PATH = SECRETS_DIR / "conversations.sqlite"

DEFAULT_EXCEL_PATTERN = (
    "Sistema de Analisis Inteligente para Operaciones Rappi - Dummy Data*.xlsx"
)
METRICS_SHEET = "RAW_INPUT_METRICS"
ORDERS_SHEET = "RAW_ORDERS"

IDENTIFIER_COLUMNS = [
    "COUNTRY",
    "CITY",
    "ZONE",
]

SEGMENT_COLUMNS = [
    "ZONE_TYPE",
    "ZONE_PRIORITIZATION",
]

ROLLING_WEEK_COLUMNS = [f"L{week}W_ROLL" for week in range(8, -1, -1)]
ORDER_WEEK_COLUMNS = [f"L{week}W" for week in range(8, -1, -1)]
CANONICAL_WEEK_COLUMNS = [f"L{week}W" for week in range(8, -1, -1)]

POSITIVE_METRICS = {
    "% PRO Users Who Breakeven",
    "% Restaurants Sessions With Optimal Assortment",
    "Gross Profit UE",
    "Lead Penetration",
    "MLTV Top Verticals Adoption",
    "Non-Pro PTC > OP",
    "Perfect Orders",
    "Pro Adoption",
    "Restaurants SS > ATC CVR",
    "Restaurants SST > SS CVR",
    "Retail SST > SS CVR",
    "Turbo Adoption",
    "Orders",
}

NEGATIVE_METRICS = {
    "Restaurants Markdowns / GMV",
}

METRIC_ALIASES = {
    "lead": "Lead Penetration",
    "lead penetration": "Lead Penetration",
    "perfect order": "Perfect Orders",
    "perfect orders": "Perfect Orders",
    "gross profit": "Gross Profit UE",
    "gross profit ue": "Gross Profit UE",
    "orders": "Orders",
    "ordenes": "Orders",
    "pro adoption": "Pro Adoption",
    "turbo": "Turbo Adoption",
    "markdowns": "Restaurants Markdowns / GMV",
    "conversion": "Non-Pro PTC > OP",
}

DEFAULT_PROVIDER_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "gemini": "gemini-1.5-flash",
    "ollama": "llama3.1",
}

CLOUD_MODE = os.getenv("CLOUD", "false").lower() == "true"
