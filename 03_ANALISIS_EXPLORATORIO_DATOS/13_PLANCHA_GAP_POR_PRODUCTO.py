"""
Genera comparativa semanal (planchas por ventas vs planchas por producción)
para productos seleccionados. Salidas:
- CSV: 13_PLANCHA_GAP_{CODE}.csv
- Gráfico: GRAFICO_13_PLANCHA_GAP_{CODE}.png

Uso: python 13_PLANCHA_GAP_POR_PRODUCTO.py
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

OUTDIR = os.path.dirname(__file__)

codes = {
    'CER001': {'sheets_per_unit':0.007},
    'CER005': {'sheets_per_unit':0.007},
    'CER004': {'sheets_per_unit':0.007},
    'CERE002':{'sheets_per_unit':0.007},
    'CEO001': {'sheets_per_unit':0.009},
    'CEO006': {'sheets_per_unit':0.009},
    'CER008': {'sheets_per_unit':0.009},
}

for code, meta in codes.items():
    infile = os.path.join(OUTDIR, f'08_SERIE_SEMANAL_{code}.csv')
    if not os.path.exists(infile):
        print(f"Archivo faltante: {infile}")
        continue
    df = pd.read_csv(infile, sep=';', encoding='latin-1')
    if 'Semana_Inicio' in df.columns:
        df['Semana_Inicio'] = pd.to_datetime(df['Semana_Inicio'], errors='coerce')
    # ensure columns exist
    df['Ventas_Semanales'] = pd.to_numeric(df.get('Ventas_Semanales', 0), errors='coerce').fillna(0)
    df['Produccion_Semanal'] = pd.to_numeric(df.get('Produccion_Semanal', 0), errors='coerce').fillna(0)

    spu = meta['sheets_per_unit']
    df['Planchas_Ventas'] = df['Ventas_Semanales'] * spu
    df['Planchas_Produccion'] = df['Produccion_Semanal'] * spu
    df['Planchas_Gap'] = df['Planchas_Produccion'] - df['Planchas_Ventas']

    outcsv = os.path.join(OUTDIR, f'13_PLANCHA_GAP_{code}.csv')
    df[['Semana_Inicio','Ventas_Semanales','Produccion_Semanal','Planchas_Ventas','Planchas_Produccion','Planchas_Gap']].to_csv(outcsv, sep=';', index=False, encoding='latin-1')
    print(f"Guardado: {outcsv}")

    # plot two lines
    plt.figure(figsize=(12,6))
    plt.plot(df['Semana_Inicio'], df['Planchas_Ventas'], label='Planchas por Ventas', color='tab:blue')
    plt.plot(df['Semana_Inicio'], df['Planchas_Produccion'], label='Planchas por Producción', color='tab:orange')
    plt.fill_between(df['Semana_Inicio'], df['Planchas_Ventas'], df['Planchas_Produccion'], 
                     where=(df['Planchas_Produccion']>=df['Planchas_Ventas']), interpolate=True, color='tab:orange', alpha=0.12)
    plt.title(f'Planchas: Ventas vs Producción - {code}')
    plt.xlabel('Semana')
    plt.ylabel('Planchas (unidades)')
    plt.legend()
    plt.tight_layout()
    outpng = os.path.join(OUTDIR, f'GRAFICO_13_PLANCHA_GAP_{code}.png')
    plt.savefig(outpng, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Guardado: {outpng}")

print('Proceso completado.')