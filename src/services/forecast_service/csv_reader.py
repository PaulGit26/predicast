"""
Reads pre-computed forecasts from the pipeline output CSV.
Used as primary data source; ML model is the fallback for unseen products.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_PREDICTIONS_FILE = "predicciones_52semanas_largo_V4.csv"

# Module-level in-memory cache (populated on first call, lives for process lifetime)
_cache: Dict[str, List[dict]] = {}


def _normalize(product_id: str) -> str:
    return product_id.replace(" ", "").upper()


def _load(csv_path: Path) -> Dict[str, List[dict]]:
    global _cache
    if _cache:
        return _cache

    result: Dict[str, List[dict]] = {}
    try:
        with open(csv_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = _normalize(row["Producto_codigo"])
                period = int(row["Semana"].replace("W+", ""))
                result.setdefault(pid, []).append({
                    "period": period,
                    "forecast": float(row["Prediccion"]),
                    "lower": float(row["Lower_Bound_95"]),
                    "upper": float(row["Upper_Bound_95"]),
                })
        # Sort each product's rows by period
        for pid in result:
            result[pid].sort(key=lambda x: x["period"])
        _cache = result
        logger.info("Loaded predictions CSV: %d products from %s", len(result), csv_path)
    except FileNotFoundError:
        logger.warning("Predictions CSV not found at %s — falling back to ML model", csv_path)
    except Exception as exc:
        logger.warning("Could not parse predictions CSV %s: %s", csv_path, exc)

    return result


def get_csv_forecasts(product_id: str, periods: int, data_dir: str) -> Optional[List[dict]]:
    """
    Return up to `periods` forecast dicts for `product_id` from the CSV, or None if unavailable.
    Each dict: {period, forecast, lower, upper}
    """
    csv_path = Path(data_dir) / _PREDICTIONS_FILE
    predictions = _load(csv_path)
    points = predictions.get(_normalize(product_id))
    if not points:
        return None
    return points[:periods]


def invalidate_cache() -> None:
    """Force reload on next call (call after pipeline re-run)."""
    global _cache
    _cache = {}
