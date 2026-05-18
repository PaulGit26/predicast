from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List
from datetime import datetime
from pathlib import Path
import uuid
import json
import logging

from src.shared.contracts.schemas import (
    ForecastRequestInput,
    ForecastResponse,
    ForecastPoint,
    ConfidenceInterval,
    RecommendationResponse,
    ProductionRecommendation,
    RecommendationLevel,
    PipelineRunResponse,
)
from src.config import settings
from src.services.forecast_service.csv_reader import get_csv_forecasts, invalidate_cache
from src.ml.inference.mlflow_loader import MLFlowLoader
from src.services.forecast_service.pipeline import run_forecast_training_pipeline

router = APIRouter()

_MODEL_VERSION_CSV = "v4.0"
_MODEL_ACCURACY_CSV = 0.9939


def _cache_key(product_id: str, periods: int) -> str:
    return f"forecast:{product_id}:p{periods}"


def _build_forecasts_from_csv(points: List[dict], include_confidence: bool) -> List[ForecastPoint]:
    return [
        ForecastPoint(
            period=p["period"],
            forecast=round(p["forecast"], 2),
            confidence_interval=ConfidenceInterval(
                lower=round(p["lower"], 2),
                upper=round(p["upper"], 2),
                confidence_level=0.95,
            ) if include_confidence else None,
        )
        for p in points
    ]


def _build_forecasts_from_model(model, base_value: float, periods: int, include_confidence: bool) -> List[ForecastPoint]:
    result = []
    for p in range(1, periods + 1):
        val = base_value + p * 1.0
        result.append(
            ForecastPoint(
                period=p,
                forecast=round(val, 2),
                confidence_interval=ConfidenceInterval(
                    lower=round(val * 0.9, 2),
                    upper=round(val * 1.1, 2),
                    confidence_level=0.95,
                ) if include_confidence else None,
            )
        )
    return result


@router.post("/forecast/predict", response_model=ForecastResponse)
async def predict(req: ForecastRequestInput):
    # Redis cache check
    try:
        import redis.asyncio as aioredis
    except Exception:
        aioredis = None

    key = _cache_key(req.product_id, req.periods)
    r = None
    if aioredis is not None:
        try:
            r = aioredis.from_url(settings.REDIS_URL)
            cached = await r.get(key)
            if cached:
                payload = json.loads(cached)
                payload["cache_hit"] = True
                return payload
        except Exception:
            r = None

    # Primary source: pre-computed predictions CSV
    csv_points = get_csv_forecasts(req.product_id, req.periods, settings.DATA_DIR)
    if csv_points:
        forecasts = _build_forecasts_from_csv(csv_points, req.include_confidence)
        model_version = _MODEL_VERSION_CSV
        model_accuracy = _MODEL_ACCURACY_CSV
    else:
        # Fallback: ML model (MLflow → joblib → dummy)
        logging.warning("Product %s not in CSV, falling back to ML model", req.product_id)
        model = None
        metadata: dict = {}
        try:
            loader = MLFlowLoader()
            model, metadata = loader.load()
        except Exception as exc:
            logging.warning("MLFlowLoader failed: %s", exc)

        base_value = 100.0
        try:
            if model is not None and hasattr(model, "predict"):
                prediction = model.predict([[req.periods]])
                base_value = float(prediction[0]) if hasattr(prediction, "__len__") else float(prediction)
        except Exception as exc:
            logging.warning("Model prediction failed, using deterministic fallback: %s", exc)

        forecasts = _build_forecasts_from_model(model, base_value, req.periods, req.include_confidence)
        model_version = str(metadata.get("model_version", "stub"))
        model_accuracy = float(metadata.get("performance", {}).get("accuracy", 0.0)) if metadata else 0.0

    resp = ForecastResponse(
        request_id=str(uuid.uuid4()),
        product_id=req.product_id,
        forecast_date=datetime.utcnow(),
        forecasts=forecasts,
        model_version=model_version,
        model_accuracy=model_accuracy,
        cache_hit=False,
    )

    if r is not None:
        try:
            await r.set(key, resp.model_dump_json(), ex=settings.REDIS_CACHE_TTL)
        except Exception:
            pass

    return resp


@router.post("/forecast/recommend", response_model=RecommendationResponse)
async def recommend(req: ForecastRequestInput):
    pred = await predict(req)
    normal_qty = float(pred.forecasts[-1].forecast) if pred.forecasts else 0.0
    recommendations = {
        RecommendationLevel.NORMAL: ProductionRecommendation(
            level=RecommendationLevel.NORMAL,
            quantity=round(normal_qty, 2),
            confidence=0.9,
            reasoning="Predicción base del modelo XGBoost",
        ),
        RecommendationLevel.OPTIMISTIC: ProductionRecommendation(
            level=RecommendationLevel.OPTIMISTIC,
            quantity=round(normal_qty * 1.1, 2),
            confidence=0.6,
            reasoning="Escenario optimista (+10%)",
        ),
        RecommendationLevel.PESSIMISTIC: ProductionRecommendation(
            level=RecommendationLevel.PESSIMISTIC,
            quantity=round(normal_qty * 0.9, 2),
            confidence=0.95,
            reasoning="Escenario pesimista (-10%)",
        ),
    }
    return RecommendationResponse(
        product_id=req.product_id,
        recommendation_date=datetime.utcnow(),
        recommendations=recommendations,
    )


@router.post("/forecast/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(background_tasks: BackgroundTasks):
    """Trigger the forecast training pipeline and invalidate the predictions cache."""
    def _run_and_invalidate():
        run_forecast_training_pipeline()
        invalidate_cache()

    background_tasks.add_task(_run_and_invalidate)
    return PipelineRunResponse(
        status="scheduled",
        message="Pipeline execution scheduled; cache will refresh on completion.",
        started_at=datetime.utcnow(),
        details={"pipeline": "prefect", "base_dir": str(Path(__file__).resolve().parents[3])},
    )
