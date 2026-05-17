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
    from fastapi import APIRouter, HTTPException
    from typing import List
    from datetime import datetime
    import uuid
    import json
    import os

    from src.shared.contracts.schemas import (
        ForecastRequestInput,
        ForecastResponse,
        ForecastPoint,
        RecommendationResponse,
        ProductionRecommendation,
        RecommendationLevel,
    )

    from src.ml.inference.mlflow_loader import MLFlowLoader
    from src.ml.predictor import XGBoostPredictor
    from src.config import settings

    try:
        import redis.asyncio as aioredis
    except Exception:
        aioredis = None

    router = APIRouter()


    def _cache_key(product_id: str, periods: int) -> str:
        return f"forecast:{product_id}:p{periods}"


    @router.post("/forecast/predict", response_model=ForecastResponse)
    async def predict(req: ForecastRequestInput):
        """Predicción con cache Redis y modelo desde MLflow/joblib.

        Flujo:
        - Comprueba cache (Redis) por key
        - Si hit -> devuelve el valor cached
        - Si miss -> carga modelo (MLflow preferred), ejecuta predictor, guarda en Redis
        """
        key = _cache_key(req.product_id, req.periods)

        # Try cache
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
                # If redis fails, continue to compute
                r = None

        # Load model (MLflow preferred)
        loader = MLFlowLoader(mlflow_model_uri=os.getenv("MLFLOW_MODEL_URI"))
        predictor = XGBoostPredictor(loader)

        # Prepare input dictionary for predictor (minimal example)
        input_data = {"product_id": req.product_id, "periods": req.periods}
        result = predictor.predict(input_data)

        # Convert to ForecastResponse-like structure (simple mapping)
        forecast_point = ForecastPoint(period=1, forecast=float(result.get("prediction", 0.0)))
        resp = ForecastResponse(
            request_id=str(uuid.uuid4()),
            product_id=req.product_id,
            forecast_date=datetime.utcnow(),
            forecasts=[forecast_point],
            model_version=result.get("model_version", "unknown"),
            model_accuracy=result.get("mae_test", 0.0),
            cache_hit=False,
        )

        # Cache the response
        if r is not None:
            try:
                await r.set(key, resp.json(), ex=settings.REDIS_CACHE_TTL)
            except Exception:
                pass

        return resp


    @router.post("/forecast/recommend", response_model=RecommendationResponse)
    async def recommend(req: ForecastRequestInput):
        # Simple recommender delegating to predict then mapping
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
