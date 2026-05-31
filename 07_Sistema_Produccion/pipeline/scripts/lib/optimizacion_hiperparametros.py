"""
Wrapper para optimización de hiperparámetros por producto.
Provee `run_optimizacion_hiperparametros(features_dir, output_dir, clustering_metadata_path=None)`
"""
import os
import json
import numpy as np
import pandas as pd

from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def run_optimizacion_hiperparametros(features_dir: str, output_dir: str, clustering_metadata_path: str = None):
    FEATURES_DIR = features_dir
    OUTPUT_DIR = output_dir
    if clustering_metadata_path is None:
        clustering_metadata_path = os.path.join(FEATURES_DIR, 'CLUSTERING_METADATA.json')

    with open(clustering_metadata_path, 'r', encoding='utf-8') as f:
        clustering_metadata = json.load(f)

    GRUPO_1 = clustering_metadata['grupos']['GRUPO_1']['productos']

    features_file = os.path.join(FEATURES_DIR, 'FEATURES_SEMANAL_PARA_MODELOS.csv')
    df_features = pd.read_csv(features_file, encoding='latin-1', sep=';')

    skip_cols = ['Código', 'Año', 'Semana', 'Salida', 'Fecha', 'Grupo']
    feature_cols = [col for col in df_features.columns if col not in skip_cols]

    # Param grids
    param_grid_xgb = {
        'n_estimators': [50],
        'max_depth': [3, 4],
        'learning_rate': [0.1],
        'subsample': [0.8],
        'colsample_bytree': [0.8],
        'min_child_weight': [3]
    }
    param_grid_rf = {
        'n_estimators': [50],
        'max_depth': [5],
        'min_samples_split': [8],
        'min_samples_leaf': [2]
    }
    param_grid_ridge = {'alpha': [1.0, 10.0, 100.0]}

    tscv = TimeSeriesSplit(n_splits=3)
    reporte_ganadores = {'grupo_1': {}}

    for producto in GRUPO_1:
        df_prod = df_features[df_features['Código'] == producto].copy()
        if df_prod.empty:
            reporte_ganadores['grupo_1'][producto] = {'error': 'Sin datos'}
            continue

        X = df_prod[feature_cols].fillna(0)
        X_numeric = X.apply(lambda s: pd.to_numeric(s, errors='coerce'))
        valid_cols = [c for c in X_numeric.columns if X_numeric[c].notna().sum() >= 2]
        if not valid_cols:
            reporte_ganadores['grupo_1'][producto] = {'error': 'No numeric cols'}
            continue
        X = X_numeric[valid_cols].fillna(0)
        y = df_prod['Salida']

        mejores = {}

        # Ridge
        gs_ridge = GridSearchCV(Ridge(), param_grid_ridge, cv=tscv, scoring='r2', n_jobs=1, verbose=0)
        gs_ridge.fit(X, y)
        yhat_ridge = gs_ridge.predict(X)
        mejores['Ridge'] = {'params': gs_ridge.best_params_, 'r2': float(r2_score(y, yhat_ridge)), 'mae': float(mean_absolute_error(y, yhat_ridge))}

        # XGBoost
        gs_xgb = GridSearchCV(XGBRegressor(random_state=42, verbosity=0, n_jobs=1), param_grid_xgb, cv=tscv, scoring='r2', n_jobs=1, verbose=0)
        gs_xgb.fit(X, y)
        yhat_xgb = gs_xgb.predict(X)
        mejores['XGBoost'] = {'params': gs_xgb.best_params_, 'r2': float(r2_score(y, yhat_xgb)), 'mae': float(mean_absolute_error(y, yhat_xgb))}

        # RandomForest
        gs_rf = GridSearchCV(RandomForestRegressor(random_state=42, n_jobs=1), param_grid_rf, cv=tscv, scoring='r2', n_jobs=1, verbose=0)
        gs_rf.fit(X, y)
        yhat_rf = gs_rf.predict(X)
        mejores['RandomForest'] = {'params': gs_rf.best_params_, 'r2': float(r2_score(y, yhat_rf)), 'mae': float(mean_absolute_error(y, yhat_rf))}

        ganador = max(mejores.keys(), key=lambda x: mejores[x]['r2'])

        reporte_ganadores['grupo_1'][producto] = {
            'algoritmo_ganador': ganador,
            'hiperparametros_ganador': mejores[ganador]['params'],
            'metricas_test': {
                'Algoritmo': ganador,
                'R2': mejores[ganador]['r2'],
                'MAE': mejores[ganador]['mae'],
                'RMSE': float(np.sqrt(mean_squared_error(y, (gs_xgb.predict(X) if ganador == 'XGBoost' else (gs_rf.predict(X) if ganador == 'RandomForest' else gs_ridge.predict(X)))))),
                'MAPE': 0.0
            },
            'comparativa': {algo: {'R2': datos['r2'], 'MAE': datos['mae']} for algo, datos in mejores.items()}
        }

    archivo_reporte = os.path.join(OUTPUT_DIR, 'REPORTE_OPTIMIZACION_HIPERPARAMETROS.json')
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        json.dump(reporte_ganadores, f, indent=2, ensure_ascii=False)

    return {'reporte': archivo_reporte, 'detalle': reporte_ganadores}
