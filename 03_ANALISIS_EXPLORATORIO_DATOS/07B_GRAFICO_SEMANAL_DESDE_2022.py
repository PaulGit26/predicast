"""
Genera una versión adicional del gráfico 07 desde 2022 en adelante.
Lee la serie semanal consolidada ya calculada y exporta:
- 07B_SERIE_SEMANAL_VENTAS_PRODUCCION_STOCK_DESDE_2022.csv
- GRAFICO_07B_SEMANAL_VENTAS_PRODUCCION_STOCK_DESDE_2022.png
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

INPUT_FILE = r"d:\Desktop\Predicast\03_ANALISIS_EXPLORATORIO_DATOS\07_SERIE_SEMANAL_VENTAS_PRODUCCION_STOCK.csv"
OUTPUT_DIR = r"d:\Desktop\Predicast\03_ANALISIS_EXPLORATORIO_DATOS"
CSV_OUT = os.path.join(OUTPUT_DIR, "07B_SERIE_SEMANAL_VENTAS_PRODUCCION_STOCK_DESDE_2022.csv")
PNG_OUT = os.path.join(OUTPUT_DIR, "GRAFICO_07B_SEMANAL_VENTAS_PRODUCCION_STOCK_DESDE_2022.png")

os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams["figure.figsize"] = (15, 7)
sns.set_style("whitegrid")


def main():
    df = pd.read_csv(INPUT_FILE, sep=";", encoding="latin-1")
    df["Semana_Inicio"] = pd.to_datetime(df["Semana_Inicio"], errors="coerce")
    df = df[df["Semana_Inicio"] >= pd.Timestamp("2022-01-01")].copy()
    df = df.sort_values("Semana_Inicio")

    df.to_csv(CSV_OUT, sep=";", index=False, encoding="latin-1")

    if df.empty:
        raise ValueError("No hay datos desde 2022 para generar el gráfico.")

    fig, ax1 = plt.subplots(figsize=(15, 7))

    ax1.plot(df["Semana_Inicio"], df["Ventas_Semanales"],
             color="tab:blue", linewidth=2, label="Ventas semanales")
    ax1.plot(df["Semana_Inicio"], df["Produccion_Semanal"],
             color="tab:orange", linewidth=2, label="Producción semanal")
    ax1.set_ylabel("Ventas / Producción (unidades)")
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(df["Semana_Inicio"], df["Stock_Cierre_Semanal"],
             color="tab:green", linewidth=2, linestyle="--", label="Stock cierre semanal")
    ax2.set_ylabel("Stock cierre (unidades)")

    ax1.set_title("Vista semanal desde 2022: Ventas, Producción y Stock de cierre")

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    plt.tight_layout()
    plt.savefig(PNG_OUT, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"CSV generado: {CSV_OUT}")
    print(f"Gráfico generado: {PNG_OUT}")
    print(f"Semanas incluidas desde 2022: {len(df)}")


if __name__ == "__main__":
    main()
