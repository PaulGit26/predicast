"""
========================================================================
PREPARAR TOP 20 - LIMPIEZA Y FILTRADO
========================================================================
Script simplificado que:
1. Carga datos enriquecidos (de script 01)
2. Aplica reglas de limpieza específicas
3. Filtra a TOP 20 productos por volumen
4. Exporta DATOS_TOP20_VENTAS.csv para script 03 y 04

Entrada: 01_Datos_Nuevos/*.csv (datos enriquecidos por script 01)
Salida:  DATOS_TOP20_VENTAS.csv (limpio, TOP 20)
         TOP20_PRODUCTOS.csv (ranking)
         RESUMEN_LIMPIEZA.json (estadísticas)
========================================================================
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

OUTPUT_DIR = r"d:\Desktop\Predicast\04_Scripts_Nuevos\EDA_Outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("\n" + "="*80)
print("PREPARAR TOP 20 - LIMPIEZA Y FILTRADO")
print("="*80)

from lib.preparar_top20 import run_preparar_top20

OUTPUT_DIR = r"d:\Desktop\Predicast\04_Scripts_Nuevos\EDA_Outputs"
DATA_DIR = r"d:\Desktop\Predicast\01_Datos_Nuevos"

if __name__ == "__main__":
    print("Running preparar_top20 wrapper...")
    res = run_preparar_top20(DATA_DIR, OUTPUT_DIR)
    print("Result:", res)

# ============================================================================
# PASO 2: LIMPIEZA - REGLAS ESPECÍFICAS
# ============================================================================

print("\n[PASO 2] LIMPIEZA CON REGLAS ESPECÍFICAS...")

df_clean = df_raw.copy()

# Convertir a numérico
for col in ["Entrada", "Salida"]:
    df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)

# Convertir Fecha
if "Fecha" in df_clean.columns:
    df_clean["Fecha"] = pd.to_datetime(df_clean["Fecha"], errors="coerce")
    print(f"  Fechas parseadas: {df_clean['Fecha'].notna().sum()} válidas, {df_clean['Fecha'].isna().sum()} inválidas")

print(f"  Registros antes de limpieza: {len(df_clean):,}")

# REGLA 1: Excluir "Traspaso entre Almac"
mask_traspaso = df_clean["Documento"].str.contains("Traspaso entre Almac", na=False, case=False)
count_traspaso = mask_traspaso.sum()
df_clean = df_clean[~mask_traspaso]
print(f"  ✓ Excluidos traspasos: {count_traspaso:,}")

# REGLA 2: Guía de Remisión - Excluir si Entrada == Salida
print(f"\n  Procesando guías de remisión...")
mask_guia = df_clean["Documento"].str.contains("Guía de remisión - R", na=False, case=False)
df_guias = df_clean[mask_guia].copy()

count_guias_excluidas = 0
if len(df_guias) > 0:
    guias_agrupadas = df_guias.groupby("Número").agg({
        "Entrada": "sum",
        "Salida": "sum"
    }).reset_index()
    
    mask_iguales = guias_agrupadas["Entrada"] == guias_agrupadas["Salida"]
    guias_a_excluir = guias_agrupadas[mask_iguales]["Número"].tolist()
    
    count_guias_excluidas = len(df_guias[df_guias["Número"].isin(guias_a_excluir)])
    df_clean = df_clean[~((df_clean["Documento"].str.contains("Guía de remisión - R", na=False)) & 
                          (df_clean["Número"].isin(guias_a_excluir)))]
    
    print(f"  ✓ Guías excluidas: {count_guias_excluidas:,}")

print(f"  Registros después de limpieza: {len(df_clean):,}")

# ============================================================================
# PASO 3: SEGMENTAR VENTAS Y FILTRAR TOP 20
# ============================================================================

print("\n[PASO 3] SEGMENTAR VENTAS Y FILTRAR TOP 20...")

# Ventas: Salida > 0
df_ventas = df_clean[df_clean["Salida"] > 0].copy()
print(f"  Registros de venta: {len(df_ventas):,}")

# Agregación por producto
if "Código" in df_ventas.columns:
    ventas_por_producto = df_ventas.groupby("Código")["Salida"].agg(["count", "sum", "mean", "std", "min", "max"]).round(2)
    ventas_por_producto.columns = ["Transacciones", "Salida_Total", "Salida_Promedio", "Salida_Std", "Salida_Min", "Salida_Max"]
    ventas_por_producto = ventas_por_producto.sort_values("Salida_Total", ascending=False)
    
    print(f"  Productos únicos: {len(ventas_por_producto)}")
    
    # TOP 20
    top20_codigos = ventas_por_producto.head(20).index.tolist()
    top20_total = ventas_por_producto.head(20)["Salida_Total"].sum()
    total_venta = ventas_por_producto["Salida_Total"].sum()
    cuota = (top20_total / total_venta) * 100
    
    print(f"  TOP 20 productos: {cuota:.1f}% de ventas totales")
    print(f"\n  TOP 20:")
    for i, (codigo, row) in enumerate(ventas_por_producto.head(20).iterrows(), 1):
        pct = (row["Salida_Total"] / total_venta) * 100
        print(f"    {i:2d}. {codigo:12s} → {row['Salida_Total']:>12,.0f} ({pct:5.1f}%)")

# Filtrar a TOP 20
df_top20 = df_ventas[df_ventas["Código"].isin(top20_codigos)].copy()
print(f"\n  Registros TOP 20: {len(df_top20):,}")

# ============================================================================
# PASO 4: EXPORTAR
# ============================================================================

print("\n[PASO 4] EXPORTANDO RESULTADOS...")

# Datos limpios TOP 20 (para script 04)
df_top20.to_csv(os.path.join(OUTPUT_DIR, "DATOS_TOP20_VENTAS.csv"), sep=";", encoding="latin-1", index=False)
print(f"  ✓ DATOS_TOP20_VENTAS.csv ({len(df_top20):,} registros)")

# Ranking TOP 20
top20_export = ventas_por_producto.head(20).reset_index()
top20_export.to_csv(os.path.join(OUTPUT_DIR, "TOP20_PRODUCTOS.csv"), sep=";", encoding="latin-1", index=False)
print(f"  ✓ TOP20_PRODUCTOS.csv")

# Resumen de limpieza
resumen = {
    "timestamp": datetime.now().isoformat(),
    "datos_raw": int(len(df_raw)),
    "datos_limpios": int(len(df_clean)),
    "registros_excluidos_traspaso": int(count_traspaso),
    "registros_excluidos_guias": int(count_guias_excluidas),
    "registros_venta": int(len(df_ventas)),
    "productos_totales": int(len(ventas_por_producto)),
    "top20_productos": top20_codigos,
    "top20_concentracion_pct": f"{cuota:.1f}%",
    "registros_top20": int(len(df_top20))
}

with open(os.path.join(OUTPUT_DIR, "RESUMEN_LIMPIEZA.json"), "w", encoding="utf-8") as f:
    json.dump(resumen, f, indent=2, ensure_ascii=False)
print(f"  ✓ RESUMEN_LIMPIEZA.json")

print("\n" + "="*80)
print("✓ LIMPIEZA Y FILTRADO COMPLETADOS")
print("  → Datos listos para Script 03 (Pareto) y Script 04 (Features)")
print("="*80 + "\n")
