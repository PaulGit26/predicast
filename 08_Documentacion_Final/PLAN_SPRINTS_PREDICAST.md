# 📅 PLAN DE SPRINTS - PREDICAST v4.0
## Productivización y Formalización del Sistema

**Documento:** Plan de Ejecución por Sprints  
**Versión:** 1.0  
**Fecha:** 18 Abril 2026  
**Estado:** En Planificación  
**Duración Total:** 14 semanas (18 Abril - 24 Julio 2026)

---

## 📊 Resumen Ejecutivo

| Fase | Sprint | Duración | Objetivos | Estado |
|------|--------|----------|-----------|--------|
| **Setup** | 0 | 1 sem | Infraestructura, CI/CD, monitoreo | 🔵 Planificado |
| **Datos** | 1 | 3 sem | Validación, auditoría, documentación | 🔵 Planificado |
| **ML** | 2 | 2 sem | Validación modelos, hardening | 🔵 Planificado |
| **Backend** | 3 | 2 sem | API hardening, optimización, caché | 🔵 Planificado |
| **Frontend** | 4 | 2 sem | Dashboard pulido, UX, performance | 🔵 Planificado |
| **Documentación** | 5 | 2 sem | Manuales, capacitación, roadmap | 🔵 Planificado |
| **Validación** | 6 | 2 sem | UAT, correcciones, go-live | 🔵 Planificado |

---

## 🚀 SPRINT 0: SETUP & INFRASTRUCTURE (1 semana)
**Duración:** 18-25 Abril 2026  
**Objetivo:** Preparar ambiente producción, CI/CD, monitoreo

### 📌 Tareas

| ID | Tarea | Responsable | Duración | Criterio de Aceptación |
|----|-------|-------------|----------|----------------------|
| S0-001 | Configurar servidor producción | DevOps | 2d | ✅ Servidor online, SSH acceso, puertos abiertos 5000/8501 |
| S0-002 | Configurar CI/CD pipeline (GitHub Actions) | DevOps | 2d | ✅ Pipeline auto-deploys commits a main; logs disponibles |
| S0-003 | Implementar monitor + alertas (Prometheus/Grafana) | DevOps | 1d | ✅ Dashboard monitoreo: uptime, latencia, errores; alertas Slack |
| S0-004 | Configurar backups automáticos | DevOps | 1d | ✅ Backups diarios modelos + datos; restore test exitoso |
| S0-005 | Documentación stack técnico | Tech Lead | 1d | ✅ Doc: Streamlit, Flask, XGBoost, ARIMA, versiones exactas |
| S0-006 | Setup logging centralizado | DevOps | 1d | ✅ Logs aggregados forecasting_routes.py y dashboard_v4.py |

### 🎯 Hito Sprint 0
**✅ Infraestructura lista para Sprint 1**
- Servidor producción disponible
- CI/CD operativo
- Monitoreo + alertas funcionales
- Backups probados
- Logs centralizados

### ⚠️ Riesgos & Mitigación
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Configuración CI/CD compleja | Media | Alto | Usar templates GitHub Actions pre-hechos |
| Servidor no soporta módulos Python | Baja | Crítico | Validar Python 3.9+ con todos los paquetes |
| Backups corruptos | Baja | Crítico | Test restore semanal automático |

---

## 📊 SPRINT 1: ANÁLISIS & PREPARACIÓN DE DATOS (3 semanas)
**Duración:** 25 Abril - 15 Mayo 2026  
**Objetivo:** Validar datos, documentar EDA, auditar calidad

### 📌 User Stories Asociadas
HU001, HU002, HU003, HU004

### 🎯 Tareas

| ID | Tarea | Responsable | Duración | Criterio de Aceptación |
|----|-------|-------------|----------|----------------------|
| S1-001 | Auditoría completa datos históricos (222 semanas) | Data Eng | 3d | ✅ Reporte: NULL%, outliers%, duplicados=0%; Logs validación |
| S1-002 | Documentar EDA completo (20 productos) | Data Scientist | 4d | ✅ Jupyter versionado: distributions, seasonality, outliers, correlaciones; plots guardados PNG |
| S1-003 | Validar integridad fechas (ISO 8601) | Data Eng | 1d | ✅ Script validación: semanas consecutivas 2023-W01 a 2025-W52; sin gaps |
| S1-004 | Crear data dictionary (columnas, tipos, rango) | Data Eng | 2d | ✅ Documento: campos, min/max, ejemplos; versionado en Git |
| S1-005 | Test reproducibilidad limpieza de datos | QA | 2d | ✅ Ejecutar limpieza 2 veces: output idéntico; hash verificado |
| S1-006 | Generar dataset shadow para testing | Data Eng | 1d | ✅ 10% datos aleatorio para testing sin afectar producción |

### 📌 Criterios de Aceptación por HU

**HU001:** Carga de datos exitosa  
```gherkin
Dado: Sistema operativo, archivo datos_semanales_pivot.csv presente
Cuando: Se ejecuta cargar_datos_forecasting() en Sprint 1 audit
Entonces: 
  - PREDICCIONES cargado con shape (20, 52)
  - Audit log: timestamp, usuario, versión datos
  - Tiempo carga < 2 seg verificado 3 veces
```

**HU002:** Validación integridad fechas  
```gherkin
Dado: Archivo predicciones_52semanas_pivot.csv cargado
Cuando: Se valida formato ISO 8601
Entonces:
  - Formato: 2026-W03 a 2027-W01 (52 semanas)
  - 0 valores NULL; 0 duplicados
  - All predicciones >= 0; max realista vs histórico
```

**HU003:** Consolidación tabla única  
```gherkin
Dado: Predicciones en formato pivot
Cuando: Se genera predicciones_52semanas_largo.csv
Entonces:
  - 1,040 registros exactos (52 × 20)
  - Estructura: Producto_codigo, Semana, Prediccion, Lower_Bound_95, Upper_Bound_95
  - Validación: Lower < Prediccion < Upper en 100% filas
```

**HU004:** Visualización resumen  
```gherkin
Dado: Dashboard Streamlit iniciado
Cuando: Usuario visualiza 🏠 Dashboard
Entonces:
  - Muestra 222 semanas históricas
  - 20 productos listados con códigos correctos
  - Modelo identificado: HYBRID_XGBoost_ARIMA (60%+40%)
  - Métricas visibles: R² > 0.99, MAPE < 5%
```

### 🎯 Hito Sprint 1
**✅ Dataset Listo para Producción**
- Auditoría de datos completada (zero defects)
- EDA documentado versionado
- Data dictionary disponible
- Validaciones automáticas implementadas
- Reset-to-production checklist firmado

### 📦 Deliverables
- `01_AUDITORIA_DATOS_SPRINT1.md` - Reporte completo
- `02_EDA_DOCUMENTADO_SPRINT1.ipynb` - Jupyter con análisis
- `03_DATA_DICTIONARY_v1.0.xlsx` - Catálogo de campos
- `04_VALIDACION_SCRIPT.py` - Script auto-validación

### ⚠️ Riesgos & Mitigación
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Descubrir datos corruptos | Media | Medio | Recolectar datos fixes en paralelo si aplica |
| EDA toma más tiempo | Baja | Bajo | Usar templates Jupyter pre-hechos |
| Inconsistencias zona horaria | Baja | Medio | Especificar UTC en data dictionary |

### 📌 Dependencias
- ⬅️ **Requiere:** Sprint 0 completado (servidor + ambiente)
- ➡️ **Desbloquea:** Sprint 2 (ML), Sprint 3 (API)

---

## 🤖 SPRINT 2: MODELADO PREDICTIVO (2 semanas)
**Duración:** 15-29 Mayo 2026  
**Objetivo:** Validar modelos ML, documentar métricas, hardening

### 📌 User Stories Asociadas
HU005, HU006, HU007, HU008, HU009, HU010

### 🎯 Tareas

| ID | Tarea | Responsable | Duración | Criterio de Aceptación |
|----|-------|-------------|----------|----------------------|
| S2-001 | Re-entrena XGBoost con datos versionados | ML Eng | 2d | ✅ 20 modelos guardados; joblib verificados hash; R² > 0.99 |
| S2-002 | Re-entrena ARIMA con parametrización | ML Eng | 2d | ✅ Parámetros orden (p,d,q) y seasonal (P,D,Q,m) documentados |
| S2-003 | Calcula métricas completas (R², MAPE, MAE, RMSE) | ML Eng | 2d | ✅ Tabla: 20 modelos × 4 métricas; comparativa benchmark guardada |
| S2-004 | Test sin data leakage | QA | 2d | ✅ Validación: punto corte Semana 222; train/test 80/20; cross-val k=5 |
| S2-005 | Documentar hiperparámetros | ML Eng | 1d | ✅ Archivo: hiperparámetros exactos XGBoost + ARIMA por producto |
| S2-006 | Crear modelo registry (versioning) | ML Eng | 1d | ✅ Sistema: v1.0 es baseline, v1.1 es mejorado; rollback posible |

### 📌 Criterios de Aceptación por HU

**HU005:** XGBoost pre-cargados ✅  
```gherkin
Dado: modelo_hybrid_xgboost_final.joblib en 03_Modelos/
Cuando: forecasting_routes.py carga modelos línea 33
Entonces:
  - 20 modelos XGBoost cargados exitosamente
  - Log: [INFO] Loaded 20 XGBoost models | timestamp
  - EN MEMORIA; tamaño ~5-10MB RAM verificado
```

**HU006:** Parámetros ARIMA ✅  
```gherkin
Dado: modelo_hybrid_arima_params_final.json existe
Cuando: Sistema carga parámetros línea 39
Entonces:
  - 20 conjuntos parámetros en memoria
  - Estructura validada: {order: [p,d,q], seasonal_order: [P,D,Q,m]}
  - Parámetros específicos: por ej CP_01 (1,1,1)(1,1,1,52)
```

**HU007:** Modelo Híbrido ✅  
```gherkin
Dado: XGBoost y ARIMA cargados
Cuando: predict_hybrid_with_loaded_models() ejecuta
Entonces:
  - Fórmula aplicada: hybrid = 0.6×XGB + 0.4×ARIMA
  - 52 predicciones por producto generadas
  - Todos valores >= 0
  - Metadata: "HYBRID_XGB_ARIMA_v1.0"
```

**HU008:** Sin Data Leakage ✅  
```gherkin
Dado: 222 semanas históricas disponibles
Cuando: Sistema genera predicciones 52 semanas futuras
Entonces:
  - Punto corte Semana 222: clear boundary
  - Modelos SOLO entrenados con 222 hist
  - Predicciones futuro: 2026-W03 a 2027-W01
```

**HU009:** Reporte métricas ✅  
```gherkin
Dado: modelo_hybrid_metadata_v1.0.json  
Cuando: Usuario consulta /model-info endpoint
Entonces:
  - Tabla 20 productos: media, std, min, max
  - Ej CP_01: media=181.12, std=81.19
  - Ej MZ_01: media=1163.36, std=484.79
  - Datos disponibles: 222 semanas
```

**HU010:** Comparación baseline ✅  
```gherkin
Dado: Modelo HYBRID entrenado 222 semanas
Cuando: Sistema reporta resumen_predicciones_hibrido.json
Entonces:
  - Estadísticas: Media (30-1200), Std proporcional
  - Min >= 0; Max realista
  - Estado: "LISTO PARA PRODUCCIÓN"
```

### 🎯 Hito Sprint 2
**✅ Modelos Validados & Certificados**
- Métricas ML documentadas (R², MAPE, MAE, RMSE)
- Data leakage test = OK
- Hiperparámetros bloqueados versión 1.0
- Model Registry operativo
- Acta de validación modelo firmada

### 📦 Deliverables
- `05_METRICAS_ML_SPRINT2.xlsx` - Tabla comparativa 20 productos
- `06_VALIDACION_DATALEAKAGE.md` - Test report
- `07_HIPERPARAMETROS_v1.0.json` - Configuración bloqueada
- `08_MODEL_REGISTRY.csv` - Versioning histórico

### ⚠️ Riesgos & Mitigación
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Metrics degradadas vs baseline | Baja | Medio | Keep v0 as fallback en model registry |
| Reentrenamiento toma >2 días | Baja | Bajo | Usar parallel training (20 cores) |
| Cross-validation encuentra overfitting | Baja | Medio | Reducir complejidad XGBoost (max_depth=5) |

### 📌 Dependencias
- ⬅️ **Requiere:** Sprint 1 completado (datos validados)
- ➡️ **Desbloquea:** Sprint 3 (API con métricas), Sprint 4 (Dashboard)

---

## ⚙️ SPRINT 3: ENGINE OPTIMIZACIÓN + API HARDENING (2 semanas)
**Duración:** 29 Mayo - 12 Junio 2026  
**Objetivo:** API production-ready, caché, validación E2E

### 📌 User Stories Asociadas
HU023, HU024, HU025, HU026, HU027, HU028

### 🎯 Tareas

| ID | Tarea | Responsable | Duración | Criterio de Aceptación |
|----|-------|-------------|----------|----------------------|
| S3-001 | Hardening API (validación input, rate limit) | Backend | 3d | ✅ Endpoint protegido: max 100 req/min; input sanitizado; 401 sin auth |
| S3-002 | Implementar caché Redis (predicciones) | Backend | 2d | ✅ Cache hit 95%+; TTL 1 hora; invalidation automática |
| S3-003 | Testing E2E API (5 endpoints) | QA | 2d | ✅ 5 endpoints testados; status 200; respuesta < 500ms |
| S3-004 | Documentación Swagger update | Backend | 1d | ✅ Swagger UI: 5+ endpoints, ejemplos request/response, modelos JSON |
| S3-005 | JWT autenticación implementada | Backend | 2d | ✅ Token requerido; 401 sin token; 403 permisos insuficientes |
| S3-006 | Load testing (simular 100 usuarios) | QA | 1d | ✅ Respuesta < 1 seg bajo carga; no memory leaks |
| S3-007 | Implementar algoritmo recomendación | Backend | 2d | ✅ Stock seguridad = media + 1.65×std; recomendación calculada <200ms |

### 📌 Criterios de Aceptación por HU

**HU023:** Endpoint GET 52 semanas ✅  
```gherkin
Dado: API Flask localhost:5000 iniciada
Cuando: GET /api/v1/forecasting/52weeks/CP_01
Entonces:
  - Status 200 OK
  - Response JSON: {producto, predicciones[], fechas[], intervalo_95}
  - Tiempo respuesta < 500ms (con cache)
```

**HU024:** Endpoint GET todos productos ✅  
```gherkin
Dado: API operativa
Cuando: GET /api/v1/forecasting/all-products
Entonces:
  - Status 200 OK
  - Array 20 productos
  - Campos: codigo, pred_media, std, min, max, tendencia
  - Tiempo respuesta < 1 seg
```

**HU025:** Endpoint GET detalle ✅  
```gherkin
Dado: API operativa
Cuando: GET /api/v1/forecasting/product/CP_01/detailed
Entonces:
  - Status 200 OK
  - Respuesta completa: predicciones, fechas, intervalos, stats
  - Estructura lista para gráficos Plotly
```

**HU026:** Análisis impacto económico ✅  
```gherkin
Dado: API operativa, metadata disponibles
Cuando: GET /api/v1/benchmarking/economic-impact
Entonces:
  - Status 200 OK
  - Por producto: ganancia_historica, margen_pct, rotacion_inv, ahorro_anual, roi_pct
  - Resumen total ahorros proyectados
```

**HU027:** Documentación Swagger ✅  
```gherkin
Dado: API ejecutando localhost:5000
Cuando: Usuario accede http://localhost:5000/api/docs
Entonces:
  - Swagger UI carga < 2 seg
  - 5+ endpoints documentados
  - Botón Try it out funcional
  - Ejemplos request/response mostrados
```

**HU028:** Validación autenticación ✅  
```gherkin
Dado: JWT autenticación configurada
Cuando: Cliente sin token: GET /api/v1/forecasting/all-products
Entonces:
  - Status 401 Unauthorized
  - Response: {error: "Token requerido"}
  - Con token válido: Status 200 OK
```

### 🎯 Hito Sprint 3
**✅ API Producción-Ready**
- 5 endpoints completamente documentados + testeados
- Caché operativo (95%+ hit rate)
- Autenticación JWT funcional
- Rate limiting implementado
- Load test: 100 usuarios simultáneos OK
- E2E testing: 100% pass

### 📦 Deliverables
- `09_API_SPECIFICATION_v1.0.json` - Swagger completo
- `10_TESTING_E2E_RESULTS.md` - Test report
- `11_LOAD_TESTING_REPORT.md` - Performance bajo carga
- `12_ENDPOINT_DOCUMENTATION.md` - Guía técnica

### ⚠️ Riesgos & Mitigación
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Cache invalidation problema | Media | Medio | Usar redis TTL + manual invalidation endpoint |
| JWT token expiration issues | Baja | Bajo | Refresh tokens implementados |
| Rate limit demasiado restrictivo | Baja | Bajo | Configurar límites por customer tier |

### 📌 Dependencias
- ⬅️ **Requiere:** Sprint 2 completado (modelos validados)
- ➡️ **Desbloquea:** Sprint 4 (Dashboard con API), Sprint 6 (UAT)

---

## 🎨 SPRINT 4: DASHBOARD & INTERFAZ EJECUTIVA (2 semanas)
**Duración:** 12-26 Junio 2026  
**Objetivo:** Dashboard pulido, UX/UI, performance, multilingual

### 📌 User Stories Asociadas
HU011, HU012, HU013, HU014, HU015, HU016, HU017, HU018, HU019, HU020, HU021, HU022

### 🎯 Tareas

| ID | Tarea | Responsable | Duración | Criterio de Aceptación |
|----|-------|-------------|----------|----------------------|
| S4-001 | UX/UI refresh (4 tabs organizadas) | UX/Dev | 3d | ✅ Demo: Tabs 🏠📊📈⚙️ con submenu; responsive mobile |
| S4-002 | Optimizar performance gráficos Plotly | Frontend | 2d | ✅ Render gráficos < 1 seg; no lag en scroll; 60 FPS |
| S4-003 | Implementar multilingual (ES/EN) | Frontend | 2d | ✅ Todos labels traducidos; selector idioma en sidebar; persist idioma |
| S4-004 | Funcionalidades recomendación | Developer | 2d | ✅ Stock seguridad calc OK; botón Producir; descarga plan CSV |
| S4-005 | Testing usabilidad con 5 usuarios | QA | 2d | ✅ SUS score > 75; sin errores; time-on-task < 3 min c/tarea |
| S4-006 | Dark mode + personalizaciones | Frontend | 1d | ✅ Toggle dark/light mode; tema persiste; custom colors setup |
| S4-007 | Descarga gráficos PNG + reportes PDF | Frontend | 1d | ✅ Click botón: descargar PNG 1200×800; PDF 4-5 páginas |

### 📌 Criterios de Aceptación por HU

**HU011:** Stock de seguridad ✅  
```gherkin
Dado: Predicciones con media y std
Cuando: Dashboard ejecuta análisis recomendación
Entonces:
  - Fórmula: S.S. = media + 1.65×std (nivel 95%)
  - Ej CP_01: 181.12 + 1.65×81.19 ≈ 315 unidades
  - Visible en tab Recomendación
```

**HU012:** Recomendación semanal ✅  
```gherkin
Dado: Stock actual, demanda predicha, S.S.
Cuando: Usuario selecciona CP_01 en tab 💡 Recomendación
Entonces:
  - Calcula: Prod_Recom = max(0, Demanda - Stock_Actual + S.S.)
  - Display: Número grande + justificación
  - Respuesta < 1 seg
```

**HU013-015:** Exportación, simulación, ajuste ✅  
```gherkin
Dado: 1,040 recomendaciones (52×20)
Cuando: Usuario ejecuta simulación o exporta plan
Entonces:
  - Simulación: gráfico stock actual vs recomendado en <1 seg
  - Exportación: CSV 1,040 filas; columnas correctas
  - Ajuste nivel: Z-score 1.65→2.33; refresca automático
```

**HU016-22:** Visualización, tabs, filtros, descarga ✅  
```gherkin
Dado: Dashboard Streamlit operativo
Cuando: Usuario navega tabs, cambia producto, filtra fechas
Entonces:
  - Gráfico Plotly actualiza < 500ms
  - Tabla detallada con 52 filas; scrolleable
  - Descarga PNG: 1200×800px; alta calidad
  - Dark mode toggle funciona
  - Idioma ES/EN persiste
```

### 🎯 Hito Sprint 4
**✅ Dashboard Producción-Ready**
- UX/UI polished (4 tabs operativos)
- Performance: load < 2 seg, tab switch < 500ms
- Multilingual completado (ES/EN)
- Recomendaciones automáticas validadas
- Descarga gráficos + PDF operativa
- Usability test: SUS > 75

### 📦 Deliverables
- `13_DASHBOARD_SCREENSHOTS.md` - Visual walkthrough
- `14_USABILITY_TEST_REPORT.md` - 5 usuarios feedback
- `15_PERFORMANCE_METRICS.xlsx` - Load times, FPS, RAM
- `16_DARK_MODE_COLORS.json` - Tema colores

### ⚠️ Riesgos & Mitigación
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Plotly gráficos lentos con muchos datos | Media | Medio | Usar Altair o Dash alternativa; caching |
| Traducción EN inconsistente | Baja | Bajo | QA nativo-hablante revisa en Sprint 5 |
| Mobile responsive rompe en tablets | Baja | Bajo | Test en iPad/Android durante Sprint 4 |

### 📌 Dependencias
- ⬅️ **Requiere:** Sprint 2 completado (modelos), Sprint 3 API ok
- ➡️ **Desbloquea:** Sprint 5 (capacitación), Sprint 6 (UAT)

---

## 📚 SPRINT 5: DOCUMENTACIÓN & CAPACITACIÓN (2 semanas)
**Duración:** 26 Junio - 10 Julio 2026  
**Objetivo:** Manuales, capacitación, roadmap, acta conformidad

### 📌 User Stories Asociadas
HU034, HU035, HU036, HU037, HU038, HU039

### 🎯 Tareas

| ID | Tarea | Responsable | Duración | Criterio de Aceptación |
|----|-------|-------------|----------|----------------------|
| S5-001 | Manual de Usuario completo (25-30 pág) | Product | 3d | ✅ WORD: portada, TOC, intro, uso por tab +screenshots, troubleshooting |
| S5-002 | Manual Técnico completo (15-20 pág) | Tech Lead | 3d | ✅ WORD: arqui diagrama, stack, endpoints, modelos ML, DB schema, deployment |
| S5-003 | Presentación capacitación (30-40 slides) | Product | 2d | ✅ PPT: contexto+problema, solución, demo vivo, casos reales, impacto, Q&A |
| S5-004 | Ejecutar capacitación vivo (1.5 horas) | Product | 1d | ✅ 8-15 personas; survey al final: >95% entiende valor; Q&A respondidas |
| S5-005 | Plan Migración (fases, KPIs, rollback) | PM | 2d | ✅ WORD: 3 fases (PILOTO, AMPLIACIÓN, PRODUCCIÓN); cronograma; responsables |
| S5-006 | Procedimiento Mantenimiento (ops checklist) | Tech Lead | 1d | ✅ WORD: checklist semanal/mensual/trimestral; monitoreo; escalamiento |
| S5-007 | Roadmap 2026-2027 (futuras releases) | PM | 1d | ✅ WORD: Q2-Q4 2026 + Q1 2027; features, ROI, dependencies; timeline |
| S5-008 | Crear Acta de Aceptación | PM | 1d | ✅ Documento legal: funcionalidades entregadas, aceptación cliente, firma |

### 📌 Criterios de Aceptación por HU

**HU034:** Manual Usuario ✅  
```gherkin
Dado: Sistema PREDICAST operativo
Cuando: Se revisa Manual_de_Usuario_PREDICAST_v4.0.docx
Entonces:
  - Portada + versión + fecha
  - TOC con enlaces
  - 1. Intro (qué es, problema, solución)
  - 2-5. Uso por tab: paso a paso + screenshots
  - 6. Interpretación recomendaciones
  - 7. Exportación
  - 8. Troubleshooting
  - Total: 25-30 páginas con imágenes
```

**HU035:** Manual Técnico ✅  
```gherkin
Dado: Sistema en producción
Cuando: Se revisa Manual_Tecnico_PREDICAST_v4.0.docx
Entonces:
  - Diagrama arquitectura: Front-Back-DB-ML
  - Stack: Streamlit, Flask, XGBoost, ARIMA, versiones
  - Carpetas + archivos principales
  - 5 endpoints API completos
  - Ubicación modelos ML + carga
  - DB schema + ERD
  - Logs, monitoreo, deployment steps
  - Troubleshooting técnico
  - Total: 15-20 páginas
```

**HU036:** Presentación Capacitación ✅  
```gherkin
Dado: Equipo planificación (8-15 personas)
Cuando: Se ejecuta sesión capacitación vivo (1.5 horas)
Entonces:
  - 30-40 slides:
    * Slides 1-5: Contexto + Problema (por qué?; impacto actual)
    * Slides 6-10: Solución (qué es PREDICAST; beneficios)
    * Slides 11-15: ML 101 (modelos; accuracy; no abrumar técnica)
    * Slides 16-25: Demo VIVO 5 min (navegación, recomendaciones)
    * Slides 26-30: Casos reales (qué pasó con CP_01, MZ_01)
    * Slides 31-35: Impacto económico (ahorros proyectados)
    * Slides 36-40: Roadmap + Q&A
  - Survey post-capacitación: >= 95% entiende valor
```

**HU037-39:** Plan Migración, Mantenimiento, Roadmap ✅  
```gherkin
Plan Migración:
  - 3 fases: PILOTO (Sem 1-2, 5 productos), AMPLIACIÓN (Sem 3-4, 20), PRODUCCIÓN (Sem 5, live)
  - Cronograma con hitos
  - Responsables + recursos
  - Riesgos + rollback plan
  - KPIs éxito

Procedimiento Mantenimiento:
  - Checklist Semanal: validar pred vs reales
  - Checklist Mensual: auditoría datos, outliers
  - Checklist Trimestral: retrain modelos
  - Monitoreo: uptime>99%, respuesta<500ms
  - Backups, escalamiento, bugs proceso

Roadmap 2026-2027:
  - Q2 2026: v1.1 Análisis ABC
  - Q3 2026: v1.2 Dashboards + reportes
  - Q4 2026: v2.0 Retrain automático + alertas
  - Q1 2027: v2.1 ERP + API externas
  - C/release: features, recursos, ROI, dependencias
```

### 🎯 Hito Sprint 5
**✅ Documentación Completa & Equipo Capacitado**
- Manual Usuario completado + validado
- Manual Técnico completado + validado
- Presentación capacitación ejecutada (95%+ satisfacción)
- Plan Migración documentado + aprobado
- Procedimiento Mantenimiento definido
- Roadmap 2026-2027 aprobado
- Acta Aceptación preparada para firmar

### 📦 Deliverables
- `17_MANUAL_USUARIO_v4.0.docx` - 25-30 páginas
- `18_MANUAL_TECNICO_v4.0.docx` - 15-20 páginas
- `19_PRESENTACION_CAPACITACION_v1.0.pptx` - 40 slides
- `20_PLAN_MIGRACION_v1.0.docx` - Cronograma
- `21_PROCEDIMIENTO_MANTENIMIENTO_v1.0.docx` - Checklist
- `22_ROADMAP_2026_2027.docx` - Futuras releases
- `23_ACTA_ACEPTACION_v1.0.docx` - Legal doc

### ⚠️ Riesgos & Mitigación
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|--------|-----------|
| Capacitación requiere >1.5 horas | Baja | Bajo | Dividir en 2 sesiones si aplica |
| Documentación desactualizada al cambiar UI | Media | Bajo | Revisar screenshots Sprint 4 final |
| Roadmap poco realista | Baja | Medio | Validar con arquitecto antes de publicar |

### 📌 Dependencias
- ⬅️ **Requiere:** Sprint 4 completado (dashboard final)
- ➡️ **Desbloquea:** Sprint 6 (UAT)

---

## ✅ SPRINT 6: UAT & GO-LIVE (2 semanas)
**Duración:** 10-24 Julio 2026  
**Objetivo:** Pruebas usuario final, correcciones, cutover producción

### 🎯 Tareas

| ID | Tarea | Responsable | Duración | Criterio de Aceptación |
|----|-------|-------------|----------|----------------------|
| S6-001 | Preparar ambiente UAT (copia exacta producción) | DevOps | 1d | ✅ UAT server online; datos replicados; usuarios test creados |
| S6-002 | Ejecutar UAT con usuarios reales (5-8 personas, 5 días) | QA + Users | 5d | ✅ Testeadores en UAT; 50+ casos de prueba ejecutados; bugs log |
| S6-003 | Bugs encontrados + re-test ciclo | Dev | 3d | ✅ Bugs críticos: 0; medianos: <5; menores: <10 en UAT pre-go live |
| S6-004 | Entrenamiento operaciones (support team) | Tech Lead | 1d | ✅ 3-5 ops personas capacitadas; manual support OK; checklist operaciones |
| S6-005 | Cutover plan (horario, rollback) | DevOps + PM | 1d | ✅ Documento: horario cutover (ej domingo 20:00-02:00); rollback steps; comunicación |
| S6-006 | Ejecutar cutover a producción | DevOps | 1d | ✅ Deployado a prod; smoke tests pasados; users acceso OK; 0 errores críticos |
| S6-007 | Post-go-live support (1-2 semanas monitoreo) | Support | 10d | ✅ On-call support 24/7; bugs hotfixed; performance monitoreada; tickets respondidos <1 hora |

### 🎯 Hito Sprint 6 = Project Complete ✅
**✅ PREDICAST v4.0 EN PRODUCCIÓN**
- UAT exitoso (50+ test cases pass)
- Usuarios capacitados + empoderados
- Cutover ejecutado sin incidentes
- Post-go-live support activo
- Sistema estable: uptime 99%+; respuesta <500ms
- Acta Final de Aceptación firmada por cliente

### 📦 Deliverables
- `24_UAT_TEST_CASES.xlsx` - 50+ casos + resultados
- `25_BUGS_LOG_UAT.md` - Solución + verificación
- `26_CUTOVER_PLAN.md` - Horario, rollback, comms
- `27_OPERACIONES_RUNBOOK.md` - Support procedures
- `28_ACTA_ACEPTACION_FINAL.pdf` - Cliente firma

### 📌 Dependencias
- ⬅️ **Requiere:** Sprint 5 completado (manuales + capacitación)
- ➡️ **Habilita:** Mantenimiento Post-Lanzamiento (soporte 24/7)

---

## 📈 RESUMEN TIMELINE

```
Semana 1  (18-25 Abril):   Sprint 0 - Setup & Infrastructure
Semana 2-4 (25 Abril-15 Mayo):  Sprint 1 - Análisis & Datos
Semana 5-6 (15-29 Mayo):    Sprint 2 - Modelado ML
Semana 7-8 (29 Mayo-12 Junio):  Sprint 3 - API + Engine
Semana 9-10 (12-26 Junio):   Sprint 4 - Dashboard
Semana 11-12 (26 Jun-10 Julio):  Sprint 5 - Documentación
Semana 13-14 (10-24 Julio):   Sprint 6 - UAT + Go-Live

Total: 14 semanas = 3.5 meses
Fecha Go-Live: 24 Julio 2026 🚀
```

---

## 👥 ROLES & RESPONSABILIDADES

| Rol | Sprint | Tareas Clave | FTE |
|-----|--------|--------------|-----|
| **Product Manager** | 0-6 | Planning, stakeholder comms, acceptance | 1.0 |
| **Tech Lead** | 0-6 | Arquitectura, technical decisions, docs | 1.0 |
| **Data Engineer** | 1-2 | Data pipeline, auditoría, modelo prep | 0.8 |
| **ML Engineer** | 2 | Modelado, validación, experiment tracking | 1.0 |
| **Backend Developer** | 3 | API hardening, caché, seguridad | 1.0 |
| **Frontend Developer** | 4 | Dashboard UI/UX, performance, multilingual | 1.0 |
| **DevOps/SRE** | 0, 6 | Infra, CI/CD, deployment, monitoring | 0.5 |
| **QA Engineer** | 2-6 | Testing, compliance, UAT coordination | 1.0 |
| **Support/Trainer** | 5-6 | Capacitación, documentación, support | 0.5 |

**Total Team Size:** ~7-8 personas FTE

---

## 🎯 CRITERIOS DE ÉXITO PROYECTO

### Por Sprint
- ✅ Sprint 0: Infra lista; CI/CD operativo; monitoring on
- ✅ Sprint 1: Auditoría datos zero--defects; EDA documentado
- ✅ Sprint 2: Modelos certificados; data leakage test OK
- ✅ Sprint 3: API E2E testing 100% pass; load test OK
- ✅ Sprint 4: Dashboard UX score >75; performance <1 seg
- ✅ Sprint 5: Capacitación >95% satisfacción; documentación OK
- ✅ Sprint 6: UAT pass; cutover sin incidentes; uptime 99%+

### Métricas Globales Go-Live
| Métrica | Target | Verificación |
|---------|--------|---|
| **Uptime Sistema** | >99% | Prometheus uptime check |
| **Tiempo Respuesta API** | <500ms | Load test results |
| **MAPE Predicciones** | <5% | Modelo validation report |
| **Usability Score (SUS)** | >75 | Usability test survey |
| **Bugs Críticos en UAT** | 0 | UAT test log |
| **Documentación Completitud** | 100% | Doc checklist |
| **Capacitación Asistencia** | >90% | Sign-in sheet |

---

## ⚠️ RIESGOS GLOBALES & MITIGACIÓN

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|-------------|--------|-----------|
| R1 | Timeline slip (> 14 semanas) | Media | Alto | Sprint planning riguroso; daily standups; buffer 10% |
| R2 | Recursos insuficientes | Baja | Alto | Contratar contractors si FTE no disponible |
| R3 | Cambios scope mid-project | Alta | Medio | Change control board; cliente solo fixes críticos |
| R4 | Performance degradada vs MVP | Baja | Medio | Load testing early (Sprint 3); optimize antes ir UAT |
| R5 | Datos producción inconsistentes | Baja | Crítico | Data audit Sprint 1 riguroso; validations automáticas |
| R6 | Usuarios no adoptan sistema | Baja | Medio | Capacitación Sprint 5 obligatoria; champions program |

---

## 📋 CHECKLIST GO-LIVE

### Pre-Go-Live (Sprint 6 - Día 1-7)
- [ ] Ambiente UAT espejo exacto producción
- [ ] 50+ test cases ejecutados (>95% pass)
- [ ] Bugs críticos solucionados
- [ ] Operaciones equipo capacitado
- [ ] Cutover plan revisado + aprobado
- [ ] Backups probados + restore OK
- [ ] Rollback plan definido + testeado
- [ ] Comunicación a usuarios enviada

### Go-Live (Sprint 6 - Día 8)
- [ ] Cutover ejecutado a horario planeado
- [ ] Smoke tests pasados en producción
- [ ] Usuarios pueden acceder (0 auth issues)
- [ ] Datos correctos en producción
- [ ] Monitoring + alertas operativas
- [ ] Support team on-call
- [ ] CEO/stakeholders notificados

### Post-Go-Live (Sprint 6 - Semana 2-3)
- [ ] Monitoring 24/7 (uptime 99%+)
- [ ] Bugs hotfixed en <2 horas
- [ ] Performance validada (<500ms)
- [ ] Usuarios reportan satisfacción >4.5/5
- [ ] First forecast cycle exitoso
- [ ] Acta de Aceptación Final firmada
- [ ] Soporte transiciona a BAU

---

## 📞 ESCALAMIENTO & DECISIONES

### Escalamiento por Severidad
- **CRÍTICO** (sistema down, data loss): CEO + Tech Lead + decision en <15 min
- **MAYOR** (feature broken, performance hit): PM + Tech Lead + decision en <4 horas
- **MENOR** (UI typo, small bug): Dev lead autonomía; log en change tracker

### Change Control
- **Cambios menores** (docs, small fixes): Dev autonomía; log en change log
- **Cambios medianos** (new endpoint, new KPI): PM approval + tech review
- **Cambios mayores** (new feature, scope change): Steering committee + cliente approval

---

## 📚 DOCUMENTOS A GENERAR (Cada Sprint)

Cada sprint genera:
1. **Sprint Plan** - Tareas + timeline
2. **Sprint Review** - Completado + pendiente + learnings
3. **Sprint Retro** - Qué salió bien; qué mejorar
4. **Deliverables** - Código, documentos, reports
5. **Risk Log Update** - Riesgos nuevos + mitigaciones

---

**Documento Preparado por:** AI Assistant  
**Fecha Revisión:** 18 Abril 2026  
**Próxima Revisión:** 25 Abril 2026 (Sprint 0 end)  
**Estado:** 🔵 En Planificación → Listo para Sprint 0 Kickoff

---

## 🚀 PRÓXIMOS PASOS

1. ✅ **Validar Plan con Stakeholders** (18-20 Abril)
   - Meeting con cliente, CFO, ops
   - Feedback sobre timeline, scope, recursos
   - Sign-off documento

2. ✅ **Asignar Equipo & Recursos** (20-22 Abril)
   - Contratar/asignar roles
   - Setup herramientas (Git, Jira, Slack, etc)
   - Kickoff team meeting

3. ✅ **Ejecutar Sprint 0** (22-29 Abril)
   - Setup infraestructura
   - CI/CD pipeline
   - Monitoring + alertas
   - **Hito:** Infraestructura lista

4. ✅ **Sprint 1 Kick-off** (25 Abril)
   - Data audit
   - EDA analysis
   - Documentación

---

**¡Listo para Comenzar!** 🎯

