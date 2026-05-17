"""
Configuración centralizada de logging con structlog.
Soporta JSON y texto con trazabilidad por request_id.
"""

import logging
import structlog
import sys
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
from src.config import settings


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configura logging estructurado con structlog y python-json-logger.
    """
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Handler con formato JSON o texto
    handler = logging.StreamHandler(sys.stdout)
    
    if settings.LOG_FORMAT == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> structlog.PrintLogger:
    """Obtiene un logger estructurado por nombre."""
    return structlog.get_logger(name)


class RequestIDMiddleware:
    """
    Middleware que agrega un request_id único a cada request
    para trazabilidad en logs.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        import uuid
        scope["request_id"] = str(uuid.uuid4())
        await self.app(scope, receive, send)


# Inicializar logging al importar
configure_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)
