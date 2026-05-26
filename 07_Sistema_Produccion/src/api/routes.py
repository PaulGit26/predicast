"""
API Routes
Endpoints para predicción, auth, model info
"""

import logging
from datetime import datetime, timedelta
from flask import jsonify, request, current_app
from functools import wraps
import os
from src.utils.auth import TokenManager
from src.db.config import SessionLocal
from src.db.models import Tenant, User, Prediction, ModelMetadata
from src.utils.auth import hash_password, verify_password

logger = logging.getLogger(__name__)


def create_routes(app):
    """Registra todas las rutas en la app"""
    
    # ============================================
    # MIDDLEWARE: JWT Authentication
    # ============================================
    def token_required(f):
        """Decorator para endpoints que requieren autenticación"""
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            # Obtener token del header
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                try:
                    token = auth_header.split(" ")[1]
                except IndexError:
                    return jsonify({"error": "Invalid token format"}), 401
            
            if not token:
                return jsonify({"error": "Token is missing"}), 401
            
            try:
                # Verificar token
                payload = TokenManager.verify_token(token)
                request.user_id = payload['user_id']
                request.tenant_id = payload['tenant_id']
                request.email = payload['email']
                request.is_admin = payload.get('is_admin', False)
            except Exception as e:
                logger.warning(f"⚠️ Token verification failed: {e}")
                return jsonify({"error": "Invalid token"}), 401
            
            return f(*args, **kwargs)
        return decorated
    
    
    # ============================================
    # AUTH ENDPOINTS
    # ============================================
    @app.route("/api/v1/auth/register", methods=["POST"])
    def register():
        """Registrar nueva empresa y usuario"""
        try:
            data = request.get_json()
            
            # Validar campos
            required = ['empresa_name', 'email', 'password']
            for field in required:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}), 400
            
            db = SessionLocal()
            
            # Verificar si empresa existe
            existing_tenant = db.query(Tenant).filter_by(name=data['empresa_name']).first()
            if existing_tenant:
                return jsonify({"error": "Enterprise already exists"}), 409
            
            # Verificar si email existe
            existing_user = db.query(User).filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({"error": "Email already registered"}), 409
            
            # Crear tenant
            tenant = Tenant(name=data['empresa_name'])
            db.add(tenant)
            db.flush()  # Para obtener el ID
            
            # Crear usuario
            user = User(
                tenant_id=tenant.id,
                email=data['email'],
                password_hash=hash_password(data['password']),
                full_name=data.get('full_name', ''),
                is_admin=True  # Primer usuario es admin
            )
            db.add(user)
            db.commit()
            
            # Crear token
            token = TokenManager.create_token(
                user_id=user.id,
                tenant_id=tenant.id,
                email=user.email,
                is_admin=True
            )
            
            logger.info(f"✅ Nueva empresa registrada: {tenant.name}")
            
            return jsonify({
                "status": "success",
                "message": "Enterprise registered successfully",
                "tenant_id": tenant.id,
                "user_id": user.id,
                "token": token
            }), 201
            
        except Exception as e:
            logger.error(f"❌ Register error: {e}")
            return jsonify({"error": str(e), "status": "error"}), 500
        finally:
            db.close()
    
    
    @app.route("/api/v1/auth/login", methods=["POST"])
    def login():
        """Login de usuario"""
        try:
            data = request.get_json()
            
            if not data.get('email') or not data.get('password'):
                return jsonify({"error": "Missing email or password"}), 400
            
            db = SessionLocal()
            
            # Buscar usuario
            user = db.query(User).filter_by(email=data['email']).first()
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            # Verificar contraseña
            if not verify_password(data['password'], user.password_hash):
                return jsonify({"error": "Invalid password"}), 401
            
            if not user.is_active:
                return jsonify({"error": "User is inactive"}), 403
            
            # Crear token
            token = TokenManager.create_token(
                user_id=user.id,
                tenant_id=user.tenant_id,
                email=user.email,
                is_admin=user.is_admin
            )
            
            logger.info(f"✅ Login exitoso: {user.email}")
            
            return jsonify({
                "status": "success",
                "token": token,
                "tenant_id": user.tenant_id,
                "is_admin": user.is_admin
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return jsonify({"error": str(e), "status": "error"}), 500
        finally:
            db.close()
    
    
    # ============================================
    # MODEL INFO ENDPOINTS
    # ============================================
    @app.route("/api/v1/model/info", methods=["GET"])
    @token_required
    def model_info():
        """Información del modelo"""
        if not current_app.predictor:
            return jsonify({"error": "Model not loaded"}), 503
        
        try:
            info = current_app.predictor.get_model_info()
            return jsonify({
                "status": "success",
                "model": info
            }), 200
        except Exception as e:
            logger.error(f"❌ Error obteniendo info: {e}")
            return jsonify({"error": str(e)}), 500
    
    
    # ============================================
    # PREDICTION ENDPOINTS
    # ============================================
    @app.route("/api/v1/predict", methods=["POST"])
    @token_required
    def predict():
        """Hacer predicción individual"""
        if not current_app.predictor:
            return jsonify({"error": "Model not loaded"}), 503
        
        db = None
        try:
            data = request.get_json()
            
            # Hacer predicción
            result = current_app.predictor.predict(data)
            
            if result.get("status") == "error":
                return jsonify(result), 400
            
            # Guardar predicción en BD (multi-tenancy)
            db = SessionLocal()
            prediction = Prediction(
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                stock_anterior=data.get('Stock_anterior'),
                stock_posterior=data.get('Stock_posterior'),
                precio_unitario=data.get('Precio_unitario'),
                año=data.get('Año'),
                mes=data.get('Mes'),
                trimestre=data.get('Trimestre'),
                dia_semana=data.get('Día_Semana'),
                canal_venta_encoded=data.get('Canal_venta_encoded'),
                campana_encoded=data.get('Campana_encoded'),
                empresa_cliente_encoded=data.get('Empresa_cliente_encoded'),
                producto_codigo_encoded=data.get('Producto_codigo_encoded'),
                predicted_quantity=result['prediction'],
                confidence=result['confidence'],
                model_version=result['model_version']
            )
            db.add(prediction)
            db.commit()
            
            logger.info(f"✅ Predicción guardada: {prediction.id}")
            
            return jsonify({
                "status": "success",
                "prediction": result['prediction'],
                "confidence": result['confidence'],
                "mae_test": result['mae_test'],
                "model_version": result['model_version'],
                "target": result['target'],
                "input_features": result['input_features'],
                "prediction_id": prediction.id,
                "tenant_id": request.tenant_id,
                "timestamp": datetime.utcnow().isoformat()
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            return jsonify({"error": str(e), "status": "error"}), 500
        finally:
            if db:
                db.close()
    
    
    @app.route("/api/v1/predict/batch", methods=["POST"])
    @token_required
    def predict_batch():
        """Hacer predicciones en batch"""
        if not current_app.predictor:
            return jsonify({"error": "Model not loaded"}), 503
        
        db = None
        try:
            data_list = request.get_json()
            
            if not isinstance(data_list, list):
                return jsonify({"error": "Expected list of predictions"}), 400
            
            # Hacer predicciones
            results = current_app.predictor.predict_batch(data_list)
            
            # Guardar en BD
            db = SessionLocal()
            prediction_ids = []
            
            for data, result in zip(data_list, results):
                if result.get("status") == "success":
                    prediction = Prediction(
                        tenant_id=request.tenant_id,
                        user_id=request.user_id,
                        predicted_quantity=result['prediction'],
                        confidence=result['confidence'],
                        model_version=result['model_version']
                    )
                    db.add(prediction)
                    prediction_ids.append(prediction.id)
            
            db.commit()
            logger.info(f"✅ {len(prediction_ids)} predicciones guardadas en batch")
            
            return jsonify({
                "status": "success",
                "predictions": results,
                "saved": len(prediction_ids),
                "timestamp": datetime.utcnow().isoformat()
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Batch prediction error: {e}")
            return jsonify({"error": str(e), "status": "error"}), 500
        finally:
            if db:
                db.close()
    
    
    # ============================================
    # HISTORY ENDPOINTS
    # ============================================
    @app.route("/api/v1/predictions", methods=["GET"])
    @token_required
    def get_predictions():
        """Obtener historial de predicciones del tenant"""
        try:
            db = SessionLocal()
            
            # Query con filtro de tenant (multi-tenancy)
            predictions = db.query(Prediction)\
                .filter_by(tenant_id=request.tenant_id)\
                .order_by(Prediction.created_at.desc())\
                .limit(100)\
                .all()
            
            result = [
                {
                    "id": p.id,
                    "prediction": p.predicted_quantity,
                    "confidence": p.confidence,
                    "created_at": p.created_at.isoformat(),
                    "model_version": p.model_version
                }
                for p in predictions
            ]
            
            return jsonify({
                "status": "success",
                "count": len(result),
                "predictions": result
            }), 200
            
        except Exception as e:
            logger.error(f"❌ History error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    
    
    # ============================================
    # USER MANAGEMENT ENDPOINTS (ADMIN ONLY)
    # ============================================
    @app.route("/api/v1/users", methods=["POST"])
    @token_required
    def create_user():
        """Crear nuevo usuario en la empresa (admin only)"""
        if not request.is_admin:
            return jsonify({"error": "Only admins can create users"}), 403
        
        try:
            data = request.get_json()
            required = ['email', 'password', 'full_name']
            for field in required:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}), 400
            
            db = SessionLocal()
            
            # Verificar si email ya existe en esta empresa
            existing = db.query(User).filter_by(
                tenant_id=request.tenant_id,
                email=data['email']
            ).first()
            if existing:
                return jsonify({"error": "Email already exists in this enterprise"}), 409
            
            # Crear usuario
            user = User(
                tenant_id=request.tenant_id,
                email=data['email'],
                password_hash=hash_password(data['password']),
                full_name=data['full_name'],
                is_admin=data.get('is_admin', False),
                is_active=True
            )
            db.add(user)
            db.commit()
            
            logger.info(f"✅ Nuevo usuario creado: {user.email}")
            
            return jsonify({
                "status": "success",
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_admin": user.is_admin
            }), 201
            
        except Exception as e:
            logger.error(f"❌ Create user error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    
    
    @app.route("/api/v1/users", methods=["GET"])
    @token_required
    def list_users():
        """Listar usuarios de la empresa (admin only)"""
        if not request.is_admin:
            return jsonify({"error": "Only admins can list users"}), 403
        
        try:
            db = SessionLocal()
            users = db.query(User).filter_by(
                tenant_id=request.tenant_id,
                is_active=True
            ).all()
            
            result = [
                {
                    "user_id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                    "is_admin": u.is_admin,
                    "created_at": u.created_at.isoformat()
                }
                for u in users
            ]
            
            return jsonify({
                "status": "success",
                "count": len(result),
                "users": result
            }), 200
            
        except Exception as e:
            logger.error(f"❌ List users error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    
    
    @app.route("/api/v1/users/<user_id>", methods=["DELETE"])
    @token_required
    def delete_user(user_id):
        """Desactivar usuario (admin only)"""
        if not request.is_admin:
            return jsonify({"error": "Only admins can delete users"}), 403
        
        try:
            db = SessionLocal()
            user = db.query(User).filter_by(
                id=user_id,
                tenant_id=request.tenant_id
            ).first()
            
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            user.is_active = False
            db.commit()
            
            logger.info(f"✅ Usuario desactivado: {user.email}")
            
            return jsonify({
                "status": "success",
                "message": "User deactivated"
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Delete user error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
    
    
    @app.route("/api/v1/me", methods=["GET"])
    @token_required
    def get_current_user():
        """Obtener info del usuario actual"""
        try:
            db = SessionLocal()
            user = db.query(User).filter_by(id=request.user_id).first()
            tenant = db.query(Tenant).filter_by(id=request.tenant_id).first()
            
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            return jsonify({
                "status": "success",
                "user": {
                    "user_id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_admin": user.is_admin,
                    "tenant_id": tenant.id,
                    "tenant_name": tenant.name
                }
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Get current user error: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            db.close()
