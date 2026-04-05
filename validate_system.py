"""
Validación del sistema MVP
Ejecutar: python validate_system.py
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, '.')

print('="*50')
print('VALIDACION DEL SISTEMA PREDICAST MVP')
print('='*50)
print()

# 1. Verificar archivos modelo existen
print('1. Verificando archivos de modelo...')
# Paths relativos desde 07_Sistema_Produccion
model_file = Path('../03_Modelos/xgboost_model_V2_V2_Realista.joblib')
metadata_file = Path('../03_Modelos/xgboost_metadata_V2_V2_Realista.json')

print(f'   Modelo: {model_file.exists()} ({model_file})')
print(f'   Metadata: {metadata_file.exists()} ({metadata_file})')

if not (model_file.exists() and metadata_file.exists()):
    print('   ERROR: Archivos de modelo no encontrados')
    sys.exit(1)

print()

# 2. Cargar modelo
print('2. Cargando modelo XGBoost...')
try:
    from src.ml.model_loader import ModelLoader
    loader = ModelLoader(str(model_file), str(metadata_file))
    model, metadata = loader.load()
    print(f'   Version: {metadata["model_version"]}')
    print(f'   Features: {metadata["n_features"]}')
    print(f'   R2 Score: {metadata["performance"]["R2_Test"]:.4f}')
except Exception as e:
    print(f'   ERROR: {e}')
    sys.exit(1)

print()

# 3. Test predictor
print('3. Testeando Predictor...')
try:
    from src.ml.predictor import XGBoostPredictor
    predictor = XGBoostPredictor(loader)
    
    test_input = {
        'Stock_anterior': 100,
        'Stock_posterior': 95,
        'Precio_unitario': 150.0,
        'Año': 2026,
        'Mes': 4,
        'Trimestre': 2,
        'Día_Semana': 2,
        'Canal_Promedio_Demanda': 75.0,
        'Campana_Promedio_Demanda': 60.0,
        'Cliente_Promedio_Demanda': 80.0,
        'Producto_Promedio_Demanda': 85.0,
        'Canal_venta_encoded': 0,
        'Campana_encoded': 3,
        'Empresa_cliente_encoded': 0,
        'Producto_codigo_encoded': 0
    }
    
    result = predictor.predict(test_input)
    
    if result.get('status') == 'success':
        print(f'   Prediccion: {result["prediction"]:.2f} unidades')
        print(f'   Confianza: {result["confidence"]:.4f}')
    else:
        print(f'   ERROR: {result.get("error")}')
        sys.exit(1)
        
except Exception as e:
    print(f'   ERROR: {e}')
    sys.exit(1)

print()

# 4. Test DB
print('4. Testeando Database...')
try:
    from src.db.config import init_db, SessionLocal
    from src.db.models import Tenant, User
    init_db()
    print('   BD inicializada (SQLite: predicast.db)')
    
    # Test sesion
    db = SessionLocal()
    db.close()
    print('   Conexion exitosa')
except Exception as e:
    print(f'   ERROR: {e}')
    sys.exit(1)

print()

# 5. Test Auth
print('5. Testeando Auth...')
try:
    from src.utils.auth import TokenManager, hash_password, verify_password
    
    token = TokenManager.create_token('user123', 'tenant456', 'user@test.com', True)
    print(f'   JWT Token creado: OK')
    
    payload = TokenManager.verify_token(token)
    print(f'   Token verificado: {payload["email"]}')
    
    hashed = hash_password('password123')
    verify_ok = verify_password('password123', hashed)
    print(f'   Password hashing: {verify_ok}')
except Exception as e:
    print(f'   ERROR: {e}')
    sys.exit(1)

print()
print('='*50)
print('TODOS LOS TESTS PASARON!')
print('='*50)
print()
print('PROXIMO PASO:')
print('Terminal 1: python run.py api')
print('Terminal 2: python run.py dashboard')
print()
