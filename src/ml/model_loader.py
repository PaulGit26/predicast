"""Model loading helpers for PREDICAST.

This module keeps the system runnable even when the serialized model files
are not available. In that case, a lightweight dummy model is returned.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Tuple

import joblib

logger = logging.getLogger(__name__)


class DummyModel:
    """Fallback model used when the serialized model cannot be loaded."""

    def predict(self, X: Any):
        try:
            import numpy as np
            import pandas as pd
        except Exception:  # pragma: no cover
            np = None
            pd = None

        if pd is not None and isinstance(X, pd.DataFrame):
            numeric = X.select_dtypes(include=["number"])
            if numeric.empty:
                return [0.0] * len(X)
            values = numeric.to_numpy(dtype=float)
            return list(values.sum(axis=1) * 0.1)

        if np is not None:
            arr = np.asarray(X, dtype=float)
            if arr.ndim == 1:
                return [float(arr.sum()) * 0.1]
            return list(arr.sum(axis=1) * 0.1)

        if isinstance(X, list):
            return [float(sum(row)) * 0.1 if isinstance(row, (list, tuple)) else float(row) * 0.1 for row in X]

        return [0.0]


class ModelLoader:
    """Carga un modelo serializado y su metadata."""

    def __init__(self, model_path: str, metadata_path: str):
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)
        self.model = None
        self.metadata = None

    def _load_metadata(self) -> dict:
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    if isinstance(metadata, dict):
                        return metadata
            except Exception as exc:
                logger.warning("No se pudo leer metadata desde %s: %s", self.metadata_path, exc)

        return {
            "version": "dummy-model",
            "model_version": "dummy-model",
            "n_features": 0,
            "target": "Demand",
            "performance": {"R2_Test": 0.0, "MAE_Test": 0.0, "RMSE_Test": 0.0},
            "features": [],
        }

    def load(self) -> Tuple[Any, dict]:
        metadata = self._load_metadata()

        model = None
        if self.model_path.exists():
            try:
                model = joblib.load(self.model_path)
                logger.info("✅ Modelo cargado desde %s", self.model_path)
            except Exception as exc:
                logger.warning(
                    "No se pudo cargar el modelo desde %s, usando DummyModel: %s",
                    self.model_path,
                    exc,
                )
                model = DummyModel()
        else:
            logger.warning("Modelo no encontrado en %s, usando DummyModel", self.model_path)
            model = DummyModel()

        metadata.setdefault("model_version", metadata.get("version", "dummy-model"))
        metadata.setdefault("n_features", 0)
        metadata.setdefault("target", "Demand")
        metadata.setdefault("performance", {"R2_Test": 0.0, "MAE_Test": 0.0, "RMSE_Test": 0.0})
        metadata.setdefault("features", [])

        self.model = model
        self.metadata = metadata
        return model, metadata
