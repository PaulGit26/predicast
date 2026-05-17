"""
SCRIPT 10 V4 - PREDICCIONES CON AUTO-REGRESION DE ERRORES
Usa residuales de entrenamiento para inyectar variación realista
"""

import os
from lib.predicciones_final import run_predicciones_final

FEATURES_DIR = r"04_Scripts_Nuevos\EDA_Outputs"
DATA_DIR = r"01_Datos"
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
import xgboost as xgb

print("\n" + "="*120)
print("SCRIPT 10 V4 - PREDICCIONES RECURSIVAS CON AUTO-REGRESION DE ERRORES")
print("="*120 + "\n")

OUTPUT_DIR = r"d:\Desktop\Predicast\04_Scripts_Nuevos\EDA_Outputs"
DATA_DIR = r"d:\Desktop\Predicast\01_Datos"

# ============================================================================
# PASO 1: CARGAR PARAMETROS Y FEATURES
# ============================================================================

print("[PASO 1] Ejecutando wrapper de predicción final...")

REPORTE_PATH = os.path.join('04_Scripts_Nuevos', 'REPORTE_OPTIMIZACION_HIPERPARAMETROS.json')

resultado = run_predicciones_final(FEATURES_DIR, DATA_DIR, REPORTE_PATH)

print('Resultados:')
print('  Largo :', resultado.get('largo'))
print('  Pivot :', resultado.get('pivot'))
print('  Meta  :', resultado.get('metadata'))

print('\nPredicciones generadas.')
# script now delegates to wrapper; exit

