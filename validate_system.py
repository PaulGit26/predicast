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
print('1. Verificando archivos de predicciones y scripts (01_Datos, 01_Datos_Nuevos, 04_Scripts_Nuevos)')

# Verificar CSVs finales en 01_Datos
base_path = Path(__file__).resolve().parent
pred_pivot = base_path / "01_Datos" / "predicciones_52semanas_pivot_V4.csv"
pred_largo = base_path / "01_Datos" / "predicciones_52semanas_largo_V4.csv"
metadata_json = base_path / "01_Datos" / "predicciones_52semanas_METADATA_V4.json"

print(f'   predicciones_pivot: {pred_pivot.exists()} ({pred_pivot})')
print(f'   predicciones_largo: {pred_largo.exists()} ({pred_largo})')
print(f'   metadata_json: {metadata_json.exists()} ({metadata_json})')

missing = []
if not pred_pivot.exists():
    missing.append(str(pred_pivot))
if not pred_largo.exists():
    missing.append(str(pred_largo))
if not metadata_json.exists():
    missing.append(str(metadata_json))

if missing:
    print('   ERROR: Faltan archivos de predicciones finales. Faltan:')
    for m in missing:
        print('    -', m)
    sys.exit(1)

print()

# 2. Cargar modelo
print('2. Verificando scripts de procesamiento en 04_Scripts_Nuevos (02_... -> 10_...)')
scripts_dir = Path('04_Scripts_Nuevos')
required_prefixes = [
    '02_PREPARAR_DATA_ESPECIFICO',
    '03_ANALISIS_PARETO',
    '04_AGREGACION_SEMANAL_Y_FEATURES',
    '05_SELECCION_FILTRADO_FEATURES',
    '08_OPTIMIZACION_HIPERPARAMETROS_PRODUCCION',
    '10_PREDICCIONES_FINAL_PRODUCCION'
]

found = {p: False for p in required_prefixes}
if scripts_dir.exists():
    for f in scripts_dir.iterdir():
        name = f.name.upper()
        for pref in required_prefixes:
            if name.startswith(pref):
                found[pref] = True

for k, v in found.items():
    print(f'   {k}:', 'OK' if v else 'MISSING')

if not all(found.values()):
    print('   ERROR: Faltan scripts críticos en 04_Scripts_Nuevos. Verifica el pipeline de procesamiento.')
    sys.exit(1)

print()

# 3. Test predictor
print('3. Validación rápida de salida de predicciones (muestreo)')
try:
    import pandas as pd
    df = pd.read_csv(pred_largo)
    sample = df.head(1)
    if sample.empty:
        print('   ERROR: predicciones_largo está vacío')
        sys.exit(1)
    else:
        print('   Predicciones largo: OK - filas=', len(df))
except Exception as e:
    print(f'   ERROR leyendo predicciones: {e}')
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
