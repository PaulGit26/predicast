from pathlib import Path
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime


def run_agregacion_features(eda_output_dir: str):
    eda_output_dir = Path(eda_output_dir)
    pareto_file = eda_output_dir / "PARETO_RESULTADO.json"
    datos_top20 = eda_output_dir / "DATOS_TOP20_VENTAS.csv"

    if not pareto_file.exists():
        raise FileNotFoundError(f"Pareto result not found: {pareto_file}")
    if not datos_top20.exists():
        raise FileNotFoundError(f"DATOS_TOP20_VENTAS.csv not found: {datos_top20}")

    with open(pareto_file, "r", encoding="utf-8") as f:
        pareto = json.load(f)
        productos_criticos = pareto.get("productos_seleccionados", [])

    df_ventas = pd.read_csv(datos_top20, sep=";", encoding="latin-1", parse_dates=["Fecha"]) if datos_top20.exists() else pd.DataFrame()

    if df_ventas.empty:
        raise RuntimeError("No ventas data available for aggregation")

    df_ventas["Salida"] = pd.to_numeric(df_ventas["Salida"], errors="coerce").fillna(0)

    # Filter to critical products
    df_ventas = df_ventas[df_ventas["Código"].isin(productos_criticos)].copy()
    df_ventas = df_ventas.dropna(subset=["Fecha"]) if "Fecha" in df_ventas.columns else df_ventas

    # Weekly aggregation
    df_ventas["Año"] = df_ventas["Fecha"].dt.isocalendar().year
    df_ventas["Semana"] = df_ventas["Fecha"].dt.isocalendar().week

    agg_semanal = df_ventas.groupby(["Año", "Semana", "Código"]).agg({
        "Salida": ["sum", "count", "mean", "std", "min", "max"],
        "Empresa_Cliente": lambda x: x.mode()[0] if len(x.mode()) > 0 else "Unknown",
        "Canal_Venta": lambda x: x.mode()[0] if len(x.mode()) > 0 else "Unknown",
        "Punto_Venta": lambda x: x.mode()[0] if len(x.mode()) > 0 else "Unknown",
    }).reset_index()

    agg_semanal.columns = ["Año", "Semana", "Código", "Salida", "Transacciones", "Salida_Promedio", "Salida_Std", "Salida_Min", "Salida_Max", "Empresa_Modo", "Canal_Modo", "Punto_Modo"]

    # Feature engineering - minimal: add temporal cols and lags
    features_list = []
    for codigo in productos_criticos:
        df_prod = agg_semanal[agg_semanal["Código"] == codigo].sort_values(["Año", "Semana"]).copy()
        if len(df_prod) < 2:
            continue
        df_prod = df_prod.reset_index(drop=True)
        df_prod["Mes"] = df_prod["Fecha"].dt.month
        df_prod["Trimestre"] = df_prod["Fecha"].dt.quarter
        for lag in [1, 2, 3, 4, 13]:
            df_prod[f"Lag_{lag}"] = df_prod["Salida"].shift(lag)
        salida_shifted = df_prod["Salida"].shift(1)
        for window in [2, 4, 8, 13]:
            df_prod[f"MA_{window}"] = salida_shifted.rolling(window=window, min_periods=1).mean()
        features_list.append(df_prod)

    df_features = pd.concat(features_list, ignore_index=True) if features_list else pd.DataFrame()

    output_dir = eda_output_dir
    df_features.to_csv(output_dir / "FEATURES_SEMANAL_COMPLETO.csv", sep=";", encoding="latin-1", index=False)

    feature_cols = [col for col in df_features.columns if col not in ["Código", "Año", "Semana", "Fecha", "Salida", "Transacciones"]]
    df_export_features = df_features[["Código", "Año", "Semana", "Fecha", "Salida"] + feature_cols].copy() if not df_features.empty else df_features
    df_export_features.to_csv(output_dir / "FEATURES_SEMANAL_PARA_MODELOS.csv", sep=";", encoding="latin-1", index=False)

    metadata = {
        "productos_criticos": productos_criticos,
        "total_registros": int(len(df_features)) if not df_features.empty else 0,
        "total_features": len(feature_cols)
    }
    with open(output_dir / "FEATURES_METADATA.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return {
        "features_csv": str(output_dir / "FEATURES_SEMANAL_PARA_MODELOS.csv"),
        "metadata": metadata
    }
