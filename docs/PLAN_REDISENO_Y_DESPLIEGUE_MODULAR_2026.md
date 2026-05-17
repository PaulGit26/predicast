# 🚀 Plan Maestro de Rediseño y Despliegue Modular (Predicast 2026)

## 1) Objetivo
Diseñar y desplegar Predicast sobre una arquitectura de microservicios con FastAPI + API Gateway + capa de datos y ML desacoplada, permitiendo agregar nuevos módulos sin romper lo existente.

---

## 2) Principios de diseño (para crecer sin rehacer)

1. **Arquitectura modular por dominio**
   - Cada dominio es un servicio: Forecast, Analytics, User/Auth, futuros módulos.
   - Cada servicio tiene contrato API, modelo de datos y ciclo de vida propios.

2. **Contract-first**
   - OpenAPI como contrato fuente para todos los servicios.
   - Versionado de APIs (`/api/v1`, `/api/v2`) para compatibilidad.

3. **Desacoplamiento por eventos y colas**
   - Predicción síncrona para consultas del usuario.
   - Tareas pesadas (entrenamiento, reprocesos, backfills) asíncronas.

4. **Infraestructura reproducible**
   - Infra como código, ambientes separados (dev/staging/prod).
   - Deploy seguro con rollback automatizable.

5. **Observabilidad desde el día 1**
   - Logs estructurados, métricas por servicio, trazabilidad por request_id.

---

## 3) Arquitectura objetivo (alineada a tus diagramas)

## 3.1 Lógica
- **Frontend** (Next.js)
- **Entrada única**: AWS API Gateway
- **Servicios FastAPI**:
  - Forecast Service
  - Dashboard/Analytics Service
  - User Service (usuarios, organizaciones, RBAC)
- **Datos**:
  - PostgreSQL (transaccional)
  - Redis (cache de predicciones)
  - S3 (datasets, modelos, backups)
- **ML y Orquestación**:
  - MLflow (registro/versionado de modelos)
  - Ray (procesamiento distribuido)
  - Prefect (orquestación de pipelines)
- **Observabilidad/DevOps**:
  - ELK, Sentry, GitHub Actions

## 3.2 Flujo principal de predicción
1. Usuario solicita predicción desde frontend.
2. API Gateway enruta al Forecast Service.
3. Forecast consulta Redis:
   - **Cache hit**: devuelve respuesta inmediata.
   - **Cache miss**: carga modelo activo (MLflow), calcula predicción.
4. Forecast persiste resultado en PostgreSQL y opcionalmente en Redis (TTL).
5. Pipeline ML en paralelo toma datos de S3, reentrena y promueve nuevas versiones de modelo.

## 3.3 Física (AWS)
- DNS/entrada: Route53 + API Gateway
- Cómputo: EKS (servicios FastAPI, workers Prefect/Ray)
- Datos: RDS PostgreSQL + ElastiCache Redis + S3
- Seguridad: Auth0 + AWS Secrets Manager
- CI/CD: GitHub Actions desplegando a EKS
- Monitoreo: CloudWatch + ELK + Sentry

---

## 4) Estructura recomendada de repositorio

```text
07_Sistema_Produccion/
  src/
    services/
      forecast_service/
      analytics_service/
      user_service/
    shared/
      contracts/        # OpenAPI, schemas pydantic compartidos
      auth/             # utilidades JWT/RBAC
      observability/    # logging, tracing, metrics
    ml/
      training/
      inference/
      feature_store/
    orchestrator/
      prefect_flows/
      ray_jobs/
  infra/
    terraform/ or cdk/
    k8s/
  .github/workflows/
  docs/
```

---

## 5) Plan de rediseño por fases (90 días)

## Fase 0 (Semana 1-2): Descubrimiento y diseño
**Entregables**
- Mapa de servicios actuales vs futuros.
- Contratos API v1 por dominio.
- ADRs (decisiones técnicas) iniciales.

**Criterio de salida**
- Interfaces definidas y aceptadas.
- Backlog priorizado por impacto/riesgo.

## Fase 1 (Semana 3-5): Base modular
**Entregables**
- Separación inicial en 3 servicios (Forecast, Analytics, User).
- Redis cache operativo en Forecast.
- Persistencia estandarizada en PostgreSQL.

**Criterio de salida**
- Servicios independientes desplegables.
- Pruebas contractuales pasando.

## Fase 2 (Semana 6-8): Plataforma ML y orquestación
**Entregables**
- Registro de modelos en MLflow.
- Flujo de entrenamiento con Prefect.
- Jobs distribuidos con Ray para cargas pesadas.

**Criterio de salida**
- Pipeline end-to-end reproducible.
- Promoción de modelo con trazabilidad.

## Fase 3 (Semana 9-10): Seguridad y observabilidad
**Entregables**
- Auth0 + RBAC por organización/tenant.
- Logging estructurado y alertas Sentry.
- Dashboards operativos (latencia, errores, throughput).

**Criterio de salida**
- SLOs mínimos definidos y monitoreados.

## Fase 4 (Semana 11-12): Hardening y salida a producción
**Entregables**
- Despliegue canary/blue-green.
- Runbooks de incidentes + rollback.
- Pruebas de carga y recuperación.

**Criterio de salida**
- Go-live con checklist de producción completo.

---

## 6) Estrategia de despliegue (dev/staging/prod)

## 6.1 Pipeline CI/CD mínimo
1. Pull Request:
   - lint + type-check + unit tests
   - pruebas de contratos API
2. Merge a main:
   - build imagen Docker por servicio
   - scan de seguridad
   - deploy automático a staging
3. Promoción a prod:
   - aprobación manual
   - deploy canary 10% → 50% → 100%
   - rollback automático si falla health check

## 6.2 Versionado y releases
- SemVer por servicio.
- Changelog por release.
- Compatibilidad backward en endpoints críticos.

## 6.3 Gestión de configuración
- Secretos en Secrets Manager.
- Variables por ambiente (sin hardcode).
- Migraciones de DB versionadas y reversibles.

---

## 7) Cómo agregar módulos futuros sin fricción

## Checklist de “Nuevo Módulo”
1. Definir dominio y límites (qué resuelve / qué no).
2. Crear contrato OpenAPI y eventos que emite/consume.
3. Definir esquema propio de datos o tablas por dominio.
4. Agregar métricas, logs y alertas desde el inicio.
5. Habilitar feature flag para rollout gradual.
6. Añadir pruebas: unitarias, integración y contrato.
7. Documentar runbook operativo.

## Reglas de gobernanza
- Cada módulo tiene owner técnico.
- No se permite acceso directo entre DBs de servicios (solo API/eventos).
- Cambios breaking requieren nueva versión de API.

---

## 8) KPIs de arquitectura y operación
- Latencia P95 de predicción.
- Tasa de cache hit en Redis.
- Error rate por servicio.
- Tiempo de despliegue y rollback.
- Tiempo de entrenamiento y promoción de modelos.
- Costo cloud por cliente/tenant.

---

## 9) Riesgos y mitigaciones
- **Riesgo**: complejidad temprana de microservicios.  
  **Mitigación**: empezar con 3 servicios core y evolucionar.
- **Riesgo**: sobrecosto cloud inicial.  
  **Mitigación**: rightsizing, autoscaling por demanda y presupuestos con alertas.
- **Riesgo**: drift entre entornos.  
  **Mitigación**: IaC + pipeline único + smoke tests obligatorios.

---

## 10) Próximo paso inmediato (esta semana)
1. Congelar alcance MVP de rediseño (qué entra / qué no entra).
2. Definir contratos API v1 de Forecast, Analytics y User.
3. Crear repositorio de infraestructura (IaC + k8s base).
4. Implementar pipeline CI/CD inicial a staging.
5. Ejecutar primer deploy vertical completo (frontend + gateway + forecast + redis + postgres).

---

## 11) Decisiones por confirmar contigo
- ¿Mantendremos monorepo o pasamos a multi-repo por servicio?
- ¿Auth0 se mantiene como proveedor principal de auth?
- ¿IaC con Terraform o AWS CDK?
- ¿Estrategia inicial de costos objetivo mensual (tope)?

Con esas 4 decisiones cerradas, este plan se transforma en backlog ejecutable de sprint (con historias, estimación y responsables).