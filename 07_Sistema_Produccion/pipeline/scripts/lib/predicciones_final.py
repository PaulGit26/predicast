"""
Wrapper para generación de predicciones finales (52 semanas) a partir
de las características y del reporte de hiperparámetros.

Provee: run_predicciones_final(features_dir, output_dir, reporte_path)
"""
import os
import re
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
import xgboost as xgb


def run_predicciones_final(features_dir: str, output_dir: str, reporte_path: str):
    FEATURES_FILE = os.path.join(features_dir, 'FEATURES_SEMANAL_PARA_MODELOS.csv')
    with open(reporte_path, 'r', encoding='utf-8') as f:
        reporte = json.load(f)

    params_ganadores = {}
    for producto, datos in reporte.get('grupo_1', {}).items():
        params_ganadores[producto] = {
            'algoritmo': datos.get('algoritmo_ganador'),
            'parametros': datos.get('hiperparametros_ganador', {}),
            'r2': datos.get('metricas_test', {}).get('R2', 0),
            'mae': datos.get('metricas_test', {}).get('MAE', 50),
            'rmse': datos.get('metricas_test', {}).get('RMSE', 0)
        }

    df_features = pd.read_csv(FEATURES_FILE, sep=';', encoding='latin-1')

    base_cols = ['Código', 'Año', 'Semana', 'Fecha', 'Salida']
    feature_cols = [c for c in df_features.columns if c not in base_cols]

    modelos_finales = {}
    residuales_por_producto = {}
    historia_real = {}
    ultimo_features = {}

    for producto in sorted(params_ganadores.keys()):
        df_prod = df_features[df_features['Código'] == producto].copy()
        df_prod = df_prod.sort_values('Semana').reset_index(drop=True)
        if df_prod.empty:
            continue

        X = df_prod[feature_cols].fillna(0)
        X_numeric = X.apply(lambda s: pd.to_numeric(s, errors='coerce'))
        valid_cols = [c for c in X_numeric.columns if X_numeric[c].notna().sum() >= 2]
        if not valid_cols:
            continue
        X = X_numeric[valid_cols].fillna(0)
        y = df_prod['Salida']

        params = params_ganadores[producto]['parametros']
        algo = params_ganadores[producto]['algoritmo']

        if algo == 'XGBoost':
            modelo = xgb.XGBRegressor(random_state=42, n_jobs=1, **params)
        elif algo == 'Ridge':
            modelo = Ridge(**params)
        else:
            modelo = RandomForestRegressor(random_state=42, n_jobs=1, **params)

        modelo.fit(X, y)
        modelos_finales[producto] = modelo

        y_pred = modelo.predict(X)
        residuales = y - y_pred
        residuales_por_producto[producto] = {
            'residuales': residuales.values.tolist(),
            'media': float(residuales.mean()),
            'std': float(residuales.std()),
        }

        # Guardar historial real de ventas y último vector de features
        historia_real[producto] = y.values.tolist()
        ultimo_features[producto] = {
            'features': X.iloc[-1].copy(),
            'valid_cols': valid_cols
        }

    # Generar predicciones 52 semanas — forecast recursivo
    predicciones_largo = []
    predicciones_pivot = {}

    for producto in sorted(modelos_finales.keys()):
        features_base = ultimo_features[producto]['features'].copy()
        valid_cols = ultimo_features[producto]['valid_cols']

        # Parsear columnas de lag y MA para actualización recursiva
        lag_map = {}  # col_name -> n (Lag_N)
        ma_map = {}   # col_name -> window (MA_N)
        for col in features_base.index:
            m = re.match(r'Lag_(\d+)$', str(col), re.IGNORECASE)
            if m:
                lag_map[col] = int(m.group(1))
            m = re.match(r'MA_(\d+)$', str(col), re.IGNORECASE)
            if m:
                ma_map[col] = int(m.group(1))

        # Buffer de historia: valores reales suficientes para cubrir el lag máximo
        max_lag = max(lag_map.values()) if lag_map else 0
        max_ma = max(ma_map.values()) if ma_map else 0
        buffer_needed = max(max_lag, max_ma, 1)

        ventas_reales = historia_real[producto]
        # Inicializar buffer con los últimos N valores reales
        history = list(ventas_reales[-buffer_needed:]) if len(ventas_reales) >= buffer_needed else list(ventas_reales)

        residuales_media = residuales_por_producto[producto]['media']
        residuales_std = residuales_por_producto[producto]['std']

        predicciones_pivot[producto] = []
        np.random.seed(42)

        for semana_num in range(1, 53):
            features_pd = features_base.copy()

            # Actualizar lags con el valor correcto del buffer histórico
            # Lag_N = valor de N semanas atrás en la historia combinada
            for col, lag_n in lag_map.items():
                if len(history) >= lag_n:
                    features_pd.loc[col] = history[-lag_n]

            # Actualizar medias móviles con rolling mean del buffer
            for col, window in ma_map.items():
                if len(history) >= window:
                    features_pd.loc[col] = float(np.mean(history[-window:]))
                elif len(history) > 0:
                    features_pd.loc[col] = float(np.mean(history))

            features_array = features_pd.values.reshape(1, -1)
            features_array = np.nan_to_num(features_array, nan=0.0)
            pred_base = float(modelos_finales[producto].predict(features_array)[0])
            pred_base = max(0, pred_base)

            # Añadir ruido residual con decaimiento (incertidumbre crece con horizonte)
            residual_ajuste = np.random.normal(residuales_media, residuales_std + abs(residuales_std * 0.3))
            decay_factor = 1.0 - (semana_num - 1) / 52 * 0.7
            residual_final = residual_ajuste * decay_factor
            pred = max(0, pred_base + residual_final)

            # Agregar predicción al buffer para la siguiente iteración
            history.append(pred)

            mae = params_ganadores[producto].get('mae', 50)
            lower_bound = max(0, pred - 1.96 * mae)
            upper_bound = pred + 1.96 * mae

            predicciones_largo.append({
                'Producto_codigo': producto,
                'Semana': f'W+{semana_num}',
                'Prediccion': round(pred, 2),
                'Lower_Bound_95': round(lower_bound, 2),
                'Upper_Bound_95': round(upper_bound, 2)
            })

            predicciones_pivot[producto].append(round(pred, 2))

    # Export
    data_dir = output_dir
    archivo_largo = os.path.join(data_dir, 'predicciones_52semanas_largo_V4.csv')
    pd.DataFrame(predicciones_largo).to_csv(archivo_largo, index=False)

    # pivot
    df_pivot_data = []
    for semana_num in range(1, 53):
        fila = {'Semana': f'W+{semana_num}'}
        for producto in sorted(predicciones_pivot.keys()):
            fila[producto] = predicciones_pivot[producto][semana_num - 1]
        df_pivot_data.append(fila)
    df_pivot = pd.DataFrame(df_pivot_data)
    archivo_pivot = os.path.join(data_dir, 'predicciones_52semanas_pivot_V4.csv')
    df_pivot.to_csv(archivo_pivot, index=False)

    modelos_meta = {}
    for prod, datos in params_ganadores.items():
        modelos_meta[prod] = {
            'algoritmo': datos.get('algoritmo'),
            'r2': float(datos.get('r2', 0)),
            'mae': float(datos.get('mae', 0)),
            'rmse': float(datos.get('rmse', 0))
        }

    metadata = {
        'version': 'V4 - AutoRegresion Recursiva',
        'residuales_entrenamiento': residuales_por_producto,
        'modelos': modelos_meta
    }

    archivo_metadata = os.path.join(data_dir, 'predicciones_52semanas_METADATA_V4.json')
    with open(archivo_metadata, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, default=str)

    return {
        'largo': archivo_largo,
        'pivot': archivo_pivot,
        'metadata': archivo_metadata
    }
