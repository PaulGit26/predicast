# PREDICAST MVP - GUÍA DE INICIO RÁPIDO

## ✅ Estado Actual

```
✅ Estructura escalable creada
✅ Modelo XGBoost integrado (94.43% R²)
✅ API Flask funcional
✅ Dashboard Streamlit listo
✅ Multi-tenancy desde día 1
✅ Autenticación JWT
✅ Base de datos con SQLAlchemy
```

### Validación de Componentes
```
✅ Modelo: CARGADO (V2_V2_Realista)
✅ Features: 15 features optimizadas
✅ Predicción test: 32.26 unidades (exitosa)
✅ Confianza: 94.43%
```

---

## 🚀 InstalaciónRápida (5 minutos)

### Opción 1: Instalación Manual

```bash
# 1. Navegar a carpeta
cd 07_Sistema_Produccion

# 2. Crear virtual environment
python -m venv venv
.\venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar y editar .env
copy .env.example .env

# 5. Ejecutar validación
python validate_system.py
```

### Opción 2: Script Automático (TODO)

```bash
python setup.py
```

### Opción 3: Docker (Futura)

```bash
docker-compose up
```

---

## ▶️ Ejecutar el Sistema

### Terminal 1 - API Backend (puerto 5000)

```bash
cd 07_Sistema_Produccion
.\venv\Scripts\activate
python run.py api
```

Verás:
```
* Running on http://0.0.0.0:5000
```

### Terminal 2 - Dashboard Frontend (puerto 8501)

```bash
cd 07_Sistema_Produccion
.\venv\Scripts\activate
python run.py dashboard
```

Abrirá automáticamente en `http://localhost:8501`

---

## 📊 Primera Vez: Workflow

### 1. Registrar Empresa

En Dashboard:
- Selecciona "Registrarse"
- Ingresa:
  - Nombre empresa: `Mi Constructora`
  - Email: `admin@miempresa.com`
  - Contaseña: `password123`

Sistema automaticamente:
- ✅ Crea empresa en BD
- ✅ Crea usuario administrador
- ✅ Genera JWT token
- ✅ Inicia sesión

### 2. Hacer Predicción

En tab "Predicción":
- Ingresa datos del producto
- Click "Obtener Predicción"
- Ves resultado: `32.26 unidades`

Sistema automáticamente:
- ✅ Prepara features
- ✅ Ejecuta XGBoost
- ✅ Guarda en BD (multi-tenancy)
- ✅ Retorna confianza

### 3. Ver Historial

En tab "Historial":
- Click "Recargar historial"
- Ves todas tus predicciones
- Gráfico de tendencia

---

## 🔧 API (para integración)

### Test con CURL

```bash
# 1. Registrar
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "empresa_name": "Test Company",
    "email": "test@company.com",
    "password": "pass123"
  }'

# Respuesta incluye: token, tenant_id

# 2. Hacer predicción (usar token de respuesta anterior)

curl -X POST http://localhost:5000/api/v1/predict \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "Stock_anterior": 100,
    "Stock_posterior": 95,
    "Precio_unitario": 150,
    "Año": 2026,
    "Mes": 4,
    "Trimestre": 2,
    "Día_Semana": 2,
    "Canal_Promedio_Demanda": 75,
    "Campana_Promedio_Demanda": 60,
    "Cliente_Promedio_Demanda": 80,
    "Producto_Promedio_Demanda": 85,
    "Canal_venta_encoded": 0,
    "Campana_encoded": 3,
    "Empresa_cliente_encoded": 0,
    "Producto_codigo_encoded": 0
  }'

# Respuesta:
# {
#   "status": "success",
#   "prediction": 32.26,
#   "prediction_id": "...",
#   "tenant_id": "...",
#   "timestamp": "2026-04-04T..."
# }
```

---

## 📁 Estructura Creada

```
07_Sistema_Produccion/
├── src/
│   ├── ml/                 ← XGBoost predictor
│   ├── api/                ← Flask endpoints
│   ├── ui/                 ← Streamlit dashboard
│   ├── db/                 ← SQLAlchemy models
│   ├── utils/              ← Auth, constants
│   └── data/               ← Data processing (future)
├── tests/                  ← Unit tests
├── validate_system.py      ← Validar todo funciona
├── run.py                  ← Script para ejecutar
├── requirements.txt        ← Dependencias
├── .env.example           ← Variables entorno
└── README.md              ← Documentación completa
```

---

## 🔐 Multi-Tenancy (Implementado Día 1)

### Cómo Funciona

```python
# 1. Usuario registra empresa
POST /auth/register
→ Crear Tenant + User

# 2. Sistema retorna JWT con tenant_id
{
  "token": "eyJhbGc...",
  "tenant_id": "abc-123-def"
}

# 3. Cada request incluye token
Authorization: Bearer <token>

# 4. Middleware automaticamente:
- Extrae tenant_id del JWT
- Filtra queries por tenant_id
- Aísla datos por empresa

# 5. Resultado: Datos completamente aislados
```

### Agregar Nueva Empresa

```bash
# Es simple: otro registro
curl -X POST http://localhost:5000/api/v1/auth/register \
  -d '{"empresa_name": "New Corp", ...}'

# Cada empresa tiene su próprio:
- JWT token
- Datos en BD (aislados)
- Modelos (inicialmente compartido)
```

---

## 📈 Performance del Modelo

```
Performance Metrics:
├─ R² Score:       94.43%     (muy bueno)
├─ MAE:            0.76 unid  (error prom)
├─ RMSE:           1.41 unid
├─ Features:       15
├─ Training set:   156,508 muestras
├─ Validation:     39,127 muestras
└─ Inference:      <50ms típico
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
python run.py tests

# Output:
# ✅ test_model_loading PASSED
# ✅ test_model_metadata_validation PASSED
# ✅ test_prediction_valid_input PASSED
# ✅ test_prediction_missing_feature PASSED
# ✅ test_batch_prediction PASSED
```

---

## 📝 TODO - Próximas Semanas

### Semana 2: Dashboard Mejorado
- [ ] Upload CSV en batch
- [ ] Gráficos de tendencias
- [ ] Export a Excel
- [ ] Notificaciones

### Semana 3: Multi-Tenancy Completo
- [ ] Per-empresa models
- [ ] Model selector
- [ ] Admin panel
- [ ] User management

### Semana 4: Production Ready
- [ ] Deploy a Render.com
- [ ] Monitoring (logs, errors)
- [ ] Load testing
- [ ] Primeros clientes pagos

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'sqlalchemy'"

```bash
# Solución: Instalar paquetes
pip install -r requirements.txt

# O instalar uno por uno:
pip install flask flask-cors flask-jwt-extended
pip install sqlalchemy alembic
pip install streamlit plotly
pip install xgboost numpy pandas
```

### "Connection refused" en http://localhost:5000

```bash
# Verificar que API está corriendo:
python run.py api

# Debe mostrar:
# * Running on http://0.0.0.0:5000
```

### "Model not found"

```bash
# Verificar rutas en .env
MODEL_PATH=../03_Modelos/xgboost_model_V2_V2_Realista.joblib
METADATA_PATH=../03_Modelos/xgboost_metadata_V2_V2_Realista.json

# Deben existir:
# D:\Desktop\Predicast\03_Modelos\xgboost_model_V2_V2_Realista.joblib ✅
# D:\Desktop\Predicast\03_Modelos\xgboost_metadata_V2_V2_Realista.json ✅
```

---

## 📞 Soporte

- 🐛 **Bugs**: Check README.md
- 💬 **Chat**: Predicast Slack
- 📧 **Email**: tech@predicast.dev

---

## 🎉 ¡Listo!

El sistema MVP está completamente funcional.

**Próximo paso:**

```bash
# Terminal 1
python run.py api

# Terminal 2
python run.py dashboard

# Luego abre: http://localhost:8501
```

¡Disfruta! 🚀
