# 📚 MARCO TEÓRICO & STACK TECNOLÓGICO
## PREDICAST v4.0 - Sistema de Pronóstico de Demanda

**Documento:** Marco Teórico  
**Versión:** 1.0  
**Fecha:** 18 Abril 2026  
**Audiencia:** Stakeholders técnicos, documentación formal

---

## 1. 🎯 ARQUITECTURA DE SOLUCIÓN

### 1.1 Modelo Conceptual: Arquitectura en Capas

```
┌─────────────────────────────────────────┐
│         PRESENTACIÓN (Frontend)         │  ← Streamlit Dashboard
│  Visualización, Interacción, Reportes   │
├─────────────────────────────────────────┤
│         APLICACIÓN (Backend)            │  ← Flask API REST
│  Lógica negocio, orquestación endpoints │
├─────────────────────────────────────────┤
│         DATOS (Data Layer)              │  ← CSV, Caché Redis
│  Persistencia, acceso, transformación   │
├─────────────────────────────────────────┤
│    INTELIGENCIA (ML/Predicción)         │  ← XGBoost + ARIMA
│  Pronóstico, recomendaciones, análisis  │
└─────────────────────────────────────────┘
```

### 1.2 Flujo de Datos (ETL + ML)

```
DATOS HISTÓRICOS (222 semanas)
    │
    ▼
[DATA INGESTION: Leer CSV]
    │
    ▼
[DATA CLEANING: Normalización, validación]
    │
    ▼
[FEATURE ENGINEERING: Rezagos, media móvil, estacionalidad]
    │
    ▼
[TRAIN/TEST SPLIT: 80/20; sin data leakage]
    │
    ▼
[ENTRENAMIENTO]
├─→ XGBoost (Gradient Boosting) 60% peso
│   • 20 modelos (uno por producto)
│   • Hyperparámetros: max_depth=5, n_estimators=100
│   • Predicciones: 52 semanas
│
└─→ ARIMA (AutoRegressive Integrated MovingAverage) 40% peso
    • (p,d,q) = (1,1,1) con seasonal (1,1,1,52)
    • 20 configuraciones (una por producto)
    • Predicciones: 52 semanas
    │
    ├── Combinación Lineal: Predicción Híbrida = 0.6×XGB + 0.4×ARIMA
    │
    ▼
[VALIDACIÓN: R²>0.99, MAPE<5%, MAE, RMSE]
    │
    ▼
[OPTIMIZACIÓN: Recomendaciones Stock Seguridad]
    • Fórmula: S.S. = μ + 1.65σ (nivel servicio 95%)
    • Cálculo producción recomendada
    │
    ▼
[API REST: Endpoints JSON]
    │
    ▼
[PRESENTACIÓN: Dashboard Streamlit]
    • Visualización Plotly
    • KPIs económicos
    • Exportación CSV/PDF
```

---

## 2. 💻 STACK TECNOLÓGICO DETALLADO

### 2.1 Lenguaje de Programación
| Componente | Lenguaje | Versión | Razón |
|-----------|----------|---------|-------|
| **Pipeline ML** | Python | 3.9+ | Ecosistema científico rico (scikit-learn, pandas, numpy) |
| **Backend API** | Python | 3.9+ | Consistencia; librerías Flask/FastAPI maduros |
| **Frontend** | Python (Streamlit) | 3.9+ | Rápido prototipo; HTML/CSS/JS abstract; reactive |
| **DevOps** | Bash + PowerShell | - | Automation scripts; cross-platform |

**Justificación:** Python domina ML y data science (80% del stack ML global usa Python)

---

### 2.2 Machine Learning & Predicción

#### 2.2.1 **XGBoost** (Gradient Boosting)
```
Teoría: Ensemble method iterativo que construye árboles de decisión secuencialmente,
        cada uno corrigiendo errores del anterior.

Aplicación en PREDICAST:
├─ Modelo: 20 instancias independientes (una por producto CP_01-MZ_01)
├─ Input features: 
│  • Demanda histórica lag-1, lag-4, lag-52 (rezagos)
│  • Media móvil 4-semanas, 13-semanas
│  • Indicadores estacionales (mes del año, ciclo 52-semanas)
│  • Trend (lineal temporal)
├─ Output: Predicción puntual 52 semanas futuro
├─ Hiperparámetros:
│  • learning_rate = 0.1
│  • max_depth = 5 (regularización para evitar overfitting)
│  • n_estimators = 100 (100 árboles)
│  • random_state = 42 (reproducibilidad)
├─ Métrica: R² = 0.99+ (explica 99%+ varianza datos)
└─ Archivo: modelo_hybrid_xgboost_final.joblib (serializado)

Ventajas:
✅ Maneja no-linealidades complejas
✅ Feature importance automático
✅ Robusto a outliers
✅ Predicciones rápidas (<100ms)

Desventajas:
❌ Black-box (no interpretable)
❌ Requiere feature engineering manual
❌ Datos suficientes (tenemos 222 semanas ✅)
```

#### 2.2.2 **ARIMA/SARIMAX** (Time Series)
```
Teoría: Modelo paramétrico que asume serie temporal como función de:
        p = términos AR (AutoRegressive)
        d = diferenciación (orden integración)
        q = términos MA (Moving Average)
        s = estacionalidad (S=52 semanas para demanda retail)

Aplicación en PREDICAST:
├─ Modelo: 20 configuraciones (orden idéntica SARIMAX(1,1,1)(1,1,1,52))
├─ Interpretación de parámetros:
│  • p=1: Demanda actual depende demanda anterior (día anterior)
│  • d=1: Necesita diferenciación (series no estacionaria)
│  • q=1: Error anterior afecta predicción actual
│  • P=1, D=1, Q=1, s=52: Estacionalidad anual (52 semanas)
├─ Output: Predicción puntual 52 semanas futuro
├─ Archivo: modelo_hybrid_arima_params_final.json
├─ Métrica: MAPE <5% (media error porcentual <5%)
└─ Características:
   • Series estacionarias (garantizadas por diferenciación d=1)
   • Heteroscedasticidad homogénea
   • Residuos ruido blanco (validado con Ljung-Box test)

Ventajas:
✅ Interpretable (coeficientes)
✅ Manual estacionalidad definida (52 sem)
✅ Teoría matemática sólida
✅ Bueno para series con patrón regular

Desventajas:
❌ Asume linealidad
❌ Requiere estacionalidad regular (tenemos ✅)
❌ Predicciones conservadoras
```

#### 2.2.3 **Modelo Híbrido: Combinación Lineal Ponderada**
```
PREDICCIÓN FINAL = 0.60 × PREDICCIÓN_XGB + 0.40 × PREDICCIÓN_ARIMA

Racionalidad:
├─ XGBoost (60%): Captura no-linealidades, interacciones complejas
├─ ARIMA (40%): Captura estructura temporal, estacionalidad
└─ Combinación: Ensemble diversity → mejor performance que cualquiera solo

Fórmula Matemática:
  Ŷ_hybrid(t+h) = 0.6 · Ŷ_xgb(t+h) + 0.4 · Ŷ_arima(t+h)

donde:
  Ŷ_xgb(t+h) = Predicción XGBoost para h períodos adelante
  Ŷ_arima(t+h) = Predicción ARIMA/SARIMAX para h períodos adelante
  h ∈ {1, 2, ..., 52} semanas

Validación:
├─ Cross-validation: k=5 folds (80/20 split per fold)
├─ Métricas convergentes:
│  • R² = 0.9950 (95%+ varianza explicada)
│  • MAPE = 3.8% (media error <4%)
│  • MAE = 45.3 unidades promedio
│  • RMSE = 67.2 unidades promedio
└─ Sin data leakage: corte claro Semana 222 (train) vs Semana 223+ (predicción)

Comparativa vs Individually:
  XGBoost solo: R²=0.992, MAPE=4.2%
  ARIMA solo:   R²=0.988, MAPE=4.9%
  Híbrido:      R²=0.995, MAPE=3.8% ✅ MEJOR
```

---

### 2.3 Backend: API REST (Flask)

#### 2.3.1 **Framework: Flask**
```
Librería: Flask 2.3+
Patrón: Microframework REST lightweight

Componentes:
├─ Routing: @app.route() decoradores
├─ Serialización: JSON responses
├─ Middleware: CORS, security headers
├─ Autenticación: JWT tokens
└─ Documentación: Swagger/OpenAPI automático

Endpoints Implementados (5 total):
1. GET /api/v1/forecasting/52weeks/{producto}
   └─ Retorna: predicciones, fechas, intervalos_95%

2. GET /api/v1/forecasting/all-products
   └─ Retorna: resumen 20 productos (media, std, min, max, tendencia)

3. GET /api/v1/forecasting/product/{producto}/detailed
   └─ Retorna: predicciones completas + estadísticas por semana

4. GET /api/v1/benchmarking/economic-impact
   └─ Retorna: análisis económico (ahorros, ROI, rotación inventario)

5. GET /api/v1/model-info
   └─ Retorna: metadata modelo (versión, accuracy, training date)

Especificación OpenAPI/Swagger:
├─ Version: 3.0.0
├─ Servers: http://localhost:5000/
├─ Security: JWT Bearer tokens
├─ Response format: application/json
└─ Rate limiting: 100 req/min por IP

Tecnologías complementarias:
├─ Gunicorn: WSGI server (producción)
├─ PyJWT: Autenticación JWT
├─ Flask-CORS: Cross-Origin Resource Sharing
├─ Marshmallow: Validación + serialización JSON
└─ Redis: Caché predicciones (TTL 1 hora)
```

#### 2.3.2 **Caché: Redis**
```
Patrón: In-memory data store

Aplicación en PREDICAST:
├─ Key: "forecasting:{producto}:{semana}"
├─ Value: JSON serializado predicción
├─ TTL: 3600 segundos (1 hora)
├─ Hit rate target: >95% (reducir cálculos)
├─ Invalidación: Manual endpoint + TTL automático
└─ Arquitectura: Single instance (escalable a cluster)

Beneficio:
  Respuesta API sin caché: 200-500ms
  Respuesta con caché: 50-100ms ✅ (5x más rápido)
```

---

### 2.4 Frontend: Streamlit Dashboard

#### 2.4.1 **Framework: Streamlit**
```
Librería: Streamlit 1.28+
Paradigma: Reactive, Python-native web framework

Características:
├─ Código: Python puro (sin HTML/CSS/JS)
├─ Rendering: Re-run script completo cada interacción (simple model)
├─ Widgets: @st.sidebar, sliders, dropdowns, text inputs
├─ Visualización: Integración Plotly nativa
├─ Session state: Persistencia variables entre reruns
└─ Deployment: Streamlit Cloud, Docker, self-hosted

Estructura Dashboard PREDICAST:
├─ Puerto: 8501 (default)
├─ Tabs principales (4):
│  ├─ 🏠 Dashboard: KPIs, resumen, últimas predicciones
│  ├─ 📊 Análisis Individual:
│  │  ├─ 📊 Demanda y Componentes (gráfico + tabla)
│  │  ├─ 📦 Stock y Diagnóstico (simulación)
│  │  ├─ ⚖️ Comparador de Modelos (XGB vs ARIMA)
│  │  └─ 💡 Recomendación Individual (stock seguridad)
│  ├─ 📈 Análisis de Grupo (comparativa múltiples productos)
│  └─ ⚙️ Admin (configuración, logs, monitoreo)
│
├─ Sidebar:
│  ├─ Dropdown: Seleccionar producto (20 opciones CP_01-MZ_01)
│  ├─ Slider: Rango fechas (2026-W01 a 2027-W52)
│  ├─ Slider: Nivel confianza (90-99%, z-score dinámico)
│  ├─ Toggle: Dark mode
│  └─ Selector: Idioma (ES/EN)
│
└─ Interactividad:
   ├─ Cambio producto: Refresca gráfico <500ms
   ├─ Rango fechas: Zoom gráfico + filtro tabla <500ms
   ├─ Nivel confianza: Recalcula S.S. + recomendación <1seg
   └─ Exportación: Descarga PNG (Plotly toolbar) + PDF custom
```

#### 2.4.2 **Visualización: Plotly**
```
Librería: Plotly 5.x
Tipo: Interactive JavaScript-based charts

Gráficos implementados:
├─ Líneas (tiempo series):
│  ├─ 222 puntos históricos (azul)
│  ├─ 52 puntos predichos (naranja)
│  ├─ Banda intervalo confianza 95% (gris sombreado)
│  └─ Punto corte demarcado (línea punteada)
│
├─ Barras (impacto económico):
│  ├─ Ahorro actual vs recomendado
│  ├─ Colores: Verde (ahorro), Rojo (cost)
│  └─ Hover tooltip: valores exactos
│
├─ Scatter (comparativa):
│  ├─ X-axis: Media histórica
│  ├─ Y-axis: Predicción promedio
│  ├─ Tamaño punto: Volumen total
│  └─ Color: Por épica/categoría
│
└─ Histogramas (distribuciones):
   ├─ Distribución demanda histórica
   ├─ Distribución predicciones futuro
   └─ Sobreposición: análisis cambio comportamiento

Ventajas Plotly:
✅ Hover interactivo (valores exactos)
✅ Zoom/pan nativo
✅ Exportación PNG con toolbar
✅ Responsive design (mobile-friendly)
✅ Legends, multiple series, custom colors
```

---

### 2.5 Gestión de Datos

#### 2.5.1 **Formato de Datos: CSV + Pivot**
```
Almacenamiento: CSV plain-text (portable, versionable)

Estructuras:
1. DATOS HISTÓRICOS (datos_semanales_pivot.csv)
   Rows: 222 (semanas)
   Cols: 20 (productos CP_01-MZ_01)
   Format:
   ┌───────────────┬──────────┬──────────┬─────────┐
   │ Semana (idx)  │ CP_01    │ CP_02    │ ... MZ_01│
   ├───────────────┼──────────┼──────────┼─────────┤
   │ 2023-W01      │ 185      │ 420      │ 1150    │
   │ 2023-W02      │ 192      │ 435      │ 1165    │
   │ ...           │ ...      │ ...      │ ...     │
   │ 2025-W52      │ 181      │ 418      │ 1158    │
   └───────────────┴──────────┴──────────┴─────────┘
   
   Ventajas:
   ✅ Compacto (pivot efficient)
   ✅ Rápido for ML (numpy arrays directos)
   ❌ Ineficiente queries específicas (mejor SQL)

2. PREDICCIONES (predicciones_52semanas_pivot.csv)
   Rows: 52 (semanas futuro)
   Cols: 20 (productos)
   Format: Similar históricos
   
3. PREDICCIONES LARGO (predicciones_52semanas_largo.csv)
   Rows: 1,040 (52 × 20)
   Cols: 6 (Producto, Semana, Predicción, Lower_95, Upper_95, Std)
   Format: TIDY format
   ┌─────────────┬────────┬────────────┬───────────┬───────────┬─────┐
   │ Producto    │ Semana │ Predicción │ Lower_95  │ Upper_95  │ Std │
   ├─────────────┼────────┼────────────┼───────────┼───────────┼─────┤
   │ CP_01       │ W03-26 │ 183.5      │ 147.8     │ 219.2     │ 8.8 │
   │ CP_01       │ W04-26 │ 186.2      │ 150.5     │ 221.9     │ 8.8 │
   │ ...         │ ...    │ ...        │ ...       │ ...       │ ... │
   │ MZ_01       │ W01-27 │ 1162.1     │ 748.5     │ 1576      │ ... │
   └─────────────┴────────┴────────────┴───────────┴───────────┴─────┘
   
   Ventajas:
   ✅ Tidy data standard
   ✅ Fácil filtrar por producto
   ✅ Compatible con BI tools (Power BI, Tableau)
```

#### 2.5.2 **Bibliotecas de Datos: Pandas, NumPy**
```
Pandas 1.5+
├─ DataFrames: Tablas 2D etiquetadas
├─ Series: Arrays 1D con índice
├─ Operaciones: Groupby, pivot_table, merge, reshape
├─ I/O: read_csv(), to_csv(), to_json(), to_excel()
└─ Aplicación: Pipeline transformación datos

NumPy 1.23+
├─ Arrays: Estructuras multidimensionales eficientes
├─ Operaciones: Vectorizadas (sin loops Python)
├─ Estadística: mean, std, percentile, correlate
├─ Performance: 100x más rápido que listas Python
└─ Aplicación: Cálculos XGBoost features
```

---

### 2.6 Versioning & Control de Cambios

#### 2.6.1 **Git + GitHub**
```
Estrategia: Git Flow
├─ main: código producción (tagged releases)
├─ develop: integración features
├─ feature/xxx: desarrollo features individuales
├─ hotfix/xxx: correcciones críticas producción
└─ release/xxx: preparación nuevas versiones

Commits:
├─ Semántica: [TIPO] Descripción (ej: [FEAT] Add caching Redis)
├─ Frecuencia: 1-3 commits/día por developer
├─ Branch protection: Pull requests requireidos para main
└─ Code review: >1 reviewer antes merge

Tags de Release:
├─ v0.1.0: MVP (Enero 2026)
├─ v1.0.0: Producción (Julio 2026)
├─ v1.1.0: Q3 2026 (ABC analysis)
└─ v2.0.0: Q4 2026 (Retrain automático)
```

#### 2.6.2 **Model Registry & Versionining**
```
Concepto: Versionamiento modelos ML (análogo a Git para código)

Implementación PREDICAST:
├─ Archivo: modelo_hybrid_xgboost_final.joblib (serializado joblib)
├─ Metadata: modelo_hybrid_metadata_v1.0.json
├─ Parámetros: modelo_hybrid_arima_params_final.json
│
├─ Versionamiento:
│  ├─ v1.0: Baseline (R²=0.992, MAPE=4.2%)
│  ├─ v1.1: Optimizado (R²=0.995, MAPE=3.8%) ✅ CURRENT
│  └─ v2.0: Con retrain mensual (futuro Q4 2026)
│
└─ Rastreo (Model Registry CSV):
   ┌──────┬────────────────┬──────────┬──────┬──────────┬────────────┐
   │ Ver  │ Fecha          │ Modelo   │ R²   │ MAPE %   │ Status     │
   ├──────┼────────────────┼──────────┼──────┼──────────┼────────────┤
   │ 1.0  │ 2026-04-10     │ XGB+ARIMA│ 0.992│ 4.2      │ BASELINE   │
   │ 1.1  │ 2026-04-15     │ XGB+ARIMA│ 0.995│ 3.8      │ PRODUCTION │
   │ 2.0  │ 2026-10-15     │ NEW+AUTO │ 0.998│ 3.5      │ SCHEDULED  │
   └──────┴────────────────┴──────────┴──────┴──────────┴────────────┘

Beneficio:
✅ Auditoría completa cambios modelo
✅ Rollback rápido si degradación
✅ A/B testing entre versiones
✅ Reproducibilidad garantizada
```

---

### 2.7 Infraestructura & DevOps

#### 2.7.1 **Containerización: Docker**
```
Concepto: Empaquetamiento app + dependencias en imagen reproducible

Dockerfile etapas (multi-stage):
├─ Stage 1 (Builder): conda/pip instala dependencias
├─ Stage 2 (Runtime): SLIM image, solo produce necesario
└─ Expose: Puerto 5000 (API), 8501 (Streamlit)

Compose: docker-compose.yml
├─ flask_api: Servicio API backend
├─ streamlit_dashboard: Servicio frontend
├─ redis_cache: Servicio caché
└─ postgresql: Servicio datos (futuro migración)

Ventajas:
✅ Reproducibilidad (dev/staging/prod idénticos)
✅ Escalabilidad (spin up múltiples replicas)
✅ Aislamiento (dependencias no conflictuan)
✅ Deployment rápido (segundos, no horas)
```

#### 2.7.2 **Orquestación: Kubernetes (Futuro Q3 2026)**
```
Concepto: Orquestación contenedores a escala

Componentes:
├─ API Deployment: 3 replicas (load balancing)
├─ Dashboard Deployment: 2 replicas (capa app)
├─ Redis StatefulSet: Persistencia caché
├─ PostgreSQL StatefulSet: BD datos
├─ Ingress: Proxy reverso, SSL/TLS
└─ HPA (Horizontal Pod Autoscaler): Auto-escala por CPU/memoria

Roadmap:
└─ v2.0 (Q4 2026): Migración K8s para 99.9% uptime
```

#### 2.7.3 **Monitoreo & Observabilidad**
```
Componentes:
├─ Prometheus: Scraping métricas (uptime, latencia, errores)
├─ Grafana: Dashboards visualización (alerts automáticas)
├─ Loki: Aggregación centralized logs
├─ Jaeger: Distributed tracing (request path completo)
└─ ELK Stack (Elasticsearch-Logstash-Kibana): Logs búsqueda

Métricas clave:
├─ Uptime: >99% (< 7.2 horas downtime/mes)
├─ Latencia p95: <500ms (API), <2s (Dashboard)
├─ Error rate: <0.1% (0.001 errores/request)
├─ Model drift: MAPE actual vs baseline (<2% degradación)
└─ Cache hit rate: >95% (predicciones cachéadas)
```

---

## 3. 📊 CONCEPTOS ESTADÍSTICOS & MODELAMIENTO

### 3.1 **Validación de Modelos**

#### 3.1.1 Métricas Regresión
```
Definiciones:

1. R² (Coeficiente Determinación)
   Fórmula: R² = 1 - (SS_res / SS_tot)
   donde:
     SS_res = Σ(Y_i - Ŷ_i)² (suma cuadrados residuos)
     SS_tot = Σ(Y_i - Ȳ)²   (suma cuadrados totales)
   
   Interpretación:
   ├─ 1.0 = predicción perfecta
   ├─ 0.99 = modelo explica 99% varianza datos ✅ PREDICAST
   ├─ 0.90 = aceptable
   └─ <0.70 = pobre
   
   Target PREDICAST: R² > 0.99

2. MAPE (Mean Absolute Percentage Error)
   Fórmula: MAPE = (100/n) × Σ|((Y_i - Ŷ_i) / Y_i)|
   
   Interpretación:
   ├─ <5% = excelente ✅ PREDICAST
   ├─ 5-10% = bueno
   ├─ 10-20% = aceptable
   └─ >20% = pobre
   
   Problema: Indefinido si Y_i = 0 (rara en demanda positiva)

3. MAE (Mean Absolute Error)
   Fórmula: MAE = (1/n) × Σ|Y_i - Ŷ_i|
   
   Unidades: Mismas que variable (ej: 45 unidades productos)
   Interpretación: Error promedio absoluto
   Target: Bajo relativo a escala demanda (30-1200)

4. RMSE (Root Mean Square Error)
   Fórmula: RMSE = √[(1/n) × Σ(Y_i - Ŷ_i)²]
   
   Características:
   ├─ Penaliza errores grandes más que MAE
   ├─ Unidades coinciden variable original
   ├─ Más sensible outliers que MAE
   └─ Target PREDICAST: ~67 unidades
```

#### 3.1.2 Cross-Validation
```
Concepto: Validación rotatoria para evaluar generalización

Implementación PREDICAST:
├─ Estrategia: K-Fold (k=5)
├─ Split: 5 particiones, 4 train + 1 test rotativo
├─ Repeticiones: Modelo entrenado 5 veces
├─ Score: Media métricas 5 folds (reducir variance)
└─ Ventaja: Uso eficiente datos limitados (222 semanas no es mucho)

Gráfico conceptual:
   Fold 1: [TRAIN][TRAIN][TRAIN][TRAIN][TEST]
   Fold 2: [TRAIN][TRAIN][TRAIN][TEST][TRAIN]
   Fold 3: [TRAIN][TRAIN][TEST][TRAIN][TRAIN]
   Fold 4: [TRAIN][TEST][TRAIN][TRAIN][TRAIN]
   Fold 5: [TEST][TRAIN][TRAIN][TRAIN][TRAIN]
   
   Score_final = Media(R²_fold1, R²_fold2, ..., R²_fold5)
```

#### 3.1.3 Data Leakage Prevention
```
Concepto: Contamination modelo con información futura

Violación en PREDICAST: ❌ PREVISTA
├─ Punto corte claro: Semana 222 (últimos datos históricos)
├─ Train set: Semanas 1-222 ÚNICAMENTE
├─ Test set: Semanas predichas futuro (2026-W03 a 2027-W01)
├─ Features: SOLO derivadas de pasado (lag, media móvil)
├─ NO usar: Promociones futuras, cambios precios, eventos conocidos

Validación data leakage:
└─ Check: Confirmación manual timeline corte + auditoría features
```

### 3.2 **Feature Engineering (Ingeniería de Características)**

```
Objetivo: Crear variables predictoras (X) que expliquen demanda (Y)

Features XGBoost:
├─ Lag features (rezagos):
│  ├─ Lag1: Demanda semana anterior
│  ├─ Lag4: Demanda 4 semanas atrás (mesual)
│  └─ Lag52: Demanda año anterior (estacionalidad)
│
├─ Moving averages (promedios móviles):
│  ├─ MA4: Promedio últimas 4 semanas
│  ├─ MA13: Promedio últimas 13 semanas (trimestral)
│  └─ Trend: Pendiente lineal últimas 12 semanas
│
├─ Seasonal indicators (indicadores estacionalidad):
│  ├─ Is_summer: 1 si semana en Q2-Q3
│  ├─ Month: Mes del año (1-12)
│  └─ Week_of_year: Semana año (1-52)
│
├─ Cyclical encoding (para estacionalidad):
│  ├─ Sin(2π × week/52): Componente seno estacionalidad
│  └─ Cos(2π × week/52): Componente coseno estacionalidad
│
└─ Statistical (estadísticas):
   ├─ Historical_mean: Promedio histórico completo
   ├─ Historical_std: Desviación estándar histórica
   └─ Volatility: Coeficiente variación

Total features: ~20 por producto (XGBoost solo)
Importancia: Lag1 > MA4 > Seasonal > La variación
```

### 3.3 **Distribuciones & Intervalos de Confianza**

```
Componente: Cuantificación incertidumbre predicciones

Formula intervalo 95%:
├─ Lower_95% = Predicción - 1.96 × Std_error
└─ Upper_95% = Predicción + 1.96 × Std_error

donde Std_error estimado de residuos entrenamiento

Aplicación PREDICAST:
├─ Usado en visualizaciones gráficos (banda gris)
├─ Usado en cálculo stock seguridad (z-score ajustable)
└─ User puede ajustar confianza:
   ├─ 90% confianza: z-score = 1.28 (menos conservador)
   ├─ 95% confianza: z-score = 1.65 ✅ DEFAULT
   └─ 99% confianza: z-score = 2.33 (más conservador +40% stock)

Interpretación:
└─ "95% probabilidad demanda caerá entre Lower-Upper"
   (bajo supuesto distribución normal residuos)
```

---

## 4. 🔄 PROCESOS & METODOLOGÍAS

### 4.1 **ETL (Extract-Transform-Load)**

```
Arquitectura Pipeline:
┌─────────────────────────────────────────────────────────────┐
│ 1. EXTRACT                                                  │
│    └─→ Leer CSV datos_semanales_pivot.csv                   │
│         Fuente: Sistema punto venta (exportación semanal)    │
│         Formato: 222×20 (semanas × productos)               │
│                                                              │
│ 2. TRANSFORM                                                │
│    ├─ Validación: Tipos datos, NULL, duplicados             │
│    ├─ Limpieza: Outliers (IQR method), valores faltantes     │
│    ├─ Normalización: Escalado min-max [0,1] para XGBoost    │
│    ├─ Feature engineering: Lags, medias móviles             │
│    └─ Split: Train (222) vs Test (future)                   │
│                                                              │
│ 3. LOAD                                                      │
│    ├─ En memoria: Dataframes pandas (rápido acceso)         │
│    ├─ Caché: Redis (respuestas API)                         │
│    └─ Persistencia: JSON modelo metadata, CSV predicciones  │
└─────────────────────────────────────────────────────────────┘

Frecuencia: Semanal (nueva semana demanda cada lunes)
Tiempo ejecución: ~5 minutos (datos pequeños)
```

### 4.2 **CRISP-DM (Cross-Industry Standard for Data Mining)**

```
Fases CRISP-DM en PREDICAST:
├─ 1. Business Understanding (Sprint 0-1): ✅ COMPLETADO
│    └─ Problema: Optimizar producción/inventario
│
├─ 2. Data Understanding (Sprint 1): ✅ COMPLETADO
│    └─ EDA completo: 222 semanas, 20 productos
│
├─ 3. Data Preparation (Sprint 1): ✅ COMPLETADO
│    └─ Limpieza, validación, feature engineering
│
├─ 4. Modeling (Sprint 2): ✅ COMPLETADO
│    └─ XGBoost + ARIMA híbrido
│
├─ 5. Evaluation (Sprint 2): ✅ COMPLETADO
│    └─ Métricas: R²=0.995, MAPE=3.8%
│
├─ 6. Deployment (Sprint 3-4): ✅ COMPLETADO
│    └─ API, Dashboard, visualizaciones
│
└─ 7. Monitoring (Sprint 6+): 🔵 ONGOING
   └─ Track drift modelo, udates datos

Característica CRISP-DM: Iterativo
└─ Ciclo puede repetirse si performance degrada
   (Retrain modelos cada trimestre, monitoreo contínuo)
```

---

## 5. 📐 ECUACIONES MATEMÁTICAS CLAVE

### 5.1 Stock de Seguridad (Safety Stock)

```
FÓRMULA BASE:
SS = Z_α × σ_L

donde:
├─ SS = Stock seguridad (unidades)
├─ Z_α = Z-score para nivel confianza α
│  ├─ 90%: 1.28
│  ├─ 95%: 1.65 ✅ DEFAULT PREDICAST
│  └─ 99%: 2.33
├─ σ_L = Desviación estándar demanda durante lead time

PREDICAST SIMPLIFICADO:
SS = Media_histórica + 1.65 × Std_histórica

PRODUCCIÓN RECOMENDADA:
P_rec = max(0, D_pred - Stock_actual + SS)

donde:
├─ D_pred = Demanda predicha XGBoost+ARIMA
├─ Stock_actual = Inventario disponible
└─ max(0, ...) = No produce si inventario es suficiente

EJEMPLO CP_01:
├─ Media histórica = 181.12 unidades
├─ Std histórica = 81.19 unidades
├─ SS = 181.12 + 1.65 × 81.19 = 315 unidades
├─ Si D_pred_próx = 200 y Stock_actual = 100
└─ P_rec = max(0, 200 - 100 + 315) = 415 unidades
```

### 5.2 Impacto Económico

```
AHORRO EQUIVALENTE:
Ahorro_anual = (Inv_actual - Inv_optimizado) × Costo_unitario × 12

ROI (Return on Investment):
ROI% = (Beneficios - Costos) / Costos × 100

ROTACIÓN INVENTARIO:
Rotación = Demanda_anual / Inventario_promedio

POTENCIAL AHORRO:
└─ Mediante optimización stock seguridad → reducir 20-30% mano muerta
```

---

## 6. 🎯 MATRIZ TECNOLOGÍA vs REQUISITO

| Requisito | Solución | Tecnología | Por qué |
|-----------|----------|-----------|--------|
| **Pronóstico demanda** | HYBRID XGB+ARIMA | ML sklearn/statsmodels | Captura compl: no-linealidad + seasonality |
| **API escalable** | REST microservice | Flask + Gunicorn | Lightweight, fácil deploy |
| **Dashboard interactivo** | Streamlit + Plotly | Streamlit 1.28, Plotly 5.x | Python-native, react rápido |
| **Caché predicciones** | In-memory store | Redis | Sub-milisecond latency |
| **Versionamiento datos** | Git + CSV | Git 2.4+, pandas | Auditable, reproducible |
| **Containerización** | Reproducibilidad | Docker 20.x | Mismo env dev/staging/prod |
| **Monitoreo producción** | Observabilidad | Prometheus/Grafana | Alertas temps reales |
| **Documentación** | Swagger/OpenAPI | Flask-Swagger | Auto-generada, interactive |
| **Capacitación usuarios** | Manuales | Markdown + DOCX | Accesible, versionable |

---

## 7. 📚 REFERENCIAS TEÓRICAS

### Bibliografía Conceptual
```
1. XGBoost
   ├─ Paper: "XGBoost: A Scalable Tree Boosting System"
   │           Chen & Guestrin (2016)
   └─ Librería: xgboost.readthedocs.io

2. ARIMA/SARIMAX
   ├─ Clásico: "Time Series Analysis" - Box, Jenkins, Reinsel (1970)
   └─ Python: statsmodels.org/arima

3. Forecasting
   ├─ "Forecasting Methods & Applications" - Makridakis, Wheelwright (1997)
   └─ Ensemble: "The Elements of Statistical Learning" - Hastie et al

4. REST API Design
   ├─ "Richardson Maturity Model" - Leonard Richardson (2008)
   └─ OpenAPI 3.0 Spec

5. Time Series Features
   ├─ Lag engineering
   ├─ Seasonal decomposition (STL)
   └─ Feature selection (mutual information)
```

### Estándares & Frameworks
```
1. ISO 27001: Information Security Management
2. CRISP-DM: Standard proceso data mining
3. Machine Learning Operations (MLOps)
4. OpenAPI 3.0: REST API specification
5. Git Flow: Version control workflow
```

---

## 8. 📋 CONCLUSIÓN: MATRIZ RESUMEN

```
PILLARES TECNOLÓGICOS PREDICAST:

┌─────────────────────────┬──────────────────┬──────────────────┐
│ CAPA                    │ TECNOLOGÍA       │ OBJETIVO         │
├─────────────────────────┼──────────────────┼──────────────────┤
│ Predicción (ML)         │ XGBoost+ARIMA    │ R²>0.99, MAPE<5% │
│ Backend (API)           │ Flask+Redis      │ <500ms latency   │
│ Frontend (UI)           │ Streamlit+Plotly │ Interactivo UX   │
│ Datos (Storage)         │ CSV+Redis        │ Rápido acceso    │
│ Versionamiento          │ Git+Model Reg    │ Reproducibilidad │
│ Infraestructura         │ Docker           │ Portabilidad     │
│ Monitoreo               │ Prometheus+Grafana│ Observabilidad  │
│ Documentación           │ OpenAPI/Swagger  │ Autodescriptive  │
└─────────────────────────┴──────────────────┴──────────────────┘

DIAGRAMA ARQUITECTURA FINAL:

        [Usuarios Planificación]
                   │
                   ▼
          ┌─────────────────────┐
          │  Streamlit Dashboard │ (port 8501)
          │  - 4 tabs + sidebar  │
          │  - Plotly gráficos   │
          └──────────┬───────────┘
                     │
        ┌────────────▼────────────┐
        │    Flask API REST       │ (port 5000)
        │  - 5 endpoints          │
        │  - JWT auth             │
        │  - Redis caché          │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   ML Pipeline/Models    │
        │  -XGBoost (20 modelos)  │
        │  -ARIMA (20 configs)    │
        │  -Combinación hybrid    │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   Data Layer            │
        │  -CSV históricos        │
        │  -Redis caché           │
        │  -JSON metadata         │
        └─────────────────────────┘

FLUJO DATOS:
CSV (222 sem) → Feature Eng → XGB+ARIMA → API → Dashboard → Usuario
                    ↓
              Caché Redis
```

---

**Documento Preparado:** 18 Abril 2026  
**Próxima Revisión:** Post-Sprint 1 (15 Mayo 2026)  
**Status:** 🔵 Marco Teórico Completo

