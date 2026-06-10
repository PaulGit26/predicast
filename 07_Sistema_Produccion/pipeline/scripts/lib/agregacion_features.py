"""
Wrapper para agregación semanal y feature engineering.
Provee `run_agregacion_features(output_dir, datos_top20_path=None, pareto_result_path=None)`
"""
import os
import json
from datetime import datetime
import pandas as pd
import numpy as np


def _week_to_date(year: int, week: int):
    try:
        # Primer día (lunes) de la ISO week
        return datetime.fromisocalendar(int(year), int(week), 1)
    except Exception:
        return pd.NaT


def run_agregacion_features(output_dir: str, datos_top20_path: str = None, pareto_result_path: str = None):
    OUTPUT_DIR = output_dir
    if datos_top20_path is None:
        datos_top20_path = os.path.join(OUTPUT_DIR, "DATOS_TOP20_VENTAS.csv")
    if pareto_result_path is None:
        pareto_result_path = os.path.join(OUTPUT_DIR, "PARETO_RESULTADO.json")

    with open(pareto_result_path, "r", encoding="utf-8") as f:
        pareto = json.load(f)
        productos_criticos = pareto.get("productos_seleccionados", [])

    # Load sales
    df_ventas = pd.read_csv(datos_top20_path, sep=";", encoding="latin-1", parse_dates=["Fecha"], dayfirst=False)
    df_ventas["Salida"] = pd.to_numeric(df_ventas.get("Salida", 0), errors="coerce").fillna(0)

    # Filter to critical products
    df_ventas = df_ventas[df_ventas["Código"].isin(productos_criticos)].copy()
    df_ventas = df_ventas.dropna(subset=["Fecha"])  # drop rows without date

    # Week/year columns
    df_ventas["Año"] = df_ventas["Fecha"].dt.isocalendar().year
    df_ventas["Semana"] = df_ventas["Fecha"].dt.isocalendar().week

    # Aggregation
    agg_semanal = df_ventas.groupby(["Año", "Semana", "Código"]).agg({
        "Salida": ["sum", "count", "mean", "std", "min", "max"],
        "Empresa_Cliente": lambda x: x.mode().iat[0] if len(x.mode()) > 0 else "Unknown",
        "Canal_Venta": lambda x: x.mode().iat[0] if len(x.mode()) > 0 else "Unknown",
        "Punto_Venta": lambda x: x.mode().iat[0] if len(x.mode()) > 0 else "Unknown",
    }).reset_index()

    agg_semanal.columns = ["Año", "Semana", "Código", "Salida", "Transacciones",
                           "Salida_Promedio", "Salida_Std", "Salida_Min", "Salida_Max",
                           "Empresa_Modo", "Canal_Modo", "Punto_Modo"]

    # Reconstruct Fecha from ISO year-week
    agg_semanal["Fecha"] = agg_semanal.apply(lambda r: _week_to_date(r["Año"], r["Semana"]), axis=1)

    # Feature engineering per product
    features_list = []
    for codigo in productos_criticos:
        df_prod = agg_semanal[agg_semanal["Código"] == codigo].sort_values(["Año", "Semana"]).copy()
        if len(df_prod) < 2:
            continue
        df_prod = df_prod.reset_index(drop=True)

        # Temporal
        df_prod["Mes"] = df_prod["Fecha"].dt.month
        df_prod["Trimestre"] = df_prod["Fecha"].dt.quarter
        df_prod["Día_Semana"] = df_prod["Fecha"].dt.dayofweek
        df_prod["Día_Año"] = df_prod["Fecha"].dt.dayofyear
        df_prod["Num_Semana_Año"] = df_prod["Fecha"].dt.isocalendar().week

        # Lags — Lag_52 captures annual seasonality (same week last year)
        for lag in [1, 2, 3, 4, 13, 52]:
            df_prod[f"Lag_{lag}"] = df_prod["Salida"].shift(lag)

        # Moving averages (use previous values only)
        salida_shifted = df_prod["Salida"].shift(1)
        for window in [2, 4, 8, 13, 26]:
            df_prod[f"MA_{window}"] = salida_shifted.rolling(window=window, min_periods=1).mean()

        # Volatility
        for window in [4, 8, 13]:
            df_prod[f"Volatilidad_{window}"] = salida_shifted.rolling(window=window, min_periods=1).std().fillna(0)

        # Trends
        df_prod["Trend_vs_MA4"] = ((df_prod["Salida"] - df_prod.get("MA_4", 0)) / df_prod.get("MA_4", 1)).fillna(0)
        df_prod["Trend_vs_MA8"] = ((df_prod["Salida"] - df_prod.get("MA_8", 0)) / df_prod.get("MA_8", 1)).fillna(0)

        # Ratios
        df_prod["Ratio_Min_Max"] = df_prod["Salida_Min"] / df_prod["Salida_Max"].replace(0, 1)
        df_prod["Ratio_Transacciones"] = df_prod["Transacciones"] / df_prod["Transacciones"].rolling(4, min_periods=1).mean()
        df_prod["Variabilidad_Intra"] = df_prod["Salida_Std"] / df_prod["Salida_Promedio"].replace(0, 1)

        # Seasonal encoding
        df_prod["Semana_Sin"] = np.sin(2 * np.pi * df_prod["Num_Semana_Año"] / 52)
        df_prod["Semana_Cos"] = np.cos(2 * np.pi * df_prod["Num_Semana_Año"] / 52)
        df_prod["Mes_Sin"] = np.sin(2 * np.pi * (df_prod["Mes"] - 1) / 12)
        df_prod["Mes_Cos"] = np.cos(2 * np.pi * (df_prod["Mes"] - 1) / 12)

        # One-hot categoricals
        empresa_dummies = pd.get_dummies(df_prod["Empresa_Modo"], prefix="Empresa")
        canal_dummies = pd.get_dummies(df_prod["Canal_Modo"], prefix="Canal")
        punto_dummies = pd.get_dummies(df_prod["Punto_Modo"], prefix="Punto")
        for col in empresa_dummies.columns:
            df_prod[col] = empresa_dummies[col].astype(int)
        for col in canal_dummies.columns:
            df_prod[col] = canal_dummies[col].astype(int)
        for col in punto_dummies.columns:
            df_prod[col] = punto_dummies[col].astype(int)

        # Trim dummies
        trim_dummies = pd.get_dummies(df_prod["Trimestre"], prefix="Trim")
        for col in trim_dummies.columns:
            df_prod[col] = trim_dummies[col].astype(int)

        df_prod["Semana_Consecutivas_Venta"] = (df_prod["Salida"] > 0).astype(int).cumsum()

        features_list.append(df_prod)

    if not features_list:
        return {'complete': False, 'message': 'No features generated for critical products'}

    df_features = pd.concat(features_list, ignore_index=True)

    # Impute lags
    lag_cols = [col for col in df_features.columns if any(prefix in col for prefix in ["Lag_", "MA_", "Volatilidad_"])]
    df_features[lag_cols] = df_features.groupby("Código")[lag_cols].transform(lambda x: x.ffill().bfill().fillna(0))

    # Prepare export
    feature_cols = [col for col in df_features.columns
                    if col not in ["Código", "Año", "Semana", "Fecha", "Empresa_Modo", "Canal_Modo", "Punto_Modo",
                                   "Salida", "Transacciones", "Salida_Promedio", "Salida_Std", "Salida_Min", "Salida_Max"]]

    # Export completo
    archivo_completo = os.path.join(OUTPUT_DIR, "FEATURES_SEMANAL_COMPLETO.csv")
    df_features.to_csv(archivo_completo, sep=";", encoding="latin-1", index=False)

    # Export para modelos
    archivo_modelos = os.path.join(OUTPUT_DIR, "FEATURES_SEMANAL_PARA_MODELOS.csv")
    df_export_features = df_features[["Código", "Año", "Semana", "Fecha", "Salida"] + feature_cols].copy()
    df_export_features.to_csv(archivo_modelos, sep=";", encoding="latin-1", index=False)

    # Metadata
    feature_metadata = {
        "productos_criticos": productos_criticos,
        "total_registros": int(len(df_features)),
        "total_features": len(feature_cols),
        "feature_names": feature_cols
    }
    archivo_meta = os.path.join(OUTPUT_DIR, "FEATURES_METADATA.json")
    with open(archivo_meta, "w", encoding="utf-8") as f:
        json.dump(feature_metadata, f, indent=2, ensure_ascii=False)

    return {
        'complete': True,
        'archivo_completo': archivo_completo,
        'archivo_modelos': archivo_modelos,
        'archivo_meta': archivo_meta,
        'n_registros': len(df_features)
    }
