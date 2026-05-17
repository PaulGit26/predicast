"""
Análisis acumulado de costo de planchas por producto.
Compara:
- Costo total de planchas usadas en PRODUCCIÓN
- Costo total de planchas usadas en VENTAS
- Diferencia (dinero que se gastó pero no se vendió)

Salidas:
- CSV: 14_COSTO_PLANCHA_ACUMULADO_POR_PRODUCTO.csv
- Gráfico: GRAFICO_14_COSTO_PLANCHA_ACUMULADO.png
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

OUTDIR = os.path.dirname(__file__)

codes = {
    'CER001': {'sheets_per_unit': 0.007, 'price': 129.95},
    'CER005': {'sheets_per_unit': 0.007, 'price': 129.95},
    'CER004': {'sheets_per_unit': 0.007, 'price': 201.63},
    'CERE002': {'sheets_per_unit': 0.007, 'price': 201.63},
    'CEO001': {'sheets_per_unit': 0.009, 'price': 129.95},
    'CEO006': {'sheets_per_unit': 0.009, 'price': 129.95},
    'CER008': {'sheets_per_unit': 0.009, 'price': 201.63},
}

summary_rows = []

for code, meta in codes.items():
    infile = os.path.join(OUTDIR, f'08_SERIE_SEMANAL_{code}.csv')
    if not os.path.exists(infile):
        print(f"Archivo faltante: {infile}")
        continue
    
    df = pd.read_csv(infile, sep=';', encoding='latin-1')
    df['Ventas_Semanales'] = pd.to_numeric(df.get('Ventas_Semanales', 0), errors='coerce').fillna(0)
    df['Produccion_Semanal'] = pd.to_numeric(df.get('Produccion_Semanal', 0), errors='coerce').fillna(0)
    
    spu = meta['sheets_per_unit']
    price = meta['price']
    
    # Acumulados del período histórico
    total_produccion = df['Produccion_Semanal'].sum()
    total_ventas = df['Ventas_Semanales'].sum()
    
    # Planchas
    planchas_produccion = total_produccion * spu
    planchas_ventas = total_ventas * spu
    planchas_gap = planchas_produccion - planchas_ventas
    
    # Costos
    costo_produccion = planchas_produccion * price
    costo_ventas = planchas_ventas * price
    ahorro_potencial = costo_produccion - costo_ventas
    
    # Eficiencia
    eficiencia_pct = (total_ventas / total_produccion * 100) if total_produccion > 0 else 0
    
    summary_rows.append({
        'Código': code,
        'Producción_Total': int(total_produccion),
        'Ventas_Total': int(total_ventas),
        'Planchas_Producción': round(planchas_produccion, 2),
        'Planchas_Ventas': round(planchas_ventas, 2),
        'Planchas_Gap': round(planchas_gap, 2),
        'Costo_Producción_S/': round(costo_produccion, 2),
        'Costo_Ventas_S/': round(costo_ventas, 2),
        'Ahorro_Potencial_S/': round(ahorro_potencial, 2),
        'Eficiencia_%': round(eficiencia_pct, 1),
    })

# Exportar resumen
summary_df = pd.DataFrame(summary_rows)
outcsv = os.path.join(OUTDIR, '14_COSTO_PLANCHA_ACUMULADO_POR_PRODUCTO.csv')
summary_df.to_csv(outcsv, sep=';', index=False, encoding='latin-1')
print(f"Guardado: {outcsv}\n")

# Mostrar tabla en consola
print(summary_df.to_string(index=False))

# Gráfico comparativo: Costo Producción vs Costo Ventas
fig, ax = plt.subplots(figsize=(14, 7))
x = np.arange(len(summary_df))
width = 0.35

bars1 = ax.bar(x - width/2, summary_df['Costo_Producción_S/'], width, label='Costo Producción', color='tab:orange', alpha=0.8)
bars2 = ax.bar(x + width/2, summary_df['Costo_Ventas_S/'], width, label='Costo Ventas', color='tab:green', alpha=0.8)

# Línea de ahorro potencial
ax2 = ax.twinx()
ax2.plot(x, summary_df['Ahorro_Potencial_S/'], color='tab:red', marker='o', linewidth=2, markersize=8, label='Ahorro Potencial')
ax2.set_ylabel('Ahorro Potencial S/', color='tab:red')

ax.set_xlabel('Producto')
ax.set_ylabel('Costo S/')
ax.set_title('Costo acumulado de planchas: Producción vs Ventas (período histórico)')
ax.set_xticks(x)
ax.set_xticklabels(summary_df['Código'], rotation=45, ha='right')
ax.legend(loc='upper left')
ax2.legend(loc='upper right')
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
outpng = os.path.join(OUTDIR, 'GRAFICO_14_COSTO_PLANCHA_ACUMULADO.png')
plt.savefig(outpng, dpi=150, bbox_inches='tight')
plt.close()
print(f"\nGuardado: {outpng}")

# Totales globales
print(f"\n--- TOTALES GLOBALES (7 PRODUCTOS) ---")
total_costo_prod = summary_df['Costo_Producción_S/'].sum()
total_costo_ventas = summary_df['Costo_Ventas_S/'].sum()
total_ahorro = summary_df['Ahorro_Potencial_S/'].sum()
print(f"Costo total producción: S/ {total_costo_prod:.2f}")
print(f"Costo total ventas: S/ {total_costo_ventas:.2f}")
print(f"Ahorro potencial total: S/ {total_ahorro:.2f}")
print(f"Eficiencia promedio: {summary_df['Eficiencia_%'].mean():.1f}%")

print('\nProceso completado.')
