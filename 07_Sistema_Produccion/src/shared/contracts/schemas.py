"""
Contratos OpenAPI compartidos entre todos los servicios.
Esquemas Pydantic para validación de requests/responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ===== MODELOS COMUNES =====

class OrgBase(BaseModel):
    """Organización base."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class OrgResponse(OrgBase):
    """Respuesta de organización."""
    id: str
    created_at: datetime
    updated_at: datetime


class UserBase(BaseModel):
    """Usuario base."""
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    full_name: str = Field(..., min_length=1, max_length=255)


class UserResponse(UserBase):
    """Respuesta de usuario."""
    id: str
    org_id: str
    created_at: datetime
    updated_at: datetime


# ===== FORECAST SERVICE CONTRACTS =====

class ForecastProductBase(BaseModel):
    """Producto para predicción."""
    product_code: str = Field(..., description="Código SKU del producto")
    product_name: str
    category: str | None = None


class ForecastRequestInput(BaseModel):
    """Request para predicción."""
    product_id: str
    periods: int = Field(default=52, ge=1, le=365, description="Semanas a predecir")
    include_confidence: bool = True
    include_components: bool = False


class ConfidenceInterval(BaseModel):
    """Intervalo de confianza."""
    lower: float
    upper: float
    confidence_level: float = 0.95


class ForecastPoint(BaseModel):
    """Un punto de predicción."""
    period: int
    forecast: float
    confidence_interval: ConfidenceInterval | None = None
    components: dict[str, Any] | None = None


class ForecastResponse(BaseModel):
    """Respuesta de predicción."""
    request_id: str
    product_id: str
    forecast_date: datetime
    forecasts: list[ForecastPoint]
    model_version: str
    model_accuracy: float
    cache_hit: bool


class PipelineRunResponse(BaseModel):
    """Respuesta de ejecución de pipeline."""
    status: str
    message: str
    started_at: datetime
    details: dict[str, Any] | None = None


class RecommendationLevel(str, Enum):
    """Niveles de recomendación."""
    PESSIMISTIC = "pessimistic"
    NORMAL = "normal"
    OPTIMISTIC = "optimistic"


class ProductionRecommendation(BaseModel):
    """Recomendación de producción."""
    level: RecommendationLevel
    quantity: float
    confidence: float
    reasoning: str | None = None


class RecommendationResponse(BaseModel):
    """Respuesta de recomendación."""
    product_id: str
    recommendation_date: datetime
    recommendations: dict[RecommendationLevel, ProductionRecommendation]


# ===== ANALYTICS SERVICE CONTRACTS =====

class MetricPoint(BaseModel):
    """Un punto de métrica temporal."""
    timestamp: datetime
    value: float
    dimensions: dict[str, str] | None = None


class TimeSeriesResponse(BaseModel):
    """Serie temporal."""
    metric_name: str
    product_id: str
    data_points: list[MetricPoint]
    aggregation_level: str = "daily"  # daily, weekly, monthly


class DashboardMetrics(BaseModel):
    """Métricas para dashboard."""
    total_forecast_accuracy: float
    avg_cache_hit_rate: float
    model_retraining_frequency: str
    last_model_update: datetime
    system_health: dict[str, Any]


# ===== USER SERVICE CONTRACTS =====

class LoginRequest(BaseModel):
    """Request de login."""
    email: str
    password: str


class LoginResponse(BaseModel):
    """Response de login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class RegistrationRequest(BaseModel):
    """Request de registro."""
    email: str
    password: str = Field(..., min_length=8)
    full_name: str
    org_name: str


class RegistrationResponse(BaseModel):
    """Response de registro."""
    user: UserResponse
    org: OrgResponse
    access_token: str


# ===== HEALTH CHECK =====

class HealthCheckResponse(BaseModel):
    """Respuesta de health check."""
    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    timestamp: datetime
    dependencies: dict[str, str]  # name -> status


# ===== ERROR RESPONSES =====

class ErrorDetail(BaseModel):
    """Detalle de error."""
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Response de error."""
    error: ErrorDetail
    timestamp: datetime
