"""
SCRIPT 10 V4 - PREDICCIONES CON AUTO-REGRESION DE ERRORES
Usa residuales de entrenamiento para inyectar variación realista
"""

import pandas as pd
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
import xgboost as xgb

print("\n" + "="*120)
print("SCRIPT 10 V4 - PREDICCIONES RECURSIVAS CON AUTO-REGRESION DE ERRORES")
print("="*120 + "\n")

OUTPUT_DIR = r"d:\Desktop\Predicast\04_Scripts_Nuevos\EDA_Outputs"
DATA_DIR = r"d:\Desktop\Predicast\01_Datos"

# ============================================================================
# PASO 1: CARGAR PARAMETROS Y FEATURES
# ============================================================================

print("[PASO 1] Cargando parametros...")

with open(r"d:\Desktop\Predicast\04_Scripts_Nuevos\REPORTE_OPTIMIZACION_HIPERPARAMETROS.json") as f:
    reporte = json.load(f)

params_ganadores = {}
for producto, datos in reporte['grupo_1'].items():
    params_ganadores[producto] = {
        'algoritmo': datos['algoritmo_ganador'],
        'parametros': datos['hiperparametros_ganador'],
        'r2': datos['metricas_test']['R2'],
        'mae': datos['metricas_test']['MAE'],
        'rmse': datos['metricas_test'].get('RMSE', 100),
    }

print(f"  ✓ {len(params_ganadores)} modelos cargados")

# Load features
features_df = pd.read_csv(
    os.path.join(OUTPUT_DIR, "FEATURES_SEMANAL_PARA_MODELOS.csv"),
    sep=";", encoding="latin-1"
)

base_cols = ['Código', 'Año', 'Semana', 'Fecha', 'Salida']
feature_cols = [c for c in features_df.columns if c not in base_cols]

print(f"  ✓ Features: {len(feature_cols)} columnas\n")

# ============================================================================
# PASO 2: ENTRENAR MODELOS Y CALCULAR RESIDUALES
# ============================================================================

print("[PASO 2] Entrenando modelos y calculando residuales...")

modelos_finales = {}
residuales_por_producto = {}
ultimo_dato = {}

for producto in sorted(params_ganadores.keys()):
    df_prod = features_df[features_df['Código'] == producto].copy()
    df_prod = df_prod.sort_values('Semana').reset_index(drop=True)
    
    X = df_prod[feature_cols].fillna(0)
    y = df_prod['Salida']
    
    # Entrenar modelo
    params = params_ganadores[producto]['parametros']
    algo = params_ganadores[producto]['algoritmo']
    
    if algo == 'XGBoost':
        modelo = xgb.XGBRegressor(random_state=42, n_jobs=-1, **params)
    elif algo == 'Ridge':
        modelo = Ridge(**params)
    else:  # RandomForest
        # RandomForest no usa 'alpha', solo los parámetros de árbol
        modelo = RandomForestRegressor(random_state=42, n_jobs=-1, **params)
    
    modelo.fit(X, y)
    modelos_finales[producto] = modelo
    
    # Calcular predicciones en training
    y_pred = modelo.predict(X)
    residuales = y - y_pred  # Error real = valor_real - predicción
    
    residuales_por_producto[producto] = {
        'residuales': residuales.values.tolist(),  # Convert to list for JSON
        'media': float(residuales.mean()),
        'std': float(residuales.std()),
        'min': float(residuales.min()),
        'max': float(residuales.max()),
        'cv': float(residuales.std() / residuales.mean()) if residuales.mean() != 0 else 0
    }
    
    ultimo_dato[producto] = {
        'features_ultima': X.iloc[-1].copy(),
        'salida_ultima': y.iloc[-1],
        'historico': {
            'media': float(y.mean()),
            'std': float(y.std()),
            'min': float(y.min()),
            'max': float(y.max()),
            'cv': float(y.std() / y.mean()) if y.mean() != 0 else 0
        }
    }
    
    print(f"  {producto}: {algo}")
    print(f"    - Residuales: media={residuales.mean():.2f}, std={residuales.std():.2f}")

# ============================================================================
# PASO 3: GENERAR PREDICCIONES 52 SEMANAS CON AUTO-REGRESION
# ============================================================================

print("\n[PASO 3] Predicciones 52 semanas con auto-regresion de errores...\n")

predicciones_largo = []
predicciones_pivot = {}

for producto in sorted(modelos_finales.keys()):
    print(f"  {producto}...")
    
    # Inicializar
    features_pd = ultimo_dato[producto]['features_ultima'].copy()
    salida_anterior = ultimo_dato[producto]['salida_ultima']
    
    # Buffer de predicciones y residuales para actualizar lags
    historico_pred = [salida_anterior] * 16
    
    # Residuales históricos para inyectar variación
    residuales_hist = residuales_por_producto[producto]['residuales']
    residuales_media = residuales_por_producto[producto]['media']
    residuales_std = residuales_por_producto[producto]['std']
    
    predicciones_semanas = []
    predicciones_pivot[producto] = []
    
    # Obtener indices de lags
    lag_indices = {}
    for i, col in enumerate(feature_cols):
        if col in ['Lag_1', 'Lag_2', 'Lag_3', 'Lag_4', 'Lag_13']:
            lag_indices[col] = i
    
    np.random.seed(42)  # Para reproducibilidad
    
    for semana_num in range(1, 53):
        
        # ACTUALIZAR LAG FEATURES
        if 'Lag_1' in lag_indices:
            features_pd.iloc[lag_indices['Lag_1']] = historico_pred[-1]
        if 'Lag_2' in lag_indices:
            features_pd.iloc[lag_indices['Lag_2']] = historico_pred[-2] if len(historico_pred) >= 2 else historico_pred[-1]
        if 'Lag_3' in lag_indices:
            features_pd.iloc[lag_indices['Lag_3']] = historico_pred[-3] if len(historico_pred) >= 3 else historico_pred[-1]
        if 'Lag_4' in lag_indices:
            features_pd.iloc[lag_indices['Lag_4']] = historico_pred[-4] if len(historico_pred) >= 4 else historico_pred[-1]
        if 'Lag_13' in lag_indices:
            features_pd.iloc[lag_indices['Lag_13']] = historico_pred[-13] if len(historico_pred) >= 13 else historico_pred[-1]
        
        # PREDICCION BASE
        features_array = features_pd.values.reshape(1, -1)
        features_array = np.nan_to_num(features_array, nan=0.0)
        pred_base = modelos_finales[producto].predict(features_array)[0]
        
        # AJUSTE CON AUTO-REGRESION DE RESIDUALES
        # Sample residual from historical distribution
        residual_ajuste = np.random.normal(residuales_media, residuales_std + abs(residuales_std * 0.3))
        
        # Aplicar ajuste con decayment (mengua con el tiempo)
        decay_factor = 1.0 - (semana_num - 1) / 52 * 0.7  # Más ajuste al inicio
        residual_final = residual_ajuste * decay_factor
        
        pred = max(0, pred_base + residual_final)
        
        historico_pred.append(pred)
        
        # INTERVALO DE CONFIANZA (usando MAE del modelo)
        mae = params_ganadores[producto].get('mae', 50)
        lower_bound = max(0, pred - 1.96 * mae)
        upper_bound = pred + 1.96 * mae
        
        predicciones_semanas.append({
            'Producto_codigo': producto,
            'Semana': f'W+{semana_num}',
            'Prediccion': round(pred, 2),
            'Lower_Bound_95': round(lower_bound, 2),
            'Upper_Bound_95': round(upper_bound, 2)
        })
        
        predicciones_pivot[producto].append(round(pred, 2))
    
    predicciones_largo.extend(predicciones_semanas)
    
    # Estadísticas
    preds_array = np.array(predicciones_pivot[producto])
    print(f"    → Rango: {preds_array.min():.2f} - {preds_array.max():.2f}")
    print(f"    → Media: {preds_array.mean():.2f}")
    print(f"    → Desv.Est: {preds_array.std():.2f} ✓")

# ============================================================================
# PASO 4-6: EXPORTAR
# ============================================================================

print("\n[PASO 4-6] Exportando resultados...\n")

# Formato largo
df_largo = pd.DataFrame(predicciones_largo)
archivo_largo = os.path.join(DATA_DIR, "predicciones_52semanas_largo_V4.csv")
df_largo.to_csv(archivo_largo, index=False)
print(f"  ✓ {archivo_largo}")

# Formato pivot
df_pivot_data = []
for semana_num in range(1, 53):
    fila = {'Semana': f'W+{semana_num}'}
    for producto in sorted(predicciones_pivot.keys()):
        fila[producto] = predicciones_pivot[producto][semana_num - 1]
    df_pivot_data.append(fila)

df_pivot = pd.DataFrame(df_pivot_data)
archivo_pivot = os.path.join(DATA_DIR, "predicciones_52semanas_pivot_V4.csv")
df_pivot.to_csv(archivo_pivot, index=False)
print(f"  ✓ {archivo_pivot}")

# Metadata con residuales (convertir params a dict simple)
metadata_modelos = {}
for prod, datos in params_ganadores.items():
    metadata_modelos[prod] = {
        'algoritmo': datos['algoritmo'],
        'r2': float(datos['r2']),
        'mae': float(datos['mae']),
        'rmse': float(datos['rmse'])
    }

metadata = {
    'version': 'V4 - AutoRegresion',
    'residuales_entrenamiento': residuales_por_producto,
    'modelos': metadata_modelos
}

archivo_metadata = os.path.join(DATA_DIR, "predicciones_52semanas_METADATA_V4.json")
with open(archivo_metadata, 'w') as f:
    json.dump(metadata, f, indent=2, default=str)
print(f"  ✓ {archivo_metadata}")

volumen_total = sum(sum(preds) for preds in predicciones_pivot.values())
print(f"\n📊 TOTAL: {volumen_total:,.0f} unidades")
print("✅ Predicciones generadas con variación auto-regresiva\n")
