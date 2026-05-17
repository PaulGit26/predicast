"""
Contratos OpenAPI compartidos entre todos los servicios.
Esquemas Pydantic para validación de requests/responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from enum import Enum


# ===== MODELOS COMUNES =====

class OrgBase(BaseModel):
    """Organización base."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class OrgResponse(OrgBase):
    """Respuesta de organización."""
    id: str
    created_at: datetime
    updated_at: datetime


class UserBase(BaseModel):
    """Usuario base."""
    email: str = Field(..., regex=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
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
    category: Optional[str] = None


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
    confidence_interval: Optional[ConfidenceInterval] = None
    components: Optional[Dict[str, Any]] = None


class ForecastResponse(BaseModel):
    """Respuesta de predicción."""
    request_id: str
    product_id: str
    forecast_date: datetime
    forecasts: List[ForecastPoint]
    model_version: str
    model_accuracy: float
    cache_hit: bool


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
    reasoning: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Respuesta de recomendación."""
    product_id: str
    recommendation_date: datetime
    recommendations: Dict[RecommendationLevel, ProductionRecommendation]


# ===== ANALYTICS SERVICE CONTRACTS =====

class MetricPoint(BaseModel):
    """Un punto de métrica temporal."""
    timestamp: datetime
    value: float
    dimensions: Optional[Dict[str, str]] = None


class TimeSeriesResponse(BaseModel):
    """Serie temporal."""
    metric_name: str
    product_id: str
    data_points: List[MetricPoint]
    aggregation_level: str = "daily"  # daily, weekly, monthly


class DashboardMetrics(BaseModel):
    """Métricas para dashboard."""
    total_forecast_accuracy: float
    avg_cache_hit_rate: float
    model_retraining_frequency: str
    last_model_update: datetime
    system_health: Dict[str, Any]


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
    dependencies: Dict[str, str]  # name -> status


# ===== ERROR RESPONSES =====

class ErrorDetail(BaseModel):
    """Detalle de error."""
    code: str
    message: str
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Response de error."""
    error: ErrorDetail
    timestamp: datetime
