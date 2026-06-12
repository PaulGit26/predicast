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
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, make_scorer


def _mape(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    mask = y_true > 0
    if not mask.any():
        return 0.0
    # Cap each observation at 200% to prevent intermittent-demand weeks from exploding MAPE
    raw = np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]) * 100
    return float(np.mean(np.clip(raw, 0, 200)))


mape_scorer = make_scorer(_mape, greater_is_better=False)


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

    # 5 folds para mayor robustez en la estimación de métricas
    tscv = TimeSeriesSplit(n_splits=5)
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

        # Con pocos datos (< 20 muestras) reducir folds para evitar splits vacíos
        n_splits_efectivos = min(5, max(2, len(X) // 4))
        tscv_prod = TimeSeriesSplit(n_splits=n_splits_efectivos)

        mejores = {}

        gs_ridge = GridSearchCV(Ridge(), param_grid_ridge, cv=tscv_prod, scoring='r2', n_jobs=1, verbose=0)
        gs_ridge.fit(X, y)
        mejores['Ridge'] = {
            'params': gs_ridge.best_params_,
            'r2_cv': float(gs_ridge.best_score_),   # R² de cross-validation, no de entrenamiento
            'estimator': gs_ridge.best_estimator_,
        }

        gs_xgb = GridSearchCV(XGBRegressor(random_state=42, verbosity=0, n_jobs=1), param_grid_xgb, cv=tscv_prod, scoring='r2', n_jobs=1, verbose=0)
        gs_xgb.fit(X, y)
        mejores['XGBoost'] = {
            'params': gs_xgb.best_params_,
            'r2_cv': float(gs_xgb.best_score_),
            'estimator': gs_xgb.best_estimator_,
        }

        gs_rf = GridSearchCV(RandomForestRegressor(random_state=42, n_jobs=1), param_grid_rf, cv=tscv_prod, scoring='r2', n_jobs=1, verbose=0)
        gs_rf.fit(X, y)
        mejores['RandomForest'] = {
            'params': gs_rf.best_params_,
            'r2_cv': float(gs_rf.best_score_),
            'estimator': gs_rf.best_estimator_,
        }

        # Seleccionar ganador por CV R²
        ganador = max(mejores.keys(), key=lambda x: mejores[x]['r2_cv'])
        best_estimator = mejores[ganador]['estimator']

        # Calcular métricas honestas con cross_val_score sobre el modelo ganador
        cv_r2   = float(mejores[ganador]['r2_cv'])
        cv_mae  = float(-np.mean(cross_val_score(best_estimator, X, y, cv=tscv_prod, scoring='neg_mean_absolute_error', n_jobs=1)))
        cv_rmse = float(-np.mean(cross_val_score(best_estimator, X, y, cv=tscv_prod, scoring='neg_root_mean_squared_error', n_jobs=1)))
        cv_mape = float(-np.mean(cross_val_score(best_estimator, X, y, cv=tscv_prod, scoring=mape_scorer, n_jobs=1)))

        reporte_ganadores['grupo_1'][producto] = {
            'algoritmo_ganador': ganador,
            'hiperparametros_ganador': mejores[ganador]['params'],
            'metricas_test': {
                'Algoritmo': ganador,
                'R2':   cv_r2,
                'MAE':  cv_mae,
                'RMSE': cv_rmse,
                'MAPE': cv_mape,
            },
            'comparativa': {
                algo: {'R2_CV': datos['r2_cv']}
                for algo, datos in mejores.items()
            }
        }

    archivo_reporte = os.path.join(OUTPUT_DIR, 'REPORTE_OPTIMIZACION_HIPERPARAMETROS.json')
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        json.dump(reporte_ganadores, f, indent=2, ensure_ascii=False)

    return {'reporte': archivo_reporte, 'detalle': reporte_ganadores}
