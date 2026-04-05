"""
Rutas de Forecasting para API Flask

Endpoints:
  - GET /api/v1/forecasting/52weeks/<producto>
  - GET /api/v1/forecasting/all-products
  - GET /api/v1/forecasting/product/<producto>/detailed
  - GET /api/v1/forecasting/model-info
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import pandas as pd
import json
from pathlib import Path
import os

# Crear blueprint
forecasting_bp = Blueprint('forecasting', __name__, url_prefix='/api/v1')

# ========================================================================
# CARGAR DATOS AL INICIAR (caching)
# ========================================================================

PREDICCIONES = None
PREDICCIONES_LARGO = None
ESTADISTICAS = None
METADATA = None

def cargar_datos_forecasting():
    """Cargar datos de predicciones en memoria"""
    global PREDICCIONES, PREDICCIONES_LARGO, ESTADISTICAS, METADATA
    
    try:
        # Obtener ruta base relativa desde donde se ejecuta
        base_path = Path(__file__).resolve().parent.parent.parent.parent
        
        # Datos pivot (semanas x productos)
        pred_pivot = base_path / "01_Datos" / "predicciones_52semanas_pivot.csv"
        PREDICCIONES = pd.read_csv(pred_pivot, index_col=0)
        
        # Datos largo (tidy format)
        pred_largo = base_path / "01_Datos" / "predicciones_52semanas_largo.csv"
        PREDICCIONES_LARGO = pd.read_csv(pred_largo)
        
        # Estadisticas
        stats_csv = base_path / "01_Datos" / "predicciones_estadisticas.csv"
        ESTADISTICAS = pd.read_csv(stats_csv, index_col=0)
        
        # Metadata
        metadata_json = base_path / "03_Modelos" / "forecasting_metadata.json"
        with open(metadata_json, 'r') as f:
            METADATA = json.load(f)
        
        print("[✅] Datos de forecasting cargados en memoria")
        return True
        
    except Exception as e:
        print(f"[❌] Error cargando datos forecasting: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ========================================================================
# ENDPOINT 1: Predicciones de 52 semanas para un producto
# ========================================================================
@forecasting_bp.route('/forecasting/52weeks/<producto>', methods=['GET'])
def get_52weeks_forecast(producto):
    """
    GET /api/v1/forecasting/52weeks/{PRODUCTO}
    
    Retorna predicciones de 52 semanas para un producto especifico
    
    Response:
    {
      "producto": "CP_01",
      "semanas": 52,
      "predicciones": [10.5, 11.2, ...],
      "fechas": ["2026-W14", "2026-W15", ...],
      "intervalo_95": {
        "lower": [8.1, 9.0, ...],
        "upper": [13.2, 13.5, ...]
      },
      "estadisticas": {
        "media": 10.8,
        "std": 1.2,
        "min": 8.1,
        "max": 13.5
      }
    }
    """
    
    if PREDICCIONES is None:
        return jsonify({"error": "Datos de forecasting no disponibles"}), 503
    
    # Validar que producto existe
    if producto not in PREDICCIONES.columns:
        return jsonify({
            "error": f"Producto '{producto}' no encontrado",
            "productos_disponibles": list(PREDICCIONES.columns)
        }), 404
    
    try:
        # Extraer predicciones
        preds = PREDICCIONES[producto].values.tolist()
        
        # Extraer intervalo de confianza
        preds_largo = PREDICCIONES_LARGO[PREDICCIONES_LARGO['Producto_codigo'] == producto]
        lower = preds_largo['Lower_Bound_95'].values.tolist()
        upper = preds_largo['Upper_Bound_95'].values.tolist()
        
        # Estadisticas
        stats = preds_largo['Prediccion'].describe().to_dict()
        
        response = {
            "success": True,
            "producto": producto,
            "semanas": len(preds),
            "predicciones": [round(p, 2) for p in preds],
            "fechas_prediccion": PREDICCIONES.index.tolist(),
            "intervalo_confianza_95_pct": {
                "lower": [round(l, 2) for l in lower],
                "upper": [round(u, 2) for u in upper]
            },
            "estadisticas_predicciones": {
                "media": round(float(stats['mean']), 2),
                "desv_estandar": round(float(stats['std']), 2),
                "minimo": round(float(stats['min']), 2),
                "maximo": round(float(stats['max']), 2)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ========================================================================
# ENDPOINT 2: Todos los productos (resumen)
# ========================================================================
@forecasting_bp.route('/forecasting/all-products', methods=['GET'])
def get_all_forecasts():
    """
    GET /api/v1/forecasting/all-products
    
    Retorna resumen de predicciones para TODOS los productos
    
    Response:
    {
      "total_productos": 20,
      "semanas_predichas": 52,
      "productos": [
        {
          "codigo": "CP_01",
          "prediccion_media": 10.8,
          "prediccion_std": 1.2,
          "tendencia": "estable"
        },
        ...
      ]
    }
    """
    
    if PREDICCIONES is None:
        return jsonify({"error": "Datos de forecasting no disponibles"}), 503
    
    try:
        productos_resumen = []
        
        for producto in PREDICCIONES.columns:
            preds = PREDICCIONES[producto].values
            media = float(preds.mean())
            std = float(preds.std())
            
            # Calcular tendencia simple
            primera_mitad = preds[:26].mean()
            segunda_mitad = preds[26:].mean()
            
            if segunda_mitad > primera_mitad * 1.05:
                tendencia = "creciente"
            elif segunda_mitad < primera_mitad * 0.95:
                tendencia = "decreciente"
            else:
                tendencia = "estable"
            
            productos_resumen.append({
                "codigo": producto,
                "prediccion_media": round(media, 2),
                "prediccion_std": round(std, 2),
                "prediccion_min": round(float(preds.min()), 2),
                "prediccion_max": round(float(preds.max()), 2),
                "tendencia_52sem": tendencia
            })
        
        response = {
            "success": True,
            "total_productos": len(productos_resumen),
            "semanas_predichas": len(PREDICCIONES),
            "fecha_inicio_predicciones": PREDICCIONES.index[0],
            "fecha_fin_predicciones": PREDICCIONES.index[-1],
            "productos": sorted(productos_resumen, key=lambda x: x['codigo']),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ========================================================================
# ENDPOINT 3: Detalle completo (historico + predicciones)
# ========================================================================
@forecasting_bp.route('/forecasting/product/<producto>/detailed', methods=['GET'])
def get_detailed_forecast(producto):
    """
    GET /api/v1/forecasting/product/{PRODUCTO}/detailed
    
    Retorna informacion COMPLETA con predicciones futuras
    Util para graficar en dashboard
    
    Response:
    {
      "producto": "CP_01",
      "predicciones": {...},
      "intervalos": {...}
    }
    """
    
    if PREDICCIONES is None:
        return jsonify({"error": "Datos de forecasting no disponibles"}), 503
    
    if producto not in PREDICCIONES.columns:
        return jsonify({"error": f"Producto '{producto}' no encontrado"}), 404
    
    try:
        preds = PREDICCIONES[producto].values.tolist()
        preds_largo = PREDICCIONES_LARGO[PREDICCIONES_LARGO['Producto_codigo'] == producto]
        
        response = {
            "success": True,
            "producto": producto,
            "predicciones_52_semanas": [round(p, 2) for p in preds],
            "fechas": PREDICCIONES.index.tolist(),
            "intervalos_confianza_95": {
                "lower_bounds": [round(float(x), 2) for x in preds_largo['Lower_Bound_95'].values],
                "upper_bounds": [round(float(x), 2) for x in preds_largo['Upper_Bound_95'].values]
            },
            "contexto_estadistico": {
                "media_historica": round(float(preds_largo.iloc[0]['Media_Historica']), 2) if len(preds_largo) > 0 else 0,
                "std_historica": round(float(preds_largo.iloc[0]['Std_Historica']), 2) if len(preds_largo) > 0 else 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ========================================================================
# ENDPOINT 4: Informacion del modelo
# ========================================================================
@forecasting_bp.route('/forecasting/model-info', methods=['GET'])
def get_model_info():
    """
    GET /api/v1/forecasting/model-info
    
    Retorna informacion sobre el modelo de forecasting
    """
    
    if METADATA is None:
        return jsonify({"error": "Metadata del modelo no disponible"}), 503
    
    try:
        response = {
            "success": True,
            "tipo_modelo": METADATA.get('tipo_modelo', 'N/A'),
            "version": METADATA.get('version', 'N/A'),
            "algoritmo": METADATA.get('algoritmo', 'N/A'),
            "fecha_entrenamiento": METADATA.get('fecha_entrenamiento', 'N/A'),
            "features": METADATA.get('features', {}),
            "performance": METADATA.get('performance', {}),
            "proposito": "Predecir ventas semanales de 20 productos para 52 semanas",
            "total_predicciones": 1040,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ========================================================================
# Inicializar datos al importar
# ========================================================================

def init_forecasting_data():
    """Cargar datos al inicializar el modulo"""
    cargar_datos_forecasting()
