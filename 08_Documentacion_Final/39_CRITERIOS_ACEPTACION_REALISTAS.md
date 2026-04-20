# 📋 CRITERIOS DE ACEPTACIÓN REALISTAS - PREDICAST v4.0
## 39 Historias de Usuario con Criterios Verificables

**Documento realista basado en funcionalidades actuales del sistema**  
**Última actualización:** 18 de Abril de 2026

---

## ÉPICA 001: CARGA Y CONSOLIDACIÓN DE DATOS

### HU001 - Carga exitosa de datos semanales
**Criterio:** Validación de importación y consolidación

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Sistema operativo, archivo `datos_semanales_pivot.csv` con 222 filas (semanas) × 20 columnas (productos) |
| **Cuando** | El sistema ejecuta `cargar_datos_forecasting()` en `forecasting_routes.py` |
| **Entonces** | ✅ `PREDICCIONES` cargado en memoria con shape (20, 52)  |
| | ✅ Productos: ['CP_01', 'CP_02',...'MZ_01'] (20 total) |
| | ✅ Tiempo carga: <2 segundos |
| | ✅ Variables globales: `PREDICCIONES`, `PREDICCIONES_LARGO`, `ESTADISTICAS`, `METADATA` |

---

### HU002 - Validación de integridad de fechas en predicciones
**Criterio:** Formato correcto de semanas ISO

| Aspecto | Detalle |
|---------|---------|
| **Dado** | DataFrames cargados con índices de predicciones |
| **Cuando** | Se verifica formato de semanas en `predicciones_52semanas_pivot.csv` |
| **Entonces** | ✅ Formato: `2026-W03`, `2026-W04`, ... `2027-W01` (ISO 8601) |
| | ✅ No existen valores vacíos (NULL count = 0) |
| | ✅ Rango temporal: 52 semanas consecutivas sin gaps |
| | ✅ Todas las predicciones >= 0 (no valores negativos) |

---

### HU003 - Consolidación en tabla única
**Criterio:** Estructura flat de predicciones

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Predicciones generadas en pivot (productos × semanas) |
| **Cuando** | Sistema genera `predicciones_52semanas_largo.csv` (tidy format) |
| **Entonces** | ✅ 1,040 registros (52 semanas × 20 productos) |
| | ✅ Columnas: `Producto_codigo`, `Semana`, `Prediccion`, `Lower_Bound_95`, `Upper_Bound_95` |
| | ✅ Intervalo de confianza 95%: Lower < Prediccion < Upper (100% de casos) |
| | ✅ Sin duplicados (producto_codigo + semana es unique key) |

---

### HU004 - Visualización de resumen de datos
**Criterio:** Información visible en dashboard

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Dashboard Streamlit iniciado en puerto 8501 |
| **Cuando** | Usuario accede a sección "🏠 Dashboard" |
| **Entonces** | ✅ Muestra período: 222 semanas históricas cargadas |
| | ✅ 20 productos procesados: CP_01 a MZ_01 |
| | ✅ Modelo: HYBRID_XGBoost_ARIMA (60% + 40%) |
| | ✅ R² histórico: >0.99 |
| | ✅ MAPE promedio: <5% |

---

## ÉPICA 002: ENTRENAMIENTO Y VALIDACIÓN DE MODELOS

### HU005 - Entrenamiento XGBoost con modelos pre-cargados
**Criterio:** Modelos disponibles en producción

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Archivo `modelo_hybrid_xgboost_final.joblib` existe en `03_Modelos/` |
| **Cuando** | `forecasting_routes.py` ejecuta `cargar_datos_forecasting()` (línea 33) |
| **Entonces** | ✅ Modelos cargados: 20 modelos XGBoost (uno por producto) |
| | ✅ Confirmación: `[✅] Modelos XGBoost cargados: 20 productos` |
| | ✅ Modelos EN MEMORIA, listos para predicción sin re-entrenar |
| | ✅ Tamaño: ~5-10 MB en memoria RAM |

---

### HU006 - Parámetros ARIMA cargados
**Criterio:** Configuración ARIMA disponible

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Archivo `modelo_hybrid_arima_params_final.json` existe |
| **Cuando** | Sistema carga parámetros en línea 39 |
| **Entonces** | ✅ 20 conjuntos de parámetros cargados (uno por producto) |
| | ✅ Estructura por producto: `{"order": [1,1,1], "seasonal_order": [1,1,1,52]}` |
| | ✅ Confirmación: `[✅] Parámetros ARIMA cargados: 20 productos` |

---

### HU007 - Verificación de modelo híbrido
**Criterio:** Combinación 60% XGBoost + 40% ARIMA

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Ambos modelos (XGBoost y ARIMA) cargados en memoria |
| **Cuando** | Sistema ejecuta predicción mediante `predict_hybrid_with_loaded_models()` |
| **Entonces** | ✅ Fórmula aplicada: `pred_hybrid = 0.6 × pred_xgb + 0.4 × pred_arima` |
| | ✅ Resultado final: 52 predicciones por producto |
| | ✅ Valores validados: todos >= 0 (sin negativos) |
| | ✅ Metadata guardada confirmando: HYBRID_XGB_ARIMA en `resumen_predicciones_hibrido.json` |

---

### HU008 - Validación sin data leakage en histórico
**Criterio:** Datos históricos separados de predicción

| Aspecto | Detalle |
|---------|---------|
| **Dado** | 222 semanas de datos históricos en `datos_semanales_pivot.csv` |
| **Cuando** | Sistema genera predicciones para próximas 52 semanas |
| **Entonces** | ✅ Punto de corte claro: Semana histórica 222 vs Semana predicha 1 |
| | ✅ No hay overlap temporal: última histórica != primera predicha |
| | ✅ Modelos entrenados solo con 222 semanas históricas |
| | ✅ Predicciones generadas hacia futuro: 2026-W03 a 2027-W01 |

---

### HU009 - Reporte de métricas por producto
**Criterio:** Metadata validada de modelos

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Archivo `modelo_hybrid_metadata_v1.0.json` cargado |
| **Cuando** | Usuario consulta estadísticas en `forecasting_routes.py` endpoint `/model-info` |
| **Entonces** | ✅ Tabla con 20 productos mostrando:  |
| | - CP_01: volumen_promedio=181.12, std=81.19 |
| | - CP_09: volumen_promedio=665.37, std=282.89 |
| | - MZ_01: volumen_promedio=1163.36, std=484.79 |
| | ✅ Todos productos con `datos_disponibles: 222` semanas |
| | ✅ Tiempos de entrenamiento: 25-56 segundos (histórico) |

---

### HU010 - Comparación vs línea base histórica
**Criterio:** Validación de precisión del modelo

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Modelo HYBRID entrenado con 222 semanas |
| **Cuando** | Sistema reporta métricas en `resumen_predicciones_hibrido.json` |
| **Entonces** | ✅ Estadísticas de predicciones: |
| | - Media: variable por producto (rango 30-1200) |
| | - Std: proporcional a volumen |
| | - Min: >= 0 |
| | - Max: realista vs histórico |
| | ✅ Modelo listo para producción (estado: "LISTO PARA PRODUCCIÓN") |

---

## ÉPICA 003: MOTOR DE RECOMENDACIÓN

### HU011 - Cálculo de stock de seguridad
**Criterio:** Fórmula de stock de seguridad 95% service level

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Predicciones disponibles con media y desviación estándar por producto |
| **Cuando** | Dashboard ejecuta análisis de recomendación (líneas 750-1181 en dashboard_v4.py) |
| **Entonces** | ✅ Fórmula: `Stock_Seguridad = media + 1.65 × std` |
| | ✅ Ejemplo CP_01: Media=181.12, Std=81.19 → S.S.≈315 unidades |
| | ✅ Nivel de servicio: 95% (z=1.65) |
| | ✅ Valor calculado visible en recomendación individual |

---

### HU012 - Recomendación semanal por producto
**Criterio:** Cálculo de producción recomendada

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Stock actual, demanda predicha, stock seguridad conocidos |
| **Cuando** | Usuario selecciona producto en tab "💡 Recomendación Individual" |
| **Entonces** | ✅ Sistema calcula: `Prod_Recom = max(0, Demanda - Stock_Actual + S.S.)` |
| | ✅ Visualiza: número recomendado en grande, justificación en texto |
| | ✅ Ejemplo: "SIN PRODUCCIÓN (stock suficiente)" o "PRODUCIR 150 unidades" |
| | ✅ Respuesta en <1 segundo |

---

### HU013 - Simulación de escenarios
**Criterio:** Visualización comparativa

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Plan de producción recomendado generado |
| **Cuando** | Usuario visualiza tab "📊 Stock y Diagnóstico" |
| **Entonces** | ✅ Gráfico muestra: Stock actual vs Stock con recomendación |
| | ✅ Línea roja: Proyecto sin cambios |
| | ✅ Línea verde: Proyección con recomendaciones |
| | ✅ Banda naranja: Zona de stock seguridad |
| | ✅ Identifica semanas críticas (rojo bajo línea) |

---

### HU014 - Ajuste de nivel de servicio
**Criterio:** Re-cálculo de parámetros dinámico

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Usuario puede ajustar z-score en sidebar |
| **Cuando** | Usuario cambia "Nivel de Confianza" de 95% a 99% |
| **Entonces** | ✅ Z-score cambia de 1.65 a 2.33 |
| | ✅ Stock de seguridad recalculado (+40% aproximadamente) |
| | ✅ Recomendaciones actualizadas automáticamente |
| | ✅ Visualización se refresca en <1 segundo |

---

### HU015 - Exportación de plan de 52 semanas
**Criterio:** Generación de archivo CSV

| Aspecto | Detalle |
|---------|---------|
| **Dado** | 1,040 recomendaciones calculadas (52 semanas × 20 productos) |
| **Cuando** | Usuario hace clic en botón "Descargar Plan de Producción CSV" |
| **Entonces** | ✅ Se genera archivo `plan_produccion_52semanas.csv` |
| | ✅ Columnas: Producto, Semana, Demanda_Predicha, Stock_Seguridad, Produccion_Recomendada |
| | ✅ 1,040 filas (verificables) |
| | ✅ Descarga en <2 segundos |
| | ✅ Encoding: UTF-8 |

---

## ÉPICA 004: DASHBOARD INTERACTIVO

### HU016 - Visualización serie histórica + pronóstico
**Criterio:** Gráfico combinado con intervalo de confianza

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Dashboard Streamlit con datos cargados (puerto 8501) |
| **Cuando** | Usuario abre tab "📊 Demanda y Componentes" |
| **Entonces** | ✅ Gráfico Plotly carga en <3 segundos |
| | ✅ Muestra: 222 puntos históricos (azul) |
| | ✅ 52 puntos predichos (naranja) |
| | ✅ Banda gris: intervalo confianza 95% |
| | ✅ Eje X: semanas, Eje Y: volumen |
| | ✅ Punto de corte marcado visualmente |

---

### HU017 - Cambio de producto mediante dropdown
**Criterio:** Actualización reactiva del dashboard

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Dropdown con 20 productos (CP_01 a MZ_01) |
| **Cuando** | Usuario selecciona "CP_09" |
| **Entonces** | ✅ Gráfico actualiza en <500ms |
| | ✅ Tabla de predicciones: 52 filas con datos de CP_09 |
| | ✅ Estadísticas recalculadas: Media=665.37, Std=282.89 |
| | ✅ Título actual: muestra código y nombre producto |

---

### HU018 - Tabla detallada de predicciones
**Criterio:** Display de 52 semanas

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Producto seleccionado en dropdown |
| **Cuando** | Usuario visualiza tabla en tab "⚖️ Comparador de Modelos" o "💡 Recomendación Individual" |
| **Entonces** | ✅ Tabla con 52 filas (una por semana) |
| | ✅ Columnas mínimas: Semana, Predicción, Lower_95%, Upper_95% |
| | ✅ Formato números: 2 decimales |
| | ✅ Scrolleable si necesario |
| | ✅ Actualiza en <1 segundo al cambiar producto |

---

### HU019 - Comparación múltiple de productos
**Criterio:** Análisis de Grupo

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Tab "📈 Análisis de Grupo" disponible |
| **Cuando** | Usuario selecciona múltiples productos (ej: CP_01, CP_09, CT_01) |
| **Entonces** | ✅ Gráfico muestra 3 líneas superpuestas (colores distintos) |
| | ✅ Leyenda identifica cada línea con código producto |
| | ✅ Escalas automáticas para visibilidad |
| | ✅ Carga en <2 segundos |

---

### HU020 - Filtro por rango de fechas
**Criterio:** Zoom temporal

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Slider de rango temporal en sidebar |
| **Cuando** | Usuario ajusta: inicio=2026-W09, fin=2026-W22 (Q2 2026) |
| **Entonces** | ✅ Gráfico zoomed a 14 semanas visibles |
| | ✅ Tabla filtrada a 14 filas |
| | ✅ Desempeño: <500ms actualización |

---

### HU021 - Cambio de idioma
**Criterio:** Soporte multiidioma

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Dashboard en español |
| **Cuando** | Usuario selecciona "English" en selector idioma (sidebar) |
| **Entonces** | ✅ Todos labels: "Demanda y Componentes" → "Demand & Components" |
| | ✅ Botones: "Descargar" → "Download" |
| | ✅ Tooltips: traducidos automáticamente |
| | ✅ Sesión guarda idioma (consulta localStorage o cookies) |

---

### HU022 - Descarga de gráficos
**Criterio:** Exportación de visualización

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Gráfico Plotly visible en pantalla |
| **Cuando** | Usuario hace clic en ícono "📥 Descargar" (toolbar Plotly) |
| **Entonces** | ✅ PNG generado: 1200×800px, resolución alta |
| | ✅ Título incluido en imagen |
| | ✅ Ejes etiquetados correctamente |
| | ✅ Descarga como `predicciones_[producto]_[fecha].png` |

---

## ÉPICA 005: API REST

### HU023 - Endpoint GET predicciones 52 semanas
**Criterio:** API forecasting operativa

| Aspecto | Detalle |
|---------|---------|
| **Dado** | API Flask iniciada en http://localhost:5000 |
| **Cuando** | Cliente realiza: `GET /api/v1/forecasting/52weeks/CP_01` |
| **Entonces** | ✅ Status: 200 OK |
| | ✅ JSON response contiene: |
| | - `"producto": "CP_01"` |
| | - `"predicciones": [174.5, 189.2, ..., 201.8]` (52 valores) |
| | - `"fechas_prediccion": ["W+1", "W+2", ..., "W+52"]` |
| | - `"intervalo_confianza_95_pct": {"lower": [...], "upper": [...]}` |
| | ✅ Tiempo respuesta: <500ms |

---

### HU024 - Endpoint GET todos los productos
**Criterio:** API lista completa

| Aspecto | Detalle |
|---------|---------|
| **Dado** | API operativa |
| **Cuando** | Cliente realiza: `GET /api/v1/forecasting/all-products` |
| **Entonces** | ✅ Status: 200 OK |
| | ✅ JSON array con 20 productos |
| | ✅ Cada producto contiene: |
| | - `"codigo": "CP_01"` |
| | - `"prediccion_media": 181.12` |
| | - `"prediccion_std": 81.19` |
| | - `"prediccion_min": 2.0` |
| | - `"prediccion_max": 335.0` |
| | - `"tendencia_52sem": "estable"/"creciente"/"decreciente"` |
| | ✅ Tiempo respuesta: <1 segundo |

---

### HU025 - Endpoint GET detalle completo
**Criterio:** API información detallada

| Aspecto | Detalle |
|---------|---------|
| **Dado** | API operativa |
| **Cuando** | Cliente realiza: `GET /api/v1/forecasting/product/CP_01/detailed` |
| **Entonces** | ✅ Status: 200 OK |
| | ✅ Response incluye: predicciones, fechas, intervalos, estadísticas |
| | ✅ Estructura completa para construir gráficos |

---

### HU026 - Análisis de impacto económico
**Criterio:** API benchmarking

| Aspecto | Detalle |
|---------|---------|
| **Dado** | API operativa, datos estadísticos disponibles |
| **Cuando** | Cliente realiza: `GET /api/v1/benchmarking/economic-impact` |
| **Entonces** | ✅ Status: 200 OK |
| | ✅ Response con análisis por producto: |
| | - `"ganancia_total_historica"`: valor estimado |
| | - `"margen_promedio_pct"`: porcentaje |
| | - `"rotacion_inventario"`: veces/año |
| | - `"potencial_ahorro_anual"`: S/. XX,XXX |
| | - `"roi_proyectado_pct"`: % |
| | ✅ Resumen total: ahorros agregados |

---

### HU027 - Documentación Swagger
**Criterio:** OpenAPI disponible

| Aspecto | Detalle |
|---------|---------|
| **Dado** | API en ejecución en localhost:5000 |
| **Cuando** | Usuario accede a `http://localhost:5000/api/docs` |
| **Entonces** | ✅ Interfaz Swagger UI carga en <2 segundos |
| | ✅ Lista de 5+ endpoints documentados |
| | ✅ Métodos: GET, POST viables y documentados |
| | ✅ Botón "Try it out" funcional |
| | ✅ Ejemplos de request/response visibles |

---

### HU028 - Validación de autenticación API
**Criterio:** Seguridad de endpoints

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Sistema de autenticación configurado (JWT) |
| **Cuando** | Cliente realiza request SIN token: `GET /api/v1/forecasting/all-products` |
| **Entonces** | ✅ Status: 401 Unauthorized |
| | ✅ Response: `{"error": "Token requerido"}` |
| **Y Cuando** | Cliente incluye token válido |
| **Entonces** | ✅ Status: 200 OK |
| | ✅ Datos retornados normalmente |

---

## ÉPICA 006: ANÁLISIS ECONÓMICO

### HU029 - Cálculo de impacto en inventario
**Criterio:** Reducción proyectada

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Recomendaciones calculadas para 52 semanas |
| **Cuando** | Dashboard ejecuta análisis "💰 Impacto Económico" |
| **Entonces** | ✅ Muestra métricas: |
| | - Inventario Promedio Actual: [valor base] |
| | - Inventario Promedio Recomendado: [valor optimizado] |
| | - Reducción %: calculada correctamente |
| | - Semanas de Cobertura Actual vs Recomendado |

---

### HU030 - Conversión a valor monetario
**Criterio:** Cálculo de ahorro

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Reducción de inventario calculada |
| **Cuando** | Sistema aplica costo unitario por producto |
| **Entonces** | ✅ Ahorro Semanal = Reducción × Costo_Unitario |
| | ✅ Ahorro Mensual y Anual proyectados |
| | ✅ Moneda: S/. (Soles) |
| | ✅ Display formato: S/. XX,XXX con decimales |

---

### HU031 - Comparativa KPIs escenarios
**Criterio:** Tabla comparativa

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Datos de escenario actual y optimizado |
| **Cuando** | Usuario visualiza "Comparativa de Escenarios" |
| **Entonces** | ✅ Tabla 2 columnas: Actual | Recomendado |
| | ✅ Filas: Rotación Inv., Días de Cobertura, Ahorro Anual, ROI |
| | ✅ Destacado: mejora % en cada métrica |

---

### HU032 - Gráfico ahorro acumulado mensual
**Criterio:** Tendencia temporal

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Proyecciones para 12 meses |
| **Cuando** | Usuario visualiza tab "Análisis de Impacto" |
| **Entonces** | ✅ Gráfico línea con puntos: Mes 1, Mes 2, ..., Mes 12 |
| | ✅ Eje Y: Ahorro acumulado en S/. |
| | ✅ Curva ascendente suave |
| | ✅ Línea punteada: proyección continuidad |

---

### HU033 - Exportación resumen ejecutivo
**Criterio:** Generación PDF

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Análisis económico completado |
| **Cuando** | Usuario hace clic en "Descargar Resumen PDF" |
| **Entonces** | ✅ PDF de 4-5 páginas generado |
| | ✅ Incluye: Portada, Resumen Ejecutivo, Gráficos, Tabla de Comparativa |
| | ✅ Fecha de generación incluida |
| | ✅ Nombre: `PREDICAST_Resumen_Ejecutivo_[fecha].pdf` |
| | ✅ Tamaño: <5 MB |

---

## ÉPICA 007: DOCUMENTACIÓN Y TRANSICIÓN

### HU034 - Manual de Usuario completado
**Criterio:** Documento de guía

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Sistema PREDICAST operativo |
| **Cuando** | Se revisa "Manual_de_Usuario_PREDICAST_v4.0.docx" |
| **Entonces** | ✅ Contiene:  |
| | - Portada con logo y versión |
| | - Tabla de contenidos |
| | - 1. Introducción al Sistema (problema + solución) |
| | - 2. Inicio de Sesión (credenciales) |
| | - 3. Interfaz Principal (tabs principales) |
| | - 4. Cómo Usar Cada Sección (paso a paso con screenshots) |
| | - 5. Interpretación de Recomendaciones |
| | - 6. Exportación de Reportes |
| | - 7. Troubleshooting |
| | ✅ 25-30 páginas, con imágenes incluidas |

---

### HU035 - Manual Técnico completado
**Criterio:** Documentación técnica

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Sistema en producción |
| **Cuando** | Se revisa "Manual_Tecnico_PREDICAST_v4.0.docx" |
| **Entonces** | ✅ Contiene:  |
| | - Diagrama arquitectura (Frontend-Backend-DB-ML) |
| | - Stack tecnológico (Streamlit, Flask, XGBoost, ARIMA) |
| | - Estructura de carpetas explicada |
| | - Endpoints API documentados (parámetros, responses) |
| | - Modelos ML: donde están guardados, cómo se cargan |
| | - Base de datos: esquema ERD (si aplica) |
| | - Logs y monitoreo: ubicaciones, formato |
| | - Procedimiento de deployment |
| | - Troubleshooting técnico (errores comunes + soluciones) |
| | ✅ 15-20 páginas técnicas |

---

### HU036 - Presentación de capacitación
**Criterio:** Sesión de entrenamiento

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Equipo de planificación disponible (8-15 personas) |
| **Cuando** | Se ejecuta sesión de capacitación en vivo (1.5 horas) |
| **Entonces** | ✅ Presentación con 30-40 slides: |
| | - Slide 1-5: Contexto + Problema original |
| | - Slide 6-10: Solución propuesta (PREDICAST) |
| | - Slide 11-15: Modelo ML explicado (no técnico) |
| | - Slide 16-25: Demo en VIVO (5 minutos interacción) |
| | - Slide 26-30: Interpretación de recomendaciones (casos reales) |
| | - Slide 31-35: Impacto económico esperado |
| | - Slide 36-40: Próximos pasos + Q&A |
| | ✅ Al final: Survey de entendimiento (>=95% entiende valor) |

---

### HU037 - Plan de Migración definido
**Criterio:** Estrategia de implementación

| Aspecto | Detalle |
|---------|---------|
| **Dado** | PREDICAST v4 listo para deployment |
| **Cuando** | Se revisa "Plan_Migracion_PREDICAST.docx" |
| **Entonces** | ✅ Especifica fases: |
| | - Fase 1 PILOTO (Semana 1-2): 5 productos, ambiente test |
| | - Fase 2 AMPLIACIÓN (Semana 3-4): 20 productos, validación |
| | - Fase 3 PRODUCCIÓN (Semana 5): Todos los productos, ambiente live |
| | ✅ Por cada fase: objetivos, recursos, riesgos, rollback plan |
| | ✅ Cronograma detallado con responsables |
| | ✅ Criterios de éxito por fase (KPIs) |

---

### HU038 - Procedimiento de mantenimiento
**Criterio:** Operaciones post-deployment

| Aspecto | Detalle |
|---------|---------|
| **Dado** | Sistema en producción operando |
| **Cuando** | Se revisa "Procedimiento_Mantenimiento_PREDICAST.docx" |
| **Entonces** | ✅ Incluye:  |
| | - Checklist Semanal: validar predicciones vs reales actualizado |
| | - Checklist Mensual: auditoría de datos, revisar outliers |
| | - Checklist Trimestral: reentrenamiento de modelos |
| | - Monitoreo: uptime API (>99%), tiempo respuesta (<500ms) |
| | - Backups: frecuencia y validación |
| | - Escalamiento: cuándo agregar recursos |
| | - Bugs: proceso de reporte y priorización |

---

### HU039 - Roadmap de evolución futura
**Criterio:** Visión a largo plazo

| Aspecto | Detalle |
|---------|---------|
| **Dado** | PREDICAST v1 operativa |
| **Cuando** | Se revisa "Roadmap_PREDICAST_2026_2027.docx" |
| **Entonces** | ✅ Estructura por trimestres: |
| | - Q2 2026 (v1.1): Análisis ABC, segmentación de productos |
| | - Q3 2026 (v1.2): Dashboards adicionales, reportes avanzados |
| | - Q4 2026 (v2.0): Reentrenamiento automático, alertas smart |
| | - Q1 2027 (v2.1): Integraciones ERP, API externa |
| | ✅ Por cada release: features, estimación recursos, ROI esperado |
| | ✅ Dependencias técnicas documentadas |
| | ✅ Timeline realista (evita over-promise) |

---

## 📊 RESUMEN DE CRITERIOS

| Épica | HU Range | Criterios Clave | Estado |
|-------|----------|-----------------|--------|
| Datos | HU001-004 | Carga, validación, consolidación | ✅ Operacional |
| ML | HU005-010 | Modelos cargados, predicciones, validación | ✅ Operacional |
| Recom. | HU011-015 | Stock seguridad, recomendaciones, exportación | ✅ Operacional |
| Dashboard | HU016-022 | Visualización, filtros, descarga | ✅ Operacional |
| API | HU023-028 | Endpoints, documentación, seguridad | ✅ Operacional |
| Económico | HU029-033 | Impacto, ahorro, reportes | ✅ Operacional |
| Docs | HU034-039 | Manuales, capacitación, roadmap | 🟡 En Desarrollo |

---

## ✅ VALIDACIÓN FINAL

**Estos criterios de aceptación son:**

✓ Realistas - Basados en funcionalidad actual del sistema  
✓ Verificables - Cada uno tiene pasos concretos (Dado-Cuando-Entonces)  
✓ Específicos - Valores reales, no genéricos  
✓ Cuantificables - Tiempos, cantidades, formatos definidos  
✓ Relevantes - Alineados con HU originales  

**Fecha de validación:** 18 de Abril de 2026  
**Responsable:** Equipo Técnico PREDICAST  
**Próxima revisión:** Post-deployment

