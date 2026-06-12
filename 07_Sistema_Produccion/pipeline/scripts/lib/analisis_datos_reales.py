"""
EDA pipeline stage: genera todos los CSVs de análisis histórico
que consume el frontend (03_ANALISIS_EXPLORATORIO_DATOS/).

Funciones principales:
  run_analisis_datos_reales(data_dir, output_dir)  — scripts 01 + 07B
  run_analisis_planchas(output_dir)                — scripts 13 + 14
"""

from __future__ import annotations

import json
import os
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless — sin display
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

# Productos objetivo para vistas semanales individuales
_CODIGOS_OBJETIVO = ["CER 001", "CER 005", "CEO 001", "CEO 006", "CERE 002", "CER 004", "CER 008"]

# Configuración plancha por producto
_PLANCHA_META = {
    "CER001":  {"sheets_per_unit": 0.007, "price": 129.95},
    "CER005":  {"sheets_per_unit": 0.007, "price": 129.95},
    "CER004":  {"sheets_per_unit": 0.007, "price": 201.63},
    "CERE002": {"sheets_per_unit": 0.007, "price": 201.63},
    "CEO001":  {"sheets_per_unit": 0.009, "price": 129.95},
    "CEO006":  {"sheets_per_unit": 0.009, "price": 129.95},
    "CER008":  {"sheets_per_unit": 0.009, "price": 201.63},
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _save(df: pd.DataFrame, output_dir: str, filename: str, sep: str = ";") -> None:
    path = os.path.join(output_dir, filename)
    df.to_csv(path, sep=sep, index=False, encoding="latin-1")
    print(f"  ✓ {filename}")


def _load_raw(data_dir: str) -> pd.DataFrame:
    archivos = sorted([
        f for f in os.listdir(data_dir)
        if f.startswith("Movimientos_") and f.endswith(".csv") and "backup" not in f.lower()
    ])
    if not archivos:
        raise FileNotFoundError(f"No se encontraron archivos Movimientos_*.csv en {data_dir}")

    dfs = []
    for arch in archivos:
        print(f"  Cargando: {arch}")
        df = pd.read_csv(os.path.join(data_dir, arch), sep=";", encoding="latin-1")
        df.columns = df.columns.str.strip()
        rename = {"salida": "Salida", "entrada": "Entrada", "documento": "Documento",
                  "número": "Número", "código": "Código", "fecha": "Fecha", "saldo": "Saldo"}
        for old, new in rename.items():
            if old in df.columns and new not in df.columns:
                df.rename(columns={old: new}, inplace=True)
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    print(f"  Total registros: {len(df):,}")
    return df


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["Entrada", "Salida", "Saldo"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df.fillna({"Bodega": "Sin asignar", "Documento": "Desconocido",
                "Canal_Venta": "Sin canal", "Empresa_Cliente": "Sin cliente"}, inplace=True)

    # Regla 1: excluir traspasos
    if "Documento" in df.columns:
        df = df[~df["Documento"].str.contains("Traspaso entre Almac", na=False, case=False)]

    # Regla 2: excluir guías donde Entrada == Salida
    if "Documento" in df.columns and "Número" in df.columns:
        mask_guia = df["Documento"].str.contains(
            "Guía de remisión - R|GUIA ELECTRONICA-REM", na=False, case=False)
        df_guias = df[mask_guia]
        if len(df_guias) > 0:
            agg = df_guias.groupby("Número").agg({"Entrada": "sum", "Salida": "sum"})
            excluir = agg[agg["Entrada"] == agg["Salida"]].index.tolist()
            df = df[~(mask_guia & df["Número"].isin(excluir))]

    return df.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISIS DATOS REALES  (scripts 01 + 07B)
# ─────────────────────────────────────────────────────────────────────────────

def run_analisis_datos_reales(data_dir: str, output_dir: str) -> None:
    """Genera archivos 01-08 y 07B en output_dir a partir de data_dir."""
    os.makedirs(output_dir, exist_ok=True)
    plt.rcParams["figure.figsize"] = (12, 7)
    sns.set_style("whitegrid")

    print("\n[EDA] Cargando datos...")
    df = _load_raw(data_dir)
    df = _clean(df)

    df_ventas = df[df["Salida"] > 0].copy()
    df_produccion = df[df["Entrada"] > 0].copy()

    # ── 01: Ventas por producto ──────────────────────────────────────────────
    ventas_prod = df_ventas.groupby("Código").agg(
        Num_Transacciones=("Salida", "count"),
        Salida_Total=("Salida", "sum"),
        Salida_Promedio=("Salida", "mean"),
        Salida_Std=("Salida", "std"),
        Salida_Min=("Salida", "min"),
        Salida_Max=("Salida", "max"),
        Descripción=("Descripción", "first"),
    ).reset_index().sort_values("Salida_Total", ascending=False)
    total_ventas = ventas_prod["Salida_Total"].sum()
    ventas_prod["Acumulado_pct"] = 100 * ventas_prod["Salida_Total"].cumsum() / total_ventas
    _save(ventas_prod, output_dir, "01_VENTAS_POR_PRODUCTO.csv")

    # ── 01B: Producción por producto ────────────────────────────────────────
    prod_prod = df_produccion.groupby("Código").agg(
        Num_Transacciones=("Entrada", "count"),
        Entrada_Total=("Entrada", "sum"),
        Entrada_Promedio=("Entrada", "mean"),
        Entrada_Std=("Entrada", "std"),
        Entrada_Min=("Entrada", "min"),
        Entrada_Max=("Entrada", "max"),
        Descripción=("Descripción", "first"),
    ).reset_index().sort_values("Entrada_Total", ascending=False)
    total_prod = prod_prod["Entrada_Total"].sum()
    prod_prod["Acumulado_pct"] = 100 * prod_prod["Entrada_Total"].cumsum() / total_prod
    _save(prod_prod, output_dir, "01B_PRODUCCION_POR_PRODUCTO.csv")

    # ── 02: Stock por producto ──────────────────────────────────────────────
    stock_prod = df.groupby("Código").agg(
        Stock_Min=("Saldo", "min"),
        Stock_Promedio=("Saldo", "mean"),
        Stock_Max=("Saldo", "max"),
        Stock_Std=("Saldo", "std"),
        Num_Registros=("Saldo", "count"),
        Bodega_Principal=("Bodega", lambda x: x.mode()[0] if len(x) > 0 else "Unknown"),
    ).reset_index().sort_values("Stock_Promedio", ascending=False)
    _save(stock_prod, output_dir, "02_STOCK_POR_PRODUCTO.csv")

    # ── 03: Rotación ────────────────────────────────────────────────────────
    rotacion = ventas_prod[["Código", "Salida_Total", "Descripción"]].merge(
        stock_prod[["Código", "Stock_Promedio"]], on="Código", how="left")
    rotacion["Rotacion"] = rotacion["Salida_Total"] / rotacion["Stock_Promedio"].replace(0, 1)
    rotacion = rotacion.sort_values("Rotacion", ascending=False)
    _save(rotacion, output_dir, "03_ROTACION_INVENTARIO.csv")

    # ── 04: Por bodega ──────────────────────────────────────────────────────
    bodega = df_ventas.groupby("Bodega").agg(
        Num_Transacciones=("Salida", "count"),
        Salida_Total=("Salida", "sum"),
        Productos_Unicos=("Código", "nunique"),
    ).reset_index().sort_values("Salida_Total", ascending=False)
    _save(bodega, output_dir, "04_VENTAS_POR_BODEGA.csv")

    # ── 05: Por canal ───────────────────────────────────────────────────────
    canal = df_ventas.groupby("Canal_Venta").agg(
        Num_Transacciones=("Salida", "count"),
        Salida_Total=("Salida", "sum"),
        Productos_Unicos=("Código", "nunique"),
    ).reset_index().sort_values("Salida_Total", ascending=False)
    _save(canal, output_dir, "05_VENTAS_POR_CANAL.csv")

    # ── 06: Tendencia mensual ───────────────────────────────────────────────
    dv = df_ventas[df_ventas["Fecha"].notna()].copy()
    dv["Año"] = dv["Fecha"].dt.year
    dv["Mes"] = dv["Fecha"].dt.month
    tend = dv.groupby(["Año", "Mes"]).agg(
        Num_Transacciones=("Salida", "count"),
        Salida_Total=("Salida", "sum"),
    ).reset_index()
    tend["Año_Mes"] = tend["Año"].astype(str) + "-" + tend["Mes"].astype(str).str.zfill(2)
    _save(tend, output_dir, "06_TENDENCIA_MENSUAL.csv")

    # ── 07: Serie semanal consolidada ───────────────────────────────────────
    ds = df[df["Fecha"].notna()].copy()
    ds["Semana_Inicio"] = ds["Fecha"].dt.to_period("W").dt.start_time
    ventas_sem = ds.groupby("Semana_Inicio", as_index=False)["Salida"].sum().rename(
        columns={"Salida": "Ventas_Semanales"})
    prod_sem = ds.groupby("Semana_Inicio", as_index=False)["Entrada"].sum().rename(
        columns={"Entrada": "Produccion_Semanal"})
    stock_cierre = (ds.sort_values(["Código", "Fecha"])
                    .groupby(["Semana_Inicio", "Código"], as_index=False).tail(1)
                    .groupby("Semana_Inicio", as_index=False)["Saldo"].sum()
                    .rename(columns={"Saldo": "Stock_Cierre_Semanal"}))
    serie_sem = (ventas_sem.merge(prod_sem, on="Semana_Inicio", how="outer")
                 .merge(stock_cierre, on="Semana_Inicio", how="outer")
                 .sort_values("Semana_Inicio").fillna(0))
    _save(serie_sem, output_dir, "07_SERIE_SEMANAL_VENTAS_PRODUCCION_STOCK.csv")

    # ── 07B: Serie semanal desde 2022 ───────────────────────────────────────
    serie_2022 = serie_sem.copy()
    serie_2022["Semana_Inicio"] = pd.to_datetime(serie_2022["Semana_Inicio"], errors="coerce")
    serie_2022 = serie_2022[serie_2022["Semana_Inicio"] >= pd.Timestamp("2022-01-01")]
    _save(serie_2022, output_dir, "07B_SERIE_SEMANAL_VENTAS_PRODUCCION_STOCK_DESDE_2022.csv")

    # ── 08: Series semanales por producto ───────────────────────────────────
    cod_norm = ds["Código"].astype(str).str.upper().str.replace("'", "", regex=False).str.strip()
    for cod_obj in _CODIGOS_OBJETIVO:
        df_p = ds[cod_norm == cod_obj].copy()
        if df_p.empty:
            print(f"  ! Sin datos para {cod_obj}")
            continue
        serie_p = (df_p.sort_values("Fecha")
                   .groupby("Semana_Inicio", as_index=False)
                   .agg(Ventas_Semanales=("Salida", "sum"),
                        Produccion_Semanal=("Entrada", "sum"),
                        Stock_Cierre_Semanal=("Saldo", "last"))
                   .sort_values("Semana_Inicio"))
        _save(serie_p, output_dir, f"08_SERIE_SEMANAL_{cod_obj.replace(' ', '')}.csv")

    # ── Resumen JSON ────────────────────────────────────────────────────────
    pareto_80 = int(len(ventas_prod[ventas_prod["Acumulado_pct"] <= 80]))
    resumen = {
        "timestamp": datetime.now().isoformat(),
        "registros_totales": int(len(df)),
        "productos_totales": int(df["Código"].nunique()),
        "productos_con_ventas": int(len(ventas_prod)),
        "productos_pareto_80pct": pareto_80,
        "rango_fechas": f"{df['Fecha'].min()} a {df['Fecha'].max()}",
        "semanas_analizadas": int(len(serie_sem)),
    }
    with open(os.path.join(output_dir, "RESUMEN_ANALISIS.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    print("  ✓ RESUMEN_ANALISIS.json")

    print("[EDA] Análisis de datos reales completado.")


# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISIS PLANCHAS  (scripts 13 + 14)
# ─────────────────────────────────────────────────────────────────────────────

def run_analisis_planchas(output_dir: str) -> None:
    """Genera archivos 09, 13 y 14 de planchas. Depende de los 08_SERIE_SEMANAL_*.csv."""
    os.makedirs(output_dir, exist_ok=True)
    summary_rows = []

    for code, meta in _PLANCHA_META.items():
        infile = os.path.join(output_dir, f"08_SERIE_SEMANAL_{code}.csv")
        if not os.path.exists(infile):
            print(f"  ! Archivo faltante, skip: 08_SERIE_SEMANAL_{code}.csv")
            continue

        df = pd.read_csv(infile, sep=";", encoding="latin-1")
        if "Semana_Inicio" in df.columns:
            df["Semana_Inicio"] = pd.to_datetime(df["Semana_Inicio"], errors="coerce")
        df["Ventas_Semanales"] = pd.to_numeric(df.get("Ventas_Semanales", 0), errors="coerce").fillna(0)
        df["Produccion_Semanal"] = pd.to_numeric(df.get("Produccion_Semanal", 0), errors="coerce").fillna(0)

        spu = meta["sheets_per_unit"]
        price = meta["price"]

        # ── 09: Consumo de planchas por producto ────────────────────────────
        df_09 = df.copy()
        df_09["Planchas_Ventas"] = df_09["Ventas_Semanales"] * spu
        df_09["Planchas_Produccion"] = df_09["Produccion_Semanal"] * spu
        _save(df_09[["Semana_Inicio", "Ventas_Semanales", "Produccion_Semanal",
                      "Planchas_Ventas", "Planchas_Produccion"]],
              output_dir, f"09_PLANCHA_CONSUMO_{code}.csv")

        # ── 13: GAP planchas ventas vs producción ───────────────────────────
        df["Planchas_Ventas"] = df["Ventas_Semanales"] * spu
        df["Planchas_Produccion"] = df["Produccion_Semanal"] * spu
        df["Planchas_Gap"] = df["Planchas_Produccion"] - df["Planchas_Ventas"]
        _save(df[["Semana_Inicio", "Ventas_Semanales", "Produccion_Semanal",
                   "Planchas_Ventas", "Planchas_Produccion", "Planchas_Gap"]],
              output_dir, f"13_PLANCHA_GAP_{code}.csv")

        # ── 14: acumulados para resumen ─────────────────────────────────────
        tp = df["Produccion_Semanal"].sum()
        tv = df["Ventas_Semanales"].sum()
        pp = tp * spu
        pv = tv * spu
        summary_rows.append({
            "Código": code,
            "Producción_Total": int(tp),
            "Ventas_Total": int(tv),
            "Planchas_Producción": round(pp, 2),
            "Planchas_Ventas": round(pv, 2),
            "Planchas_Gap": round(pp - pv, 2),
            "Costo_Producción_S/": round(pp * price, 2),
            "Costo_Ventas_S/": round(pv * price, 2),
            "Ahorro_Potencial_S/": round((pp - pv) * price, 2),
            "Eficiencia_%": round(tv / tp * 100, 1) if tp > 0 else 0,
        })

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        _save(summary_df, output_dir, "14_COSTO_PLANCHA_ACUMULADO_POR_PRODUCTO.csv")

        # ── 10: Consumo agregado semanal ────────────────────────────────────
        agg_frames = []
        for code in _PLANCHA_META:
            f = os.path.join(output_dir, f"09_PLANCHA_CONSUMO_{code}.csv")
            if os.path.exists(f):
                tmp = pd.read_csv(f, sep=";", encoding="latin-1")
                tmp["Código"] = code
                agg_frames.append(tmp)
        if agg_frames:
            agg = pd.concat(agg_frames, ignore_index=True)
            agg["Semana_Inicio"] = pd.to_datetime(agg["Semana_Inicio"], errors="coerce")
            agg_sem = agg.groupby("Semana_Inicio", as_index=False).agg(
                Planchas_Ventas_Total=("Planchas_Ventas", "sum"),
                Planchas_Produccion_Total=("Planchas_Produccion", "sum"),
            ).sort_values("Semana_Inicio")
            _save(agg_sem, output_dir, "10_PLANCHA_CONSUMO_AGREGADO_SEMANAL.csv")

        # ── 11: Totales por producto ────────────────────────────────────────
        totales = summary_df[["Código", "Planchas_Producción", "Planchas_Ventas", "Planchas_Gap"]].copy()
        _save(totales, output_dir, "11_PLANCHA_CONSUMO_TOTALES_POR_PRODUCTO.csv")

    print("[EDA] Análisis de planchas completado.")
