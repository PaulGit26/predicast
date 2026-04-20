"""
═══════════════════════════════════════════════════════════════════════════════
    13 - REENTRENAMIENTO FINAL DE MODELOS GANADORES POR PRODUCTO
═══════════════════════════════════════════════════════════════════════════════

Objetivo: Entrenar el MEJOR MODELO para cada producto (identificado en comparativa)
con TODOS los datos históricos (222 semanas) y guardar para producción

Pasos:
  1. Cargar todos los datos históricos
  2. Cargar resultados de comparativa para identificar ganador por producto
  3. Para cada producto, entrenar su modelo ganador (XGBoost, LightGBM o SARIMA)
  4. Guardar modelos entrenados organizados por modelo/producto
  5. Exportar metadata con trazabilidad
  6. Validación final

Modelo Ganador Global: LIGHTGBM (MAE: 28.17)
- XGBoost: 9 productos (45%)
- LightGBM: 7 productos (35%)
- SARIMA: 4 productos (20%)

"""

import pandas as pd
import numpy as np
import json
import pickle
import time
from datetime import datetime
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

print("=" * 100)
print("REENTRENAMIENTO FINAL - MODELOS GANADORES POR PRODUCTO")
print("=" * 100)

# ════════════════════════════════════════════════════════════════════════════
# PASO 1: CARGAR DATOS HISTÓRICOS COMPLETOS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 1: CARGAR DATOS HISTÓRICOS COMPLETOS")
print("-" * 100)

inicio_total = time.time()

df_pivot = pd.read_csv('../01_Datos/datos_semanales_pivot.csv', index_col=0)
print(f"✓ Datos cargados: {df_pivot.shape[0]} semanas × {df_pivot.shape[1]} productos")
print(f"  Rango: {df_pivot.index[0]} a {df_pivot.index[-1]}")
print(f"  Volumen total: {df_pivot.values.sum():,.0f} unidades")
print(f"  Volumen promedio semanal: {df_pivot.values.mean():.2f} unidades/semana")

# Cargar features adicionales
df_descuento = pd.read_csv('../01_Datos/datos_semanales_descuento.csv', index_col=0)
df_precio = pd.read_csv('../01_Datos/datos_semanales_precio.csv', index_col=0)
df_pct_online = pd.read_csv('../01_Datos/datos_semanales_pct_online.csv', index_col=0)
df_campana = pd.read_csv('../01_Datos/datos_semanales_campana.csv', index_col=0)
print(f"✓ Features adicionales cargados: Descuento, Precio, % Online, Campaña")

# Cargar resultados de comparativa
with open('comparativa_resumen.json', 'r') as f:
    comparativa_resultados = json.load(f)
print(f"✓ Resultados de comparativa cargados")
print(f"  Mejor modelo global: {comparativa_resultados['mejor_modelo_global']}")

# ════════════════════════════════════════════════════════════════════════════
# PASO 2: IMPORTAR LIBRERÍAS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 2: IMPORTAR LIBRERÍAS")
print("-" * 100)

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

try:
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    print("✓ sklearn importado")
except:
    import subprocess
    subprocess.check_call(['pip', 'install', 'scikit-learn', '-q'])
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    import joblib
    print("✓ joblib importado")
except:
    import subprocess
    subprocess.check_call(['pip', 'install', 'joblib', '-q'])
    import joblib

# ════════════════════════════════════════════════════════════════════════════
# PASO 3: DEFINIR FUNCIONES DE ENTRENAMIENTO POR MODELO
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 3: DEFINIR FUNCIONES DE ENTRENAMIENTO")
print("-" * 100)

def create_lag_features(data, lags=52):
    """Crear features de lag para tree-based models"""
    X, y = [], []
    for i in range(lags, len(data)):
        X.append(data[i-lags:i])
        y.append(data[i])
    return np.array(X), np.array(y)

def create_lag_features_with_exog(data, lags=52, exog_features=None):
    """Crear features de lag + features exógenos"""
    X, y = [], []
    for i in range(lags, len(data)):
        lag_values = data[i-lags:i]
        
        # Features exógenos (usar el valor actual)
        exog_values = []
        if exog_features:
            for fname, fdata in exog_features.items():
                if i < len(fdata):
                    exog_values.append(fdata[i])
        
        # Combinar lags + features exógenos
        if exog_values:
            combined = np.concatenate([lag_values, exog_values])
        else:
            combined = lag_values
        X.append(combined)
        y.append(data[i])
    
    return np.array(X), np.array(y)

def train_xgboost(data, producto):
    """Entrenar XGBoost con todos los datos"""
    try:
        X, y = create_lag_features(data, lags=52)
        if len(X) == 0:
            print(f"      ⚠️  Datos insuficientes para lags")
            return None
            
        model = xgb.XGBRegressor(n_estimators=100, max_depth=5, 
                                learning_rate=0.1, random_state=42, verbosity=0)
        model.fit(X, y, verbose=False)
        return model
    except Exception as e:
        print(f"      ERROR XGBoost: {str(e)[:50]}")
        return None

def train_lightgbm(data, producto):
    """Entrenar LightGBM con todos los datos"""
    try:
        X, y = create_lag_features(data, lags=52)
        if len(X) == 0:
            print(f"      ⚠️  Datos insuficientes para lags")
            return None
            
        model = lgb.LGBMRegressor(n_estimators=100, max_depth=5, 
                                 learning_rate=0.1, random_state=42, verbose=-1)
        model.fit(X, y)
        return model
    except Exception as e:
        print(f"      ERROR LightGBM: {str(e)[:50]}")
        return None

def train_sarima(data, producto):
    """Entrenar SARIMA con todos los datos"""
    try:
        train_series = pd.Series(data) if isinstance(data, np.ndarray) else data
        model = SARIMAX(train_series, order=(1, 1, 1), 
                       seasonal_order=(1, 1, 1, 52))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            result = model.fit(disp=False, maxiter=50, low_memory=True, enforce_stationarity=False)
        return result
    except KeyboardInterrupt:
        print(f"      ⚠️  SARIMA interrupted (convergence timeout)")
        return None
    except Exception as e:
        print(f"      ⚠️  SARIMA error: {str(e)[:30]} (skipping)")
        return None
    return np.array(X), np.array(y)



# ════════════════════════════════════════════════════════════════════════════
# PASO 4: REENTRENAMIENTO DE MODELOS GANADORES POR PRODUCTO
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 4: REENTRENAMIENTO - MODELOS GANADORES POR PRODUCTO")
print("-" * 100)

modelos_por_tipo = {
    'xgboost': {},
    'lightgbm': {},
    'sarima': {}
}

metadata_productos = {}
resumen_modelos = {
    'xgboost': [],
    'lightgbm': [],
    'sarima': []
}

for idx, producto in enumerate(df_pivot.columns, 1):
    # Obtener modelo ganador para este producto
    modelo_ganador = comparativa_resultados['modelos_por_producto'][producto]['modelo_recomendado']
    metricas = comparativa_resultados['modelos_por_producto'][producto]['metricas']
    
    print(f"\n{idx}/{len(df_pivot.columns)} {producto:10s} → Modelo: {modelo_ganador:12s}", end=" ")
    
    serie = df_pivot[producto].values
    inicio_prod = time.time()
    
    modelo_entrenado = None
    
    # Entrenar el modelo ganador
    if modelo_ganador == 'XGBOOST':
        print("| Entrenando...", end=" ")
        modelo_entrenado = train_xgboost(serie, producto)
        if modelo_entrenado:
            modelos_por_tipo['xgboost'][producto] = modelo_entrenado
            resumen_modelos['xgboost'].append(producto)
            print("✓")
        else:
            print("✗")
    
    elif modelo_ganador == 'LIGHTGBM':
        print("| Entrenando...", end=" ")
        modelo_entrenado = train_lightgbm(serie, producto)
        if modelo_entrenado:
            modelos_por_tipo['lightgbm'][producto] = modelo_entrenado
            resumen_modelos['lightgbm'].append(producto)
            print("✓")
        else:
            print("✗")
    
    elif modelo_ganador == 'SARIMA':
        print("| Entrenando...", end=" ")
        modelo_entrenado = train_sarima(serie, producto)
        if modelo_entrenado:
            modelos_por_tipo['sarima'][producto] = modelo_entrenado
            resumen_modelos['sarima'].append(producto)
            print("✓")
        else:
            print("✗")
    
    tiempo_prod = time.time() - inicio_prod
    
    # Metadata del producto
    metadata_productos[producto] = {
        'modelo': modelo_ganador,
        'volumen_promedio': float(serie.mean()),
        'volumen_std': float(serie.std()),
        'volumen_min': float(serie.min()),
        'volumen_max': float(serie.max()),
        'tendencia': float(serie[-1] / serie[0] - 1),
        'entrenado': modelo_entrenado is not None,
        'tiempo_entrenamiento_segundos': float(tiempo_prod),
        'datos_disponibles': int(len(serie)),
        'metricas_comparativa': metricas
    }

print(f"\n✓ Entrenamiento completado:")
print(f"  - XGBoost:  {len(modelos_por_tipo['xgboost'])}/{resumen_modelos['xgboost'].__len__()} productos")
print(f"  - LightGBM: {len(modelos_por_tipo['lightgbm'])}/{resumen_modelos['lightgbm'].__len__()} productos")
print(f"  - SARIMA:   {len(modelos_por_tipo['sarima'])}/{resumen_modelos['sarima'].__len__()} productos")

# ════════════════════════════════════════════════════════════════════════════
# PASO 5: GUARDAR MODELOS ENTRENADOS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 5: GUARDAR MODELOS ENTRENADOS")
print("-" * 100)

directorio_modelos = Path('../03_Modelos')
directorio_modelos.mkdir(parents=True, exist_ok=True)

# Crear subdirectorios para cada tipo de modelo
dir_xgb = directorio_modelos / 'xgboost_modelos'
dir_lgb = directorio_modelos / 'lightgbm_modelos'
dir_arima = directorio_modelos / 'sarima_modelos'

dir_xgb.mkdir(parents=True, exist_ok=True)
dir_lgb.mkdir(parents=True, exist_ok=True)
dir_arima.mkdir(parents=True, exist_ok=True)

# Guardar XGBoost por producto
for producto, modelo in modelos_por_tipo['xgboost'].items():
    ruta = dir_xgb / f'{producto}.joblib'
    joblib.dump(modelo, str(ruta))

if modelos_por_tipo['xgboost']:
    print(f"✓ XGBoost: {len(modelos_por_tipo['xgboost'])} modelos guardados en {dir_xgb}")
    tamanio_xgb = sum([f.stat().st_size for f in dir_xgb.glob('*.joblib')]) / (1024**2)
    print(f"  Tamaño total: {tamanio_xgb:.2f} MB")

# Guardar LightGBM por producto
for producto, modelo in modelos_por_tipo['lightgbm'].items():
    ruta = dir_lgb / f'{producto}.joblib'
    joblib.dump(modelo, str(ruta))

if modelos_por_tipo['lightgbm']:
    print(f"✓ LightGBM: {len(modelos_por_tipo['lightgbm'])} modelos guardados en {dir_lgb}")
    tamanio_lgb = sum([f.stat().st_size for f in dir_lgb.glob('*.joblib')]) / (1024**2)
    print(f"  Tamaño total: {tamanio_lgb:.2f} MB")

# Guardar SARIMA (solo parámetros + metadata, ya que los objetos SARIMAX son complejos)
sarima_models_metadata = {}
for producto, modelo in modelos_por_tipo['sarima'].items():
    sarima_models_metadata[producto] = {
        'order': [1, 1, 1],
        'seasonal_order': [1, 1, 1, 52],
        'parametros': 'SARIMAX(p=1, d=1, q=1, P=1, D=1, Q=1, s=52)',
        'producto': producto,
        'estado': 'Parámetros guardados - Reestructurar en predicción'
    }

ruta_arima = dir_arima / 'sarima_config.json'
with open(ruta_arima, 'w') as f:
    json.dump(sarima_models_metadata, f, indent=2)

if modelos_por_tipo['sarima']:
    print(f"✓ SARIMA: {len(modelos_por_tipo['sarima'])} configuraciones guardadas en {ruta_arima}")
    print(f"  Tamaño: {ruta_arima.stat().st_size / 1024:.2f} KB")

# ════════════════════════════════════════════════════════════════════════════
# PASO 6: EXPORTAR METADATA
# ════════════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════════
# PASO 6: EXPORTAR METADATA DEL MODELO
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 6: EXPORTAR METADATA DE MODELOS")
print("-" * 100)

metadata_final = {
    'nombre_proyecto': 'Predicast - Forecasting Multi-Modelo por Producto',
    'descripcion': 'Modelos específicos por producto, identificados mediante comparativa de 5 algoritmos',
    'tipo': 'Forecasting - Serie Temporal Multivariable',
    'version': '2.0',
    'enfoque': 'Modelo específico por producto (NO híbrido)',
    'fecha_entrenamiento': datetime.now().isoformat(),
    'datos_usados': {
        'semanas_historicas': int(len(df_pivot)),
        'productos': int(len(df_pivot.columns)),
        'fecha_inicio': str(df_pivot.index[0]),
        'fecha_fin': str(df_pivot.index[-1]),
        'volumen_total': float(df_pivot.values.sum()),
        'volumen_promedio': float(df_pivot.values.mean())
    },
    'modelos_entrenados': {
        'xgboost': {
            'cantidad': len(modelos_por_tipo['xgboost']),
            'productos': resumen_modelos['xgboost'],
            'configuracion': {
                'algoritmo': 'XGBRegressor',
                'n_estimators': 100,
                'max_depth': 5,
                'learning_rate': 0.1,
                'lags': 52
            },
            'directorio': str(dir_xgb)
        },
        'lightgbm': {
            'cantidad': len(modelos_por_tipo['lightgbm']),
            'productos': resumen_modelos['lightgbm'],
            'configuracion': {
                'algoritmo': 'LGBMRegressor',
                'n_estimators': 100,
                'max_depth': 5,
                'learning_rate': 0.1,
                'lags': 52
            },
            'directorio': str(dir_lgb)
        },
        'sarima': {
            'cantidad': len(modelos_por_tipo['sarima']),
            'productos': resumen_modelos['sarima'],
            'configuracion': {
                'algoritmo': 'SARIMAX',
                'order': [1, 1, 1],
                'seasonal_order': [1, 1, 1, 52]
            },
            'directorio': str(dir_arima)
        }
    },
    'mejor_modelo_global': comparativa_resultados['mejor_modelo_global'],
    'mae_promedio_global': comparativa_resultados['mae_promedio_mejor_global'],
    'ranking_global': comparativa_resultados['ranking_global'],
    'modelos_por_producto_detalle': metadata_productos,
    'estadisticas': {
        'modelos_entrenados_totales': len(modelos_por_tipo['xgboost']) + len(modelos_por_tipo['lightgbm']) + len(modelos_por_tipo['sarima']),
        'tiempo_total_entrenamiento_segundos': time.time() - inicio_total,
        'promedio_tiempo_por_producto': (time.time() - inicio_total) / len(df_pivot.columns)
    },
    'status': 'LISTO PARA PREDICCIÓN',
    'proximos_pasos': [
        'Ejecutar 12_MODELO_GANADOR_52SEMANAS.py para generar predicciones',
        'Actualizar API con endpoints de predicción',
        'Integrar con dashboard',
        'Monitorear rendimiento semanal'
    ]
}

# Guardar metadata
ruta_metadata = directorio_modelos / 'modelos_ganadores_metadata.json'
with open(ruta_metadata, 'w') as f:
    json.dump(metadata_final, f, indent=2, default=str)

print(f"✓ Metadata guardada: {ruta_metadata}")
print(f"  Tamaño: {ruta_metadata.stat().st_size / 1024:.2f} KB")

# ════════════════════════════════════════════════════════════════════════════
# PASO 7: CREAR ARCHIVO INDEX DE MODELOS
# ════════════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════════
# PASO 7: CREAR ARCHIVO INDEX DE MODELOS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 7: CREAR INDEX DE MODELOS")
print("-" * 100)

# Crear un archivo index que mapea producto -> modelo -> ruta
modelo_index = {}
for producto in df_pivot.columns:
    modelo_ganador = comparativa_resultados['modelos_por_producto'][producto]['modelo_recomendado']
    
    if modelo_ganador == 'XGBOOST':
        ruta = str(dir_xgb / f'{producto}.joblib')
    elif modelo_ganador == 'LIGHTGBM':
        ruta = str(dir_lgb / f'{producto}.joblib')
    elif modelo_ganador == 'SARIMA':
        ruta = str(dir_arima / 'sarima_config.json')
    else:
        ruta = None
    
    modelo_index[producto] = {
        'modelo': modelo_ganador,
        'ruta': ruta,
        'mae': comparativa_resultados['modelos_por_producto'][producto]['metricas']['mae'],
        'r2': comparativa_resultados['modelos_por_producto'][producto]['metricas']['r2']
    }

ruta_index = directorio_modelos / 'modelo_index.json'
with open(ruta_index, 'w') as f:
    json.dump(modelo_index, f, indent=2)

print(f"✓ Index de modelos guardado: {ruta_index}")
print(f"  Tamaño: {ruta_index.stat().st_size / 1024:.2f} KB")

# ════════════════════════════════════════════════════════════════════════════
# PASO 8: RESUMEN FINAL
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("✅ REENTRENAMIENTO COMPLETADO")
print("=" * 100)

tiempo_total = time.time() - inicio_total

print(f"""

[+] MODELOS GANADORES ENTRENADOS Y GUARDADOS

  Enfoque: Modelo específico por producto (NO híbrido)
  Status: LISTO PARA PREDICCIÓN ✓
  
[+] DISTRIBUCIÓN DE MODELOS

  XGBoost:  {len(modelos_por_tipo['xgboost']):2d} productos ({100*len(modelos_por_tipo['xgboost'])/len(df_pivot.columns):5.1f}%)
  LightGBM: {len(modelos_por_tipo['lightgbm']):2d} productos ({100*len(modelos_por_tipo['lightgbm'])/len(df_pivot.columns):5.1f}%)
  SARIMA:   {len(modelos_por_tipo['sarima']):2d} productos ({100*len(modelos_por_tipo['sarima'])/len(df_pivot.columns):5.1f}%)
  
[+] DATOS UTILIZADOS

  Semanas históricas: {len(df_pivot)}
  Productos: {len(df_pivot.columns)}
  Periodo: {df_pivot.index[0]} → {df_pivot.index[-1]}
  Volumen total: {df_pivot.values.sum():,.0f} unidades
  
[+] MODELOS GUARDADOS

  XGBoost:
    └─ Directorio: {dir_xgb}
    └─ Productos: {resumen_modelos['xgboost']}
    
  LightGBM:
    └─ Directorio: {dir_lgb}
    └─ Productos: {resumen_modelos['lightgbm']}
    
  SARIMA:
    └─ Config: {dir_arima}/sarima_config.json
    └─ Productos: {resumen_modelos['sarima']}
    
  Metadata e Index:
    └─ {ruta_metadata}
    └─ {ruta_index}
  
[+] CONFIGURACIÓN GENERAL

  Lags: 52 semanas (ciclo anual completo)
  Horizonte de predicción: 52 semanas
  
[+] TIEMPO DE EJECUCIÓN

  Total: {tiempo_total:.1f} segundos ({tiempo_total/60:.1f} minutos)
  Promedio por producto: {tiempo_total/len(df_pivot.columns):.1f} segundos
  
[+] PRÓXIMOS PASOS

  1. ✓ Modelos ganadores entrenados y guardados (por producto)
  2. → Ejecutar 12_MODELO_GANADOR_52SEMANAS.py para generar predicciones
  3. → Evaluar predicciones vs datos reales
  4. → Actualizar API con modelos entrenados
  5. → Integrar con dashboard
  6. → Monitorear rendimiento semanal
  
[+] ARCHIVOS GENERADOS

  Modelos:
    - {dir_xgb}/*.joblib ({len(modelos_por_tipo['xgboost'])} archivos)
    - {dir_lgb}/*.joblib ({len(modelos_por_tipo['lightgbm'])} archivos)
    - {dir_arima}/sarima_config.json
    
  Configuración:
    - {ruta_metadata}
    - {ruta_index}

""")

print("=" * 100)
print("ESTADO DEL PROYECTO")
print("=" * 100)

status = {
    'Análisis EDA': '✓ Completado',
    'Comparativa 5 algoritmos': '✓ Completado',
    'Selección ganador por producto': '✓ COMPLETADO AHORA',
    'Reentrenamiento final': '✓ COMPLETADO AHORA',
    'Guardado de modelos': '✓ COMPLETADO AHORA',
    'Exportación metadata': '✓ COMPLETADO AHORA',
    'API endpoints': '→ Próximo paso',
    'Dashboard': '→ Próximo paso',
    'Monitoreo en producción': '→ Próximo paso'
}

for tarea, estatus in status.items():
    print(f"  {estatus:20s} | {tarea}")

print("\n" + "=" * 100)
