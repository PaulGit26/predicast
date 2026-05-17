from fastapi import APIRouter
from typing import List
from datetime import datetime
import uuid

from src.shared.contracts.schemas import (
    ForecastRequestInput,
    ForecastResponse,
    ForecastPoint,
    ConfidenceInterval,
    RecommendationResponse,
    ProductionRecommendation,
    RecommendationLevel,
)

router = APIRouter()


@router.post("/forecast/predict", response_model=ForecastResponse)
async def predict(req: ForecastRequestInput):
    """Genera una predicción dummy para desarrollo.
    Reemplazar por lógica real de inferencia que use MLflow y cache Redis.
    """
    forecasts: List[ForecastPoint] = []
    base = 100.0
    for i in range(1, req.periods + 1):
        forecasts.append(ForecastPoint(period=i, forecast=base + i))

    resp = ForecastResponse(
        request_id=str(uuid.uuid4()),
        product_id=req.product_id,
        forecast_date=datetime.utcnow(),
        forecasts=forecasts,
        model_version="dev-0.1",
        model_accuracy=0.0,
        cache_hit=False,
    )
    return resp


@router.post("/forecast/recommend", response_model=RecommendationResponse)
async def recommend(req: ForecastRequestInput):
    """Genera recomendaciones de producción simples basadas en la predicción.
    Reemplazar por la lógica de recomendador real.
    """
    # Simple mapping: normal = last point forecast, optimistic = +10%, pessimist = -10%
    normal_qty = 150.0
    recommendations = {
        RecommendationLevel.NORMAL: ProductionRecommendation(
            level=RecommendationLevel.NORMAL,
            quantity=normal_qty,
            confidence=0.9,
            reasoning="Baseline recommendation (dev)",
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
