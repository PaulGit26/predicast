"""
═══════════════════════════════════════════════════════════════════════════════
    FORECASTING EDA - Análisis de Series de Tiempo para Predicción de Ventas
═══════════════════════════════════════════════════════════════════════════════

Objetivo: Preparar datos para forecasting de ventas semanales por producto
- Agregar datos diarios a semanales
- Análisis de estacionalidad, tendencias, autocorrelación
- Identificar patrones por producto
- Preparar datasets para comparación de algoritmos

Fecha inicio: 2021-01-01 | Fecha fin: 2026-04-04 (5 años de datos)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuración visual
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)

print("=" * 80)
print("PASO 1: CARGAR DATOS")
print("=" * 80)

# Cargar datos
df = pd.read_csv('../01_Datos/Data.csv', sep=';')
print(f"\n[+] Datos cargados: {df.shape[0]:,} registros x {df.shape[1]} columnas")
print(f"[+] Fecha rango: {df['Fecha'].min()} a {df['Fecha'].max()}")
print(f"\nColumnas: {list(df.columns)}")
print(f"\nPrimer registros:\n{df.head()}")

# Convertir tipos
df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y')
df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce')
df['Tipo_movimiento'] = df['Tipo_movimiento'].fillna('Desconocido')

print(f"\n[+] Conversiones realizadas")
print(f"[+] Cantidad (ventas + producción): min={df['Cantidad'].min()}, max={df['Cantidad'].max()}, mean={df['Cantidad'].mean():.2f}")

# Ver productos únicos
productos = df['Producto_codigo'].nunique()
print(f"\n[+] Productos unicos: {productos}")
print(f"[+] Tipo de movimientos: {df['Tipo_movimiento'].unique()}")

print("\n" + "=" * 80)
print(f"\n[+] Filtrar SOLO VENTAS (no produccion)")
print("=" * 80)

# Solo ventas (no producción)
df_ventas = df[df['Tipo_movimiento'] == 'Venta'].copy()
print(f"\n[+] Ventas filtradas: {df_ventas.shape[0]:,} registros")
print(f"[+] Rango de fechas (ventas): {df_ventas['Fecha'].min()} a {df_ventas['Fecha'].max()}")

print("\n" + "=" * 80)
print("PASO 3: AGREGAR POR SEMANA Y PRODUCTO")
print("=" * 80)

# Agregar por semana (ISO week)
df_ventas['Año'] = df_ventas['Fecha'].dt.isocalendar().year
df_ventas['Semana'] = df_ventas['Fecha'].dt.isocalendar().week
df_ventas['AñoSemana'] = df_ventas['Año'].astype(str) + '-W' + df_ventas['Semana'].astype(str).str.zfill(2)

# Agregar ventas por semana y producto - CON FEATURES ADICIONALES
df_semanal = (df_ventas.groupby(['AñoSemana', 'Año', 'Semana', 'Producto_codigo', 'Producto_nombre'])
              .agg({
                  'Cantidad': 'sum',
                  'Descuento_pct': 'mean',
                  'Precio_unitario': 'mean',
                  'Canal_venta': lambda x: (x.str.contains('Online', case=False, na=False).sum() / len(x) * 100) if len(x) > 0 else 0,
                  'Departamento_cliente': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Desconocido',
                  'Campana': lambda x: 1 if (x != 'Sin Campaña').any() else 0
              })
              .reset_index()
              .rename(columns={
                  'Cantidad': 'Ventas_Semana',
                  'Descuento_pct': 'Descuento_promedio',
                  'Precio_unitario': 'Precio_promedio',
                  'Canal_venta': 'Pct_Online',
                  'Departamento_cliente': 'Depto_Principal',
                  'Campana': 'Hay_Campana'
              }))

# Ordenar
df_semanal = df_semanal.sort_values(['Producto_codigo', 'Año', 'Semana']).reset_index(drop=True)

print(f"\n✓ Agregación completada: {df_semanal.shape[0]:,} registros (semana × producto)")
print(f"✓ Semanas únicas: {df_semanal['AñoSemana'].nunique()}")
print(f"✓ Productos únicos: {df_semanal['Producto_codigo'].nunique()}")

print(f"\nEjemplo - 3 primeras semanas del producto MECO_01:")
print(df_semanal[df_semanal['Producto_codigo'] == 'MECO_01'].head(10))

print("\n" + "=" * 80)
print("PASO 4: ANALISIS DE COBERTURA TEMPORAL")
print("=" * 80)

# Crear matriz temporal completa (todas las semanas x todos los productos)
semanas_unicas = sorted(df_semanal['AñoSemana'].unique())
productos_unico = sorted(df_semanal['Producto_codigo'].unique())

print(f"\n[+] Semanas disponibles: {len(semanas_unicas)} (desde {semanas_unicas[0]} hasta {semanas_unicas[-1]})")
print(f"[+] Productos unicos: {len(productos_unico)}")

# Ver cobertura por producto
cobertura = df_semanal.groupby('Producto_codigo').agg({
    'Ventas_Semana': ['count', 'sum', 'mean', 'std', 'min', 'max'],
    'Producto_nombre': 'first'
}).round(2)

cobertura.columns = ['Semanas_con_datos', 'Total_Ventas', 'Promedio_Semanal', 'StdDev', 'Min', 'Max', 'Nombre']
cobertura = cobertura.sort_values('Total_Ventas', ascending=False)

print(f"\nCobertura por PRODUCTO (Top 10):\n")
print(cobertura.head(10))

print(f"\nEstadísticas generales:")
print(f"  - Productos con 1-10 semanas: {(cobertura['Semanas_con_datos'] <= 10).sum()}")
print(f"  - Productos con 11-52 semanas: {((cobertura['Semanas_con_datos'] > 10) & (cobertura['Semanas_con_datos'] <= 52)).sum()}")
print(f"  - Productos con 53-260 semanas: {((cobertura['Semanas_con_datos'] > 52) & (cobertura['Semanas_con_datos'] <= 260)).sum()}")
print(f"  - Productos con 260+ semanas: {(cobertura['Semanas_con_datos'] > 260).sum()}")

print("\n" + "=" * 80)
print("PASO 5: CREAR DATASET PARA FORECASTING")
print("=" * 80)

# Seleccionar productos con suficiente historico (minimo 52 semanas = 1 año)
productos_validos = cobertura[cobertura['Semanas_con_datos'] >= 52].index.tolist()
print(f"\n[+] Productos con historico >= 52 semanas: {len(productos_validos)}")

df_forecast = df_semanal[df_semanal['Producto_codigo'].isin(productos_validos)].copy()
print(f"[+] Registros para forecasting: {df_forecast.shape[0]:,}")

# Crear estructura pivot (semanas como indice, productos como columnas)
# Pivot para ventas (serie temporal principal)
df_pivot = df_forecast.pivot_table(
    index='AñoSemana',
    columns='Producto_codigo',
    values='Ventas_Semana',
    fill_value=0  # Rellenar con 0 si no hay ventas esa semana
)

# Crear pivots para features adicionales (para usar en XGBoost/LightGBM)
df_pivot_descuento = df_forecast.pivot_table(
    index='AñoSemana',
    columns='Producto_codigo',
    values='Descuento_promedio',
    fill_value=0
)

df_pivot_precio = df_forecast.pivot_table(
    index='AñoSemana',
    columns='Producto_codigo',
    values='Precio_promedio',
    fill_value=0
)

df_pivot_pct_online = df_forecast.pivot_table(
    index='AñoSemana',
    columns='Producto_codigo',
    values='Pct_Online',
    fill_value=0
)

df_pivot_campana = df_forecast.pivot_table(
    index='AñoSemana',
    columns='Producto_codigo',
    values='Hay_Campana',
    fill_value=0
)

print(f"\n[+] Matriz principal creada: {df_pivot.shape[0]} semanas x {df_pivot.shape[1]} productos")
print(f"[+] Rango temporal: {df_pivot.index[0]} a {df_pivot.index[-1]}")
print(f"[+] Features adicionales creados: Descuento, Precio, % Online, Campaña")

print("\nPrimeras 5 semanas - Primeros 5 productos:")
print(df_pivot.iloc[:5, :5])

# Info de sparcidad
sparcidad = (df_pivot == 0).sum().sum() / (df_pivot.shape[0] * df_pivot.shape[1]) * 100
print(f"\n[+] Sparcidad (% de ceros): {sparcidad:.2f}%")

print("\n" + "=" * 80)
print("PASO 6: VISUALIZACIÓN - SERIES TEMPORALES")
print("=" * 80)

# Seleccionar top 6 productos por volumen
top_productos = cobertura.head(6).index.tolist()

fig, axes = plt.subplots(3, 2, figsize=(15, 12))
axes = axes.flatten()

for idx, producto in enumerate(top_productos):
    ax = axes[idx]
    data = df_pivot[producto]
    
    ax.plot(range(len(data)), data.values, linewidth=2, marker='o', markersize=3)
    ax.set_title(f'{producto} - Ventas Semanales\n(Media: {data.mean():.0f}, Std: {data.std():.0f})', fontsize=10, fontweight='bold')
    ax.set_xlabel('Semana')
    ax.set_ylabel('Cantidad vendida')
    ax.grid(True, alpha=0.3)
    
    # Destacar tendencia
    z = np.polyfit(range(len(data)), data.values, 1)
    p = np.poly1d(z)
    ax.plot(range(len(data)), p(range(len(data))), "r--", alpha=0.5, label='Tendencia')
    ax.legend()

plt.tight_layout()
plt.savefig('../05_Visualizaciones/01_Series_Temporales_Top6.png', dpi=300, bbox_inches='tight')
print("[+] Grafico guardado: 01_Series_Temporales_Top6.png")
plt.close()

print("\n" + "=" * 80)
print("PASO 7: ANALISIS DE ESTACIONALIDAD")
print("=" * 80)

# Análisis de estacionalidad (seasonal decomposition) para top 3
from statsmodels.tsa.seasonal import seasonal_decompose

fig, axes = plt.subplots(3, 4, figsize=(18, 12))

for idx, producto in enumerate(top_productos[:3]):
    data = df_pivot[producto]
    
    # Evitar series muy cortas / con demasiados ceros
    if data.sum() > 0 and len(data) > 26:
        try:
            # Decomposición
            decomposition = seasonal_decompose(data, model='additive', period=52)
            
            # Graficar
            axes[idx, 0].plot(data, label='Original')
            axes[idx, 0].set_title(f'{producto} - Original', fontweight='bold')
            axes[idx, 0].legend()
            axes[idx, 0].grid(True, alpha=0.3)
            
            axes[idx, 1].plot(decomposition.trend)
            axes[idx, 1].set_title(f'{producto} - Tendencia (52 semanas)', fontweight='bold')
            axes[idx, 1].grid(True, alpha=0.3)
            
            axes[idx, 2].plot(decomposition.seasonal)
            axes[idx, 2].set_title(f'{producto} - Estacionalidad', fontweight='bold')
            axes[idx, 2].grid(True, alpha=0.3)
            
            axes[idx, 3].plot(decomposition.resid)
            axes[idx, 3].set_title(f'{producto} - Residuos', fontweight='bold')
            axes[idx, 3].grid(True, alpha=0.3)
            
        except Exception as e:
            print(f"  ✗ No se pudo descomponer {producto}: {str(e)}")

plt.tight_layout()
plt.savefig('../05_Visualizaciones/02_Descomposicion_Estacional.png', dpi=300, bbox_inches='tight')
print("[+] Grafico guardado: 02_Descomposicion_Estacional.png")
plt.close()

print("\n" + "=" * 80)
print("PASO 8: ANALISIS DE AUTOCORRELACION")
print("=" * 80)

from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

fig, axes = plt.subplots(3, 2, figsize=(14, 10))

for idx, producto in enumerate(top_productos[:3]):
    data = df_pivot[producto]
    
    if data.sum() > 0:
        # ACF
        plot_acf(data, lags=40, ax=axes[idx, 0])
        axes[idx, 0].set_title(f'{producto} - ACF', fontweight='bold')
        
        # PACF
        plot_pacf(data, lags=40, ax=axes[idx, 1])
        axes[idx, 1].set_title(f'{producto} - PACF', fontweight='bold')

plt.tight_layout()
plt.savefig('../05_Visualizaciones/03_Autocorrelacion_ACF_PACF.png', dpi=300, bbox_inches='tight')
print("[+] Grafico guardado: 03_Autocorrelacion_ACF_PACF.png")
plt.close()

print("\n" + "=" * 80)
print("PASO 9: PRUEBAS ESTADISTICAS")
print("=" * 80)

from statsmodels.tsa.stattools import adfuller, kpss

print("\nPrueba ADF (Augmented Dickey-Fuller) - Estacionariedad:")
print("H0: Serie tiene raíz unitaria (NO estacionaria)")
print("H1: Serie es estacionaria\n")

adf_resultados = []
for producto in top_productos[:5]:
    data = df_pivot[producto]
    if data.sum() > 0:
        try:
            adf_result = adfuller(data, autolag='AIC')
            es_estacionaria = "Sí ✓" if adf_result[1] < 0.05 else "No ✗"
            adf_resultados.append({
                'Producto': producto,
                'ADF_Statistic': adf_result[0],
                'P_Value': adf_result[1],
                'Estacionaria': es_estacionaria,
                'Lags': adf_result[2]
            })
        except Exception as e:
            print(f"  ✗ Error en {producto}: {str(e)}")

adf_df = pd.DataFrame(adf_resultados)
print(adf_df.to_string())

print("\n" + "=" * 80)
print("PASO 10: GUARDAR DATASETS PARA MODELOS")
print("=" * 80)

# Guardar para entrenamiento
df_pivot.to_csv('../01_Datos/datos_semanales_pivot.csv')
print(f"[+] Guardado: datos_semanales_pivot.csv ({df_pivot.shape[0]} x {df_pivot.shape[1]})")

# Guardar features adicionales
df_pivot_descuento.to_csv('../01_Datos/datos_semanales_descuento.csv')
print(f"[+] Guardado: datos_semanales_descuento.csv ({df_pivot_descuento.shape[0]} x {df_pivot_descuento.shape[1]})")

df_pivot_precio.to_csv('../01_Datos/datos_semanales_precio.csv')
print(f"[+] Guardado: datos_semanales_precio.csv ({df_pivot_precio.shape[0]} x {df_pivot_precio.shape[1]})")

df_pivot_pct_online.to_csv('../01_Datos/datos_semanales_pct_online.csv')
print(f"[+] Guardado: datos_semanales_pct_online.csv ({df_pivot_pct_online.shape[0]} x {df_pivot_pct_online.shape[1]})")

df_pivot_campana.to_csv('../01_Datos/datos_semanales_campana.csv')
print(f"[+] Guardado: datos_semanales_campana.csv ({df_pivot_campana.shape[0]} x {df_pivot_campana.shape[1]})")

df_forecast.to_csv('../01_Datos/datos_semanales_long.csv', index=False)
print(f"[+] Guardado: datos_semanales_long.csv ({df_forecast.shape[0]} registros)")

# Guardar metadatos
metadata = {
    'fecha_inicio': df_pivot.index[0],
    'fecha_fin': df_pivot.index[-1],
    'semanas_totales': len(df_pivot),
    'productos': list(df_pivot.columns),
    'num_productos': df_pivot.shape[1],
    'productos_validos_52sem': len(productos_validos),
    'sparcidad_pct': sparcidad,
    'features_adicionales': {
        'Descuento_promedio': 'Promedio de descuento % por semana/producto',
        'Precio_promedio': 'Precio unitario promedio por semana/producto',
        'Pct_Online': 'Porcentaje de ventas online por semana/producto',
        'Hay_Campana': 'Indicador binario: 1 si hay campaña esa semana, 0 si no'
    }
}

import json
with open('../01_Datos/metadata_forecasting.json', 'w') as f:
    json.dump(metadata, f, indent=2, default=str)
print(f"[+] Guardado: metadata_forecasting.json")

print("\n" + "=" * 80)
print("RESUMEN FINAL")
print("=" * 80)

print(f"""
✓ DATOS PREPARADOS PARA FORECASTING:

  Dataset principal:
    - Período: {df_pivot.index[0]} → {df_pivot.index[-1]} ({len(df_pivot)} semanas)
    - Productos: {df_pivot.shape[1]} (con histórico >= 52 semanas)
    - Estructura: {df_pivot.shape[0]} × {df_pivot.shape[1]}
    - Sparcidad: {sparcidad:.2f}%
    
  Archivos generados:
    ✓ datos_semanales_pivot.csv - Formato largo (semana × producto)
    ✓ datos_semanales_long.csv - Formato tidy (rows × columnas)
    ✓ metadata_forecasting.json - Metadatos

  Visualizaciones:
    ✓ 01_Series_Temporales_Top6.png
    ✓ 02_Descomposicion_Estacional.png
    ✓ 03_Autocorrelacion_ACF_PACF.png

  Próximo paso: 11_COMPARATIVA_FORECASTING.py
    → Comparar algoritmos (Prophet, ARIMA, LSTM, XGBoost, LightGBM, etc.)
    → Elegir el mejor según MAE, RMSE, MAPE

""")
