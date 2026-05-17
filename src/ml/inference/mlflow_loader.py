"""
Loader que intenta obtener el modelo desde MLflow Registry o desde un path local (joblib).
Provee una interfaz similar a ModelLoader para compatibilidad.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Tuple

try:
    import mlflow
    import mlflow.pyfunc
except Exception:  # pragma: no cover - mlflow optional at runtime
    mlflow = None
    mlflow = None

import joblib

logger = logging.getLogger(__name__)


class MLFlowLoader:
    """Carga un modelo desde MLflow o desde una ruta local.

    Configuración esperada (env / config):
    - MLFLOW_MODEL_URI: URI de modelo en MLflow (ej: "models:/predicast_model/Production")
    - MODEL_PATH: ruta local a archivo serializado (joblib)
    - METADATA_PATH: ruta al JSON con metadata
    """

    def __init__(self, mlflow_model_uri: str | None = None, model_path: str | None = None, metadata_path: str | None = None):
        self.mlflow_model_uri = mlflow_model_uri or os.getenv("MLFLOW_MODEL_URI")
        self.model_path = Path(model_path) if model_path else (Path(os.getenv("MODEL_PATH")) if os.getenv("MODEL_PATH") else None)
        self.metadata_path = Path(metadata_path) if metadata_path else (Path(os.getenv("METADATA_PATH")) if os.getenv("METADATA_PATH") else None)
        self.model = None
        self.metadata = None

    def _load_metadata(self) -> dict:
        if self.metadata_path and self.metadata_path.exists():
            try:
                import json
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as exc:
                logger.warning("No se pudo leer metadata: %s", exc)
        return {"model_version": "unknown", "performance": {}}

    def load(self) -> Tuple[Any, dict]:
        """Intenta cargar desde MLflow; si falla, intenta joblib; si falla, devuelve DummyModel."""
        self.metadata = self._load_metadata()

        # Try MLflow
        if self.mlflow_model_uri and mlflow is not None:
            try:
                logger.info("Cargando modelo desde MLflow URI: %s", self.mlflow_model_uri)
                model = mlflow.pyfunc.load_model(self.mlflow_model_uri)
                self.model = model
                logger.info("Modelo MLflow cargado correctamente")
                return model, self.metadata
            except Exception as exc:  # pragma: no cover - runtime errors
                logger.warning("No se pudo cargar modelo desde MLflow %s: %s", self.mlflow_model_uri, exc)

        # Try joblib/local
        if self.model_path and self.model_path.exists():
            try:
                model = joblib.load(self.model_path)
                self.model = model
                logger.info("Modelo cargado desde joblib: %s", self.model_path)
                return model, self.metadata
            except Exception as exc:
                logger.warning("No se pudo cargar modelo joblib %s: %s", self.model_path, exc)

        # Fallback dummy model (self-contained, no external dependency)
        class _DummyModel:
            def predict(self, X):
                try:
                    import numpy as np
                    import pandas as pd
                except Exception:
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

        model = _DummyModel()
        self.model = model
        return model, self.metadata
