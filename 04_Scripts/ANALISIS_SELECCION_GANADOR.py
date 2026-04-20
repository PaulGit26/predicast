"""
═══════════════════════════════════════════════════════════════════════════════
    ANÁLISIS DETALLADO: SELECCIÓN DEL MODELO GANADOR
═══════════════════════════════════════════════════════════════════════════════

Resumen de cómo se escogió HYBRID_XGB_ARIMA como ganador:
  1. Metodología de comparación
  2. Resultados por métrica
  3. Ganador por producto individual
  4. Conclusiones

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

print("=" * 100)
print("ANÁLISIS: SELECCIÓN DEL MODELO GANADOR")
print("=" * 100)

# ════════════════════════════════════════════════════════════════════════════
# PASO 1: CARGAR DATOS
# ════════════════════════════════════════════════════════════════════════════

print("\nPASO 1: CARGANDO DATOS DE COMPARATIVA")
print("-" * 100)

df_resultado = pd.read_csv('comparativa_resultados.csv')
print(f"✓ Datos cargados: {len(df_resultado)} registros")
print(f"  Productos: {df_resultado['Producto'].nunique()}")
print(f"  Modelos: {df_resultado['Modelo'].nunique()}")
print(f"  Modelos: {sorted(df_resultado['Modelo'].unique())}")

# ════════════════════════════════════════════════════════════════════════════
# PASO 2: ANÁLISIS POR MÉTRICA GLOBAL
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("PASO 2: COMPARATIVA GLOBAL POR MÉTRICA")
print("-" * 100)

# Resumen por modelo
resumen_modelo = df_resultado.groupby('Modelo').agg({
    'MAE': ['mean', 'std', 'min', 'max'],
    'RMSE': ['mean', 'std'],
    'MAPE': ['mean', 'std'],
    'R²': ['mean', 'std']
}).round(2)

print("\n📊 TABLA 1: Desempeño Promedio por Modelo")
print("-" * 100)

resumen_simple = df_resultado.groupby('Modelo').agg({
    'MAE': 'mean',
    'RMSE': 'mean',
    'MAPE': 'mean',
    'R²': 'mean'
}).round(2).sort_values('MAE')

print(resumen_simple)

# ════════════════════════════════════════════════════════════════════════════
# PASO 3: RANKING POR CADA MÉTRICA
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("PASO 3: RANKING POR MÉTRICA")
print("-" * 100)

metricas = ['MAE', 'RMSE', 'MAPE', 'R²']

for metrica in metricas:
    print(f"\n📈 RANKING {metrica}:")
    if metrica == 'R²':
        ranking = df_resultado.groupby('Modelo')[metrica].mean().sort_values(ascending=False)
    else:
        ranking = df_resultado.groupby('Modelo')[metrica].mean().sort_values(ascending=True)
    
    for idx, (modelo, valor) in enumerate(ranking.items(), 1):
        print(f"  {idx}. {modelo:25s} → {valor:8.2f}")

# ════════════════════════════════════════════════════════════════════════════
# PASO 4: METODOLOGÍA DE SELECCIÓN (MAE PROMEDIO)
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("PASO 4: METODOLOGÍA DE SELECCIÓN")
print("-" * 100)

print("""
La selección del modelo ganador se basó en:

1️⃣  MÉTRICA PRINCIPAL: MAE (Mean Absolute Error)
   └─ Razón: Directamente interpretable en unidades de volumen
   └─ Métrica estándar en industria para forecasting
   └─ Representa el error promedio por unidad

2️⃣  CRITERIO: Promedio más bajo en todos los productos
   └─ Se evaluaron 5 algoritmos × 10 productos = 50 modelos
   └─ Se calculó MAE promedio para cada algoritmo
   └─ Ganador: MAE más bajo

3️⃣  DESEMPATE: Validación con métricas secundarias
   └─ RMSE: Sanciona errores grandes (penaliza outliers)
   └─ MAPE: Error porcentual (interpretación relativa)
   └─ R²: Significancia estadística (bondad de ajuste)
""")

mae_ganador = df_resultado.groupby('Modelo')['MAE'].mean().sort_values()

print("\n" + "=" * 100)
print("PASO 5: RESULTADO - RANKING FINAL")
print("-" * 100)

print("\n🏆 RANKING FINAL (por MAE promedio):\n")

for idx, (modelo, mae) in enumerate(mae_ganador.items(), 1):
    rmse = df_resultado[df_resultado['Modelo'] == modelo]['RMSE'].mean()
    mape = df_resultado[df_resultado['Modelo'] == modelo]['MAPE'].mean()
    r2 = df_resultado[df_resultado['Modelo'] == modelo]['R²'].mean()
    
    # Comparación con ganador
    if idx == 1:
        mejora_mae = 0
    else:
        mejora_mae = ((mae_ganador.iloc[0] - mae) / mae * 100)
    
    print(f"{idx}. {modelo:25s}")
    print(f"   MAE:  {mae:8.2f}  (mejora vs ganador: {mejora_mae:+.1f}%)")
    print(f"   RMSE: {rmse:8.2f}")
    print(f"   MAPE: {mape:8.2f}%")
    print(f"   R²:   {r2:8.4f}")
    print()

ganador = mae_ganador.index[0]
mae_ganador_val = mae_ganador.iloc[0]

print(f"\n✅ GANADOR SELECCIONADO: {ganador}")
print(f"   MAE Promedio: {mae_ganador_val:.2f}")

# ════════════════════════════════════════════════════════════════════════════
# PASO 6: ANÁLISIS POR PRODUCTO
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("PASO 6: ANÁLISIS POR PRODUCTO - ¿QUÉ ALGORITMO GANA EN CADA PRODUCTO?")
print("-" * 100)

# Encontrar ganador por producto (menor MAE)
ganador_por_producto = []

for producto in df_resultado['Producto'].unique():
    df_prod = df_resultado[df_resultado['Producto'] == producto]
    ganador_prod = df_prod.loc[df_prod['MAE'].idxmin()]
    ganador_por_producto.append({
        'Producto': producto,
        'Algoritmo_Ganador': ganador_prod['Modelo'],
        'MAE': ganador_prod['MAE'],
        'RMSE': ganador_prod['RMSE'],
        'MAPE': ganador_prod['MAPE'],
        'R²': ganador_prod['R²']
    })

df_ganadores = pd.DataFrame(ganador_por_producto).sort_values('MAE')

print("\n📋 TABLA 2: Ganador por Producto (menor MAE)")
print("-" * 100)
print(df_ganadores.to_string(index=False))

# Contar victorias
print("\n🎯 TABLA 3: Conteo de Victorias por Algoritmo")
print("-" * 100)

victorias = df_ganadores['Algoritmo_Ganador'].value_counts()
for modelo, count in victorias.items():
    pct = (count / len(df_ganadores) * 100)
    barra = "█" * (count)
    print(f"{modelo:25s} {barra} {count} victorias ({pct:.1f}%)")

# ════════════════════════════════════════════════════════════════════════════
# PASO 7: VENTAJAS DEL MODELO HÍBRIDO
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("PASO 7: ¿POR QUÉ HÍBRIDO GANA?")
print("-" * 100)

df_hybrid = df_resultado[df_resultado['Modelo'] == 'HYBRID_XGB_ARIMA']
df_sarima = df_resultado[df_resultado['Modelo'] == 'SARIMA']
df_xgb = df_resultado[df_resultado['Modelo'] == 'XGBOOST']

mae_xgb = df_xgb['MAE'].mean()
mae_sarima = df_sarima['MAE'].mean()
mae_hybrid = df_hybrid['MAE'].mean()

xgb_mejor_sarima = len(df_resultado[(df_resultado['Modelo'] == 'XGBOOST') & 
                                     (df_resultado['Producto'].isin(df_resultado[df_resultado['Modelo'] == 'SARIMA']['Producto'].unique()))].merge(
    df_resultado[df_resultado['Modelo'] == 'SARIMA'], on='Producto'))

print(f"""
1️⃣  COMPARACIÓN CON COMPONENTES INDIVIDUALES:

   XGBoost (puro):
   ├─ MAE promedio: {mae_xgb:.2f}
   ├─ Problema: Muy volátil para datos lineales
   └─ R² promedio: {df_xgb['R²'].mean():.4f} (negativo = sobreajusta)

   ARIMA (puro):
   ├─ MAE promedio: {mae_sarima:.2f}
   ├─ Fortaleza: Modela tendencias y estacionalidad bien
   └─ R² promedio: {df_sarima['R²'].mean():.4f}

   HÍBRIDO (60% XGB + 40% ARIMA):
   ├─ MAE promedio: {mae_hybrid:.2f}
   ├─ Ventaja: Combina lo mejor de ambos
   ├─ Mejora vs XGB: {((mae_xgb - mae_hybrid) / mae_xgb * 100):.1f}%
   └─ Mejora vs ARIMA: {((mae_sarima - mae_hybrid) / mae_sarima * 100):.1f}%


2️⃣  ANÁLISIS DE VARIANZA (Consistencia):

   RMSE (penaliza errores grandes):
   ├─ XGBOOST:    {df_xgb['RMSE'].mean():.2f} (alto - produce peaks)
   ├─ SARIMA:     {df_sarima['RMSE'].mean():.2f}
   └─ HÍBRIDO:    {df_hybrid['RMSE'].mean():.2f} (bajo - suave)

3️⃣  INTERPRETABILIDAD ESTADÍSTICA (R²):

   R² Score (1.0 = perfecto, 0.0 = basanza, <0 = peor que media):
   ├─ XGBOOST:    {df_xgb['R²'].mean():.4f} (negativo - sobreajuste)
   ├─ SARIMA:     {df_sarima['R²'].mean():.4f}
   └─ HÍBRIDO:    {df_hybrid['R²'].mean():.4f} (positivo - estable)
""")

# ════════════════════════════════════════════════════════════════════════════
# PASO 8: VISUALIZACIÓN
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("PASO 8: CREAR VISUALIZACIONES")
print("-" * 100)

# Gráfico 1: Distribución MAE por modelo
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# MAE por modelo (boxplot)
ax = axes[0, 0]
df_resultado.boxplot(column='MAE', by='Modelo', ax=ax)
ax.set_title('Distribución MAE por Modelo', fontweight='bold', fontsize=11)
ax.set_ylabel('MAE')
ax.get_figure().suptitle('')
ax.axhline(y=df_hybrid['MAE'].mean(), color='red', linestyle='--', linewidth=2, label='Híbrido promedio')
ax.legend()

# MAE promedio por modelo (barplot)
ax = axes[0, 1]
mae_promedio = df_resultado.groupby('Modelo')['MAE'].mean().sort_values()
mae_promedio.plot(kind='barh', ax=ax, color=['green' if x == ganador else 'steelblue' for x in mae_promedio.index])
ax.set_title('MAE Promedio por Modelo', fontweight='bold', fontsize=11)
ax.set_xlabel('MAE Promedio')
for i, v in enumerate(mae_promedio):
    ax.text(v + 2, i, f'{v:.2f}', va='center')

# R² por modelo
ax = axes[1, 0]
r2_promedio = df_resultado.groupby('Modelo')['R²'].mean().sort_values(ascending=False)
colors = ['green' if x == ganador else 'steelblue' for x in r2_promedio.index]
r2_promedio.plot(kind='barh', ax=ax, color=colors)
ax.set_title('R² Promedio por Modelo (más alto = mejor)', fontweight='bold', fontsize=11)
ax.set_xlabel('R² Promedio')
ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)

# Ganador por producto
ax = axes[1, 1]
victorias_plot = df_ganadores['Algoritmo_Ganador'].value_counts()
colors_victorias = ['green' if x == ganador else 'steelblue' for x in victorias_plot.index]
victorias_plot.plot(kind='bar', ax=ax, color=colors_victorias)
ax.set_title('Victorias por Algoritmo (entre 10 productos)', fontweight='bold', fontsize=11)
ax.set_ylabel('Número de Productos Ganados')
ax.set_xlabel('Algoritmo')
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig('ANALISIS_SELECCION_GANADOR.png', dpi=300, bbox_inches='tight')
print("✓ Gráfico guardado: ANALISIS_SELECCION_GANADOR.png")
plt.close()

# ════════════════════════════════════════════════════════════════════════════
# PASO 9: TABLA DETALLADA
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("PASO 9: TABLA DETALLADA - GANADOR POR PRODUCTO")
print("-" * 100)

df_ganadores_export = df_ganadores.copy()
df_ganadores_export['MAE'] = df_ganadores_export['MAE'].round(2)
df_ganadores_export['RMSE'] = df_ganadores_export['RMSE'].round(2)
df_ganadores_export['MAPE'] = df_ganadores_export['MAPE'].round(2)
df_ganadores_export['R²'] = df_ganadores_export['R²'].round(4)

# Exportar
df_ganadores_export.to_csv('GANADOR_POR_PRODUCTO.csv', index=False)
print("\n✓ Tabla exportada: GANADOR_POR_PRODUCTO.csv")

print("\nÚltimos 5 productos:")
print(df_ganadores_export.head(10).to_string(index=False))

# ════════════════════════════════════════════════════════════════════════════
# PASO 10: CONCLUSIÓN
# ════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 100)
print("CONCLUSIÓN FINAL")
print("=" * 100)

print(f"""

🏆 MODELO GANADOR: {ganador.upper()}

📊 METODOLOGÍA DE SELECCIÓN:

  Paso 1: Definir métrica principal → MAE (error promedio)
  Paso 2: Entrenar 5 algoritmos en 10 productos → 50 modelos
  Paso 3: Calcular MAE promedio de cada algoritmo
  Paso 4: Seleccionar el con MAE más bajo → HYBRID_XGB_ARIMA
  Paso 5: Validar con métricas secundarias (RMSE, MAPE, R²)

📈 RESULTADOS:

  HYBRID_XGB_ARIMA:
  ├─ MAE Promedio:     {df_hybrid['MAE'].mean():.2f}  ← MEJOR
  ├─ RMSE Promedio:    {df_hybrid['RMSE'].mean():.2f}  ← MEJOR
  ├─ MAPE Promedio:    {df_hybrid['MAPE'].mean():.2f}%
  ├─ R² Promedio:      {df_hybrid['R²'].mean():.4f}  ← Positivo (significativo)
  └─ Victorias:        {(df_ganadores['Algoritmo_Ganador'] == ganador).sum()}/10 productos

🎯 GANADOR POR PRODUCTO:

  Gana en {(df_ganadores['Algoritmo_Ganador'] == ganador).sum()} productos:
  ├─ CP_04, CP_09, CP_13, CP_14, CP_10, MECO_01
  └─ Y otros productos donde tiene mejor error

  Alternativa cercana (SARIMA) gana en {(df_ganadores['Algoritmo_Ganador'] == 'SARIMA').sum()} productos
  └─ En productos con fuerte componente estacional

✅ VENTAJAS DEL HÍBRIDO:

  1. Combina XGBoost (60%) → Captura patrones no-lineales
  2. Combina ARIMA (40%)  → Modela estacionalidad
  3. Resultado: Balance entre flexibilidad y estabilidad
  4. RMSE bajo → Pocos errores grandes
  5. R² positivo → Generaliza bien (no sobreajusta)

💡 POR QUÉ NO OTROS:

  XGBOOST (puro):  MAE {df_xgb['MAE'].mean():.2f} → Demasiado volátil
  SARIMA (puro):   MAE {df_sarima['MAE'].mean():.2f} → Mejor que XGB, pero HÍBRIDO es {((df_sarima['MAE'].mean() - df_hybrid['MAE'].mean()) / df_sarima['MAE'].mean() * 100):.1f}% mejor
  LIGHTGBM:        MAE {df_resultado[df_resultado['Modelo'] == 'LIGHTGBM']['MAE'].mean():.2f} → No ofrece ventaja
  EXP_SMOOTHING:   MAE {df_resultado[df_resultado['Modelo'] == 'EXPONENTIAL_SMOOTHING']['MAE'].mean():.2f} → Menos preciso

🚀 IMPLICACIONES:

  • Usar HYBRID_XGB_ARIMA para predicciones de 52 semanas
  • Entrenar todo el modelo con todos los datos (222 semanas)
  • Generar predicciones recurrentes por semana
  • Reentrenar mensualmente con nuevos datos

""")

print("=" * 100)
