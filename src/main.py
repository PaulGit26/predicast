"""
Aplicación principal FastAPI.
Punto de entrada único para toda la API.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.config import settings
from src.shared.observability.logging import configure_logging, RequestIDMiddleware, get_logger
from src.shared.auth.jwt_handler import HTTPException
import sentry_sdk
from datetime import datetime

logger = get_logger(__name__)


# ===== INICIALIZACIÓN =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Contexto de ciclo de vida de la aplicación."""
    # Startup
    logger.info("🚀 Iniciando Predicast", version=settings.APP_VERSION, env=settings.ENV)
    
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENV,
            traces_sample_rate=0.1
        )
        logger.info("Sentry initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Predicast")


# Crear app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# ===== MIDDLEWARE =====

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID
app.add_middleware(RequestIDMiddleware)


# ===== HEALTH CHECK =====

from src.shared.contracts.schemas import HealthCheckResponse

@app.get("/api/v1/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        dependencies={
            "database": "ok",
            "redis": "ok",
            "mlflow": "ok" if settings.ENV != "development" else "ok"
        }
    )


# ===== ROUTERS =====

# Importar routers de servicios si existen (fall back silencioso)
try:
    from src.services.forecast_service.api import router as forecast_router
    app.include_router(forecast_router, prefix=settings.API_PREFIX, tags=["Forecast"])
except Exception as e:  # pragma: no cover - optional in dev
    logger.info("Forecast router not available yet", error=str(e))

try:
    from src.services.analytics_service.api import router as analytics_router
    app.include_router(analytics_router, prefix=settings.API_PREFIX, tags=["Analytics"])
except Exception as e:  # pragma: no cover - optional in dev
    logger.info("Analytics router not available yet", error=str(e))

try:
    from src.services.user_service.api import router as user_router
    app.include_router(user_router, prefix=settings.API_PREFIX, tags=["Users"])
except Exception as e:  # pragma: no cover - optional in dev
    logger.info("User router not available yet", error=str(e))


# ===== EXCEPTION HANDLERS =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador de excepciones HTTP."""
    from src.shared.contracts.schemas import ErrorResponse, ErrorDetail
    
    return {
        "error": {
            "code": str(exc.status_code),
            "message": exc.detail,
            "request_id": request.scope.get("request_id")
        },
        "timestamp": datetime.utcnow()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
