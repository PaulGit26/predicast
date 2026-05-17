"""Forecast service pipeline integration.

Este módulo conecta el servicio FastAPI con el pipeline ML existente
ubicado en el orquestador Prefect.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.orchestrator.prefect.pipeline_flow import pipeline_flow

logger = logging.getLogger(__name__)


def run_forecast_training_pipeline(base_dir: str | None = None) -> dict[str, Any]:
    """Ejecuta el pipeline de forecast y devuelve un resumen simple."""
    repo_root = Path(base_dir) if base_dir else Path(__file__).resolve().parents[3]
    logger.info("Starting forecast training pipeline from %s", repo_root)

    try:
        pipeline_flow(str(repo_root))
    except Exception as exc:
        logger.exception("Forecast training pipeline failed: %s", exc)
        raise

    output_dir = repo_root / "04_Scripts_Nuevos" / "EDA_Outputs"
    return {
        "status": "success",
        "output_dir": str(output_dir),
        "reporte": str(repo_root / "04_Scripts_Nuevos" / "REPORTE_OPTIMIZACION_HIPERPARAMETROS.json"),
    }
