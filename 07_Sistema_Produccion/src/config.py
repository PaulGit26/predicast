"""
Configuración centralizada del sistema Predicast.
Carga variables de entorno con pydantic-settings para type-safety.
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from pathlib import Path
import os

class Settings(BaseSettings):
    """Configuración global del sistema."""
    
    # ===== APPLICATION =====
    APP_NAME: str = "Predicast v5"
    APP_VERSION: str = "5.0.0"
    ENV: str = os.getenv("ENV", "development")  # development, staging, production
    DEBUG: bool = ENV == "development"
    
    # ===== API =====
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "http://localhost:8000",
    ]
    
    # ===== DATABASE =====
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost/predicast_dev"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = DEBUG
    
    # ===== CACHE (Redis) =====
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_CACHE_TTL: int = 3600  # 1 hora
    
    # ===== AUTHENTICATION =====
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # ===== AWS S3 =====
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_MODELS: str = "predicast-models"
    S3_BUCKET_DATA: str = "predicast-data"
    
    # ===== ML / MLFLOW =====
    MLFLOW_TRACKING_URI: str = os.getenv(
        "MLFLOW_TRACKING_URI",
        "http://localhost:5000"
    )
    MODEL_REGISTRY: str = "mlflow"  # mlflow, local, s3
    MODEL_VERSION_PRODUCTION: str = "production"
    
    # ===== OBSERVABILITY =====
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO" if not DEBUG else "DEBUG")
    LOG_FORMAT: str = "json"  # json, text
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    ENABLE_TRACING: bool = ENV == "production"
    
    # ===== DATA =====
    DATA_DIR: str = os.getenv(
        "DATA_DIR",
        str(Path(__file__).parents[2] / "01_Datos")
    )

    # ===== PREFECT (Orchestration) =====
    PREFECT_API_URL: str = os.getenv("PREFECT_API_URL", "http://localhost:4200/api")
    
    # ===== RAY (Distributed Computing) =====
    RAY_CLUSTER_HEAD: str = os.getenv("RAY_CLUSTER_HEAD", "127.0.0.1")
    RAY_CLUSTER_PORT: int = 6379
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Instancia global
settings = Settings()
