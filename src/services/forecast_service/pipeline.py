"""Forecast service pipeline integration.

Este módulo conecta el servicio FastAPI con el pipeline ML existente
ubicado en el orquestador Prefect.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    from src.orchestrator.prefect.pipeline_flow import pipeline_flow as _pipeline_flow
except ImportError:
    try:
        import sys
        from pathlib import Path as _Path
        sys.path.insert(0, str(_Path(__file__).resolve().parents[3] / "orchestrator"))
        from prefect.pipeline_flow import pipeline_flow as _pipeline_flow
    except ImportError:
        _pipeline_flow = None

logger = logging.getLogger(__name__)


def run_forecast_training_pipeline(base_dir: str | None = None) -> dict[str, Any]:
    """Ejecuta el pipeline de forecast y devuelve un resumen simple."""
    repo_root = Path(base_dir) if base_dir else Path(__file__).resolve().parents[3]
    logger.info("Starting forecast training pipeline from %s", repo_root)

    if _pipeline_flow is None:
        raise RuntimeError("Prefect pipeline flow not available in this environment")
    try:
        _pipeline_flow(str(repo_root))
    except Exception as exc:
        logger.exception("Forecast training pipeline failed: %s", exc)
        raise

    output_dir = repo_root / "04_Scripts_Nuevos" / "EDA_Outputs"
    return {
        "status": "success",
        "output_dir": str(output_dir),
        "reporte": str(repo_root / "04_Scripts_Nuevos" / "REPORTE_OPTIMIZACION_HIPERPARAMETROS.json"),
    }
