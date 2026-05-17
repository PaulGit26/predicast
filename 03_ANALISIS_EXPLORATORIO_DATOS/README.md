# Análisis Exploratorio - Datos Reales de Corporación Electro SVM

## Resumen Ejecutivo

Script: `01_ANALISIS_DATOS_REALES.py`

**Objetivo:** Analizar la data transaccional REAL de la empresa (Entrada, Salida, Saldo) sin inventar datos.

---

## Hallazgos Clave

### 📊 Volúmenes de Datos
| Métrica | Valor |
|---------|-------|
| **Registros cargados** | 63,329 |
| **Registros excluidos** (traspasos + guías) | 9,628 |
| **Registros válidos** | 53,701 |
| **Rango de fechas** | 2021-01-01 a 2025-05-31 |
| **Productos únicos** | 2,924 |

### 🏪 Bodegas y Canales
```
Bodega Principal              Almacén Punto de Ventas 1 (63.5%)
Canal Principal              Online (60.3%)
```

### 🎯 Concentración Pareto

**VENTAS (Salida > 0):**
- **1,518 productos** con ventas
- **13 productos** (0.9%) generan el **80% de ventas**
- **Top 3:** CER 001 (803K), CEO 001 (555K), CER 005 (538K)

**PRODUCCIÓN (Entrada > 0):**
- **1,569 productos** con producción
- **13 productos** (0.8%) generan el **80% de producción**
- Mismos productos que en ventas (altísima correlación)

### 📈 Stock Promedio (usando Saldo)

| Producto | Stock Mín | Stock Prom | Stock Máx |
|----------|-----------|-----------|-----------|
| CER 001  | -3,103    | 15,235    | 135,129   |
| CEO 001  | 0         | 13,632    | 103,997   |
| CEO 006  | 0         | 11,739    | 91,251    |
| CER 005  | -372      | 10,032    | 83,578    |

**Observación:** Stock mínimo negativo indica desabastecimiento en ciertos períodos.

### 🔄 Rotación de Inventario (Top 10)

| Producto | Rotación |
|----------|----------|
| '9       | 91.66x   |
| CP-00008 | 82.11x   |
| CP-00044 | 73.58x   |
| CER 008  | 65.29x   |
| CER 004  | 65.14x   |

Baja correlación entre TOP Ventas y TOP Rotación → **Productos con diferentes comportamientos de inventario**

### 📉 Tendencia Mensual (últimos 6 meses)

| Mes    | Salida  | Transacciones |
|--------|---------|---------------|
| 2024-12| 58,994  | 651           |
| 2025-01| 78,461  | 994           |
| 2025-02| 64,448  | 848           |
| 2025-03| 90,844  | 769           |
| 2025-04| 64,558  | 650           |
| 2025-05| 97,752  | 750           |

**Observación:** Variabilidad importante mes a mes → **Patrón estacional detectado**

---

## Archivos Generados

### 📄 CSVs de Análisis

1. **`01_VENTAS_POR_PRODUCTO.csv`**
   - Columnas: Código, Num_Transacciones, Salida_Total, Salida_Promedio, Salida_Std, Salida_Min, Salida_Max, Descripción
   - Ordenado por Salida_Total (mayor a menor)

2. **`01B_PRODUCCION_POR_PRODUCTO.csv`**
   - Columnas: Código, Num_Transacciones, Entrada_Total, Entrada_Promedio, Entrada_Std, Entrada_Min, Entrada_Max
   - Entrada = Producción o Compra

3. **`02_STOCK_POR_PRODUCTO.csv`**
   - Columnas: Código, Stock_Min, Stock_Promedio, Stock_Max, Stock_Std, Num_Registros, Bodega_Principal
   - Stock calculado del Saldo en cada transacción

4. **`03_ROTACION_INVENTARIO.csv`**
   - Columnas: Código, Salida_Total, Descripción, Stock_Promedio, Rotacion
   - Rotación = Salida_Total / Stock_Promedio

5. **`04_VENTAS_POR_BODEGA.csv`**
   - Distribución de ventas por almacén

6. **`05_VENTAS_POR_CANAL.csv`**
   - Distribución de ventas por canal (Online/Presencial)

7. **`06_TENDENCIA_MENSUAL.csv`**
   - Series temporal mensual de ventas

### 📊 Gráficos Generados

1. **`GRAFICO_01_PARETO_TOP20.png`**
   - Top 20 productos por volumen de ventas
   - Visualiza concentración de demanda

2. **`GRAFICO_02_SALIDA_VS_STOCK.png`**
   - Comparativa de Salida vs Stock Promedio (Top 20)
   - Identifica desbalances entre demanda y disponibilidad

3. **`GRAFICO_03_VENTAS_BODEGA.png`**
   - Gráfico de barras horizontal: ventas por bodega
   - Identifica bodega principal vs secundarias

4. **`GRAFICO_04_VENTAS_CANAL.png`**
   - Gráfico de pastel: distribución por canal
   - Online vs Presencial

5. **`GRAFICO_05_TENDENCIA_TEMPORAL.png`**
   - Línea de tiempo mensual de ventas
   - Patrón de demanda a lo largo del período

6. **`GRAFICO_06_ROTACION_TOP10.png`**
   - Top 10 productos por rotación
   - Orden diferente al Top de ventas

### 📋 Resumen

**`RESUMEN_ANALISIS.json`**
- Timestamp de ejecución
- Estadísticas conteo (registros totales, limpios, productos)
- Rango de fechas
- Productos Pareto 80%
- Listado de bodegas y canales
- Top 5 productos
- Observaciones

---

## Problemas Identificados en los Datos

### ⚠️ Stock Negativo
Algunos productos tienen Stock_Min negativo:
- CER 001: Stock mínimo = -3,103
- CER 005: Stock mínimo = -372

**Causa probable:** 
- Ventas registradas antes que entrada en sistema
- O ajustes contables no documentados
- **Impacto:** Falta de materialización de demanda en ciertos períodos

### ⚠️ Variabilidad Mensual Fuerte
Ventas mes a mes varían de 58K a 97K unidades
**Causa probable:**
- Patrones estacionales
- Variabilidad en pedidos de clientes
- Cierre de períodos contables

### ⚠️ Baja utilización de 2 bodegas
- Almacén Punto de Venta 2: solo 0.9% de ventas
- ¿Cerrada? ¿Subutilizada?

---

## Próximos Pasos (para modelo de predicción)

1. **Desestacionalizar series temporales** → Detectar patrón semanal/mensual real
2. **Analizar correlación Ventas vs Producción** → Validar si hay lag (retraso)
3. **Estudiar productos con stock negativo** → Ajustar método de cálculo
4. **Top 20 productos para modelo inicial** → Concentração es 80% = buena para modelado
5. **Features temporales** → Lags, moving averages, tendencia
6. **Clustering de productos** → Agrupar por comportamiento similar (rotación, estacionalidad)

---

**Generado:** Script `01_ANALISIS_DATOS_REALES.py`  
**Fecha:** May 4, 2026  
**Limpieza aplicada:** Traspasos entre almacenes excluidos ✓ | Guías de remisión (Entrada=Salida) excluidas ✓
