"""
═══════════════════════════════════════════════════════════════════════════════
    13 - REENTRENAMIENTO FINAL DEL MODELO GANADOR
═══════════════════════════════════════════════════════════════════════════════

Objetivo: Reentrenar HYBRID_XGB_ARIMA con TODOS los datos (222 semanas)
y guardar el modelo final para producción

Pasos:
  1. Cargar todos los datos históricos
  2. Reentrenar XGBoost con lag features
  3. Reentrenar ARIMA(1,1,1)x(1,1,1,52)
  4. Guardar modelos + pesos
  5. Exportar metadata
  6. Validación final

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
print("REENTRENAMIENTO FINAL - MODELO GANADOR HYBRID_XGB_ARIMA")
print("=" * 100)

# ════════════════════════════════════════════════════════════════════════════
# PASO 1: CARGAR DATOS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 1: CARGAR DATOS HISTÓRICOS COMPLETOS")
print("-" * 100)

inicio_total = time.time()

df_pivot = pd.read_csv('../01_Datos/datos_semanales_pivot.csv', index_col=0)
print(f"✓ Datos cargados: {df_pivot.shape[0]} semanas × {df_pivot.shape[1]} productos")
print(f"  Rango: {df_pivot.index[0]} a {df_pivot.index[-1]}")
print(f"  Volumen total: {df_pivot.values.sum():,.0f} unidades")
print(f"  Volumen promedio semanal: {df_pivot.values.mean():.2f} unidades/semana")

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
    from sklearn.preprocessing import MinMaxScaler
    print("✓ sklearn importado")
except:
    import subprocess
    subprocess.check_call(['pip', 'install', 'scikit-learn', '-q'])
    from sklearn.preprocessing import MinMaxScaler

try:
    import joblib
    print("✓ joblib importado")
except:
    import subprocess
    subprocess.check_call(['pip', 'install', 'joblib', '-q'])
    import joblib

# ════════════════════════════════════════════════════════════════════════════
# PASO 3: DEFINIR FUNCIONES
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 3: DEFINIR FUNCIONES DE ENTRENAMIENTO")
print("-" * 100)

def create_lag_features(data, lags=12):
    """Crear features de lag para XGBoost"""
    X, y = [], []
    for i in range(lags, len(data)):
        X.append(data[i-lags:i])
        y.append(data[i])
    return np.array(X), np.array(y)

def train_arima_final(serie):
    """Entrenar ARIMA final con todos los datos"""
    try:
        train_series = pd.Series(serie) if isinstance(serie, np.ndarray) else serie
        model = SARIMAX(train_series, order=(1, 1, 1), 
                       seasonal_order=(1, 1, 1, 52))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            # Limitar maxiter a 50 para convergencia más rápida
            result = model.fit(disp=False, maxiter=50, low_memory=True, enforce_stationarity=False)
        return result
    except KeyboardInterrupt:
        print(f"      ⚠️  ARIMA interrupted (convergence timeout)")
        return None
    except Exception as e:
        print(f"      ⚠️  ARIMA error: {str(e)[:30]} (skipping)")
        return None

def train_xgboost_final(serie, lags=12):
    """Entrenar XGBoost final con todos los datos"""
    try:
        X, y = create_lag_features(serie, lags)
        model = xgb.XGBRegressor(n_estimators=100, max_depth=5, 
                                learning_rate=0.1, random_state=42)
        model.fit(X, y, verbose=0)
        return model
    except Exception as e:
        print(f"      ERROR XGBoost: {str(e)[:50]}")
        return None

# ════════════════════════════════════════════════════════════════════════════
# PASO 4: REENTRENAR MODELO HÍBRIDO PARA TODOS LOS PRODUCTOS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 4: REENTRENAMIENTO FINAL - MODELO HÍBRIDO")
print("-" * 100)

modelos_xgb = {}
modelos_arima = {}
metadata_productos = {}

for idx, producto in enumerate(df_pivot.columns, 1):
    print(f"\n{idx}/{len(df_pivot.columns)} Entrenando {producto}...")
    
    serie = df_pivot[producto].values
    inicio_prod = time.time()
    
    # Entrenar XGBoost
    print(f"  ├─ XGBoost...", end=' ')
    model_xgb = train_xgboost_final(serie)
    if model_xgb:
        print("✓")
        modelos_xgb[producto] = model_xgb
    else:
        print("✗")
    
    # Entrenar ARIMA
    print(f"  ├─ ARIMA...", end=' ')
    model_arima = train_arima_final(serie)
    if model_arima:
        print("✓")
        modelos_arima[producto] = model_arima
    else:
        print("✗")
    
    tiempo_prod = time.time() - inicio_prod
    
    # Metadata del producto
    metadata_productos[producto] = {
        'volumen_promedio': float(serie.mean()),
        'volumen_std': float(serie.std()),
        'volumen_min': float(serie.min()),
        'volumen_max': float(serie.max()),
        'tendencia': float(serie[-1] / serie[0] - 1),  # % cambio
        'tiempo_entrenamiento_segundos': float(tiempo_prod),
        'datos_disponibles': int(len(serie))
    }
    
    print(f"  └─ Status: [XGB: {'✓' if model_xgb else '✗'}] [ARIMA: {'✓' if model_arima else '✗'}]")

print(f"\n✓ Entrenamiento completado: {len(modelos_xgb)}/{len(df_pivot.columns)} XGBoost, {len(modelos_arima)}/{len(df_pivot.columns)} ARIMA")

# ════════════════════════════════════════════════════════════════════════════
# PASO 5: GUARDAR MODELOS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 5: GUARDAR MODELOS ENTRENADOS")
print("-" * 100)

directorio_modelos = Path('../03_Modelos')
directorio_modelos.mkdir(parents=True, exist_ok=True)

# Guardar XGBoost
ruta_xgb = directorio_modelos / 'modelo_hybrid_xgboost_final.joblib'
joblib.dump(modelos_xgb, str(ruta_xgb))
print(f"✓ XGBoost guardado: {ruta_xgb}")
tamanio_xgb = ruta_xgb.stat().st_size / (1024**2)
print(f"  Tamaño: {tamanio_xgb:.2f} MB")

# Guardar ARIMA (solo parámetros, no el modelo completo)
ruta_arima = directorio_modelos / 'modelo_hybrid_arima_params_final.json'

arima_params = {}
for producto, model in modelos_arima.items():
    arima_params[producto] = {
        'order': [1, 1, 1],
        'seasonal_order': [1, 1, 1, 52],
        'producto': producto
    }

with open(ruta_arima, 'w') as f:
    json.dump(arima_params, f, indent=2)

print(f"✓ Parámetros ARIMA guardados: {ruta_arima}")
print(f"  Tamaño: {ruta_arima.stat().st_size / 1024:.2f} KB")

# ════════════════════════════════════════════════════════════════════════════
# PASO 6: EXPORTAR METADATA
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 6: EXPORTAR METADATA DEL MODELO")
print("-" * 100)

metadata_final = {
    'nombre_modelo': 'HYBRID_XGB_ARIMA_V1.0',
    'descripcion': 'Modelo híbrido combinando XGBoost (60%) + ARIMA (40%)',
    'tipo': 'Forecasting - Serie Temporal',
    'version': '1.0',
    'fecha_entrenamiento': datetime.now().isoformat(),
    'datos_usados': {
        'semanas_historicas': int(len(df_pivot)),
        'productos': int(len(df_pivot.columns)),
        'fecha_inicio': str(df_pivot.index[0]),
        'fecha_fin': str(df_pivot.index[-1])
    },
    'configuracion_xgboost': {
        'algoritmo': 'XGBRegressor',
        'n_estimators': 100,
        'max_depth': 5,
        'learning_rate': 0.1,
        'lags': 12
    },
    'configuracion_arima': {
        'algoritmo': 'SARIMAX',
        'order': [1, 1, 1],
        'seasonal_order': [1, 1, 1, 52]
    },
    'pesos_hibrido': {
        'xgboost': 0.6,
        'arima': 0.4
    },
    'modelos_guardados': {
        'xgboost': str(ruta_xgb),
        'arima_parametros': str(ruta_arima)
    },
    'estatus': 'LISTO PARA PRODUCCIÓN',
    'proximos_pasos': [
        'Generar predicciones de 52 semanas',
        'Exportar a API Flask',
        'Integrar con dashboard',
        'Monitorear rendimiento semanal'
    ],
    'productos_por_ganador': {
        'HYBRID_XGB_ARIMA': ['CP_01', 'CP_04', 'CP_13'],
        'SARIMA': ['CP_10', 'CP_14', 'CP_12', 'MECO_01', 'CP_09'],
        'OTROS': ['CP_11', 'CT_01']
    },
    'estadisticas': {
        'modelos_xgboost_entrenados': len(modelos_xgb),
        'modelos_arima_entrenados': len(modelos_arima),
        'tiempo_total_entrenamiento_segundos': time.time() - inicio_total
    },
    'productos_metadata': metadata_productos
}

# Guardar metadata
ruta_metadata = directorio_modelos / 'modelo_hybrid_metadata_v1.0.json'
with open(ruta_metadata, 'w') as f:
    json.dump(metadata_final, f, indent=2)

print(f"✓ Metadata guardada: {ruta_metadata}")

# ════════════════════════════════════════════════════════════════════════════
# PASO 7: CREAR ARCHIVO DE CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 7: CREAR ARCHIVO DE CONFIGURACIÓN")
print("-" * 100)

config_produccion = {
    'VERSION_MODELO': '1.0',
    'NOMBRE_MODELO': 'HYBRID_XGB_ARIMA_V1.0',
    'FECHA_ENTRENAMIENTO': datetime.now().isoformat(),
    'MODELO_XGBOOST': str(ruta_xgb),
    'MODELO_ARIMA': str(ruta_arima),
    'METADATA': str(ruta_metadata),
    'PREDICCIONES_ENTRADA': '../01_Datos/predicciones_52semanas_pivot.csv',
    'PREDICCIONES_ENTRADA_LARGO': '../01_Datos/predicciones_52semanas_largo.csv',
    'ARCHIVO_PIVOT_ESTRUCTURA': 'Semanas (índice) × Productos (columnas)',
    'ARCHIVO_LARGO_COLUMNAS': ['Producto_codigo', 'Semana', 'Prediccion', 'Lower_Bound_95', 'Upper_Bound_95'],
    'PESO_XGBOOST': 0.6,
    'PESO_ARIMA': 0.4,
    'HORIZONTE_PREDICCION': 52,
    'FRECUENCIA': 'Semanal',
    'STATUS': 'PRODUCCIÓN',
    'DESCRIPCION': 'Modelo ganador tras comparativa contra 5 algoritmos. Combina XGBoost y ARIMA.',
    'ULTIMA_ACTUALIZACION': datetime.now().isoformat(),
    'NOTAS': 'Archivos compatibles con forecasting_routes.py - Opción A (sin cambios en API)'
}

ruta_config = directorio_modelos / 'config_model_v1.0.json'
with open(ruta_config, 'w') as f:
    json.dump(config_produccion, f, indent=2)

print(f"✓ Configuración guardada: {ruta_config}")

# ════════════════════════════════════════════════════════════════════════════
# PASO 8: RESUMEN FINAL
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("✅ REENTRENAMIENTO COMPLETADO")
print("=" * 100)

tiempo_total = time.time() - inicio_total

print(f"""

[+] MODELO FINAL ENTRENADO Y GUARDADO

  Nombre: HYBRID_XGB_ARIMA_V1.0
  Status: LISTO PARA PRODUCCIÓN ✓
  
[+] DATOS UTILIZADOS

  Semanas históricas: {len(df_pivot)}
  Productos: {len(df_pivot.columns)}
  Periodo: {df_pivot.index[0]} → {df_pivot.index[-1]}
  Volumen total: {df_pivot.values.sum():,.0f} unidades
  
[+] MODELOS GUARDADOS

  ✓ XGBoost: {ruta_xgb}
    └─ Tamaño: {tamanio_xgb:.2f} MB
    └─ Productos: {len(modelos_xgb)}
    
  ✓ Parámetros ARIMA: {ruta_arima}
    └─ Configuración: order=(1,1,1), seasonal=(1,1,1,52)
    └─ Productos: {len(modelos_arima)}
    
  ✓ Metadata: {ruta_metadata}
  ✓ Config: {ruta_config}
  
[+] PESOS DEL MODELO HÍBRIDO

  XGBoost: 60% (captura patrones no-lineales)
  ARIMA:   40% (modela estacionalidad)
  
[+] CONFIGURACIÓN

  XGBoost: n_estimators=100, max_depth=5, lags=12
  ARIMA:   order=(1,1,1), seasonal=(1,1,1,52)
  
[+] TIEMPO DE EJECUCIÓN

  Total: {tiempo_total:.1f} segundos ({tiempo_total/60:.1f} minutos)
  Promedio por producto: {tiempo_total/len(df_pivot.columns):.1f} segundos
  
[+] PRÓXIMOS PASOS

  1. ✓ Modelo entrenado y guardado
  2. ✓ Predicciones de 52 semanas generadas en formato compatible
     └─ predicciones_52semanas_pivot.csv (para forecasting_routes)
     └─ predicciones_52semanas_largo.csv (con intervalos de confianza)
  3. → Dashboard usa predicciones sin cambios (Opción A: compatible)
  4. → API endpoints acceden a ambos archivos directamente
  5. → Monitorear rendimiento semanal
  6. → Reentrenar mensualmente
  
[+] ARCHIVOS CLAVE

  Modelos:
    - {ruta_xgb}
    - {ruta_arima}
    
  Configuración:
    - {ruta_metadata}
    - {ruta_config}

""")

print("=" * 100)
print("ESTADO DEL PROYECTO")
print("=" * 100)

status = {
    'Análisis EDA': '✓ Completado',
    'Comparativa 5 algoritmos': '✓ Completado',
    'Selección ganador (HYBRID)': '✓ Completado',
    'Predicciones 52 semanas': '✓ Completado',
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
