from pathlib import Path
import pandas as pd
import os
import json
from datetime import datetime


def run_preparar_top20(data_dir: str, output_dir: str):
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    archivos = sorted([f for f in os.listdir(data_dir)
                       if f.startswith("Movimientos_") and f.endswith(".csv") and "backup" not in f])

    if not archivos:
        raise FileNotFoundError(f"No movimiento files found in {data_dir}")

    dfs = []
    for arch in archivos:
        ruta = data_dir / arch
        df = pd.read_csv(ruta, sep=";", encoding="latin-1")
        df.columns = df.columns.str.strip()

        # Normalizar nombres de columnas
        if "salida" in df.columns and "Salida" not in df.columns:
            df.rename(columns={"salida": "Salida"}, inplace=True)
        if "entrada" in df.columns and "Entrada" not in df.columns:
            df.rename(columns={"entrada": "Entrada"}, inplace=True)
        if "documento" in df.columns and "Documento" not in df.columns:
            df.rename(columns={"documento": "Documento"}, inplace=True)
        if "número" in df.columns and "Número" not in df.columns:
            df.rename(columns={"número": "Número"}, inplace=True)
        if "código" in df.columns and "Código" not in df.columns:
            df.rename(columns={"código": "Código"}, inplace=True)

        dfs.append(df)

    df_raw = pd.concat(dfs, ignore_index=True)

    df_clean = df_raw.copy()
    for col in ["Entrada", "Salida"]:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)

    if "Fecha" in df_clean.columns:
        df_clean["Fecha"] = pd.to_datetime(df_clean["Fecha"], errors="coerce")

    # Excluir traspasos
    if "Documento" in df_clean.columns:
        mask_traspaso = df_clean["Documento"].str.contains("Traspaso entre Almac", na=False, case=False)
        df_clean = df_clean[~mask_traspaso]

    # Guía de remisión
    if "Documento" in df_clean.columns and "Número" in df_clean.columns:
        mask_guia = df_clean["Documento"].str.contains("Guía de remisión - R", na=False, case=False)
        df_guias = df_clean[mask_guia].copy()
        if len(df_guias) > 0:
            guias_agrupadas = df_guias.groupby("Número").agg({"Entrada": "sum", "Salida": "sum"}).reset_index()
            mask_iguales = guias_agrupadas["Entrada"] == guias_agrupadas["Salida"]
            guias_a_excluir = guias_agrupadas[mask_iguales]["Número"].tolist()
            df_clean = df_clean[~((df_clean["Documento"].str.contains("Guía de remisión - R", na=False)) & (df_clean["Número"].isin(guias_a_excluir)))]

    # Ventas
    df_ventas = df_clean[df_clean.get("Salida", 0) > 0].copy()

    if "Código" in df_ventas.columns:
        ventas_por_producto = df_ventas.groupby("Código")["Salida"].agg(["count", "sum", "mean", "std", "min", "max"]).round(2)
        ventas_por_producto.columns = ["Transacciones", "Salida_Total", "Salida_Promedio", "Salida_Std", "Salida_Min", "Salida_Max"]
        ventas_por_producto = ventas_por_producto.sort_values("Salida_Total", ascending=False)
        top20_codigos = ventas_por_producto.head(20).index.tolist()
    else:
        top20_codigos = []

    df_top20 = df_ventas[df_ventas["Código"].isin(top20_codigos)].copy() if top20_codigos else df_ventas

    # Export
    df_top20.to_csv(output_dir / "DATOS_TOP20_VENTAS.csv", sep=";", encoding="latin-1", index=False)
    ventas_por_producto.head(20).reset_index().to_csv(output_dir / "TOP20_PRODUCTOS.csv", sep=";", encoding="latin-1", index=False)

    resumen = {
        "timestamp": datetime.now().isoformat(),
        "datos_raw": int(len(df_raw)),
        "datos_limpios": int(len(df_clean)),
        "registros_venta": int(len(df_ventas)),
        "productos_totales": int(ventas_por_producto.shape[0]) if len(ventas_por_producto) else 0,
        "top20_productos": top20_codigos,
        "registros_top20": int(len(df_top20))
    }

    with open(output_dir / "RESUMEN_LIMPIEZA.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    return {
        "datos_top20": str(output_dir / "DATOS_TOP20_VENTAS.csv"),
        "top20_csv": str(output_dir / "TOP20_PRODUCTOS.csv"),
        "resumen": resumen
    }
