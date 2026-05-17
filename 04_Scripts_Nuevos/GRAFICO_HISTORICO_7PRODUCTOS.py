"""
Script para visualizar histórico semanal de los 7 productos Pareto
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# Cargar datos históricos
DATA_DIR = r'd:\Desktop\Predicast'
hist_file = os.path.join(DATA_DIR, '01_Datos', 'datos_semanales_long.csv')

df_hist = pd.read_csv(hist_file, encoding='utf-8')

# 7 productos Pareto objetivo
productos_pareto = ['CEO 001', 'CEO 006', 'CER 001', 'CER 004', 'CER 005', 'CER 008', 'CERE 002']

# Verificar cuáles existen
print(f"\nProductos disponibles en histórico: {df_hist['Producto_codigo'].unique()[:10]}")
print(f"¿CEO 001 existe? {'CEO 001' in df_hist['Producto_codigo'].values}")
print(f"¿CP_01 existe? {'CP_01' in df_hist['Producto_codigo'].values}")

# Filtrar productos disponibles más vendidos
# Si no están los Pareto, mostrar TOP 7 por volumen
if not any(p in df_hist['Producto_codigo'].values for p in productos_pareto):
    print("\n⚠️ Productos Pareto NO existen en histórico.")
    print("Mostrando TOP 7 productos por volumen total...\n")
    
    # Agrupar por producto y calcular volumen total
    df_volumen = df_hist.groupby('Producto_codigo')['Ventas_Semana'].sum().sort_values(ascending=False)
    productos_top7 = df_volumen.head(7).index.tolist()
    print(f"TOP 7 productos: {productos_top7}\n")
else:
    productos_top7 = [p for p in productos_pareto if p in df_hist['Producto_codigo'].values]
    print(f"\n✓ Productos Pareto encontrados: {len(productos_top7)}")

# Filtrar datos para estos productos
df_plot = df_hist[df_hist['Producto_codigo'].isin(productos_top7)].copy()

# Convertir AñoSemana a fecha
def parse_año_semana(año_semana):
    # Formato: "2021-W02"
    año, semana_str = año_semana.split('-W')
    semana = int(semana_str)
    # Usar la primera fecha de cada semana (lunes)
    fecha = pd.to_datetime(f"{año}-W{semana:02d}-1", format="%G-W%V-%u")
    return fecha

df_plot['Fecha'] = df_plot['AñoSemana'].apply(parse_año_semana)
df_plot = df_plot.sort_values('Fecha')

# ============================================================
# GRAFICO 1: Series individuales en subplots
# ============================================================

fig_subplots = make_subplots(
    rows=4, cols=2,
    subplot_titles=tuple(productos_top7 + [''] if len(productos_top7) < 8 else productos_top7[:8]),
    specs=[[{"secondary_y": False}] * 2 for _ in range(4)]
)

colors = px.colors.qualitative.Plotly

for idx, producto in enumerate(productos_top7):
    row = idx // 2 + 1
    col = idx % 2 + 1
    
    df_prod = df_plot[df_plot['Producto_codigo'] == producto]
    
    fig_subplots.add_trace(
        go.Scatter(
            x=df_prod['Fecha'],
            y=df_prod['Ventas_Semana'],
            name=producto,
            line=dict(color=colors[idx % len(colors)], width=2),
            fill='tozeroy',
            hovertemplate='<b>%{x|%Y-W%V}</b><br>Demanda: %{y:,.0f} u<extra></extra>'
        ),
        row=row, col=col
    )

fig_subplots.update_layout(
    title="Histórico Semanal - 7 Productos Pareto",
    height=1200,
    showlegend=False,
    hovermode='x unified'
)

fig_subplots.write_html(os.path.join(DATA_DIR, 'grafico_historico_subplots.html'))
print("✓ Gráfico de subplots guardado: grafico_historico_subplots.html")

# ============================================================
# GRAFICO 2: Líneas superpuestas (comparativa directa)
# ============================================================

fig_overlay = go.Figure()

for idx, producto in enumerate(productos_top7):
    df_prod = df_plot[df_plot['Producto_codigo'] == producto]
    
    fig_overlay.add_trace(go.Scatter(
        x=df_prod['Fecha'],
        y=df_prod['Ventas_Semana'],
        name=producto,
        mode='lines+markers',
        line=dict(width=2),
        hovertemplate='<b>%{fullData.name}</b><br>%{x|%Y-W%V}<br>Demanda: %{y:,.0f} u<extra></extra>'
    ))

fig_overlay.update_layout(
    title="Histórico Semanal - Comparativa de 7 Productos",
    xaxis_title="Semana",
    yaxis_title="Demanda (unidades)",
    hovermode='x unified',
    height=600,
    template='plotly_white'
)

fig_overlay.write_html(os.path.join(DATA_DIR, 'grafico_historico_overlay.html'))
print("✓ Gráfico de superposición guardado: grafico_historico_overlay.html")

# ============================================================
# GRAFICO 3: Área apilada (volumen total)
# ============================================================

df_pivot = df_plot.pivot_table(
    index='Fecha',
    columns='Producto_codigo',
    values='Ventas_Semana',
    aggfunc='sum'
)

fig_area = go.Figure()

for col in df_pivot.columns:
    fig_area.add_trace(go.Scatter(
        x=df_pivot.index,
        y=df_pivot[col],
        mode='lines',
        name=col,
        stackgroup='one',
        fillcolor=colors[list(df_pivot.columns).index(col) % len(colors)],
        hovertemplate='<b>%{fullData.name}</b><br>%{x|%Y-W%V}<br>Demanda: %{y:,.0f} u<extra></extra>'
    ))

fig_area.update_layout(
    title="Histórico Semanal - Volumen Acumulado",
    xaxis_title="Semana",
    yaxis_title="Demanda Total (unidades)",
    hovermode='x unified',
    height=600,
    template='plotly_white'
)

fig_area.write_html(os.path.join(DATA_DIR, 'grafico_historico_area.html'))
print("✓ Gráfico de área apilada guardado: grafico_historico_area.html")

# ============================================================
# ESTADISTICAS
# ============================================================

print("\n📊 ESTADÍSTICAS HISTÓRICO (por producto):\n")

for producto in productos_top7:
    df_prod = df_plot[df_plot['Producto_codigo'] == producto]
    print(f"{producto}:")
    print(f"  Semanas: {len(df_prod)}")
    media = df_prod['Ventas_Semana'].mean()
    std = df_prod['Ventas_Semana'].std()
    min_v = df_prod['Ventas_Semana'].min()
    max_v = df_prod['Ventas_Semana'].max()
    cv = (std / media * 100)
    print(f"  Media: {media:,.0f} u/semana")
    print(f"  Std: {std:,.0f} u")
    print(f"  Min: {min_v:,.0f} u")
    print(f"  Max: {max_v:,.0f} u")
    print(f"  CV: {cv:.1f}%")
    print()

print(f"✅ 3 gráficos HTML generados en: {DATA_DIR}\n")
print("Abre en navegador:")
print("  1. grafico_historico_subplots.html  (7 gráficos separados)")
print("  2. grafico_historico_overlay.html   (líneas superpuestas)")
print("  3. grafico_historico_area.html      (área acumulada)")
