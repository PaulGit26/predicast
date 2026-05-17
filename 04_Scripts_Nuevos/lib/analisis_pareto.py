"""
Wrapper para el análisis Pareto. Exporta `run_analisis_pareto(output_dir, datos_top20_path=None)`
"""
import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def run_analisis_pareto(output_dir: str, datos_top20_path: str = None):
    OUTPUT_DIR = output_dir
    if datos_top20_path is None:
        datos_top20_path = os.path.join(OUTPUT_DIR, "DATOS_TOP20_VENTAS.csv")

    df = pd.read_csv(datos_top20_path, sep=";", encoding="latin-1")
    df["Salida"] = pd.to_numeric(df["Salida"], errors="coerce").fillna(0)

    vendas_por_producto = df.groupby("Código")["Salida"].sum().sort_values(ascending=False)

    if len(vendas_por_producto) == 0 or vendas_por_producto.sum() == 0:
        productos_80 = 0
        productos_90 = 0
        cumulative_pct = pd.Series(dtype=float)
    else:
        cumulative_pct = (vendas_por_producto.cumsum() / vendas_por_producto.sum() * 100)
        productos_80 = max(1, int((cumulative_pct <= 80).sum()))
        productos_90 = max(1, int((cumulative_pct <= 90).sum()))

    productos_criticos = vendas_por_producto.head(productos_80)

    # Gráfico Pareto
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(range(len(vendas_por_producto)), vendas_por_producto.values,
           color=['#2E86AB' if i < productos_80 else '#A23B72' for i in range(len(vendas_por_producto))],
           edgecolor='black', alpha=0.7, label='Productos')

    ax2 = ax.twinx()
    cumulative_pct = (vendas_por_producto.cumsum() / vendas_por_producto.sum()) * 100
    ax2.plot(range(len(cumulative_pct)), cumulative_pct.values, 'o-', color='#F18F01', linewidth=2, markersize=6, label='% Acumulado')
    ax2.axhline(80, color='red', linestyle='--', linewidth=2, label='Umbral 80%')
    ax2.axvline(productos_80-0.5, color='red', linestyle='--', linewidth=2, alpha=0.5)
    ax2.set_ylim([0, 105])
    ax2.set_ylabel('% Acumulado de Ventas', fontsize=11, fontweight='bold')

    ax.set_title('ANÁLISIS PARETO - TOP 20 Productos', fontsize=12, fontweight='bold')
    ax.set_xlabel('Productos (Ranking)', fontsize=11)
    ax.set_ylabel('Salida Total (unidades)', fontsize=11)
    ax.grid(alpha=0.3)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)

    plt.tight_layout()
    graf_path = os.path.join(OUTPUT_DIR, "05_PARETO_ANALISIS.png")
    plt.savefig(graf_path, dpi=300, bbox_inches="tight")

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

    return {
        'grafico': graf_path,
        'reporte': os.path.join(OUTPUT_DIR, "PARETO_RESULTADO.json"),
        'productos_criticos': pareto_result['productos_seleccionados']
    }
