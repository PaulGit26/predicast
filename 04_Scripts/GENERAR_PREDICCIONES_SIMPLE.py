#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generador simple de predicciones con formato ISO para dashboard
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime, timedelta

print("[INICIO] Generando predicciones...")

# Cargar datos
df_pivot = pd.read_csv('../01_Datos/datos_semanales_pivot.csv', index_col=0)
print(f"[OK] Datos: {df_pivot.shape}")

# Cargar modelos
modelos_xgb = joblib.load('../03_Modelos/modelo_hybrid_xgboost_final.joblib')
with open('../03_Modelos/modelo_hybrid_arima_params_final.json', 'r') as f:
    arima_params = json.load(f)
print(f"[OK] Modelos cargados")

from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
warnings.filterwarnings('ignore')

def predict_arima(serie, producto, horizonte=52):
    try:
        train_series = pd.Series(serie)
        params = arima_params[producto]
        model = SARIMAX(train_series, order=params['order'], seasonal_order=params['seasonal_order'])
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            result = model.fit(disp=False, maxiter=1, low_memory=True, enforce_stationarity=False)
        forecast = result.get_forecast(steps=horizonte).predicted_mean.values
        return np.maximum(forecast, 0)
    except:
        return None

def predict_xgboost(serie, producto, horizonte=52, lags=12):
    try:
        model = modelos_xgb[producto]
        predictions = []
        hist = list(serie[-lags:])
        for i in range(horizonte):
            X_pred = np.array([hist[-lags:]])
            pred = model.predict(X_pred)[0]
            predictions.append(max(pred, 0))
            hist.append(pred)
        return np.array(predictions)
    except:
        return None

# Generar predicciones
ultima_fecha = datetime.strptime('2026-W01-1', '%Y-W%W-%w')
horizonte = 52

predicciones = {}
for idx, producto in enumerate(df_pivot.columns, 1):
    print(f"[{idx}/{len(df_pivot.columns)}] {producto}...", end=' ', flush=True)
    
    serie = df_pivot[producto].values
    pred_xgb = predict_xgboost(serie, producto, horizonte)
    pred_arima = predict_arima(serie, producto, horizonte)
    
    if pred_xgb is not None and pred_arima is not None:
        pred = 0.6 * pred_xgb + 0.4 * pred_arima
        predicciones[producto] = pred
        print(f"OK ({pred.mean():.0f})")
    else:
        print("SKIP")

# Crear fechas ISO
fechas_futuras = []
for i in range(1, horizonte + 1):
    fecha = ultima_fecha + timedelta(weeks=i)
    year, week, _ = fecha.isocalendar()
    fechas_futuras.append(f"{year}-W{week:02d}")

# Guardar PIVOT
df_pred = pd.DataFrame(predicciones).T
df_pred.columns = fechas_futuras
df_pred.to_csv('../01_Datos/predicciones_52semanas_pivot.csv')
print(f"[OK] Guardado: predicciones_52semanas_pivot.csv")

# Guardar LARGO
rows = []
for prod in predicciones:
    for fechaidx, fecha in enumerate(fechas_futuras):
        pred = predicciones[prod][fechaidx]
        std_est = pred * 0.15
        rows.append({
            'Producto_codigo': prod,
            'Semana': fecha,
            'Prediccion': pred,
            'Lower_Bound_95': max(0, pred - 1.96 * std_est),
            'Upper_Bound_95': pred + 1.96 * std_est
        })

df_largo = pd.DataFrame(rows)
df_largo.to_csv('../01_Datos/predicciones_52semanas_largo.csv', index=False)
print(f"[OK] Guardado: predicciones_52semanas_largo.csv ({len(rows)} registros)")

print("[COMPLETADO] Sistema listo para dashboard")
