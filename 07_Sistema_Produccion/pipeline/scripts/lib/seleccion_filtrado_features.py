from pathlib import Path
import pandas as pd
import numpy as np
import json
import gc
from scipy.stats import pearsonr
from statsmodels.stats.outliers_influence import variance_inflation_factor
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


def run_seleccion_filtrado_features(output_dir: str | Path):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    FEATURES_FILE = output_dir / "FEATURES_SEMANAL_PARA_MODELOS.csv"

    if not FEATURES_FILE.exists():
        raise FileNotFoundError(f"Features file not found: {FEATURES_FILE}")

    df = pd.read_csv(FEATURES_FILE, sep=";", encoding="latin-1")

    base_cols = ["Código", "Año", "Semana", "Fecha", "Salida"]
    feature_cols = [c for c in df.columns if c not in base_cols]

    df_features = df[feature_cols].copy()

    # Coerce feature columns to numeric where possible; non-numeric become NaN
    # Use float32 to halve memory usage vs float64
    df_features_numeric = df_features.apply(lambda s: pd.to_numeric(s, errors='coerce')).astype('float32')

    # Clasificación de variables
    features_pasado = {
        "Lags": [c for c in feature_cols if "Lag_" in c],
        "Moving Averages": [c for c in feature_cols if "MA_" in c],
        "Volatilidad": [c for c in feature_cols if "Volatilidad_" in c],
        "Tendencias": [c for c in feature_cols if "Trend_" in c],
        "Ratios": [c for c in feature_cols if any(x in c for x in ["Ratio_", "Variabilidad_Intra"])],
    }

    features_futuro = {
        "Categoricas_Empresa": [c for c in feature_cols if "Empresa_" in c],
        "Categoricas_Canal": [c for c in feature_cols if "Canal_" in c],
        "Categoricas_Punto": [c for c in feature_cols if "Punto_" in c],
        "Categoricas_Trimestre": [c for c in feature_cols if "Trim_" in c],
    }

    features_temporal = {
        "Temporal": [c for c in feature_cols if any(x in c for x in 
                    ["Mes", "Trimestre", "Día_Semana", "Día_Año", "Num_Semana_Año",
                     "Semana_Sin", "Semana_Cos", "Mes_Sin", "Mes_Cos"] )],
        "Otros": [c for c in feature_cols if "Semana_Consecutivas" in c],
    }

    pasado_flat = []
    for feats in features_pasado.values():
        pasado_flat.extend(feats)

    futuro_flat = []
    for feats in features_futuro.values():
        futuro_flat.extend(feats)

    temporal_flat = []
    for feats in features_temporal.values():
        temporal_flat.extend(feats)

    # Correlación (use numeric-only frame)
    corr_matrix = df_features_numeric.corr(method='pearson')
    gc.collect()

    def find_highly_correlated_pairs(corr_mat, threshold=0.95):
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

    pares_altos_095 = find_highly_correlated_pairs(corr_matrix, threshold=0.95)
    pares_altos_090 = find_highly_correlated_pairs(corr_matrix, threshold=0.90)
    del corr_matrix
    gc.collect()

    # VIF — use float64 for numerical stability, drop NaN columns first
    def calculate_vif(df_f):
        df_clean = df_f.dropna(axis=1).astype('float64')
        vif_data = pd.DataFrame()
        vif_data["Feature"] = df_clean.columns
        vif_list = []
        arr = df_clean.values
        for i in range(arr.shape[1]):
            try:
                vif_list.append(variance_inflation_factor(arr, i))
            except Exception:
                vif_list.append(np.nan)
        del arr
        vif_data["VIF"] = vif_list
        return vif_data.sort_values("VIF", ascending=False)

    vif_data = calculate_vif(df_features_numeric)
    gc.collect()
    features_problema = vif_data[vif_data["VIF"] > 10]["Feature"].tolist()

    # Construcción de feature sets
    ma_cols = [c for c in feature_cols if "MA_" in c]
    ma_keep = ["MA_2", "MA_13"]
    ma_drop = [c for c in ma_cols if c not in ma_keep]

    feature_sets = {
        "Conservative": [c for c in pasado_flat if c not in ma_drop + features_problema],
        "Intermediate": [c for c in pasado_flat if c not in ma_drop + features_problema] + 
                        [c for c in futuro_flat if c not in features_problema],
        "Aggressive": [c for c in feature_cols if c not in features_problema],
    }

    # Correlación con target
    target = pd.to_numeric(df["Salida"].copy(), errors='coerce')
    correlaciones_target = {}
    for col in feature_cols:
        try:
            series = pd.to_numeric(df_features[col], errors='coerce')
            # align non-nulls for pearsonr
            mask = series.notna() & target.notna()
            if mask.sum() < 2:
                raise ValueError("Not enough numeric observations")
            corr, pval = pearsonr(series[mask], target[mask])
            correlaciones_target[col] = {"correlacion": corr, "pvalor": pval}
        except Exception:
            correlaciones_target[col] = {"correlacion": 0, "pvalor": 1}

    df_corr_target = pd.DataFrame(correlaciones_target).T
    df_corr_target["abs_corr"] = abs(df_corr_target["correlacion"])
    df_corr_target = df_corr_target.sort_values("abs_corr", ascending=False)

    # Visualizaciones
    top_n = 30
    top_features = df_corr_target.head(top_n).index.tolist()
    corr_subset = df_features_numeric[top_features].corr()

    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(corr_subset, annot=False, fmt='.2f', cmap='coolwarm', center=0, 
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title(f'Matriz de Correlación - TOP {top_n} Features\n(Correlación de Pearson)', 
                 fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / "06_CORRELACION_HEATMAP_TOP30.png", dpi=100, bbox_inches="tight")
    plt.close('all')
    gc.collect()

    # Gráficos adicionales
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
    plt.savefig(output_dir / "07_CORRELACION_TARGET_TOP25.png", dpi=100, bbox_inches="tight")
    plt.close('all')
    gc.collect()

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
    plt.savefig(output_dir / "08_VIF_MULTICOLINEALIDAD.png", dpi=100, bbox_inches="tight")
    plt.close('all')
    gc.collect()

    # Exportar resultados
    for set_name, feats in feature_sets.items():
        df_subset = df[base_cols + feats].copy()
        filename = f"FEATURES_SEMANAL_{set_name.upper()}.csv"
        filepath = output_dir / filename
        df_subset.to_csv(filepath, sep=";", encoding="latin-1", index=False)

    df_corr_target.to_csv(output_dir / "CORRELACIONES_TARGET.csv", sep=";", encoding="latin-1")
    vif_data.to_csv(output_dir / "VIF_ANALISIS.csv", sep=";", encoding="latin-1", index=False)

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
        }
    }

    with open(output_dir / "SELECTION_METADATA.json", "w", encoding="utf-8") as f:
        json.dump(selection_metadata, f, indent=2, ensure_ascii=False, default=str)

    return {
        "feature_files": {s: str(output_dir / f"FEATURES_SEMANAL_{s.upper()}.csv") for s in feature_sets.keys()},
        "correlations": str(output_dir / "CORRELACIONES_TARGET.csv"),
        "vif": str(output_dir / "VIF_ANALISIS.csv"),
        "metadata": str(output_dir / "SELECTION_METADATA.json")
    }
