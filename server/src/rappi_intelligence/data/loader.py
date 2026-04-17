"""Data loading, schema validation, and reshaping utilities."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

from rappi_intelligence.shared.config import (
    CANONICAL_WEEK_COLUMNS,
    DATA_DIR,
    DEFAULT_EXCEL_PATTERN,
    IDENTIFIER_COLUMNS,
    METRICS_SHEET,
    ORDER_WEEK_COLUMNS,
    ORDERS_SHEET,
    ROLLING_WEEK_COLUMNS,
    SEGMENT_COLUMNS,
)
from rappi_intelligence.shared.models import AnalyticsDataset


class DataValidationError(ValueError):
    """Raised when the provided dataset does not match the expected schema."""


def find_default_workbook(root: Path | None = None) -> Path:
    """Find the first Excel workbook matching the technical-case dataset."""

    search_root = root or Path.cwd()
    candidates = sorted(search_root.glob("*.xlsx"))
    if not candidates:
        candidates = sorted(DATA_DIR.glob("*.xlsx"))
    if not candidates:
        raise FileNotFoundError(
            "No Excel dataset found. Add the Rappi workbook to the project root "
            "or place CSV files under data/."
        )
    preferred = [
        path
        for path in candidates
        if _ascii(path.name).startswith(
            _ascii(DEFAULT_EXCEL_PATTERN).replace("*", "")
        )
    ]
    return preferred[0] if preferred else candidates[0]


def load_dataset(source: Path | str | None = None) -> AnalyticsDataset:
    """Load the workbook or CSV folder into normalized analytical tables."""

    source_path = Path(source) if source else find_default_workbook()
    if source_path.is_dir():
        metrics = pd.read_csv(source_path / "metrics_input.csv")
        orders = pd.read_csv(source_path / "orders.csv")
        dictionary = _read_optional_csv(source_path / "metric_dictionary.csv")
    elif source_path.suffix.lower() in {".xlsx", ".xlsm"}:
        metrics = pd.read_excel(source_path, sheet_name=METRICS_SHEET)
        orders = pd.read_excel(source_path, sheet_name=ORDERS_SHEET)
        dictionary = _read_optional_sheet(source_path, "RAW_SUMMARY")
    else:
        raise DataValidationError(
            f"Unsupported data source {source_path}. Use .xlsx or a CSV folder."
        )

    metrics = normalize_metrics(metrics)
    orders = normalize_orders(orders, metrics)
    wide = _deduplicate_wide(pd.concat([metrics, orders], ignore_index=True))
    long = wide_to_long(wide)
    return AnalyticsDataset(wide=wide, long=long, metric_dictionary=dictionary)


def normalize_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize the operational metrics sheet."""

    metrics = _standardize_columns(metrics)
    required = IDENTIFIER_COLUMNS + SEGMENT_COLUMNS + ["METRIC"] + ROLLING_WEEK_COLUMNS
    _require_columns(metrics, required, "metrics")

    renamed = {
        column: column.replace("_ROLL", "")
        for column in ROLLING_WEEK_COLUMNS
        if column in metrics.columns
    }
    metrics = metrics.rename(columns=renamed)
    return _coerce_week_values(metrics)


def normalize_orders(orders: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    """Validate orders and enrich them with zone segmentation."""

    orders = _standardize_columns(orders)
    required = IDENTIFIER_COLUMNS + ["METRIC"] + ORDER_WEEK_COLUMNS
    _require_columns(orders, required, "orders")

    zone_segments = (
        metrics[IDENTIFIER_COLUMNS + SEGMENT_COLUMNS]
        .drop_duplicates(subset=IDENTIFIER_COLUMNS)
        .copy()
    )
    orders = orders.merge(zone_segments, on=IDENTIFIER_COLUMNS, how="left")
    orders["ZONE_TYPE"] = orders["ZONE_TYPE"].fillna("Unknown")
    orders["ZONE_PRIORITIZATION"] = orders["ZONE_PRIORITIZATION"].fillna("Unknown")
    orders["METRIC"] = "Orders"
    return _coerce_week_values(orders)


def wide_to_long(wide: pd.DataFrame) -> pd.DataFrame:
    """Convert week columns into a long table suitable for analysis."""

    id_columns = IDENTIFIER_COLUMNS + SEGMENT_COLUMNS + ["METRIC"]
    long = wide.melt(
        id_vars=id_columns,
        value_vars=CANONICAL_WEEK_COLUMNS,
        var_name="WEEK",
        value_name="VALUE",
    )
    long["WEEK_INDEX"] = long["WEEK"].str.extract(r"L(\d+)W").astype(int)
    long["WEEK_SORT"] = 8 - long["WEEK_INDEX"]
    return long.sort_values(id_columns + ["WEEK_SORT"]).reset_index(drop=True)


def metric_names(dataset: AnalyticsDataset) -> list[str]:
    """Return sorted metric names available in the dataset."""

    return sorted(dataset.wide["METRIC"].dropna().unique().tolist())


def _read_optional_sheet(path: Path, sheet_name: str) -> pd.DataFrame | None:
    try:
        return pd.read_excel(path, sheet_name=sheet_name)
    except ValueError:
        return None


def _read_optional_csv(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(column).strip().upper() for column in df.columns]
    return df


def _require_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise DataValidationError(f"Missing columns in {name}: {', '.join(missing)}")


def _coerce_week_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column in CANONICAL_WEEK_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.dropna(subset=CANONICAL_WEEK_COLUMNS, how="all").reset_index(drop=True)


def _deduplicate_wide(wide: pd.DataFrame) -> pd.DataFrame:
    group_columns = IDENTIFIER_COLUMNS + SEGMENT_COLUMNS + ["METRIC"]
    return (
        wide.groupby(group_columns, dropna=False)[CANONICAL_WEEK_COLUMNS]
        .mean()
        .reset_index()
    )


def _ascii(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    plain = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", plain).lower().strip()
