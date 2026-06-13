from pathlib import Path
import pandas as pd
import numpy as np
import json


def run_limpieza_preprocesamiento(output_dir: str) -> None:
    output_dir = Path(output_dir)
    datos_path = output_dir / "DATOS_TOP20_VENTAS.csv"

    if not datos_path.exists():
        raise FileNotFoundError(f"DATOS_TOP20_VENTAS.csv not found: {datos_path}")

    df = pd.read_csv(datos_path, sep=";", encoding="latin-1", parse_dates=["Fecha"], dayfirst=False)
    df["Salida"] = pd.to_numeric(df["Salida"], errors="coerce").fillna(0)

    reporte = {"outliers_por_sku": {}, "total_outliers": 0}

    for sku in df["Código"].unique():
        mask = df["Código"] == sku
        salidas_positivas = df.loc[mask & (df["Salida"] > 0), "Salida"]

        if len(salidas_positivas) < 4:
            continue

        Q1 = salidas_positivas.quantile(0.25)
        Q3 = salidas_positivas.quantile(0.75)
        iqr = Q3 - Q1
        upper = Q3 + 1.5 * iqr
        lower = max(0.0, Q1 - 1.5 * iqr)
        mediana = salidas_positivas.median()

        outlier_mask = mask & (df["Salida"] > 0) & ((df["Salida"] > upper) | (df["Salida"] < lower))
        n = int(outlier_mask.sum())
        if n > 0:
            df.loc[outlier_mask, "Salida"] = mediana
            reporte["outliers_por_sku"][sku] = n
            reporte["total_outliers"] += n

    df.to_csv(datos_path, sep=";", encoding="latin-1", index=False)

    reporte_path = output_dir / "LIMPIEZA_REPORTE.json"
    with open(reporte_path, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    total = reporte["total_outliers"]
    print(f"[Limpieza] {total} outliers reemplazados por mediana por SKU")
    for sku, n in reporte["outliers_por_sku"].items():
        print(f"  {sku}: {n} outliers")
    print("✓ LIMPIEZA_REPORTE.json")
