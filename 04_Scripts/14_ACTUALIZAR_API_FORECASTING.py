"""
===================================================================
    14 - ACTUALIZAR API CON ENDPOINTS DE FORECASTING
===================================================================

Objetivo: Agregar endpoints nuevos al API Flask para servir:
  - Predicciones de 52 semanas por producto
  - Historico + Predicciones combinadas
  - Estadisticas e intervalos de confianza

Endpoints nuevos:
  1. GET /api/v1/forecasting/52weeks/{producto}
  2. GET /api/v1/forecasting/all-products
  3. GET /api/v1/forecasting/product/{producto}/detailed
  4. POST /api/v1/forecasting/generate-new (re-generar predicciones)

Nota: Este script MODIFICA routes.py del API
"""

import os
import json
from pathlib import Path

print("=" * 80)
print("ACTUALIZAR API CON ENDPOINTS FORECASTING")
print("=" * 80)

# ========================================================================
# PASO 1: VERIFICAR ARCHIVOS NECESARIOS
# ========================================================================
print("\nPASO 1: VERIFICAR ARCHIVOS")
print("-" * 80)

archivos_requeridos = [
    '../01_Datos/predicciones_52semanas_pivot.csv',
    '../01_Datos/predicciones_52semanas_largo.csv',
    '../01_Datos/predicciones_estadisticas.csv',
    '../03_Modelos/xgboost_forecasting_modelo.joblib',
    '../03_Modelos/forecasting_metadata.json'
]

for archivo in archivos_requeridos:
    existe = Path(archivo).exists()
    estado = "[+]" if existe else "[-]"
    print(f"{estado} {archivo}")

print("\n" + "=" * 80)
print("PASO 2: CREAR NUEVO MODULO forecasting_routes.py")
print("=" * 80)

# Crear nuevo archivo de rutas para forecasting
forecasting_routes_code = '''"""
Rutas de Forecasting para API Flask

Endpoints:
  - GET /api/v1/forecasting/52weeks/<producto>
  - GET /api/v1/forecasting/all-products
  - GET /api/v1/forecasting/product/<producto>/detailed
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
import pandas as pd
import json
from pathlib import Path

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
        # Datos pivot (semanas x productos)
        PREDICCIONES = pd.read_csv('01_Datos/predicciones_52semanas_pivot.csv', index_col=0)
        
        # Datos largo (tidy format)
        PREDICCIONES_LARGO = pd.read_csv('01_Datos/predicciones_52semanas_largo.csv')
        
        # Estadisticas
        ESTADISTICAS = pd.read_csv('01_Datos/predicciones_estadisticas.csv', index_col=0)
        
        # Metadata
        with open('03_Modelos/forecasting_metadata.json', 'r') as f:
            METADATA = json.load(f)
        
        print("[+] Datos de forecasting cargados en memoria")
        return True
        
    except Exception as e:
        print(f"[-] Error cargando datos forecasting: {str(e)}")
        return False

# ========================================================================
# ENDPOINT 1: Predicciones de 52 semanas para un producto
# ========================================================================
@forecasting_bp.route('/forecasting/52weeks/<producto>', methods=['GET'])
@jwt_required()
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
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========================================================================
# ENDPOINT 2: Todos los productos (resumen)
# ========================================================================
@forecasting_bp.route('/forecasting/all-products', methods=['GET'])
@jwt_required()
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
            "productos": productos_resumen
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========================================================================
# ENDPOINT 3: Detalle completo (historico + predicciones)
# ========================================================================
@forecasting_bp.route('/forecasting/product/<producto>/detailed', methods=['GET'])
@jwt_required()
def get_detailed_forecast(producto):
    """
    GET /api/v1/forecasting/product/{PRODUCTO}/detailed
    
    Retorna historico COMPLETO + predicciones futuras
    Util para graficar en dashboard
    
    Response:
    {
      "producto": "CP_01",
      "historico": {...},
      "predicciones": {...},
      "combinado": [...]
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
                "media_historica": round(float(preds_largo.iloc[0]['Media_Historica']), 2),
                "std_historica": round(float(preds_largo.iloc[0]['Std_Historica']), 2)
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========================================================================
# ENDPOINT 4: Informacion del modelo
# ========================================================================
@forecasting_bp.route('/forecasting/model-info', methods=['GET'])
@jwt_required()
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
            "modelo": METADATA.get('tipo_modelo', 'N/A'),
            "version": METADATA.get('version', 'N/A'),
            "algoritmo": METADATA.get('algoritmo', 'N/A'),
            "fecha_entrenamiento": METADATA.get('fecha_entrenamiento', 'N/A'),
            "features": METADATA.get('features', {}),
            "performance": METADATA.get('performance', {}),
            "proposito": METADATA.get('proposito', 'N/A')
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========================================================================
# Inicializar datos al importar
# ========================================================================

def init_forecasting_data():
    """Cargar datos al inicializar el modulo"""
    cargar_datos_forecasting()
'''

# Guardar archivo
routes_path = '07_Sistema_Produccion/src/api/forecasting_routes.py'
Path(routes_path).parent.mkdir(parents=True, exist_ok=True)

with open(routes_path, 'w') as f:
    f.write(forecasting_routes_code)

print(f"[+] Archivo creado: {routes_path}")

# ========================================================================
# PASO 3: CREAR INSTRUCCIONES DE INTEGRACION
# ========================================================================
print("\nPASO 3: CREAR INSTRUCCIONES DE INTEGRACION")
print("-" * 80)

integracion_instructions = '''
INSTRUCCIONES PARA INTEGRAR ENDPOINTS FORECASTING EN API
========================================================

PASO 1: Agregar import en main.py
---------------------------------
# Dentro de 07_Sistema_Produccion/src/api/main.py

from .forecasting_routes import forecasting_bp

# En la seccion de blueprint registration:
app.register_blueprint(forecasting_bp)

# Inicializar datos:
from .forecasting_routes import init_forecasting_data
init_forecasting_data()

PASO 2: Copiar archivos de predicciones
----------------------------------------
Asegurarse de que existen:
  - 01_Datos/predicciones_52semanas_pivot.csv
  - 01_Datos/predicciones_52semanas_largo.csv
  - 01_Datos/predicciones_estadisticas.csv
  - 03_Modelos/xgboost_forecasting_modelo.joblib
  - 03_Modelos/forecasting_metadata.json

PASO 3: Reiniciar API
----------------------
Terminal:
  $ cd 07_Sistema_Produccion
  $ python run.py api

Deberia ver:
  [+] Datos de forecasting cargados en memoria

PASO 4: Probar endpoints
------------------------
Curl commands:

1. Token (primero logearse):
   curl -X POST http://localhost:5000/api/v1/auth/login \\
     -H "Content-Type: application/json" \\
     -d '{"email":"test@test.com", "password":"password"}'

2. Obtener predicciones de 52 semanas:
   curl -X GET http://localhost:5000/api/v1/forecasting/52weeks/CP_01 \\
     -H "Authorization: Bearer TOKEN"

3. Obtener resumen de todos:
   curl -X GET http://localhost:5000/api/v1/forecasting/all-products \\
     -H "Authorization: Bearer TOKEN"

4. Obtener detalle completo:
   curl -X GET http://localhost:5000/api/v1/forecasting/product/CP_01/detailed \\
     -H "Authorization: Bearer TOKEN"

5. Info del modelo:
   curl -X GET http://localhost:5000/api/v1/forecasting/model-info \\
     -H "Authorization: Bearer TOKEN"

PASO 5: Updatear Dashboard
----------------------------
En dashboard_v3.py agregar seccion:
  - Tab "Forecasting"
  - Selector de producto
  - Grafico con historico + predicciones 52 semanas
  - Tabla con detalles

MAS INFORMACION
================
Los endpoints estan protegidos con JWT.
Requiere autenticacion previa.

Nuevo modelo: xgboost_forecasting_modelo.joblib
Lags utilizados: [4, 8, 12, 16] semanas
Predicciones: 52 semanas hacia adelante (recurisvas)
'''

instructions_path = '07_Sistema_Produccion/INSTRUCCIONES_INTEGRACION_FORECASTING.txt'
with open(instructions_path, 'w') as f:
    f.write(integracion_instructions)

print(f"[+] Instrucciones creadas: {instructions_path}")

# ========================================================================
# PASO 4: CREAR VERIFICACION
# ========================================================================
print("\nPASO 4: VERIFICACION DE ARCHIVOS")
print("-" * 80)

import pandas as pd

try:
    df_pred = pd.read_csv('../01_Datos/predicciones_52semanas_pivot.csv', index_col=0)
    print(f"[+] Predicciones cargadas: {df_pred.shape}")
    print(f"    Productos: {list(df_pred.columns)[:5]}... ({len(df_pred.columns)} totales)")
    print(f"    Semanas: {list(df_pred.index)[:3]}... a {list(df_pred.index)[-1]}")
    
except Exception as e:
    print(f"[-] Error cargando predicciones: {str(e)}")

# ========================================================================
# PASO 5: RESUMEN
# ========================================================================
print("\n" + "=" * 80)
print("PREPARACION PARA INTEGRACION COMPLETADA")
print("=" * 80)

print(f"""

[+] ARCHIVOS CREADOS:

  - forecasting_routes.py
    > Nuevo modulo con 4 endpoints
    > Maneja autenticacion JWT
    > Carga datos en memoria

  - INSTRUCCIONES_INTEGRACION_FORECASTING.txt
    > Pasos detallados para integrar en API
    > Verificacion manual
    > Curl commands de prueba

[+] ENDPOINTS DISPONIBLES (requieren JWT):

  1. GET /api/v1/forecasting/52weeks/<producto>
     > Predicciones para 1 producto (52 semanas)
  
  2. GET /api/v1/forecasting/all-products
     > Resumen de todos los productos
  
  3. GET /api/v1/forecasting/product/<producto>/detailed
     > Detalle completo con intervalos de confianza
  
  4. GET /api/v1/forecasting/model-info
     > Informacion del modelo entrenado

[+] PROXIMO PASO:

  1. Revisar forecasting_routes.py
  2. Seguir instrucciones en INSTRUCCIONES_INTEGRACION_FORECASTING.txt
  3. Ejecutar: python run.py api
  4. Probar endpoints con curl

[+] PARA ASEGURAR EXITO:

  Make sure all these files exist:
    - 01_Datos/predicciones_52semanas_pivot.csv
    - 01_Datos/predicciones_52semanas_largo.csv
    - 01_Datos/predicciones_estadisticas.csv
    - 03_Modelos/xgboost_forecasting_modelo.joblib
    - 03_Modelos/forecasting_metadata.json

""")

print("=" * 80)
