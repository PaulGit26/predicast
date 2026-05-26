# PREDICAST MVP - Sistema Escalable de Predicción de Demanda

## 📋 Descripción

Sistema híbrido (Streamlit + Flask + XGBoost) para predicción inteligente de demanda de productos manufacturados. 

**Estado:** MVP - Semana 1 Setup ✅

### Características MVP 🎯

- ✅ Modelo XGBoost integrado (94.3% accuracy)
- ✅ API Flask con endpoints REST
- ✅ Dashboard Streamlit
- ✅ Multi-tenancy ready (JWT + Row-level security)
- ✅ Base de datos escalable
- ✅ Autenticación usuario/empresa

---

## 🚀 Inicio Rápido

### 1. Setup (5 minutos)

```bash
# Clonar / descargar proyecto
cd 07_Sistema_Produccion

# Crear virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Copiar .env
copy .env.example .env
```

### 2. Configurar .env

```bash
# .env
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=tu-secret-key
JWT_SECRET=tu-jwt-secret

# Rutas del modelo (relativas a 07_Sistema_Produccion/)
MODEL_PATH=../../03_Modelos/xgboost_model_V2_V2_Realista.joblib
METADATA_PATH=../../03_Modelos/xgboost_metadata_V2_V2_Realista.json

# BD: SQLite para desarrollo
DATABASE_URL=sqlite:///predicast.db
```

### 3. Ejecutar Sistema

**Terminal 1 - API Backend:**
```bash
cd 07_Sistema_Produccion
python -m src.api.main
```
→ API disponible en `http://localhost:5000`

**Terminal 2 - Dashboard Streamlit:**
```bash
cd 07_Sistema_Produccion
streamlit run src/ui/dashboard.py
```
→ Dashboard en `http://localhost:8501`

---

## 📁 Estructura del Proyecto

```
07_Sistema_Produccion/
├── src/
│   ├── ml/                    # Machine Learning
│   │   ├── model_loader.py    # Carga modelo + metadata
│   │   └── predictor.py       # XGBoost wrapper
│   ├── api/                   # Flask API
│   │   ├── main.py            # App Flask + config
│   │   └── routes.py          # Endpoints
│   ├── ui/                    # Streamlit Dashboard
│   │   └── dashboard.py       # UI app
│   ├── db/                    # Database
│   │   ├── config.py          # Conexión + sesión
│   │   └── models.py          # SQLAlchemy models
│   ├── data/                  # Data processing (future)
│   ├── utils/                 # Utilidades
│   │   ├── auth.py            # JWT + hashing
│   │   └── constants.py       # Enums + encodings
│   └── __init__.py
├── tests/                     # Tests unitarios
│   └── test_predictor.py      # Tests del modelo
├── requirements.txt           # Dependencias
├── .env.example              # Variables de entorno
└── README.md                 # Este archivo
```

---

## 🔌 API Endpoints

### Auth

```bash
# Registrar empresa
POST /api/v1/auth/register
{
  "empresa_name": "Mi Constructora",
  "email": "admin@constructor.com",
  "password": "securepass123",
  "full_name": "Juan Pérez"
}

# Login
POST /api/v1/auth/login
{
  "email": "admin@constructor.com",
  "password": "securepass123"
}
```

### Predicción

```bash
# Predicción individual
POST /api/v1/predict
Authorization: Bearer <token>
{
  "Stock_anterior": 100,
  "Stock_posterior": 95,
  "Precio_unitario": 150.0,
  "Año": 2026,
  "Mes": 4,
  "Trimestre": 2,
  "Día_Semana": 2,
  "Canal_Promedio_Demanda": 75.0,
  "Campana_Promedio_Demanda": 60.0,
  "Cliente_Promedio_Demanda": 80.0,
  "Producto_Promedio_Demanda": 85.0,
  "Canal_venta_encoded": 0,
  "Campana_encoded": 3,
  "Empresa_cliente_encoded": 0,
  "Producto_codigo_encoded": 0
}

Respuesta:
{
  "status": "success",
  "prediction": 45.23,
  "prediction_id": "abc123",
  "tenant_id": "empresa-001",
  "timestamp": "2026-04-04T10:30:00"
}
```

### Modelo & Historial

```bash
# Info del modelo
GET /api/v1/model/info
Authorization: Bearer <token>

# Historial predicciones
GET /api/v1/predictions
Authorization: Bearer <token>
```

---

## 🧪 Tests

```bash
# Ejecutar tests
pytest tests/ -v

# Tests con coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 🎨 Dashboard Features

1. **Autenticación**: Registro/Login de empresas
2. **Predicción**: Ingresa features → obtén predicción
3. **Historial**: Visualiza todas tus predicciones
4. **Modelo Info**: Stats y features del modelo

---

## 🔐 Multi-Tenancy (MVP)

### Sistema de Isolation

```python
# Cada usuario tiene:
- JWT token con tenant_id
- Acceso solo a sus propios datos
- Modelos compartidos inicialmente

# Base de datos:
- tenant_id en cada tabla
- Índices para queries rápidas
- Row-level security en queries
```

### Agregar Nueva Empresa

```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "empresa_name": "Nueva Constructora",
    "email": "contact@construccion.com",
    "password": "secure123"
  }'
```

---

## 📊 Modelo XGBoost

### Performance

- **R² Score**: 0.9443 (94.43% variance explained)
- **MAE**: 0.7634 unidades
- **RMSE**: 1.4091 unidades
- **Training**: 156,508 muestras
- **Validation**: 39,127 muestras

### Features

```
1. Stock_anterior / Stock_posterior
2. Precio_unitario
3. Año, Mes, Trimestre, Día_Semana
4. Canal_Promedio_Demanda
5. Campana_Promedio_Demanda
6. Cliente_Promedio_Demanda
7. Producto_Promedio_Demanda
8. Encoded: Canal, Campaña, Empresa, Producto
```

---

## 🐛 Troubleshooting

### "Model not found"
```bash
Verificar:
- Paths en .env están correctos (relativas a 07_Sistema_Produccion/)
- Archivos existe: 
  ✅ 03_Modelos/xgboost_model_V2_V2_Realista.joblib
  ✅ 03_Modelos/xgboost_metadata_V2_V2_Realista.json
```

### "Connection refused"
```bash
- ¿API en localhost:5000? 
  $ python -m src.api.main
- ¿Dashboard en localhost:8501?
  $ streamlit run src/ui/dashboard.py
```

### "Missing field: Stock_anterior"
```bash
Asegurar todas las 15 features en el request JSON
Ver ejemplo en API Endpoints
```

---

## 🔄 Roadmap Próximos

### Semana 2 (Dashboard mejorado)
- [ ] Carga de datos CSV en batch
- [ ] Gráficos de tendencia
- [ ] Exportar predicciones a Excel

### Semana 3 (Multi-tenancy activo)
- [ ] Per-tenant models
- [ ] Admin dashboard
- [ ] User management

### Semana 4 (Production)
- [ ] Deploy a Render/Railway
- [ ] Monitoring & logging
- [ ] Primeros clientes

---

## 📞 Contacto & Support

- 🐛 Issues: Documentar con stack trace
- 📧 Email: tech@predicast.dev
- 💬 Chat: Slack #predicast-dev

---

## 📄 Licencia

MIT - Predicast Team 2026
