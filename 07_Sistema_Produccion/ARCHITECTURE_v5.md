# Predicast v5 - Arquitectura Modular

## Estructura del Proyecto

```
07_Sistema_Produccion/
├── src/
│   ├── main.py                      # Aplicación FastAPI principal
│   ├── config.py                    # Configuración centralizada
│   ├── services/
│   │   ├── forecast_service/        # Servicio de predicción
│   │   ├── analytics_service/       # Servicio de analytics
│   │   └── user_service/            # Servicio de usuarios y autenticación
│   ├── shared/
│   │   ├── contracts/
│   │   │   └── schemas.py           # Esquemas Pydantic compartidos (OpenAPI)
│   │   ├── auth/
│   │   │   └── jwt_handler.py       # Utilidades JWT y RBAC
│   │   └── observability/
│   │       └── logging.py           # Logging estructurado con structlog
│   ├── ml/
│   │   ├── training/                # Pipelines de entrenamiento (Prefect)
│   │   ├── inference/               # Inferencia y scoring
│   │   └── feature_store/           # Gestión de features (Feast)
│   └── orchestrator/
│       ├── prefect_flows/           # Flujos de orquestación Prefect
│       └── ray_jobs/                # Jobs distribuidos con Ray
├── infra/
│   ├── terraform/                   # IaC para AWS
│   └── kubernetes/                  # Manifiestos K8s (EKS)
├── .github/
│   └── workflows/
│       └── ci_cd.yml                # Pipeline CI/CD
├── requirements.txt                 # Dependencias Python
├── .env.example                     # Ejemplo de configuración
└── README.md
```

## Tech Stack

### Backend
- **FastAPI**: Framework API moderno, tipo-seguro
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Pydantic**: Validación de datos y schemas

### Datos
- **PostgreSQL**: Base de datos transaccional
- **Redis**: Cache de predicciones (TTL)
- **S3**: Almacenamiento de modelos y datasets

### ML & Orquestación
- **MLflow**: Registro y versionado de modelos
- **Prefect**: Orquestación de pipelines
- **Ray**: Procesamiento distribuido
- **Feat**: Feature Store

### Observabilidad
- **Structlog**: Logging estructurado
- **Sentry**: Error tracking
- **OpenTelemetry**: Tracing distribuido (futuro)

### DevOps
- **Docker**: Containerización
- **Kubernetes (EKS)**: Orquestación de contenedores
- **GitHub Actions**: CI/CD
- **Terraform**: IaC

## Setup Local

### Requisitos
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Instalación

```bash
cd 07_Sistema_Produccion

# Crear environment virtual
python -m venv venv
source venv/bin/activate  # o `venv\Scripts\activate` en Windows

# Instalar dependencias
pip install -r requirements.txt

# Copiar configuración
cp .env.example .env

# Actualizar .env con tus valores
# DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, AWS_*, etc.
```

### Ejecutar localmente

```bash
# API (puerto 8000)
uvicorn src.main:app --reload

# En otra terminal, ejecutar un servicio específico:
# python -m src.services.forecast_service.main
```

## Estructura de Servicios

Cada servicio (forecast, analytics, user) sigue esta estructura:

```
service_name/
├── __init__.py
├── main.py              # Punto de entrada del servicio
├── router.py            # Endpoints REST
├── schemas.py           # Esquemas Pydantic (si difieren de shared)
├── models.py            # Modelos de base de datos
├── dependencies.py      # Inyección de dependencias
└── tests/
    └── test_*.py        # Tests unitarios
```

## API Endpoints

### Health Check
- `GET /api/v1/health` - Estado del sistema

### Forecast (TBD)
- `POST /api/v1/forecast/predict` - Predicción
- `POST /api/v1/forecast/recommend` - Recomendación de producción

### Analytics (TBD)
- `GET /api/v1/analytics/metrics` - Métricas

### Users (TBD)
- `POST /api/v1/users/register` - Registro
- `POST /api/v1/users/login` - Login

## Configuración

Clave: `src/config.py` con Pydantic Settings.

Variables principales:
- `ENV`: development, staging, production
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret para tokens (cambiar en producción)
- `AWS_*`: Credenciales para S3, etc.
- `MLFLOW_TRACKING_URI`: URL del servidor MLflow
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR

## Testing

```bash
# Todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html

# Tests específicos
pytest tests/test_forecast_service.py -v
```

## CI/CD

Pipeline automático en GitHub Actions (`.github/workflows/ci_cd.yml`):
1. **Lint**: ruff
2. **Type Check**: mypy
3. **Tests**: pytest
4. **Security**: Safety
5. **Build & Push**: Docker image (en main branch)

## Próximos Pasos

Fase 0 (3-5 días):
- [ ] Implementar Forecast Service (API endpoints básicos)
- [ ] Integrar PostgreSQL y Redis
- [ ] Health checks por dependencia
- [ ] Primeros tests

Fase 1 (2 semanas):
- [ ] Analytics Service
- [ ] User Service con JWT + RBAC
- [ ] Integración de MLflow
- [ ] Deploy a staging

Fase 2 (2 semanas):
- [ ] Prefect para orquestación de pipelines
- [ ] Ray para procesamiento distribuido
- [ ] Monitoring y alertas
- [ ] Deploy a producción

## Soporte

Ver documentación completa en `docs/PLAN_REDISENO_Y_DESPLIEGUE_MODULAR_2026.md`
