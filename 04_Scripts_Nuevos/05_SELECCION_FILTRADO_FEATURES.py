"""
SELECCIÓN Y FILTRADO DE CARACTERÍSTICAS
Paso Crítico: Análisis de Correlación + Clasificación para evitar Data Leakage
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings("ignore")

print("\n" + "="*80)
print("SELECCIÓN Y FILTRADO DE CARACTERÍSTICAS")
print("="*80)

OUTPUT_DIR = r"d:\Desktop\Predicast\04_Scripts_Nuevos\EDA_Outputs"
FEATURES_FILE = os.path.join(OUTPUT_DIR, "FEATURES_SEMANAL_PARA_MODELOS.csv")

# ============================================================================
# PASO 1: CARGAR DATOS
# ============================================================================

print("\n[PASO 1] CARGANDO FEATURES...")

df = pd.read_csv(FEATURES_FILE, sep=";", encoding="latin-1")
print(f"  Registros: {len(df):,}")
print(f"  Columnas totales: {df.shape[1]}")

# Columnas base (no features)
base_cols = ["Código", "Año", "Semana", "Fecha", "Salida"]

# Features (todo excepto base)
feature_cols = [c for c in df.columns if c not in base_cols]
print(f"  Features totales: {len(feature_cols)}")

df_features = df[feature_cols].copy()
print(f"\n  Primeras features: {feature_cols[:10]}")

# ============================================================================
# PASO 2: CLASIFICACIÓN DE VARIABLES (DATA LEAKAGE PREVENTION)
# ============================================================================

print("\n[PASO 2] CLASIFICACIÓN DE VARIABLES...")

# SEGURO: Solo información del pasado (no causa data leakage)
features_pasado = {
    "Lags": [c for c in feature_cols if "Lag_" in c],
    "Moving Averages": [c for c in feature_cols if "MA_" in c],
    "Volatilidad": [c for c in feature_cols if "Volatilidad_" in c],
    "Tendencias": [c for c in feature_cols if "Trend_" in c],
    "Ratios": [c for c in feature_cols if any(x in c for x in ["Ratio_", "Variabilidad_Intra"])],
}

# CONOCIDO A FUTURO: Variables que PODRÍAN ser conocidas anticipadamente
features_futuro = {
    "Categoricas_Empresa": [c for c in feature_cols if "Empresa_" in c],
    "Categoricas_Canal": [c for c in feature_cols if "Canal_" in c],
    "Categoricas_Punto": [c for c in feature_cols if "Punto_" in c],
    "Categoricas_Trimestre": [c for c in feature_cols if "Trim_" in c],
}

# TEMPORAL: Permite pero con cuidado (día, mes pueden cambiar predicciones)
features_temporal = {
    "Temporal": [c for c in feature_cols if any(x in c for x in 
                ["Mes", "Trimestre", "Día_Semana", "Día_Año", "Num_Semana_Año",
                 "Semana_Sin", "Semana_Cos", "Mes_Sin", "Mes_Cos"])],
    "Otros": [c for c in feature_cols if "Semana_Consecutivas" in c],
}

# Compilar
pasado_flat = []
for cat, feats in features_pasado.items():
    pasado_flat.extend(feats)
    print(f"  ✅ {cat}: {len(feats)} features")

futuro_flat = []
for cat, feats in features_futuro.items():
    futuro_flat.extend(feats)
    print(f"  📅 {cat}: {len(feats)} features")

temporal_flat = []
for cat, feats in features_temporal.items():
    temporal_flat.extend(feats)
    print(f"  ⏰ {cat}: {len(feats)} features")

print(f"\n  Total: {len(pasado_flat)} (pasado) + {len(futuro_flat)} (futuro) + {len(temporal_flat)} (temporal)")
print(f"  = {len(pasado_flat) + len(futuro_flat) + len(temporal_flat)} features clasificadas")

# ============================================================================
# PASO 3: ANÁLISIS DE CORRELACIÓN
# ============================================================================

print("\n[PASO 3] ANÁLISIS DE CORRELACIÓN...")

# Calcular matriz de correlación
corr_matrix = df_features.corr(method='pearson')

print(f"  Matriz de correlación: {corr_matrix.shape[0]} × {corr_matrix.shape[1]}")

# Función para encontrar features altamente correlacionadas
def find_highly_correlated_pairs(corr_mat, threshold=0.95):
    """Encuentra pares de variables con correlación alta"""
    pairs = []
    for i in range(len(corr_mat.columns)):
        for j in range(i+1, len(corr_mat.columns)):
            if abs(corr_mat.iloc[i, j]) > threshold:
                pairs.append({
                    'Feature1': corr_mat.columns[i],
                    'Feature2': corr_mat.columns[j],
                    'Correlacion': corr_mat.iloc[i, j]
                })
    return pairs

# Encontrar pares altamente correlacionados
pares_altos_095 = find_highly_correlated_pairs(corr_matrix, threshold=0.95)
pares_altos_090 = find_highly_correlated_pairs(corr_matrix, threshold=0.90)
pares_altos_085 = find_highly_correlated_pairs(corr_matrix, threshold=0.85)

print(f"\n  Pares con correlación > 0.95: {len(pares_altos_095)}")
print(f"  Pares con correlación > 0.90: {len(pares_altos_090)}")
print(f"  Pares con correlación > 0.85: {len(pares_altos_085)}")

if pares_altos_095:
    print(f"\n  TOP Correlaciones (>0.95):")
    for pair in sorted(pares_altos_095, key=lambda x: abs(x['Correlacion']), reverse=True)[:10]:
        print(f"    {pair['Feature1']:30s} ↔ {pair['Feature2']:30s} : {pair['Correlacion']:7.4f}")

# ============================================================================
# PASO 4: ESTRATEGIA DE ELIMINACIÓN
# ============================================================================

print("\n[PASO 4] ESTRATEGIA DE ELIMINACIÓN DE REDUNDANCIAS...")

# Usar VIF (Variance Inflation Factor) para multicolinealidad
from statsmodels.stats.outliers_influence import variance_inflation_factor

def calculate_vif(df_features):
    """Calcula VIF para detectar multicolinealidad"""
    vif_data = pd.DataFrame()
    vif_data["Feature"] = df_features.columns
    
    # Para evitar warnings, usar try/except
    vif_list = []
    for i in range(df_features.shape[1]):
        try:
            vif_list.append(variance_inflation_factor(df_features.values, i))
        except:
            vif_list.append(np.nan)
    
    vif_data["VIF"] = vif_list
    return vif_data.sort_values("VIF", ascending=False)

print(f"  Calculando VIF (Variance Inflation Factor)...")
vif_data = calculate_vif(df_features)

print(f"\n  TOP 15 features con MAYOR multicolinealidad (VIF > 10 es preocupante):")
print(vif_data.head(15).to_string(index=False))

# Features problemáticas (VIF > 10)
features_problema = vif_data[vif_data["VIF"] > 10]["Feature"].tolist()
print(f"\n  ⚠️  Features con VIF > 10 (multicolinealidad): {len(features_problema)}")
if features_problema:
    for f in features_problema[:10]:
        print(f"      - {f}")

# ============================================================================
# PASO 5: CONSTRUCCIÓN DE FEATURE SET FINAL
# ============================================================================

print("\n[PASO 5] CONSTRUCCIÓN DE FEATURE SETS...")

# OPCIÓN 1: Conservative (Solo pasado seguro, sin MA altamente correlacionadas)
ma_cols = [c for c in feature_cols if "MA_" in c]
# Mantener MA_2 y MA_13, eliminar MA_4 y MA_8 (pueden estar correlacionadas)
ma_keep = ["MA_2", "MA_13"]
ma_drop = [c for c in ma_cols if c not in ma_keep]

# OPCIÓN 2: Intermediate (Pasado + algunas categóricas conocidas)
# Las categóricas (Empresa, Canal, Punto) DEBERÍAN conocerse anticipadamente

# OPCIÓN 3: Aggressive (Todo pero con VIF filter)

# Crear sets
feature_sets = {
    "Conservative": [c for c in pasado_flat if c not in ma_drop + features_problema],
    
    "Intermediate": [c for c in pasado_flat if c not in ma_drop + features_problema] + 
                    [c for c in futuro_flat if c not in features_problema],
    
    "Aggressive": [c for c in feature_cols if c not in features_problema],
}

print("\n  FEATURE SETS RECOMENDADOS:")
for set_name, feats in feature_sets.items():
    print(f"\n  {set_name} ({len(feats)} features):")
    print(f"    - Pasado (lags, MA, vol, trend, ratio): {len([f for f in feats if any(x in f for x in ['Lag', 'MA', 'Volatilidad', 'Trend', 'Ratio'])])}")
    print(f"    - Categóricas (empresa, canal, punto): {len([f for f in feats if any(x in f for x in ['Empresa', 'Canal', 'Punto'])])}")
    print(f"    - Tempora/Estacional: {len([f for f in feats if any(x in f for x in ['Mes', 'Trimestre', 'Sin', 'Cos'])])}")

# ============================================================================
# PASO 6: IMPORTANCIA DE FEATURES (Correlación con Target)
# ============================================================================

print("\n[PASO 6] CORRELACIÓN CON TARGET (Salida)...")

target = df["Salida"].copy()

# Calcular correlación de cada feature con el target
correlaciones_target = {}
for col in feature_cols:
    try:
        corr, pval = pearsonr(df_features[col], target)
        correlaciones_target[col] = {"correlacion": corr, "pvalor": pval}
    except:
        correlaciones_target[col] = {"correlacion": 0, "pvalor": 1}

df_corr_target = pd.DataFrame(correlaciones_target).T
df_corr_target["abs_corr"] = abs(df_corr_target["correlacion"])
df_corr_target = df_corr_target.sort_values("abs_corr", ascending=False)

print(f"\n  TOP 20 Features MÁS correlacionadas con Salida:")
print(df_corr_target.head(20)[["correlacion", "pvalor"]].to_string())

print(f"\n  Features sin correlacion significativa (p-valor > 0.05):")
no_sig = df_corr_target[df_corr_target["pvalor"] > 0.05]
print(f"    {len(no_sig)} features (considerar eliminar)")
if len(no_sig) > 0:
    print(f"    Ejemplos: {no_sig.index[:10].tolist()}")

# ============================================================================
# PASO 7: VISUALIZACIONES
# ============================================================================

print("\n[PASO 7] GENERANDO VISUALIZACIONES...")

# Heatmap de correlación (solo top features)
top_n = 30
top_features = df_corr_target.head(top_n).index.tolist()
corr_subset = df_features[top_features].corr()

fig, ax = plt.subplots(figsize=(14, 12))
sns.heatmap(corr_subset, annot=False, fmt='.2f', cmap='coolwarm', center=0, 
            square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)
ax.set_title(f'Matriz de Correlación - TOP {top_n} Features\n(Correlación de Pearson)', 
             fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "06_CORRELACION_HEATMAP_TOP30.png"), dpi=300, bbox_inches="tight")
print(f"  ✓ Guardado: 06_CORRELACION_HEATMAP_TOP30.png")
plt.close()

# Gráfico de Correlación con Target
fig, ax = plt.subplots(figsize=(12, 8))
top_corr_target = df_corr_target.head(25)
colors = ['green' if x > 0 else 'red' for x in top_corr_target['correlacion']]
ax.barh(range(len(top_corr_target)), top_corr_target['correlacion'], color=colors, alpha=0.7, edgecolor='black')
ax.set_yticks(range(len(top_corr_target)))
ax.set_yticklabels(top_corr_target.index)
ax.set_xlabel('Correlación con Salida', fontsize=11, fontweight='bold')
ax.set_title('TOP 25 Features - Correlación con Target (Salida)', fontsize=12, fontweight='bold')
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "07_CORRELACION_TARGET_TOP25.png"), dpi=300, bbox_inches="tight")
print(f"  ✓ Guardado: 07_CORRELACION_TARGET_TOP25.png")
plt.close()

# Gráfico de VIF
fig, ax = plt.subplots(figsize=(12, 6))
vif_top = vif_data.head(20)
colors_vif = ['red' if x > 10 else 'orange' if x > 5 else 'green' for x in vif_top['VIF']]
ax.barh(range(len(vif_top)), vif_top['VIF'], color=colors_vif, alpha=0.7, edgecolor='black')
ax.set_yticks(range(len(vif_top)))
ax.set_yticklabels(vif_top['Feature'])
ax.set_xlabel('VIF (Variance Inflation Factor)', fontsize=11, fontweight='bold')
ax.set_title('TOP 20 Features - Multicolinealidad (VIF)\nRojo (>10)=Problemático, Naranja (5-10)=Moderado, Verde(<5)=OK', 
             fontsize=11, fontweight='bold')
ax.axvline(x=10, color='red', linestyle='--', linewidth=1, alpha=0.5, label='VIF=10 (threshold)')
ax.axvline(x=5, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='VIF=5')
ax.legend()
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "08_VIF_MULTICOLINEALIDAD.png"), dpi=300, bbox_inches="tight")
print(f"  ✓ Guardado: 08_VIF_MULTICOLINEALIDAD.png")
plt.close()

# ============================================================================
# PASO 8: EXPORTAR RESULTADOS
# ============================================================================

print("\n[PASO 8] EXPORTANDO RESULTADOS...")

# Guardar Feature Sets
for set_name, feats in feature_sets.items():
    df_subset = df[base_cols + feats].copy()
    filename = f"FEATURES_SEMANAL_{set_name.upper()}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)
    df_subset.to_csv(filepath, sep=";", encoding="latin-1", index=False)
    print(f"  ✓ {filename} ({len(feats)} features, {len(df_subset):,} obs)")

# Correlaciones con Target
df_corr_target.to_csv(os.path.join(OUTPUT_DIR, "CORRELACIONES_TARGET.csv"), sep=";", encoding="latin-1")
print(f"  ✓ CORRELACIONES_TARGET.csv")

# VIF
vif_data.to_csv(os.path.join(OUTPUT_DIR, "VIF_ANALISIS.csv"), sep=";", encoding="latin-1", index=False)
print(f"  ✓ VIF_ANALISIS.csv")

# Metadata de selección
selection_metadata = {
    "total_features_original": len(feature_cols),
    "features_problema_vif": len(features_problema),
    "pares_altamente_correlacionados_095": len(pares_altos_095),
    "pares_altamente_correlacionados_090": len(pares_altos_090),
    "clasificacion": {
        "Pasado_Seguro": len(pasado_flat),
        "Futuro_Conocido": len(futuro_flat),
        "Temporal": len(temporal_flat),
    },
    "feature_sets": {
        "Conservative": {
            "cantidad": len(feature_sets["Conservative"]),
            "features": feature_sets["Conservative"]
        },
        "Intermediate": {
            "cantidad": len(feature_sets["Intermediate"]),
            "features": feature_sets["Intermediate"]
        },
        "Aggressive": {
            "cantidad": len(feature_sets["Aggressive"]),
            "features": feature_sets["Aggressive"]
        }
    },
    "recomendacion": {
        "para_produccion": "Conservative (evita data leakage)",
        "para_experimentos": "Intermediate (balance riesgo-precisión)",
        "explorar_solo": "Aggressive (investigación, no producción)"
    },
    "data_leakage_protections": {
        "Categoricas_Empresa_Canal_Punto": "Usar si son CONOCIDAS anticipadamente (ej: clientes fijos, canales planificados)",
        "Temporales": "Usar con cuidado: mes, trimestre OK; día_semana OK si es recurrente",
        "Lags": "SIEMPRE seguros (información del pasado)",
        "MA_Volatilidad_Trend": "SIEMPRE seguros (estadísticas históricas)"
    }
}

with open(os.path.join(OUTPUT_DIR, "SELECTION_METADATA.json"), "w", encoding="utf-8") as f:
    json.dump(selection_metadata, f, indent=2, ensure_ascii=False, default=str)

print(f"  ✓ SELECTION_METADATA.json")

# ============================================================================
# RESUMEN FINAL
# ============================================================================

print("\n" + "="*80)
print("RESUMEN - SELECCIÓN Y FILTRADO DE CARACTERÍSTICAS")
print("="*80)

print(f"""
✓ ANÁLISIS DE CORRELACIÓN:
  • Matriz de Pearson calculada
  • Pares altamente correlacionados (>0.95): {len(pares_altos_095)}
  • Multicolinealidad (VIF > 10): {len(features_problema)} features problemáticas

✓ CLASIFICACIÓN DE VARIABLES (Data Leakage Prevention):
  • Pasado (Lags, MA, Volatilidad): {len(pasado_flat)} features ✅ SEGURO
  • Futuro (Empresa, Canal, Punto, Trimestre): {len(futuro_flat)} features ⚠️  VERIFICAR ANTICIPADAMENTE
  • Temporal: {len(temporal_flat)} features ⏰ USAR CON CUIDADO

✓ FEATURE SETS GENERADOS:
  1. Conservative ({len(feature_sets["Conservative"])} features)
     → Solo pasado seguro, sin redundancias
     → Recomendado para PRODUCCIÓN
     → Evita data leakage completamente
  
  2. Intermediate ({len(feature_sets["Intermediate"])} features)
     → Pasado + categorías conocidas anticipadamente
     → Balance riesgo-precisión
     → Recomendado para EXPERIMENTACIÓN
  
  3. Aggressive ({len(feature_sets["Aggressive"])} features)
     → Todas las features (menos VIF>10)
     → Máximo poder predictivo
     → ⚠️  Riesgo de data leakage - solo INVESTIGACIÓN

✓ ANÁLISIS DE IMPORTANCIA:
  • TOP feature correlacionada con Salida: {df_corr_target.index[0]} (r={df_corr_target.iloc[0]['correlacion']:.4f})
  • Features sin correlación significativa: {len(no_sig)}

✓ ARCHIVOS GENERADOS:
  • FEATURES_SEMANAL_CONSERVATIVE.csv - Para producción
  • FEATURES_SEMANAL_INTERMEDIATE.csv - Para experimentos
  • FEATURES_SEMANAL_AGGRESSIVE.csv - Investigación
  • CORRELACIONES_TARGET.csv - Importancia de features
  • VIF_ANALISIS.csv - Multicolinealidad
  • SELECTION_METADATA.json - Metadatos completos
  • 06_CORRELACION_HEATMAP_TOP30.png - Matriz correlación
  • 07_CORRELACION_TARGET_TOP25.png - Importancia
  • 08_VIF_MULTICOLINEALIDAD.png - Multicolinealidad

✓ RECOMENDACIÓN PARA MODELOS:
  → Usar FEATURES_SEMANAL_INTERMEDIATE.csv
    • Buen balance entre riesgo de data leakage vs poder predictivo
    • {len(feature_sets["Intermediate"])} features seleccionadas
    • Sin redundancia significativa

""")

print("="*80)
