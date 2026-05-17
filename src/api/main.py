"""
API Flask - MVP Backend
Multi-tenancy ready
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

# Cargar variables de entorno antes que todo
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.info(f"📂 Cargando .env desde: {env_path}")

# Importar módulos
from src.db.config import init_db, get_db
from src.utils.auth import TokenManager
from .routes import create_routes
from .forecasting_routes import forecasting_bp, init_forecasting_data

# ============================================
# Inicializar Flask
# ============================================
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# CORS habilitado para desarrollo
CORS(app, resources={r"/api/*": {"origins": "*"}})

# NOTE: El sistema usa predicciones precalculadas en CSVs dentro de `01_Datos`.
# Históricamente existía carga de modelo (.joblib) pero el flujo actual toma
# las predicciones resultantes generadas por los scripts de `04_Scripts_Nuevos`.
app.predictor = None


# ============================================
# Inicializar BD
# ============================================
@app.before_request
def before_request():
    """Ejecutar antes de cada request"""
    pass


@app.teardown_appcontext
def teardown_db(exception):
    """Cerrar sesión de BD"""
    pass


# ============================================
# Error handlers
# ============================================
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "status": 400}), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized", "status": 401}), 401


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "status": 404}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {error}")
    return jsonify({"error": "Internal Server Error", "status": 500}), 500


# ============================================
# Routes básicas
# ============================================
@app.route("/", methods=["GET"])
def index():
    """Health check y info"""
    return jsonify({
        "name": "PREDICAST API",
        "version": "0.2.0",
        "status": "🟢 online",
        "model_loaded": predictor is not None,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "GET /health",
            "model_info": "GET /api/v1/model/info",
            "predict": "POST /api/v1/predict",
            "batch_predict": "POST /api/v1/predict/batch",
            "forecasting_52weeks": "GET /api/v1/forecasting/52weeks/<producto>",
            "forecasting_all": "GET /api/v1/forecasting/all-products",
            "forecasting_detailed": "GET /api/v1/forecasting/product/<producto>/detailed",
            "forecasting_model_info": "GET /api/v1/forecasting/model-info",
            "register": "POST /api/v1/auth/register",
            "login": "POST /api/v1/auth/login"
        }
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "model": "ready" if predictor else "not_loaded",
        "timestamp": datetime.utcnow().isoformat()
    })


# ============================================
# Registrar routes desde módulo
# ============================================
create_routes(app)
app.register_blueprint(forecasting_bp)

# ============================================
# Inicializar datos al crear la app
# ============================================
init_db()
init_forecasting_data()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
    app.run(
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 5000)),
        debug=os.getenv("DEBUG", "True").lower() == "true"
    )
