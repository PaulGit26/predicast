"""
========================================================================
ANALISIS DE CLUSTERING - ADI/CV² (INTERMITTENT vs ERRATIC)
========================================================================
Basado en teoría de Syntetos & Boylan (2005):
- ADI (Average Demand Interval): días promedio entre demandas
- CV² (Coeficiente de Variación²): variabilidad relativa

CLASIFICACION:
  ERRATIC (Demanda frecuente, variable):
    - ADI < 1.32 (demandas casi cada día)
    - CV² > 0.49 (alta variabilidad)
    → Estrategia: 4 MODELOS LOCALES (1 por producto)

  INTERMITTENT (Demanda episódica, consistente):
    - ADI > 1.32 (demandas espaciadas)
    - CV² < 0.49 (baja variabilidad)
    → Estrategia: 1 MODELO GLOBAL (para todos combinados)

Entrada:  FEATURES_SEMANAL_PARA_MODELOS.csv
Salida:   CLUSTERING_METADATA.json (define grupos para scripts 06, 08, 09)
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
print("ANALISIS DE CLUSTERING - ADI/CV² (SYNTETOS & BOYLAN 2005)")
print("="*80)

# ============================================================================
# PASO 1: CARGAR FEATURES
# ============================================================================

print("\n[PASO 1] CARGANDO FEATURES...")

features_file = os.path.join(OUTPUT_DIR, "FEATURES_SEMANAL_PARA_MODELOS.csv")
df_features = pd.read_csv(features_file, sep=";", encoding="latin-1", parse_dates=["Fecha"])

print(f"  Registros: {len(df_features):,}")
print(f"  Productos: {df_features['Código'].nunique()}")
print(f"  Rango fechas: {df_features['Fecha'].min().date()} a {df_features['Fecha'].max().date()}")

# ============================================================================
# PASO 2: CALCULAR ADI POR PRODUCTO
# ============================================================================

print("\n[PASO 2] CALCULANDO ADI (Average Demand Interval)...")

# ADI = número total de semanas / número de semanas con demanda > 0
clustering_results = []

for producto in sorted(df_features["Código"].unique()):
    df_prod = df_features[df_features["Código"] == producto].copy()
    df_prod = df_prod.sort_values("Fecha")
    
    # Total de semanas en el período
    total_semanas = len(df_prod)
    
    # Semanas con demanda > 0
    semanas_con_demanda = (df_prod["Salida"] > 0).sum()
    
    # ADI: promedio de semanas entre demandas
    if semanas_con_demanda > 0:
        adi = total_semanas / semanas_con_demanda
    else:
        adi = np.inf
    
    # ========================================================================
    # PASO 3: CALCULAR CV² POR PRODUCTO
    # ========================================================================
    
    # CV² = (Desv.Std. de demandas / Media de demandas)²
    demandas = df_prod[df_prod["Salida"] > 0]["Salida"]
    
    if len(demandas) > 0:
        media_demanda = demandas.mean()
        std_demanda = demandas.std()
        cv = std_demanda / media_demanda if media_demanda > 0 else 0
        cv_cuadrado = cv ** 2
    else:
        cv = np.nan
        cv_cuadrado = np.nan
    
    # ========================================================================
    # PASO 4: CLASIFICACIÓN
    # ========================================================================
    
    # Umbrales de Syntetos & Boylan (2005)
    threshold_adi = 1.32
    threshold_cv2 = 0.49
    
    if adi < threshold_adi and cv_cuadrado > threshold_cv2:
        cluster = "ERRATIC"
        grupo = "GRUPO_1_ERRATIC"
    elif adi > threshold_adi and cv_cuadrado < threshold_cv2:
        cluster = "INTERMITTENT"
        grupo = "GRUPO_2_INTERMITTENT"
    else:
        # Híbrido o ambiguo - clasificar por ADI primario
        if adi < threshold_adi:
            cluster = "HYBRID_ERRATIC"
            grupo = "GRUPO_1_ERRATIC"
        else:
            cluster = "HYBRID_INTERMITTENT"
            grupo = "GRUPO_2_INTERMITTENT"
    
    # Estadísticas adicionales
    clustering_results.append({
        "Código": producto,
        "ADI": round(adi, 4),
        "CV": round(cv, 4),
        "CV2": round(cv_cuadrado, 4),
        "Semanas_Totales": int(total_semanas),
        "Semanas_Con_Demanda": int(semanas_con_demanda),
        "Pct_Semanas_Demanda": round((semanas_con_demanda / total_semanas) * 100, 2),
        "Media_Demanda": round(media_demanda, 2) if len(demandas) > 0 else 0,
        "Std_Demanda": round(std_demanda, 2) if len(demandas) > 0 else 0,
        "Cluster_Clasificacion": cluster,
        "Grupo_Asignado": grupo
    })

# Crear DataFrame de resultados
df_clustering = pd.DataFrame(clustering_results)

# ============================================================================
# PASO 5: MOSTRAR RESULTADOS
# ============================================================================

print("\n[PASO 5] RESULTADOS DE CLUSTERING:")
print("\n" + "="*80)
print("CLASIFICACION POR PRODUCTO:")
print("="*80)

for _, row in df_clustering.iterrows():
    print(f"\n{row['Código']}:")
    print(f"  ADI: {row['ADI']:.4f} (threshold: 1.32)")
    print(f"  CV²: {row['CV2']:.4f} (threshold: 0.49)")
    print(f"  Semanas: {row['Semanas_Con_Demanda']}/{row['Semanas_Totales']} con demanda ({row['Pct_Semanas_Demanda']:.1f}%)")
    print(f"  Demanda: media={row['Media_Demanda']:.0f}, std={row['Std_Demanda']:.0f}")
    print(f"  -> Cluster: {row['Cluster_Clasificacion']} | Grupo: {row['Grupo_Asignado']}")

# ============================================================================
# PASO 6: ESTADÍSTICAS POR CLUSTER
# ============================================================================

print("\n" + "="*80)
print("RESUMEN POR CLUSTER:")
print("="*80)

for grupo_name in ["GRUPO_1_ERRATIC", "GRUPO_2_INTERMITTENT"]:
    df_grupo = df_clustering[df_clustering["Grupo_Asignado"] == grupo_name]
    
    if len(df_grupo) > 0:
        grupo_label = "ERRATIC (Alto Volumen)" if "ERRATIC" in grupo_name else "INTERMITTENT (Bajo Volumen)"
        print(f"\n{grupo_label}:")
        print(f"  Productos: {len(df_grupo)}")
        print(f"  Códigos: {', '.join(df_grupo['Código'].tolist())}")
        print(f"  ADI promedio: {df_grupo['ADI'].mean():.4f}")
        print(f"  CV² promedio: {df_grupo['CV2'].mean():.4f}")
        print(f"  Semanas promedio con demanda: {df_grupo['Pct_Semanas_Demanda'].mean():.1f}%")

# ============================================================================
# PASO 7: EXPORTAR METADATA JSON
# ============================================================================

print("\n[PASO 6] EXPORTANDO METADATA...")

# Obtener listas de productos por grupo
grupo_1_productos = df_clustering[df_clustering["Grupo_Asignado"] == "GRUPO_1_ERRATIC"]["Código"].tolist()
grupo_2_productos = df_clustering[df_clustering["Grupo_Asignado"] == "GRUPO_2_INTERMITTENT"]["Código"].tolist()

# Crear JSON de metadatos
clustering_metadata = {
    "fecha_generacion": datetime.now().isoformat(),
    "metodologia": "Syntetos & Boylan (2005) - ADI/CV² Classification",
    "referencias": [
        "Syntetos, A. A., & Boylan, J. E. (2005). The accuracy of intermittent demand estimates.",
        "International Journal of Forecasting, 21(1), 137-152."
    ],
    "thresholds": {
        "ADI": 1.32,
        "CV2": 0.49
    },
    "grupos": {
        "GRUPO_1": {
            "nombre": "ERRATIC - Demanda Frecuente y Variable",
            "descripcion": "ADI < 1.32 (demandas casi diarias) Y CV² > 0.49 (alta variabilidad)",
            "estrategia": "4 MODELOS LOCALES (1 modelo por producto)",
            "productos": grupo_1_productos,
            "conteo": len(grupo_1_productos),
            "caracteristicas": {
                "frecuencia_demanda": "Frecuente (casi cada semana)",
                "variabilidad": "Alta (impredecible)",
                "recomendacion_modelo": "Ridge, XGBoost (mejor para capturar patrones complejos)"
            }
        },
        "GRUPO_2": {
            "nombre": "INTERMITTENT - Demanda Episódica y Consistente",
            "descripcion": "ADI > 1.32 (demandas espaciadas) Y CV² < 0.49 (baja variabilidad)",
            "estrategia": "1 MODELO GLOBAL (modelo único para todos)",
            "productos": grupo_2_productos,
            "conteo": len(grupo_2_productos),
            "caracteristicas": {
                "frecuencia_demanda": "Episódica (saltos en tiempo)",
                "variabilidad": "Baja (predecible cuando ocurre)",
                "recomendacion_modelo": "Ridge, LightGBM (mejor para datos dispersos)"
            }
        }
    },
    "detalles_por_producto": df_clustering.to_dict("records")
}

metadata_file = os.path.join(OUTPUT_DIR, "CLUSTERING_METADATA.json")
with open(metadata_file, "w", encoding="utf-8") as f:
    json.dump(clustering_metadata, f, indent=2, ensure_ascii=False)

print(f"  [OK] CLUSTERING_METADATA.json")

# ============================================================================
# PASO 8: EXPORTAR CSV CON ANÁLISIS
# ============================================================================

df_clustering.to_csv(
    os.path.join(OUTPUT_DIR, "CLUSTERING_ANALISIS_DETALLADO.csv"),
    sep=";",
    encoding="latin-1",
    index=False
)

print(f"  [OK] CLUSTERING_ANALISIS_DETALLADO.csv")

# ============================================================================
# CONCLUSIONES
# ============================================================================

print("\n" + "="*80)
print("CLUSTERING COMPLETADO")
print("="*80)
print(f"""
RESUMEN:
  Total productos analizados: {len(df_clustering)}
  
  GRUPO 1 - ERRATIC (Modelos Locales):
    Productos: {len(grupo_1_productos)}
    Modelos a entrenar: {len(grupo_1_productos)} (1 por producto)
    
  GRUPO 2 - INTERMITTENT (Modelo Global):
    Productos: {len(grupo_2_productos)}
    Modelos a entrenar: 1 (global para {len(grupo_2_productos)} productos)

ARCHIVOS GENERADOS:
  - CLUSTERING_METADATA.json (config para scripts 06, 08, 09)
  - CLUSTERING_ANALISIS_DETALLADO.csv (análisis completo)

PROXIMOS PASOS:
  Scripts 06, 08, 09 leeran CLUSTERING_METADATA.json
  para saber cuantos modelos entrenar y cómo agruparlos.
""")

print("="*80 + "\n")
