"""
═══════════════════════════════════════════════════════════════════════════════
    GENERACIÓN DE PREDICCIONES CON MODELOS GANADORES POR PRODUCTO - V3
═══════════════════════════════════════════════════════════════════════════════

Objetivo: CARGAR modelos PRE-ENTRENADOS por producto desde 03_Modelos y generar
predicciones para las próximas 52 semanas (1 año completo)

Modelos: Específicos por producto (identificados en comparativa de 5 algoritmos)
  - XGBoost:  9 productos (45%) - Flexible, bueno para patrones no-lineales
  - LightGBM: 7 productos (35%) - Rápido, eficiente en memoria
  - SARIMA:   4 productos (20%) - Estacionalidad fuerte
  
Dataset: datos_semanales_pivot.csv - 222 semanas x 20 productos
Output: predicciones_52semanas_pivot.csv + predicciones_52semanas_largo.csv

MEJORA V3: Usa el mejor modelo para cada producto (no híbrido global)
Velocidad: ~15-20 segundos (sin entrenamientos, solo predicciones)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import json
from pathlib import Path
import time
import joblib

warnings.filterwarnings('ignore')

# Configuración
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("=" * 100)
print("MODELOS GANADORES: PREDICCIONES PARA 52 SEMANAS")
print("=" * 100)

# ════════════════════════════════════════════════════════════════════════════
# PASO 1: CARGAR DATOS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 1: CARGAR DATOS")
print("-" * 100)

df_pivot = pd.read_csv('../01_Datos/datos_semanales_pivot.csv', index_col=0)
print(f"[OK] Datos cargados: {df_pivot.shape[0]} semanas x {df_pivot.shape[1]} productos")
print(f"[OK] Rango temporal: {df_pivot.index[0]} a {df_pivot.index[-1]}")

# ════════════════════════════════════════════════════════════════════════════
# PASO 2: IMPORTAR LIBRERÍAS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 2: IMPORTAR LIBRERÍAS")
print("-" * 100)

try:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    print("✓ sklearn importado")
except:
    import subprocess
    subprocess.check_call(['pip', 'install', 'scikit-learn', '-q'])
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    print("✓ SARIMAX importado")
except:
    import subprocess
    subprocess.check_call(['pip', 'install', 'statsmodels', '-q'])
    from statsmodels.tsa.statespace.sarimax import SARIMAX

try:
    import xgboost as xgb
    print("✓ XGBoost importado")
except:
    import subprocess
    subprocess.check_call(['pip', 'install', 'xgboost', '-q'])
    import xgboost as xgb

try:
    import lightgbm as lgb
    print("✓ LightGBM importado")
except:
    import subprocess
    subprocess.check_call(['pip', 'install', 'lightgbm', '-q'])
    import lightgbm as lgb

# ════════════════════════════════════════════════════════════════════════════
# PASO 3: CARGAR MODELOS PRE-ENTRENADOS POR PRODUCTO
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 3: CARGAR MODELOS PRE-ENTRENADOS POR PRODUCTO")
print("-" * 100)

try:
    # Cargar índice de modelos (mapea producto -> tipo de modelo -> ruta)
    with open('../03_Modelos/modelo_index.json', 'r') as f:
        modelo_index = json.load(f)
    print(f"✓ Índice de modelos cargado: {len(modelo_index)} productos")
    
    # Cargar metadata
    with open('../03_Modelos/modelos_ganadores_metadata.json', 'r') as f:
        metadata = json.load(f)
    print(f"✓ Metadata cargada")
    print(f"  Mejor modelo global: {metadata['mejor_modelo_global']}")
    print(f"  Entrenado: {metadata['fecha_entrenamiento'][:10]}")
    print(f"  Status: {metadata['status']}")
    
    # Cargar modelos XGBoost por producto
    modelos_xgb = {}
    xgb_dir = Path('../03_Modelos/xgboost_modelos')
    if xgb_dir.exists():
        for archivo in xgb_dir.glob('*.joblib'):
            producto = archivo.stem
            modelos_xgb[producto] = joblib.load(str(archivo))
    print(f"✓ Modelos XGBoost cargados: {len(modelos_xgb)} productos")
    
    # Cargar modelos LightGBM por producto
    modelos_lgb = {}
    lgb_dir = Path('../03_Modelos/lightgbm_modelos')
    if lgb_dir.exists():
        for archivo in lgb_dir.glob('*.joblib'):
            producto = archivo.stem
            modelos_lgb[producto] = joblib.load(str(archivo))
    print(f"✓ Modelos LightGBM cargados: {len(modelos_lgb)} productos")
    
    # Cargar configuración SARIMA
    with open('../03_Modelos/sarima_modelos/sarima_config.json', 'r') as f:
        sarima_config = json.load(f)
    print(f"✓ Configuración SARIMA cargada: {len(sarima_config)} productos")
    
    MODELOS_CARGADOS = True
except FileNotFoundError as e:
    print(f"\nERROR: No se encontraron los modelos guardados en 03_Modelos/")
    print(f"Solución: Ejecuta primero este archivo:")
    print(f"python 13_REENTRENAMIENTO_MODELO_FINAL.py")
    exit(1)
except Exception as e:
    print(f"\nERROR al cargar modelos: {e}")
    exit(1)

# ════════════════════════════════════════════════════════════════════════════
# PASO 4: DEFINIR FUNCIONES DE PREDICCIÓN (MODELOS ESPECÍFICOS POR PRODUCTO)
# ════════════════════════════════════════════════════════════════════════════

def create_lag_features(data, lags=52):
    """Crear features de lag para tree-based models"""
    X = []
    for i in range(lags, len(data)):
        X.append(data[i-lags:i])
    return np.array(X)

def predict_xgboost(serie, producto, horizonte=52):
    """Predecir con XGBoost pre-entrenado"""
    try:
        lags = 52
        modelo = modelos_xgb[producto]
        
        predicciones = []
        hist = list(serie[-lags:])
        
        for i in range(horizonte):
            X_pred = np.array([hist[-lags:]])
            pred = modelo.predict(X_pred)[0]
            pred = max(pred, 0)
            predicciones.append(pred)
            hist.append(pred)
        
        return np.array(predicciones)
    except Exception as e:
        print(f"XGBoost error: {str(e)[:40]}")
        return None

def predict_lightgbm(serie, producto, horizonte=52):
    """Predecir con LightGBM pre-entrenado"""
    try:
        lags = 52
        modelo = modelos_lgb[producto]
        
        predicciones = []
        hist = list(serie[-lags:])
        
        for i in range(horizonte):
            X_pred = np.array([hist[-lags:]])
            pred = modelo.predict(X_pred)[0]
            pred = max(pred, 0)
            predicciones.append(pred)
            hist.append(pred)
        
        return np.array(predicciones)
    except Exception as e:
        print(f"LightGBM error: {str(e)[:40]}")
        return None

def predict_sarima(serie, producto, horizonte=52):
    """Predecir con SARIMA re-entrenando rápidamente"""
    try:
        train_series = pd.Series(serie) if isinstance(serie, np.ndarray) else serie
        
        # Re-entrenar rápidamente con maxiter bajo
        modelo = SARIMAX(train_series, order=(1, 1, 1), 
                        seasonal_order=(1, 1, 1, 52))
        
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            resultado = modelo.fit(disp=False, maxiter=10, low_memory=True, 
                                 enforce_stationarity=False)
        
        forecast = resultado.get_forecast(steps=horizonte).predicted_mean.values
        forecast = np.maximum(forecast, 0)
        return forecast
    except Exception as e:
        print(f"SARIMA error: {str(e)[:40]}")
        return None

def predict_por_producto(producto, serie, horizonte=52):
    """Predecir usando el modelo ganador específico para cada producto"""
    modelo_tipo = modelo_index[producto]['modelo'].lower()
    
    if modelo_tipo == 'xgboost':
        return predict_xgboost(serie, producto, horizonte)
    elif modelo_tipo == 'lightgbm':
        return predict_lightgbm(serie, producto, horizonte)
    elif modelo_tipo == 'sarima':
        return predict_sarima(serie, producto, horizonte)
    else:
        print(f"Modelo desconocido: {modelo_tipo}")
        return None

# ════════════════════════════════════════════════════════════════════════════
# PASO 5: GENERAR PREDICCIONES CON MODELOS ESPECÍFICOS POR PRODUCTO
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 5: GENERAR PREDICCIONES (usando modelos ganadores por producto)")
print("-" * 100)

horizonte = 52
predicciones_por_producto = {}
tiempos = {}
modelos_usados = {'xgboost': 0, 'lightgbm': 0, 'sarima': 0}

tiempo_inicio_total = time.time()

for idx, producto in enumerate(df_pivot.columns, 1):
    modelo_tipo = modelo_index[producto]['modelo'].lower()
    print(f"{idx}/{len(df_pivot.columns)} {producto:10s} [{modelo_tipo:10s}]", end=' ')
    
    serie = df_pivot[producto].values
    inicio = time.time()
    
    # Predecir con el modelo ganador para este producto
    pred = predict_por_producto(producto, serie, horizonte)
    
    tiempo = time.time() - inicio
    tiempos[producto] = tiempo
    
    if pred is not None:
        predicciones_por_producto[producto] = pred
        modelos_usados[modelo_tipo] += 1
        
        # Mostrar resumen
        media_pred = np.mean(pred)
        std_pred = np.std(pred)
        print(f"✓ ({tiempo:.2f}s) | Media: {media_pred:7.2f} +/- {std_pred:7.2f}")
    else:
        print(f"✗ Error")

tiempo_total = time.time() - tiempo_inicio_total
print(f"\n✓ Predicciones completadas para {len(predicciones_por_producto)}/{len(df_pivot.columns)} productos")
print(f"  Tiempo total: {tiempo_total:.2f}s")
print(f"  Modelos usados: XGBoost={modelos_usados['xgboost']}, LightGBM={modelos_usados['lightgbm']}, SARIMA={modelos_usados['sarima']}")
print(f"  Promedio por producto: {np.mean(list(tiempos.values())):.2f}s")

# ════════════════════════════════════════════════════════════════════════════
# PASO 6: CREAR TABLA DE PREDICCIONES
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 6: CREAR TABLA DE PREDICCIONES")
print("-" * 100)

# Crear índice de semanas futuras
ultima_semana = df_pivot.index[-1]

try:
    if isinstance(ultima_semana, str) and 'W' in ultima_semana:
        year, week = ultima_semana.split('-W')
        year, week = int(year), int(week)
        ultima_fecha = datetime.strptime(f"{year}-W{week:02d}-1", "%Y-W%W-%w")
    else:
        ultima_fecha = pd.to_datetime(ultima_semana)
except:
    ultima_fecha = datetime.now() - timedelta(days=7)

# Generar fechas futuras (52 semanas)
fechas_futuras = [ultima_fecha + timedelta(weeks=i) for i in range(1, horizonte + 1)]
nombres_columnas = [f"W+{i}" for i in range(1, horizonte + 1)]

# Crear DataFrame con predicciones
df_predicciones = pd.DataFrame(predicciones_por_producto).T
df_predicciones.columns = nombres_columnas
df_predicciones.index.name = 'Producto'

print(f"\n✓ Tabla de predicciones creada:")
print(f"  - Productos: {df_predicciones.shape[0]}")
print(f"  - Semanas futuras: {df_predicciones.shape[1]}")
print(f"\nPrimeras 5 filas:")
print(df_predicciones.head())

# ════════════════════════════════════════════════════════════════════════════
# PASO 7: GUARDAR RESULTADOS EN DOS FORMATOS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 7: GUARDAR RESULTADOS")
print("-" * 100)

# Formato 1: PIVOT
df_predicciones_pivot = df_predicciones.T
df_predicciones_pivot.index.name = 'Semana'
df_predicciones_pivot.index = [f"W+{int(i)}" for i in range(1, len(df_predicciones_pivot) + 1)]

df_predicciones_pivot.to_csv('../01_Datos/predicciones_52semanas_pivot.csv')
print(f"✓ Guardado: predicciones_52semanas_pivot.csv")
print(f"  Formato: {df_predicciones_pivot.shape[0]} semanas x {df_predicciones_pivot.shape[1]} productos")

# Formato 2: LARGO con intervalos de confianza
z_95 = 1.96
df_largo_data = []

for producto in df_predicciones.index:
    for semana_idx, semana_col in enumerate(df_predicciones.columns, 1):
        pred_valor = df_predicciones.loc[producto, semana_col]
        
        # Calcular intervalo de confianza (±15% como margen conservador)
        std_estimado = pred_valor * 0.15
        lower_bound = max(0, pred_valor - z_95 * std_estimado)
        upper_bound = pred_valor + z_95 * std_estimado
        
        df_largo_data.append({
            'Producto_codigo': producto,
            'Semana': semana_col,
            'Prediccion': pred_valor,
            'Lower_Bound_95': lower_bound,
            'Upper_Bound_95': upper_bound
        })

df_predicciones_largo = pd.DataFrame(df_largo_data)
df_predicciones_largo = df_predicciones_largo.sort_values(['Producto_codigo', 'Semana'])
df_predicciones_largo.to_csv('../01_Datos/predicciones_52semanas_largo.csv', index=False)
print(f"✓ Guardado: predicciones_52semanas_largo.csv")
print(f"  Formato: {len(df_predicciones_largo)} registros (producto x semana)")

# Guardar resumen JSON
resumen_json = {
    'fecha_generacion': datetime.now().isoformat(),
    'modelos_usados': modelos_usados,
    'distribucion_modelos': {
        'xgboost_pct': round(100 * modelos_usados['xgboost'] / len(df_pivot.columns), 1),
        'lightgbm_pct': round(100 * modelos_usados['lightgbm'] / len(df_pivot.columns), 1),
        'sarima_pct': round(100 * modelos_usados['sarima'] / len(df_pivot.columns), 1)
    },
    'productos_totales': len(df_pivot.columns),
    'productos_predichos': len(predicciones_por_producto),
    'horizonte_semanas': horizonte,
    'ultima_semana_datos': str(ultima_semana),
    'primera_semana_prediccion': str(fechas_futuras[0].date()),
    'ultima_semana_prediccion': str(fechas_futuras[-1].date()),
    'estadisticas': {
        'predicciones_promedio': float(df_predicciones.values.mean()),
        'predicciones_std': float(df_predicciones.values.std()),
        'predicciones_min': float(df_predicciones.values.min()),
        'predicciones_max': float(df_predicciones.values.max())
    },
    'tiempo_ejecucion_segundos': float(tiempo_total),
    'tiempo_promedio_por_producto': float(np.mean(list(tiempos.values()))),
    'archivos_generados': {
        'predicciones_pivot_csv': '../01_Datos/predicciones_52semanas_pivot.csv',
        'predicciones_largo_csv': '../01_Datos/predicciones_52semanas_largo.csv'
    }
}

with open('../04_Scripts/resumen_predicciones_modelos.json', 'w') as f:
    json.dump(resumen_json, f, indent=2, default=str)
print(f"✓ Guardado: resumen_predicciones_modelos.json")

# ════════════════════════════════════════════════════════════════════════════
# PASO 8: VISUALIZACIONES
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 8: CREAR VISUALIZACIONES")
print("-" * 100)

# Gráfico 1: Top 10 productos - Últimas 20 semanas reales + 52 predicciones
top_productos = df_pivot.sum().sort_values(ascending=False).head(10).index.tolist()

fig, axes = plt.subplots(5, 2, figsize=(18, 15))
axes = axes.flatten()

for idx, producto in enumerate(top_productos):
    ax = axes[idx]
    
    # Datos reales (últimas 20 semanas)
    ultimas_20 = df_pivot[producto].tail(20).values
    semanas_reales = range(-20, 0)
    
    # Predicciones
    pred = predicciones_por_producto[producto]
    semanas_pred = range(1, horizonte + 1)
    
    # Graficar
    ax.plot(semanas_reales, ultimas_20, 'b-o', linewidth=2, markersize=5, label='Datos reales (ultimas 20 sem)')
    ax.plot(semanas_pred, pred, 'r--s', linewidth=2, markersize=4, label='Predicciones (52 sem)', alpha=0.8)
    
    ax.axvline(x=0, color='gray', linestyle=':', alpha=0.5)
    
    ax.set_title(f'{producto}\nPromedio prediccion: {np.mean(pred):.2f}', fontweight='bold')
    ax.set_xlabel('Semana')
    ax.set_ylabel('Volumen')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

plt.suptitle('Predicciones por Modelo Ganador - 52 Semanas - Top 10 Productos', 
             fontsize=16, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig('../05_Visualizaciones/09_Predicciones_52semanas_ModelosGanadores.png', dpi=300, bbox_inches='tight')
print("✓ Grafico guardado: 09_Predicciones_52semanas_ModelosGanadores.png")
plt.close()

# Gráfico 2: Distribución por modelo usado
fig, ax = plt.subplots(figsize=(10, 6))

modelos_lista = list(modelos_usados.keys())
cantidades = list(modelos_usados.values())
colores = ['#1f77b4', '#ff7f0e', '#2ca02c']

barras = ax.bar(modelos_lista, cantidades, color=colores, alpha=0.7, edgecolor='black')

# Agregar valores en las barras
for barra, cantidad in zip(barras, cantidades):
    height = barra.get_height()
    ax.text(barra.get_x() + barra.get_width()/2., height,
            f'{int(cantidad)} ({100*cantidad/20:.0f}%)',
            ha='center', va='bottom', fontweight='bold', fontsize=12)

ax.set_ylabel('Cantidad de Productos', fontsize=12)
ax.set_title('Distribución de Modelos Ganadores', fontsize=14, fontweight='bold')
ax.set_ylim(0, max(cantidades) * 1.15)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('../05_Visualizaciones/10_Distribucion_Modelos_Ganadores.png', dpi=300, bbox_inches='tight')
print("✓ Grafico guardado: 10_Distribucion_Modelos_Ganadores.png")
plt.close()

# ════════════════════════════════════════════════════════════════════════════
# PASO 9: RESUMEN FINAL
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("GENERACION DE PREDICCIONES COMPLETADA")
print("=" * 100)

total_predicciones = len(predicciones_por_producto) * horizonte

print(f"""

[+] RESUMEN EJECUTIVO:

  [MODELOS] Específicos por producto (NO híbrido)
     └─ XGBoost:  {modelos_usados['xgboost']} productos (45%)
     └─ LightGBM: {modelos_usados['lightgbm']} productos (35%)
     └─ SARIMA:   {modelos_usados['sarima']} productos (20%)
     
  [RESULTADOS]
     └─ Productos predichos: {len(predicciones_por_producto)}/{len(df_pivot.columns)}
     └─ Total predicciones: {total_predicciones} valores
     └─ Horizonte: {horizonte} semanas (1 año)
     └─ Rango temporal: {str(fechas_futuras[0].date())} a {str(fechas_futuras[-1].date())}
     
  [ESTADISTICAS DE PREDICCIONES]
     └─ Promedio: {df_predicciones.values.mean():.2f}
     └─ Desv. Est: {df_predicciones.values.std():.2f}
     └─ Minimo: {df_predicciones.values.min():.2f}
     └─ Maximo: {df_predicciones.values.max():.2f}
     
  [ARCHIVOS GENERADOS]
     ✓ predicciones_52semanas_pivot.csv - Predicciones (semanas x productos)
     ✓ predicciones_52semanas_largo.csv - Predicciones tidy + intervalos
     ✓ resumen_predicciones_modelos.json - Resumen ejecutivo
     ✓ 09_Predicciones_52semanas_ModelosGanadores.png - Graficos de series
     ✓ 10_Distribucion_Modelos_Ganadores.png - Distribucion por modelo
     
  [TIEMPO DE EJECUCION]
     └─ Tiempo total: {tiempo_total:.2f} segundos ({tiempo_total/60:.2f} minutos)
     └─ Tiempo promedio por producto: {np.mean(list(tiempos.values())):.2f} segundos
     
  [PROXIMOS PASOS]
     1. Revisar predicciones en predicciones_52semanas_pivot.csv
     2. Integrar con sistema de planificación (inventario, supply chain)
     3. Monitorear rendimiento del modelo (comparar con valores reales semanalmente)
     4. Validar cada semana y reentrenar si es necesario

""")

print("=" * 100)
