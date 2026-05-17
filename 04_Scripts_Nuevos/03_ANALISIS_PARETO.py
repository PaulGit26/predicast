"""
ANÁLISIS PARETO - DEFINIR PRODUCTOS A ANALIZAR
Identifica cuántos productos generan el 80/20 de impacto
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json

OUTPUT_DIR = r"d:\Desktop\Predicast\04_Scripts_Nuevos\EDA_Outputs"
DATOS_TOP20 = os.path.join(OUTPUT_DIR, "DATOS_TOP20_VENTAS.csv")

print("\n" + "="*80)
print("ANÁLISIS PARETO - SELECCIÓN DE PRODUCTOS CRÍTICOS")
print("="*80)

# Cargar datos de TOP 20
df = pd.read_csv(DATOS_TOP20, sep=";", encoding="latin-1")
df["Salida"] = pd.to_numeric(df["Salida"], errors="coerce").fillna(0)

# Agregar por producto
vendas_por_producto = df.groupby("Código")["Salida"].sum().sort_values(ascending=False)

print(f"\n[PASO 1] TOTAL PRODUCTOS EN TOP 20: {len(vendas_por_producto)}")
print(f"  Salida Total: {vendas_por_producto.sum():,.0f} unidades")

# ============================================================================
# CÁLCULO PARETO
# ============================================================================

cumulative = vendas_por_producto.cumsum()
cumulative_pct = (cumulative / vendas_por_producto.sum()) * 100

# Buscar thresholds
productos_80 = (cumulative_pct <= 80).sum()
productos_90 = (cumulative_pct <= 90).sum()

print(f"\n[PARETO 80/20]")
print(f"  Productos para 80%: {productos_80} ({productos_80/len(vendas_por_producto)*100:.1f}% del total)")
print(f"  Productos para 90%: {productos_90} ({productos_90/len(vendas_por_producto)*100:.1f}% del total)")

# Mostrar detalles
print(f"\n  [DETALLE - PRODUCTOS CRITICOS (80%)]")
productos_criticos = vendas_por_producto.head(productos_80)
for i, (prod, salida) in enumerate(productos_criticos.items(), 1):
    pct = (salida / vendas_por_producto.sum()) * 100
    print(f"  {i:2d}. {prod:12s} : {salida:>11,.0f} ({pct:5.1f}%)")

print(f"\n  → RECOMENDACIÓN: ANALIZAR LOS {productos_80} PRODUCTOS CRÍTICOS")
print(f"     (Representan el 80% del impacto con solo el {productos_80/len(vendas_por_producto)*100:.1f}% de la gama)")

# ============================================================================
# VISUALIZACIÓN PARETO
# ============================================================================

fig, ax = plt.subplots(figsize=(14, 6))

# Barras
ax.bar(range(len(vendas_por_producto)), vendas_por_producto.values, 
       color=['#2E86AB' if i < productos_80 else '#A23B72' for i in range(len(vendas_por_producto))],
       edgecolor='black', alpha=0.7, label='Productos')

# Línea acumulada
ax2 = ax.twinx()
ax2.plot(range(len(cumulative_pct)), cumulative_pct.values, 'o-', 
         color='#F18F01', linewidth=2, markersize=6, label='% Acumulado')
ax2.axhline(80, color='red', linestyle='--', linewidth=2, label='Umbral 80%')
ax2.axvline(productos_80-0.5, color='red', linestyle='--', linewidth=2, alpha=0.5)
ax2.set_ylim([0, 105])
ax2.set_ylabel('% Acumulado de Ventas', fontsize=11, fontweight='bold')

ax.set_title('ANÁLISIS PARETO - TOP 20 Productos', fontsize=12, fontweight='bold')
ax.set_xlabel('Productos (Ranking)', fontsize=11)
ax.set_ylabel('Salida Total (unidades)', fontsize=11)
ax.grid(alpha=0.3)

# Leyenda combinada
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "05_PARETO_ANALISIS.png"), dpi=300, bbox_inches="tight")
print(f"\n  ✓ Gráfico Pareto guardado: 05_PARETO_ANALISIS.png")

# ============================================================================
# EXPORTAR RESULTADO
# ============================================================================

pareto_result = {
    "total_top20": int(len(vendas_por_producto)),
    "productos_80pct": int(productos_80),
    "productos_90pct": int(productos_90),
    "cobertura_80pct": f"{productos_80/len(vendas_por_producto)*100:.1f}%",
    "cobertura_90pct": f"{productos_90/len(vendas_por_producto)*100:.1f}%",
    "productos_seleccionados": [str(p) for p in productos_criticos.index.tolist()],
    "salida_total_criticos": float(productos_criticos.sum()),
    "pct_ventas_totales": f"{(productos_criticos.sum()/vendas_por_producto.sum())*100:.1f}%"
}

with open(os.path.join(OUTPUT_DIR, "PARETO_RESULTADO.json"), "w", encoding="utf-8") as f:
    json.dump(pareto_result, f, indent=2, ensure_ascii=False)

print(f"  ✓ Resultado Pareto guardado: PARETO_RESULTADO.json")

print("\n" + "="*80)
print(f"✓ ESTRATEGIA SELECCIONADA: ANALIZAR {productos_80} PRODUCTOS CRÍTICOS")
print("="*80)
