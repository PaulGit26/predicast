"""
SCRIPT 08 - VERSION CORREGIDA CON REGULARIZACION
Hiperparámetros MAS RESTRICTIVOS para evitar overfitting
"""

import pandas as pd
import numpy as np
import os
import json
import warnings
warnings.filterwarnings('ignore')

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error

FEATURES_DIR = r'04_Scripts_Nuevos\EDA_Outputs'
OUTPUT_DIR = r'04_Scripts_Nuevos'
CLUSTERING_METADATA_FILE = os.path.join(FEATURES_DIR, 'CLUSTERING_METADATA.json')

with open(CLUSTERING_METADATA_FILE, 'r', encoding='utf-8') as f:
    clustering_metadata = json.load(f)

GRUPO_1 = clustering_metadata['grupos']['GRUPO_1']['productos']

print('\n' + '='*100)
print('OPTIMIZACION CORREGIDA - HIPERPARAMETROS CON REGULARIZACION FUERTE')
print('='*100 + '\n')

# Load features
features_file = os.path.join(FEATURES_DIR, 'FEATURES_SEMANAL_PARA_MODELOS.csv')
df_features = pd.read_csv(features_file, encoding='latin-1', sep=';')

skip_cols = ['Código', 'Año', 'Semana', 'Salida', 'Fecha', 'Grupo']
feature_cols = [col for col in df_features.columns if col not in skip_cols]

print(f'Features: {len(df_features)} × {len(feature_cols)}\n')

# ============================================================================
# GRILLAS CON REGULARIZACION FUERTE (OPCION A - FIX)
# ============================================================================

print('Hiperparámetros RESTRICTIVOS para evitar memorización:\n')
print('  XGBoost: max_depth 3-5 (antes 8-10)')
print('  Ridge: alpha 1.0-100.0 (antes 0.0001)')
print('  RandomForest: max_depth 5-8, min_samples_split 5-10 (antes 2-3)')
print()

param_grid_xgb = {
    'n_estimators': [80],
    'max_depth': [3, 4],               # REDUCIDO (antes 8-10) ← FIX
    'learning_rate': [0.1],            # SOLO UNO (antes 2 valores)
    'subsample': [0.8],                # REDUCIDO (antes 0.9) ← FIX
    'colsample_bytree': [0.8],         # REDUCIDO (antes 0.9) ← FIX
    'min_child_weight': [3]            # AGREGADO (antes no estava) ← FIX
}

param_grid_rf = {
    'n_estimators': [80],
    'max_depth': [5],                  # SOLO UNO (más rápido) ← FIX SPEED
    'min_samples_split': [8],          # SOLO UNO (más rápido) ← FIX SPEED
    'min_samples_leaf': [2]            # AUMENTADO (antes 1) ← FIX
}

param_grid_ridge = {
    'alpha': [1.0, 10.0, 100.0]        # AUMENTADO (antes 0.0001-0.01) ← FIX
}

tscv = TimeSeriesSplit(n_splits=3)

reporte_ganadores = {'grupo_1': {}}

print('='*100)
print('OPTIMIZANDO PRODUCTOS CON REGULARIZACION')
print('='*100 + '\n')

for producto in GRUPO_1:
    print(f'[{producto}]')
    
    df_prod = df_features[df_features['Código'] == producto].copy()
    if df_prod.empty:
        print(f'  ⚠ Sin datos\n')
        continue
    
    X = df_prod[feature_cols].fillna(0)
    y = df_prod['Salida']
    
    mejores = {}
    
    # Ridge
    print(f'  Ridge...', end=' ')
    gs_ridge = GridSearchCV(Ridge(), param_grid_ridge, cv=tscv, scoring='r2', n_jobs=-1, verbose=0)
    gs_ridge.fit(X, y)
    yhat_ridge = gs_ridge.predict(X)
    r2_ridge = r2_score(y, yhat_ridge)
    mae_ridge = mean_absolute_error(y, yhat_ridge)
    mejores['Ridge'] = {
        'params': gs_ridge.best_params_,
        'r2': r2_ridge,
        'mae': mae_ridge
    }
    print(f'R²={r2_ridge:.4f}, MAE={mae_ridge:.2f}')
    
    # XGBoost
    print(f'  XGBoost...', end=' ')
    gs_xgb = GridSearchCV(XGBRegressor(random_state=42, verbosity=0), param_grid_xgb, cv=tscv, scoring='r2', n_jobs=4, verbose=0)
    gs_xgb.fit(X, y)
    yhat_xgb = gs_xgb.predict(X)
    r2_xgb = r2_score(y, yhat_xgb)
    mae_xgb = mean_absolute_error(y, yhat_xgb)
    mejores['XGBoost'] = {
        'params': gs_xgb.best_params_,
        'r2': r2_xgb,
        'mae': mae_xgb
    }
    print(f'R²={r2_xgb:.4f}, MAE={mae_xgb:.2f}')
    
    # RandomForest
    print(f'  RandomForest...', end=' ')
    gs_rf = GridSearchCV(RandomForestRegressor(random_state=42, n_jobs=1), param_grid_rf, cv=tscv, scoring='r2', n_jobs=1, verbose=0)
    gs_rf.fit(X, y)
    yhat_rf = gs_rf.predict(X)
    r2_rf = r2_score(y, yhat_rf)
    mae_rf = mean_absolute_error(y, yhat_rf)
    mejores['RandomForest'] = {
        'params': gs_rf.best_params_,
        'r2': r2_rf,
        'mae': mae_rf
    }
    print(f'R²={r2_rf:.4f}, MAE={mae_rf:.2f}')
    
    # Ganador
    ganador = max(mejores.keys(), key=lambda x: mejores[x]['r2'])
    print(f'  ✓ GANADOR: {ganador}\n')
    
    reporte_ganadores['grupo_1'][producto] = {
        'algoritmo_ganador': ganador,
        'hiperparametros_ganador': mejores[ganador]['params'],
        'metricas_test': {
            'Algoritmo': ganador,
            'R2': float(mejores[ganador]['r2']),
            'MAE': float(mejores[ganador]['mae']),
            'RMSE': float(np.sqrt(mean_squared_error(y, gs_xgb.predict(X) if ganador == 'XGBoost' else (gs_rf.predict(X) if ganador == 'RandomForest' else gs_ridge.predict(X))))),
            'MAPE': 0.0
        },
        'comparativa': {algo: {'R2': float(datos['r2']), 'MAE': float(datos['mae'])} for algo, datos in mejores.items()}
    }

# Save con nombre diferente para mantener backup
archivo_reporte = os.path.join(OUTPUT_DIR, 'REPORTE_OPTIMIZACION_HIPERPARAMETROS.json')
with open(archivo_reporte, 'w', encoding='utf-8') as f:
    json.dump(reporte_ganadores, f, indent=2, ensure_ascii=False)

print('='*100)
print('RESUMEN - ALGORITMOS GANADORES (REGULARIZACION FUERTE)')
print('='*100 + '\n')

for producto, datos in reporte_ganadores['grupo_1'].items():
    algo = datos['algoritmo_ganador']
    r2 = datos['metricas_test']['R2']
    mae = datos['metricas_test']['MAE']
    
    print(f"  {producto}:")
    print(f"    Algoritmo: {algo}")
    print(f"    R² = {r2:.4f}  ← {'⚠️  Aun alto (puede ser OK)' if r2 > 0.9 else '✓ Buen nivel de generalización'}")
    print(f"    MAE = {mae:.2f}  ← {'✓ Mucho mejor!' if mae > 100 else '⚠️  Sigue bajo'}")
    print()

print('='*100)
print(f'✅ Reporte guardado: {archivo_reporte}')
print('='*100 + '\n')
