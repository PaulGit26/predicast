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

from src.ml.inference.mlflow_loader import MLFlowLoader
from src.services.forecast_service.pipeline import run_forecast_training_pipeline

router = APIRouter()


def _cache_key(product_id: str, periods: int) -> str:
    return f"forecast:{product_id}:p{periods}"


@router.post("/forecast/predict", response_model=ForecastResponse)
async def predict(req: ForecastRequestInput):
    # Attempt to use Redis cache if available
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

    # Load model (MLflow loader has internal fallback)
    model = None
    metadata = {"model_version": "unknown", "performance": {}}
    try:
        loader = MLFlowLoader()
        model, metadata = loader.load()
    except Exception as exc:
        logging.warning("MLFlowLoader failed, using fallback model: %s", exc)

    # Attempt to predict a base value from the loaded model
    base_value = 100.0
    try:
        if model is not None and hasattr(model, "predict"):
            prediction = model.predict([[req.periods]])
            if isinstance(prediction, (list, tuple)) and len(prediction) > 0:
                base_value = float(prediction[0])
            else:
                base_value = float(prediction)
    except Exception as exc:
        logging.warning("Model prediction failed, falling back to deterministic forecast: %s", exc)

    # Build forecast series
    forecasts: List[ForecastPoint] = []
    for p in range(1, req.periods + 1):
        forecasts.append(
            ForecastPoint(
                period=p,
                forecast=base_value + p * 1.0,
                confidence_interval=ConfidenceInterval(
                    lower=base_value + p * 0.9,
                    upper=base_value + p * 1.1,
                    confidence_level=0.95,
                ) if req.include_confidence else None,
            )
        )

    resp = ForecastResponse(
        request_id=str(uuid.uuid4()),
        product_id=req.product_id,
        forecast_date=datetime.utcnow(),
        forecasts=forecasts,
        model_version=str(metadata.get("model_version", "stub")),
        model_accuracy=float(metadata.get("performance", {}).get("accuracy", 0.0)) if metadata else 0.0,
        cache_hit=False,
    )

    if r is not None:
        try:
            await r.set(key, resp.json(), ex=settings.REDIS_CACHE_TTL)
        except Exception:
            pass

    return resp


@router.post("/forecast/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(background_tasks: BackgroundTasks):
    """Trigger the forecast training pipeline in the background."""
    background_tasks.add_task(run_forecast_training_pipeline)
    return PipelineRunResponse(
        status="scheduled",
        message="Pipeline execution has been scheduled.",
        started_at=datetime.utcnow(),
        details={"pipeline": "prefect", "base_dir": str(Path(__file__).resolve().parents[3])},
    )


@router.post("/forecast/recommend", response_model=RecommendationResponse)
async def recommend(req: ForecastRequestInput):
    pred = await predict(req)
    last_forecast = pred.forecasts[-1].forecast if pred.forecasts else 0.0
    normal_qty = float(last_forecast)
    recommendations = {
        RecommendationLevel.NORMAL: ProductionRecommendation(
            level=RecommendationLevel.NORMAL,
            quantity=normal_qty,
            confidence=0.9,
            reasoning="Baseline recommendation",
        ),
        RecommendationLevel.OPTIMISTIC: ProductionRecommendation(
            level=RecommendationLevel.OPTIMISTIC,
            quantity=normal_qty * 1.1,
            confidence=0.6,
            reasoning="Optimistic scenario",
        ),
        RecommendationLevel.PESSIMISTIC: ProductionRecommendation(
            level=RecommendationLevel.PESSIMISTIC,
            quantity=normal_qty * 0.9,
            confidence=0.95,
            reasoning="Pessimistic scenario",
        ),
    }

    resp = RecommendationResponse(
        product_id=req.product_id,
        recommendation_date=datetime.utcnow(),
        recommendations=recommendations,
    )
    return resp
