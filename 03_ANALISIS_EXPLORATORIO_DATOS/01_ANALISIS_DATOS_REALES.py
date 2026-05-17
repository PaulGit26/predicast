"""
========================================================================
ANÁLISIS EXPLORATORIO DE DATOS REALES - SIN DATOS INVENTADOS
========================================================================
Script que analiza la data transaccional real:
- Usa datos de Entrada, Salida y Saldo (stock cada transacción)
- Calcula métricas reales de ventas por producto
- Analiza tendencias de stock por bodega
- Genera Pareto de ventas
- Crea gráficos de tendencias temporales
- Exporta CSVs y gráficos para análisis

Entrada: 01_Datos_Nuevos/*.csv (datos reales transaccionales)
Salida: 03_ANALISIS_EXPLORATORIO_DATOS/ (CSVs, gráficos, análisis)
========================================================================
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# Configuración
DATA_DIR = r"d:\Desktop\Predicast\01_Datos_Nuevos"
OUTPUT_DIR = r"d:\Desktop\Predicast\03_ANALISIS_EXPLORATORIO_DATOS"
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams['figure.figsize'] = (12, 7)
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 10

print("\n" + "="*80)
print("ANÁLISIS EXPLORATORIO - DATOS REALES (SIN DATOS INVENTADOS)")
print("="*80)

# ============================================================================
# PASO 1: CARGAR DATOS REALES
# ============================================================================
print("\n[1] Cargando datos transaccionales reales...")

archivos = sorted([f for f in os.listdir(DATA_DIR) 
                   if f.startswith("Movimientos_") and f.endswith(".csv") and "backup" not in f])

dfs = []
for arch in archivos:
    ruta = os.path.join(DATA_DIR, arch)
    print(f"  Cargando: {arch}")
    df = pd.read_csv(ruta, sep=";", encoding="latin-1")
    df.columns = df.columns.str.strip()
    
    # Normalizar nombres de columnas
    rename_dict = {
        "salida": "Salida", "entrada": "Entrada", "documento": "Documento",
        "número": "Número", "código": "Código", "fecha": "Fecha", "saldo": "Saldo"
    }
    for old, new in rename_dict.items():
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)
    
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)
print(f"  Total de registros cargados: {len(df):,}")

# ============================================================================
# PASO 2: PREPARAR DATOS
# ============================================================================
print("\n[2] Preparando datos...")

# Convertir numéricos
for col in ["Entrada", "Salida", "Saldo"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Convertir fechas
if "Fecha" in df.columns:
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

# Llenar valores faltantes
df.fillna({"Bodega": "Sin asignar", "Documento": "Desconocido", 
           "Canal_Venta": "Sin canal", "Empresa_Cliente": "Sin cliente"}, inplace=True)

print(f"  Registros con fechas válidas: {df['Fecha'].notna().sum():,}")
print(f"  Rango de fechas: {df['Fecha'].min()} a {df['Fecha'].max()}")
print(f"  Productos únicos: {df['Código'].nunique():,}")
print(f"  Bodegas: {df['Bodega'].unique().tolist()}")

# ============================================================================
# PASO 2B: APLICAR REGLAS DE LIMPIEZA (IGUAL QUE EN SCRIPT 02)
# ============================================================================
print("\n[2B] Aplicando reglas de limpieza (traspasos y guías)...")

registros_antes = len(df)

# REGLA 1: Excluir "Traspaso entre Almac"
if "Documento" in df.columns:
    mask_traspaso = df["Documento"].str.contains("Traspaso entre Almac", na=False, case=False)
    count_traspaso = mask_traspaso.sum()
    df = df[~mask_traspaso]
    print(f"  Excluidos traspasos: {count_traspaso:,}")

# REGLA 2: Guía de Remisión - Excluir si Entrada == Salida
count_guias_excluidas = 0
if "Documento" in df.columns and "Número" in df.columns:
    mask_guia = df["Documento"].str.contains("Guía de remisión - R|GUIA ELECTRONICA-REM", 
                                              na=False, case=False)
    df_guias = df[mask_guia].copy()
    
    if len(df_guias) > 0:
        guias_agrupadas = df_guias.groupby("Número").agg({
            "Entrada": "sum",
            "Salida": "sum"
        }).reset_index()
        
        mask_iguales = guias_agrupadas["Entrada"] == guias_agrupadas["Salida"]
        guias_a_excluir = guias_agrupadas[mask_iguales]["Número"].tolist()
        
        count_guias_excluidas = len(df_guias[df_guias["Número"].isin(guias_a_excluir)])
        df = df[~((df["Documento"].str.contains("Guía de remisión - R|GUIA ELECTRONICA-REM", 
                                                 na=False, case=False)) & 
                  (df["Número"].isin(guias_a_excluir)))]
        
        print(f"  Excluidas guías donde Entrada == Salida: {count_guias_excluidas:,}")

registros_despues = len(df)
print(f"  Registros antes: {registros_antes:,} → después: {registros_despues:,} ({registros_antes - registros_despues:,} excluidos)")

# ============================================================================
# PASO 3: ANÁLISIS DE VENTAS (SALIDA > 0)
# ============================================================================
print("\n[3] Analizando ventas (Salida > 0)...")

df_ventas = df[df["Salida"] > 0].copy()
print(f"  Registros de venta: {len(df_ventas):,}")

# Agregación por producto
ventas_producto = df_ventas.groupby("Código").agg({
    "Salida": ["count", "sum", "mean", "std", "min", "max"],
    "Descripción": "first"
}).reset_index()

ventas_producto.columns = ["Código", "Num_Transacciones", "Salida_Total", 
                           "Salida_Promedio", "Salida_Std", "Salida_Min", 
                           "Salida_Max", "Descripción"]

ventas_producto = ventas_producto.sort_values("Salida_Total", ascending=False)

print(f"  Productos con ventas: {len(ventas_producto):,}")
print(f"\n  TOP 10 productos por Salida_Total:")
for i, row in ventas_producto.head(10).iterrows():
    print(f"    {row['Código']:12s} - {row['Salida_Total']:>10,.0f} unidades | " + 
          f"{row['Num_Transacciones']:>5.0f} transacciones")

# Pareto: qué % de productos genera qué % de ventas
total_ventas = ventas_producto["Salida_Total"].sum()
ventas_producto["Acumulado_pct"] = 100 * ventas_producto["Salida_Total"].cumsum() / total_ventas

pareto_80 = len(ventas_producto[ventas_producto["Acumulado_pct"] <= 80])
print(f"\n  Análisis Pareto (80/20):")
print(f"    {pareto_80} productos generan el 80% de ventas ({pareto_80/len(ventas_producto)*100:.1f}% de productos)")

ventas_producto.to_csv(os.path.join(OUTPUT_DIR, "01_VENTAS_POR_PRODUCTO.csv"), 
                       sep=";", index=False, encoding="latin-1")
print(f"\n  ✓ Guardado: 01_VENTAS_POR_PRODUCTO.csv")

# ============================================================================
# PASO 3B: ANÁLISIS DE PRODUCCIÓN/ENTRADAS (ENTRADA > 0)
# ============================================================================
print("\n[3B] Analizando producción (Entrada > 0)...")

df_produccion = df[df["Entrada"] > 0].copy()
print(f"  Registros de producción/entrada: {len(df_produccion):,}")

# Agregación por producto
produccion_producto = df_produccion.groupby("Código").agg({
    "Entrada": ["count", "sum", "mean", "std", "min", "max"],
    "Descripción": "first"
}).reset_index()

produccion_producto.columns = ["Código", "Num_Transacciones", "Entrada_Total", 
                               "Entrada_Promedio", "Entrada_Std", "Entrada_Min", 
                               "Entrada_Max", "Descripción"]

produccion_producto = produccion_producto.sort_values("Entrada_Total", ascending=False)

print(f"  Productos con producción/entrada: {len(produccion_producto):,}")
print(f"\n  TOP 10 productos por Entrada_Total:")
for i, row in produccion_producto.head(10).iterrows():
    print(f"    {row['Código']:12s} - {row['Entrada_Total']:>10,.0f} unidades | " + 
          f"{row['Num_Transacciones']:>5.0f} transacciones")

# Pareto producción
total_produccion = produccion_producto["Entrada_Total"].sum()
produccion_producto["Acumulado_pct"] = 100 * produccion_producto["Entrada_Total"].cumsum() / total_produccion

pareto_80_prod = len(produccion_producto[produccion_producto["Acumulado_pct"] <= 80])
print(f"\n  Análisis Pareto Producción (80/20):")
print(f"    {pareto_80_prod} productos generan el 80% de producción ({pareto_80_prod/len(produccion_producto)*100:.1f}% de productos)")

produccion_producto.to_csv(os.path.join(OUTPUT_DIR, "01B_PRODUCCION_POR_PRODUCTO.csv"), 
                           sep=";", index=False, encoding="latin-1")
print(f"\n  ✓ Guardado: 01B_PRODUCCION_POR_PRODUCTO.csv")


# ============================================================================
# PASO 4: ANÁLISIS DE STOCK (SALDO)
# ============================================================================
print("\n[4] Analizando stock (usando Saldo)...")

# Para cada producto, calcular estadísticas de stock
stock_producto = df.groupby("Código").agg({
    "Saldo": ["min", "mean", "max", "std", "count"],
    "Bodega": lambda x: x.mode()[0] if len(x.mode()) > 0 else "Unknown"
}).reset_index()

stock_producto.columns = ["Código", "Stock_Min", "Stock_Promedio", "Stock_Max", 
                          "Stock_Std", "Num_Registros", "Bodega_Principal"]

stock_producto = stock_producto.sort_values("Stock_Promedio", ascending=False)

print(f"  Productos analizados: {len(stock_producto):,}")
print(f"\n  TOP 10 productos por Stock_Promedio:")
for i, row in stock_producto.head(10).iterrows():
    print(f"    {row['Código']:12s} - Stock: min={row['Stock_Min']:>8.0f}, " +
          f"prom={row['Stock_Promedio']:>8.0f}, max={row['Stock_Max']:>8.0f}")

stock_producto.to_csv(os.path.join(OUTPUT_DIR, "02_STOCK_POR_PRODUCTO.csv"), 
                      sep=";", index=False, encoding="latin-1")
print(f"\n  ✓ Guardado: 02_STOCK_POR_PRODUCTO.csv")

# ============================================================================
# PASO 5: ANÁLISIS DE ROTACIÓN
# ============================================================================
print("\n[5] Calculando rotación de inventario...")

# Rotación = Salida_Total / Stock_Promedio
rotacion = ventas_producto[["Código", "Salida_Total", "Descripción"]].copy()
rotacion = rotacion.merge(stock_producto[["Código", "Stock_Promedio"]], on="Código", how="left")

rotacion["Rotacion"] = rotacion["Salida_Total"] / rotacion["Stock_Promedio"].replace(0, 1)
rotacion = rotacion.sort_values("Rotacion", ascending=False)

print(f"  TOP 10 productos por Rotación:")
for i, row in rotacion.head(10).iterrows():
    print(f"    {row['Código']:12s} - Rotación: {row['Rotacion']:>8.2f}x")

rotacion.to_csv(os.path.join(OUTPUT_DIR, "03_ROTACION_INVENTARIO.csv"), 
                sep=";", index=False, encoding="latin-1")
print(f"\n  ✓ Guardado: 03_ROTACION_INVENTARIO.csv")

# ============================================================================
# PASO 6: ANÁLISIS POR BODEGA
# ============================================================================
print("\n[6] Analizando distribución por bodega...")

bodega_stats = df_ventas.groupby("Bodega").agg({
    "Salida": ["count", "sum"],
    "Código": "nunique"
}).reset_index()
bodega_stats.columns = ["Bodega", "Num_Transacciones", "Salida_Total", "Productos_Unicos"]
bodega_stats = bodega_stats.sort_values("Salida_Total", ascending=False)

print(f"  Distribución de ventas por bodega:")
for i, row in bodega_stats.iterrows():
    pct = 100 * row["Salida_Total"] / df_ventas["Salida"].sum()
    print(f"    {row['Bodega']:30s} - {row['Salida_Total']:>10,.0f} ({pct:>5.1f}%)")

bodega_stats.to_csv(os.path.join(OUTPUT_DIR, "04_VENTAS_POR_BODEGA.csv"), 
                    sep=";", index=False, encoding="latin-1")
print(f"\n  ✓ Guardado: 04_VENTAS_POR_BODEGA.csv")

# ============================================================================
# PASO 7: ANÁLISIS POR CANAL DE VENTA
# ============================================================================
print("\n[7] Analizando distribución por canal de venta...")

canal_stats = df_ventas.groupby("Canal_Venta").agg({
    "Salida": ["count", "sum"],
    "Código": "nunique"
}).reset_index()
canal_stats.columns = ["Canal_Venta", "Num_Transacciones", "Salida_Total", "Productos_Unicos"]
canal_stats = canal_stats.sort_values("Salida_Total", ascending=False)

print(f"  Distribución de ventas por canal:")
for i, row in canal_stats.iterrows():
    pct = 100 * row["Salida_Total"] / df_ventas["Salida"].sum()
    print(f"    {row['Canal_Venta']:20s} - {row['Salida_Total']:>10,.0f} ({pct:>5.1f}%)")

canal_stats.to_csv(os.path.join(OUTPUT_DIR, "05_VENTAS_POR_CANAL.csv"), 
                   sep=";", index=False, encoding="latin-1")
print(f"\n  ✓ Guardado: 05_VENTAS_POR_CANAL.csv")

# ============================================================================
# PASO 8: TENDENCIAS TEMPORALES
# ============================================================================
print("\n[8] Analizando tendencias temporales...")

df_ventas_valid = df_ventas[df_ventas["Fecha"].notna()].copy()
df_ventas_valid["Año"] = df_ventas_valid["Fecha"].dt.year
df_ventas_valid["Mes"] = df_ventas_valid["Fecha"].dt.month
df_ventas_valid["Semana"] = df_ventas_valid["Fecha"].dt.isocalendar().week

tendencia_mes = df_ventas_valid.groupby(["Año", "Mes"]).agg({
    "Salida": ["count", "sum"]
}).reset_index()
tendencia_mes.columns = ["Año", "Mes", "Num_Transacciones", "Salida_Total"]
tendencia_mes["Año_Mes"] = tendencia_mes["Año"].astype(str) + "-" + tendencia_mes["Mes"].astype(str).str.zfill(2)

print(f"  Tendencia mensual (últimos 6 meses):")
for i, row in tendencia_mes.tail(6).iterrows():
    print(f"    {row['Año_Mes']} - Salida: {row['Salida_Total']:>10,.0f} | Transacciones: {row['Num_Transacciones']:>5.0f}")

tendencia_mes.to_csv(os.path.join(OUTPUT_DIR, "06_TENDENCIA_MENSUAL.csv"), 
                     sep=";", index=False, encoding="latin-1")
print(f"\n  ✓ Guardado: 06_TENDENCIA_MENSUAL.csv")

# Vista semanal consolidada: ventas, producción y stock
df_semana = df[df["Fecha"].notna()].copy()
df_semana["Semana_Inicio"] = df_semana["Fecha"].dt.to_period("W").dt.start_time

ventas_sem = (df_semana.groupby("Semana_Inicio", as_index=False)["Salida"]
              .sum()
              .rename(columns={"Salida": "Ventas_Semanales"}))

produccion_sem = (df_semana.groupby("Semana_Inicio", as_index=False)["Entrada"]
                  .sum()
                  .rename(columns={"Entrada": "Produccion_Semanal"}))

# Stock semanal como cierre: último saldo por producto en cada semana y luego suma total
stock_cierre_producto = (df_semana.sort_values(["Código", "Fecha"])
                         .groupby(["Semana_Inicio", "Código"], as_index=False)
                         .tail(1))
stock_sem = (stock_cierre_producto.groupby("Semana_Inicio", as_index=False)["Saldo"]
             .sum()
             .rename(columns={"Saldo": "Stock_Cierre_Semanal"}))

serie_semanal = ventas_sem.merge(produccion_sem, on="Semana_Inicio", how="outer")
serie_semanal = serie_semanal.merge(stock_sem, on="Semana_Inicio", how="outer")
serie_semanal = serie_semanal.sort_values("Semana_Inicio").fillna(0)

serie_semanal.to_csv(os.path.join(OUTPUT_DIR, "07_SERIE_SEMANAL_VENTAS_PRODUCCION_STOCK.csv"),
                     sep=";", index=False, encoding="latin-1")
print(f"  ✓ Guardado: 07_SERIE_SEMANAL_VENTAS_PRODUCCION_STOCK.csv")

# Vista semanal específica para los artículos solicitados
codigos_objetivo = ["CER 001", "CER 005", "CEO 001", "CEO 006", "CERE 002", "CER 004", "CER 008"]
codigo_normalizado = df_semana["Código"].astype(str).str.upper().str.replace("'", "", regex=False).str.strip()

series_semanales_objetivo = {}
for codigo_objetivo in codigos_objetivo:
    df_producto = df_semana[codigo_normalizado == codigo_objetivo].copy()
    if len(df_producto) == 0:
        print(f"  ! Sin datos para {codigo_objetivo}")
        continue

    df_producto = df_producto.sort_values("Fecha")
    serie_producto = (df_producto.groupby("Semana_Inicio", as_index=False)
                      .agg({
                          "Salida": "sum",
                          "Entrada": "sum",
                          "Saldo": "last"
                      })
                      .rename(columns={
                          "Salida": "Ventas_Semanales",
                          "Entrada": "Produccion_Semanal",
                          "Saldo": "Stock_Cierre_Semanal"
                      })
                      .sort_values("Semana_Inicio"))

    safe_name = codigo_objetivo.replace(" ", "")
    series_semanales_objetivo[codigo_objetivo] = serie_producto

    serie_producto.to_csv(os.path.join(OUTPUT_DIR, f"08_SERIE_SEMANAL_{safe_name}.csv"),
                          sep=";", index=False, encoding="latin-1")
    print(f"  ✓ Guardado: 08_SERIE_SEMANAL_{safe_name}.csv")

# ============================================================================
# PASO 9: GRÁFICOS
# ============================================================================
print("\n[9] Generando gráficos...")

# Gráfico 1: Pareto
fig, ax = plt.subplots(figsize=(14, 6))
top20 = ventas_producto.head(20)
ax.bar(range(len(top20)), top20["Salida_Total"], color="steelblue", alpha=0.8)
ax.set_xticks(range(len(top20)))
ax.set_xticklabels(top20["Código"], rotation=45, ha="right")
ax.set_ylabel("Salida Total (unidades)")
ax.set_title("Análisis Pareto - TOP 20 Productos (Datos Reales)")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "GRAFICO_01_PARETO_TOP20.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ GRAFICO_01_PARETO_TOP20.png")

# Gráfico 2: Stock promedio vs Salida total (TOP 20)
fig, ax = plt.subplots(figsize=(14, 6))
top20_merged = ventas_producto.head(20).merge(stock_producto[["Código", "Stock_Promedio"]], on="Código")
x = np.arange(len(top20_merged))
width = 0.35
ax.bar(x - width/2, top20_merged["Salida_Total"], width, label="Salida Total", color="coral", alpha=0.8)
ax.bar(x + width/2, top20_merged["Stock_Promedio"], width, label="Stock Promedio", color="skyblue", alpha=0.8)
ax.set_xticks(x)
ax.set_xticklabels(top20_merged["Código"], rotation=45, ha="right")
ax.set_ylabel("Cantidad")
ax.set_title("Salida Total vs Stock Promedio (TOP 20 Productos)")
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "GRAFICO_02_SALIDA_VS_STOCK.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ GRAFICO_02_SALIDA_VS_STOCK.png")

# Gráfico 3: Ventas por bodega
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(bodega_stats["Bodega"], bodega_stats["Salida_Total"], color="teal", alpha=0.8)
ax.set_xlabel("Salida Total (unidades)")
ax.set_title("Distribución de Ventas por Bodega")
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "GRAFICO_03_VENTAS_BODEGA.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ GRAFICO_03_VENTAS_BODEGA.png")

# Gráfico 4: Ventas por canal
fig, ax = plt.subplots(figsize=(10, 6))
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
ax.pie(canal_stats["Salida_Total"], labels=canal_stats["Canal_Venta"], autopct="%1.1f%%", 
       colors=colors[:len(canal_stats)], startangle=90)
ax.set_title("Distribución de Ventas por Canal de Venta")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "GRAFICO_04_VENTAS_CANAL.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ GRAFICO_04_VENTAS_CANAL.png")

# Gráfico 5: Tendencia temporal
if len(tendencia_mes) > 0:
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(range(len(tendencia_mes)), tendencia_mes["Salida_Total"], marker="o", 
            linewidth=2, markersize=6, color="darkgreen")
    ax.set_xticks(range(len(tendencia_mes)))
    ax.set_xticklabels(tendencia_mes["Año_Mes"], rotation=45, ha="right")
    ax.set_ylabel("Salida Total (unidades)")
    ax.set_title("Tendencia de Ventas Mensuales")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "GRAFICO_05_TENDENCIA_TEMPORAL.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ GRAFICO_05_TENDENCIA_TEMPORAL.png")

# Gráfico 6: Rotación TOP 10
fig, ax = plt.subplots(figsize=(12, 6))
top10_rotacion = rotacion.head(10)
ax.barh(top10_rotacion["Código"], top10_rotacion["Rotacion"], color="purple", alpha=0.7)
ax.set_xlabel("Rotación (Salida / Stock Promedio)")
ax.set_title("TOP 10 Productos por Rotación de Inventario")
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "GRAFICO_06_ROTACION_TOP10.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ GRAFICO_06_ROTACION_TOP10.png")

# Gráfico 7: Vista semanal consolidada (ventas, producción, stock)
if len(serie_semanal) > 0:
    fig, ax1 = plt.subplots(figsize=(15, 7))

    ax1.plot(serie_semanal["Semana_Inicio"], serie_semanal["Ventas_Semanales"],
             color="tab:blue", linewidth=2, label="Ventas semanales")
    ax1.plot(serie_semanal["Semana_Inicio"], serie_semanal["Produccion_Semanal"],
             color="tab:orange", linewidth=2, label="Producción semanal")
    ax1.set_ylabel("Ventas / Producción (unidades)")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(serie_semanal["Semana_Inicio"], serie_semanal["Stock_Cierre_Semanal"],
             color="tab:green", linewidth=2, linestyle="--", label="Stock cierre semanal")
    ax2.set_ylabel("Stock cierre (unidades)")

    ax1.set_title("Vista semanal: Ventas, Producción y Stock de cierre")

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "GRAFICO_07_SEMANAL_VENTAS_PRODUCCION_STOCK.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ GRAFICO_07_SEMANAL_VENTAS_PRODUCCION_STOCK.png")

# Gráfico 8: Vistas semanales por artículo solicitado (ventas, producción, stock)
for codigo_objetivo, serie_producto in series_semanales_objetivo.items():
    if len(serie_producto) == 0:
        continue

    safe_name = codigo_objetivo.replace(" ", "")
    fig, ax1 = plt.subplots(figsize=(15, 7))

    ax1.plot(serie_producto["Semana_Inicio"], serie_producto["Ventas_Semanales"],
             color="tab:blue", linewidth=2, label="Ventas semanales")
    ax1.plot(serie_producto["Semana_Inicio"], serie_producto["Produccion_Semanal"],
             color="tab:orange", linewidth=2, label="Producción semanal")
    ax1.set_ylabel("Ventas / Producción (unidades)")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(serie_producto["Semana_Inicio"], serie_producto["Stock_Cierre_Semanal"],
             color="tab:green", linewidth=2, linestyle="--", label="Stock cierre semanal")
    ax2.set_ylabel("Stock cierre (unidades)")

    ax1.set_title(f"{codigo_objetivo} - Vista semanal: Ventas, Producción y Stock de cierre")

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, f"GRAFICO_08_SEMANAL_{safe_name}.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ GRAFICO_08_SEMANAL_{safe_name}.png")

# ============================================================================
# PASO 10: RESUMEN
# ============================================================================
print("\n[10] Generando resumen...")

resumen = {
    "timestamp": datetime.now().isoformat(),
    "registros_totales": int(len(df)),
    "registros_venta": int(len(df_ventas)),
    "registros_produccion": int(len(df_produccion)),
    "rango_fechas": f"{df['Fecha'].min()} a {df['Fecha'].max()}",
    "semanas_analizadas": int(len(serie_semanal)),
    "semanas_analizadas_codigos_objetivo": {
        codigo: int(len(serie)) for codigo, serie in series_semanales_objetivo.items()
    },
    "productos_totales": int(df["Código"].nunique()),
    "productos_con_ventas": int(len(ventas_producto)),
    "productos_pareto_80pct": int(pareto_80),
    "bodegas": bodega_stats["Bodega"].tolist(),
    "canales_venta": canal_stats["Canal_Venta"].tolist(),
    "top_5_productos": ventas_producto.head(5)[["Código", "Salida_Total"]].to_dict("records"),
    "observaciones": {
        "concentracion_ventas": f"{pareto_80} productos ({pareto_80/len(ventas_producto)*100:.1f}%) generan el 80% de ventas",
        "bodega_principal": bodega_stats.iloc[0]["Bodega"] if len(bodega_stats) > 0 else "N/A",
        "canal_principal": canal_stats.iloc[0]["Canal_Venta"] if len(canal_stats) > 0 else "N/A"
    }
}

with open(os.path.join(OUTPUT_DIR, "RESUMEN_ANALISIS.json"), "w", encoding="utf-8") as f:
    json.dump(resumen, f, indent=2, ensure_ascii=False)

print(f"  ✓ RESUMEN_ANALISIS.json")

print("\n" + "="*80)
print("✓ ANÁLISIS COMPLETADO")
print("="*80)
print(f"\nSalidas en: {OUTPUT_DIR}")
print("  - Archivos CSV: 01_*.csv a 08_*.csv (incluye vistas semanales por artículo)")
print("  - Gráficos: GRAFICO_*.png")
print("  - Resumen: RESUMEN_ANALISIS.json")
print("\n")
