# 🎯 MVP PLAN: Predicast para 1 Empresa (4 Semanas)

## VISIÓN

```
┌───────────────────────────────────────────────────────────────┐
│ Convertir su sistema_tesis + modelo XGBoost en UNA SOLUCIÓN   │
│ lista para 1 empresa AHORA, preparada para multi-tenancy       │
│ de forma que escale a 50+ empresas sin reconversión futura     │
└───────────────────────────────────────────────────────────────┘

TIEMPO:  4 semanas
COSTO:   ~$500 (infraestructura cloud)
EQUIPO:  1 dev full-time
ENTRADA: Data de empresa A (ya entrenada en Predicast)
SALIDA:  API + Dashboard funcionando, 1 cliente pagando
```

---

## FASE 1: SEMANA 1 - SETUP PROYECTO

### 1.1 Objetivo Semana 1

```
✅ Proyecto estructurado híbrido
✅ Código base compilando
✅ Ambiente cloud listo (Supabase, S3, Render)
✅ Pipeline data ejecutándose
✅ Predictor XGBoost integrado
```

### 1.2 Actividades Día a Día

```
DÍA 1:
─────
1. Create new Git repository
   $ git init predicast-mvp-singlecompany
   $ git remote add origin <your-repo>

2. Merge código base
   ├─ Copy sistema_tesis/ → predicast-mvp/
   ├─ Copy models/ de Predicast → predicast-mvp/models/
   └─ Copy data/ (Data.csv) → predicast-mvp/data/

3. Setup folder structure
   predicast-mvp/
   ├─ src/
   │  ├─ ui/
   │  │  └─ dashboard.py (from sistema_tesis, SIN cambios)
   │  ├─ api/
   │  │  ├─ backend.py (from sistema_tesis + modificar)
   │  │  └─ routes_predictor.py (NEW)
   │  ├─ ml/
   │  │  ├─ xgboost_predictor.py (NEW)
   │  │  ├─ recomendador.py (NEW)
   │  │  └─ preprocessing.py (NEW)
   │  ├─ data/
   │  │  └─ (del sistema_tesis - mantener)
   │  └─ db/
   │     └─ (del sistema_tesis - mantener)
   ├─ models/
   │  └─ xgboost_model_V2_V2_Realista.joblib (COPY)
   ├─ requirements.txt (MERGE)
   └─ .env.example

4. Initialize Git
   $ git add .
   $ git commit -m "Initial commit: Merge sistema_tesis + Predicast"


DÍA 2:
─────
1. Setup ambiente local
   $ python -m venv venv
   $ source venv/bin/activate  (or venv\Scripts\activate.bat en Windows)
   $ pip install -r requirements.txt

2. Merge requirements.txt
   MANTENER de sistema_tesis:
   ├─ streamlit>=1.36
   ├─ pandas>=2.0
   ├─ numpy>=1.24
   ├─ plotly>=5.18
   ├─ scikit-learn>=1.3
   ├─ supabase>=1.0
   └─ python-dotenv>=1.0

   AGREGAR de Predicast:
   ├─ xgboost==2.0.3
   ├─ flask==2.3.0
   ├─ flask-cors==4.0
   └─ python-jose==3.3.0

   AGREGAR para multi-tenancy prep:
   ├─ pydantic==2.0  (validation)
   ├─ sqlalchemy==2.0  (ORM)
   └─ cryptography==41.0  (JWT)

3. Setup .env
   cp .env.example .env
   
   Contenido .env:
   ─────────────────
   # DATABASE
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJxxxxx...
   
   # S3
   AWS_ACCESS_KEY_ID=AKIAXXXXXXX
   AWS_SECRET_ACCESS_KEY=xxxxx
   AWS_BUCKET_NAME=predicast-mvp
   AWS_REGION=us-east-1
   
   # APP
   EMPRESA_ID=empresa_a
   EMPRESA_NOMBRE=Mi Empresa
   FLASK_ENV=development
   FLASK_SECRET_KEY=dev-secret-key-change-production
   
   # MODEL
   MODEL_PATH=./models/xgboost_model_V2_V2_Realista.joblib
   
   # JWT (para multi-tenancy prep)
   JWT_ALGORITHM=HS256
   JWT_SECRET_KEY=your-super-secret-key-change-prod

4. Test setup
   $ python -m pytest tests/ -v
   (should be empty at this point, creating placeholder)


DÍA 3-4:
────────
1. Integrar XGBoost predictor
   
   Create: src/ml/xgboost_predictor.py
   ┌──────────────────────────────────────┐
   │ class XGBoostPredictor:              │
   │   def __init__(model_path):          │
   │     self.model = joblib.load(...)    │
   │                                      │
   │   def predict(features_dict):        │
   │     → Convert dict to features       │
   │     → Predict                        │
   │     → Return prediction + confidence │
   └──────────────────────────────────────┘

2. Create: src/ml/preprocessing.py
   ├─ Feature engineering (temporal, lags, etc.)
   ├─ Normalization
   └─ Error handling

3. Create: src/ml/recomendador.py
   ├─ Fórmula: Producción = Predicción - Stock + Buffer
   ├─ 3 escenarios (pesimista/normal/optimista)
   └─ Alerts si demanda extrema

4. Test predictor locally
   $ python test_xgboost_predictor.py
   (should output: "✅ Predictor works")


DÍA 5:
─────
1. Crear endpoints API básicos
   
   Create: src/api/routes_predictor.py
   
   @app.route('/api/v1/health', methods=['GET'])
   └─ Return {"status": "ok"}
   
   @app.route('/api/v1/predict', methods=['POST'])
   ├─ Input: {"producto_id": "SKU-003", "stock_actual": 150}
   ├─ Process: XGBoost predictor
   └─ Output: {"demanda": 650, "confianza": 0.943}
   
   @app.route('/api/v1/recommend', methods=['POST'])
   ├─ Input: {"producto_id": "SKU-003", "stock": 150}
   ├─ Process: recomendador
   └─ Output: {"pessimista": 530, "normal": 650, "optimista": 450}

2. Test endpoints con curl/Postman
   $ curl http://localhost:5000/api/v1/health

3. Commit
   $ git add . && git commit -m "Add XGBoost predictor + API endpoints"


DÍA 6-7:
────────
1. Setup cloud infrastructure

   AWS S3 Bucket:
   ├─ Create bucket: predicast-mvp-data
   ├─ Create folder: /models
   ├─ Upload xgboost_model_V2_V2_Realista.joblib
   └─ Set permissions: private (solo app access)

   Supabase Database:
   ├─ Crear conexión (ya existe, verificar)
   ├─ Review schema (debe tener tenant_id prep)
   └─ Backup existing data

   Render.com:
   ├─ Create account
   ├─ Connect GitHub repo
   ├─ (Deploy pendiente, solo setup)

2. Setup CI/CD (GitHub Actions)
   
   Create: .github/workflows/tests.yml
   ├─ Trigger: on push to main/develop
   ├─ Run: pytest
   ├─ Run: linting
   └─ Deploy if tests pass

3. Documentation
   ┌─────────────────────────────────────┐
   │ Create README_MVP_SETUP.md          │
   ├─ Local setup instructions           │
   ├─ Environment variables needed       │
   ├─ How to run dashboard               │
   ├─ How to test API                    │
   └─ Deployment instructions            │
   └─────────────────────────────────────┘


DELIVERABLES FIN DE SEMANA 1:
─────────────────────────────
✅ Código base compilando
✅ XGBoost predictor funcional
✅ API endpoints básicos (health, predict, recommend)
✅ Cloud infrastructure setup (S3, Supabase, Render)
✅ CI/CD pipeline creado
✅ Documentation README
✅ Tests pasando

GIT STATUS:
├─ Commits: ~5 (setup, predictor, api, cloud, docs)
└─ Ready: pasar a Semana 2
```

---

## FASE 2: SEMANA 2 - INTEGRACIÓN + DASHBOARD

### 2.1 Objetivo Semana 2

```
✅ Dashboard conectado a API
✅ Predicciones funcionando end-to-end
✅ Datos guardándose correctamente
✅ 1 cliente viendo el sistema
✅ Performance optimizado
```

### 2.2 Actividades

```
DÍA 8:
─────
1. Modificar Dashboard (src/ui/dashboard.py)
   
   AGREGAR endpoints configuración:
   ├─ API_URL = os.getenv("API_URL", "http://localhost:5000")
   ├─ EMPRESA_ID = os.getenv("EMPRESA_ID", "empresa_a")
   └─ JWT_TOKEN = (por ahora hardcoded, multi-tenancy luego)

2. Crear sección "PREDICCIÓN"
   ┌──────────────────────────────┐
   │ 📊 Predicción de Demanda     │
   ├──────────────────────────────┤
   │ Producto: [Dropdown SKU]     │
   │ Stock Actual: [input number] │
   │ [CALCULAR]                   │
   ├──────────────────────────────┤
   │ Resultado:                   │
   │ Demanda predicha: 650        │
   │ Confianza: 94.3%             │
   └──────────────────────────────┘

3. Crear sección "RECOMENDACIÓN"
   ┌──────────────────────────────────┐
   │ 📈 Recomendación Producción      │
   ├──────────────────────────────────┤
   │ Escenario Pessimista: 530        │
   │ Escenario Normal: 650 ✅         │
   │ Escenario Optimista: 450         │
   ├──────────────────────────────────┤
   │ Análisis: Stock bajo, producir   │
   │ al menos 650 unidades            │
   └──────────────────────────────────┘

4. Test dashboard local
   $ streamlit run src/ui/dashboard.py
   (should show new sections, integrate with API)


DÍA 9-10:
──────────
1. Conectar Dashboard ↔ API

   dashboard.py event flow:
   ├─ Usuario selecciona producto
   ├─ Usuario ingresa stock
   ├─ Click "Calcular"
   ├─ POST /api/v1/predict (backend)
   ├─ Backend calcula predicción
   ├─ Backend calcula recomendación
   └─ Mostrar resultados en GUI

2. Agregar visualizaciones Plotly
   ├─ Gráfico: Histórico demanda (últimos 30 días)
   ├─ Gráfico: Predicción vs Real (si existe histórico)
   ├─ Gauge: Confianza del modelo (94.3%)
   └─ Table: Top 5 productos por demanda

3. Error handling
   ├─ Validar inputs (stock >= 0, etc.)
   ├─ Manejo errors API (timeout, 500, etc.)
   ├─ User feedback (toast/alert)
   └─ Logging de errores

4. Caching (reducir API calls)
   ├─ Cache predicciones 24h
   ├─ Cache histórico data
   └─ Refresh button manual


DÍA 11:
────────
1. Guardar predicciones en BD
   
   Create table: predicciones
   ├─ id (PK)
   ├─ empresa_id (FK, multi-tenancy prep)
   ├─ producto_id
   ├─ demanda_predicha
   ├─ stock_actual
   ├─ recomendacion_produccion
   ├─ confianza
   ├─ created_at
   └─ actualizacion_real (NULL al inicio)

   Backend:
   ├─ Cada predicción se guarda en DB
   ├─ Permite auditoría posterior
   └─ Basis para comparación predicción-real

2. Crear vista "HISTORIAL"
   ┌─────────────────────────────┐
   │ 📋 Historial Predicciones   │
   ├─────────────────────────────┤
   │ Producto │ Predicción │Real │
   │ SKU-003  │ 650        │ 620 │
   │ SKU-001  │ 245        │ -   │
   └─────────────────────────────┘

3. Crear endpoint para traer historial
   GET /api/v1/historial-predicciones
   └─ Retorna predicciones recientes


DÍA 12:
────────
1. Performance optimization
   ├─ Caché predicciones comunes
   ├─ Async processing si hay múltiples requests
   ├─ Database indexing (empresa_id, created_at)
   └─ Response time target: <200ms

2. Monitoring básico
   ├─ Log API calls (method, endpoint, status, time)
   ├─ Alert si response > 500ms
   ├─ Dashboard metrics (requests/min, errors/day)
   └─ Save logs a Supabase table


DÍA 13-14:
───────────
1. Testing completo
   ├─ Unit tests (predictor, recomendador)
   ├─ Integration tests (API endpoints)
   ├─ UI tests (dashboard calls API correctly)
   └─ E2E tests (usuario completo: input → output)

2. Documentation
   ├─ API docs (endpoints, payloads, responses)
   ├─ User guide (cómo usar dashboard)
   ├─ Troubleshooting guide
   └─ Known issues / roadmap

3. First client setup
   ├─ Compartir acceso dashboard
   ├─ Share API documentation
   ├─ Explicar cómo interpretar resultados
   └─ Setup feedback channel (Slack, email)


DELIVERABLES FIN DE SEMANA 2:
──────────────────────────────
✅ Dashboard completamente funcional
✅ Predicciones en tiempo real
✅ Recomendaciones funcionando
✅ Datos guardándose
✅ Performance optimizado
✅ 1 cliente usando el sistema
✅ Tests pasando completos
✅ Documentación completa

GIT STATUS:
├─ Commits: ~8 (dashboard, api-integration, tests, docs)
└─ Ready: pasar a Semana 3
```

---

## FASE 3: SEMANA 3 - MULTI-TENANCY PREP

### 3.1 Objetivo Semana 3

```
✅ Sistema preparado para 2+ empresas
✅ Datos completamente aislados (tenant_id)
✅ JWT auth funcionando
✅ Model selector (global/personal)
✅ Test con 2 empresas simultáneas
```

### 3.2 Cambios Código Críticos

```
DÍA 15-16:
──────────
1. Database Schema v2 (Add tenant_id)
   
   NEW SQL:
   ────────
   ALTER TABLE demanda ADD COLUMN tenant_id INT;
   ALTER TABLE demanda ADD COLUMN empresa_id INT;
   ALTER TABLE demanda ADD CONSTRAINT fk_tenant 
     FOREIGN KEY (tenant_id) REFERENCES empresas(id);
   CREATE INDEX idx_demanda_tenant ON demanda(tenant_id);
   
   -- Similar para todas las tables
   ALTER TABLE predicciones ADD COLUMN tenant_id INT;
   ALTER TABLE stock ADD COLUMN tenant_id INT;
   ALTER TABLE usuarios ADD COLUMN tenant_id INT;
   
   -- Row-Level Security (PostgreSQL)
   CREATE POLICY tenant_policy ON demanda
     USING (tenant_id = current_setting('app.current_tenant'));

2. JWT Token Creation
   
   Create: src/auth/jwt_handler.py
   ────────────────────────────────
   def create_token(user_id, empresa_id):
       payload = {
           "sub": user_id,
           "empresa_id": empresa_id,
           "iat": datetime.utcnow(),
           "exp": datetime.utcnow() + timedelta(hours=24)
       }
       token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
       return token

   def decode_token(token):
       → extracts empresa_id from payload
       → devuelve {"user_id": ..., "empresa_id": ...}

3. Middleware (Attach tenant to context)
   
   Create: src/api/middleware.py
   ──────────────────────────────
   @app.middleware("http")
   async def add_tenant_middleware(request, call_next):
       # Extraer token del header
       auth_header = request.headers.get("Authorization", "")
       
       # Si no tiene token, bloquear
       if not auth_header:
           return JSONResponse({"error": "Unauthorized"}, 401)
       
       # Extraer empresa_id del token
       token = auth_header.replace("Bearer ", "")
       payload = decode_token(token)
       empresa_id = payload["empresa_id"]
       
       # Guardar en request context (disponible en todas partes)
       request.state.empresa_id = empresa_id
       request.state.tenant_id = empresa_id  # mismo
       
       response = await call_next(request)
       return response


DÍA 17:
────────
1. Update todas las queries para usar tenant_id
   
   ANTES:
   ───────
   def get_demanda():
       return db.query(Demanda).all()  # ❌ Devuelve TODAS

   DESPUÉS:
   ────────
   def get_demanda(request):
       tenant_id = request.state.tenant_id
       return db.query(Demanda).filter(
           Demanda.tenant_id == tenant_id
       ).all()  # ✅ Solo su empresa

2. Update endpoints
   
   @app.post("/api/v1/predict")
   def predict(data, request):
       tenant_id = request.state.tenant_id
       
       # Usar modelo correcto para empresa
       model = model_selector.get_model(tenant_id)
       
       prediction = model.predict(data)
       
       # Guardar con tenant_id
       db.save_prediction(
           tenant_id=tenant_id,  ← KEY
           prediction=prediction
       )
       return prediction

3. Model Selector
   
   Create: src/ml/model_selector.py
   ─────────────────────────────────
   class ModelSelector:
       def __init__(self):
           self.cache = {}
       
       def get_model(self, tenant_id):
           # ¿Existe en caché?
           if tenant_id in self.cache:
               return self.cache[tenant_id]
           
           # ¿Existe modelo personal?
           custom_path = f"s3://models/enterprise-{tenant_id}/model.pkl"
           if s3_exists(custom_path):
               model = load_from_s3(custom_path)
           else:
               # Si no, usa global
               model = load_from_s3("s3://models/global/model.pkl")
           
           self.cache[tenant_id] = model
           return model


DÍA 18:
────────
1. Register/Login endpoints
   
   @app.post("/api/v1/register")
   def register(email, password, empresa_nombre):
       # Crear usuario
       user = create_user(email, password)
       
       # Crear empresa
       empresa = create_empresa(empresa_nombre, owner_id=user.id)
       
       # Crear token
       token = create_token(user.id, empresa.id)
       
       return {
           "token": token,
           "empresa_id": empresa.id,
           "mensaje": "¡Bienvenido a PREDICAST!"
       }
   
   @app.post("/api/v1/login")
   def login(email, password):
       # Validar credenciales
       user = validate_user(email, password)
       
       # Obtener empresa del usuario
       empresa = get_empresa_by_user(user.id)
       
       # Generar token
       token = create_token(user.id, empresa.id)
       
       return {"token": token}

2. Dashboard update (add login screen)
   ├─ Login button
   ├─ Store JWT token en session
   ├─ Attach token a todas las requests
   └─ Logout button


DÍA 19-20:
──────────
1. Test multi-tenancy completo

   Create: tests/test_multitenant.py
   
   # Test 1: Aislar datos empresa A vs empresa B
   def test_tenant_isolation():
       empresa_a_data = call_api("/historial", token_a)
       empresa_b_data = call_api("/historial", token_b)
       
       assert empresa_a_data != empresa_b_data  ✅
       assert no_cross_contamination  ✅

   # Test 2: Model selector
   def test_model_selector():
       model_a = selector.get_model(empresa_a_id)
       model_global = selector.get_model(empresa_sin_modelo_id)
       
       assert model_a != model_global  ✅

   # Test 3: End-to-end multi-tenant
   def test_full_flow():
       token_a = login("usuario@empresa-a.com")
       token_b = login("usuario@empresa-b.com")
       
       # Empresa A hace predicción
       pred_a = predict({"producto": "X"}, token_a)
       
       # Empresa B hace predicción diferente
       pred_b = predict({"producto": "Y"}, token_b)
       
       # Verificar que no se cruza
       assert data_isolated  ✅

2. Documentation: Multi-tenancy setup
   ├─ Especificaciones JWT
   ├─ Endpoints de auth
   ├─ Cómo agregar nueva empresa
   └─ Troubleshooting


DELIVERABLES FIN DE SEMANA 3:
──────────────────────────────
✅ Database con tenant_id en todas partes
✅ JWT auth funcionando
✅ Middleware automático
✅ Model selector funcionando
✅ Register/Login endpoints
✅ 2+ empresas testeadas aisladamente
✅ Tests de multi-tenancy pasando
✅ Documentación multi-tenancy

GIT STATUS:
├─ Commits: ~6 (schema, jwt, middleware, tests)
└─ Ready: pasar a Semana 4 (Deploy)
```

---

## FASE 4: SEMANA 4 - DEPLOYMENT + HARDENING

### 4.1 Objetivo Semana 4

```
✅ Sistema deployado a producción
✅ 1-2 clientes pagos usando
✅ Security hardened
✅ Performance monitoreando
✅ Escala lista para siguiente fase
```

### 4.2 Última Semana de Acciones

```
DÍA 21-22:
──────────
1. Security audit
   ├─ JWT tokens con HTTPS
   ├─ Passwords hashed (bcrypt)
   ├─ Rate limiting (100 req/min por IP)
   ├─ CORS configurado (solo dominios nuestros)
   ├─ SQL injection protección (use ORM)
   ├─ CSRF tokens en forms
   └─ Environment variables (no hardcode secrets)

2. Setup production environment
   
   Create: .env.production
   ────────────────────────
   FLASK_ENV=production
   FLASK_SECRET_KEY=<random-64-char-key>
   JWT_SECRET_KEY=<random-64-char-key>
   API_URL=https://predicast-api.render.com
   SUPABASE_URL=<prod-supabase-url>
   SUPABASE_KEY=<prod-supabase-key>
   AWS_PRODUCTION_BUCKET=predicast-prod
   DEBUG=False

3. Database backups
   ├─ Daily automated backups (Supabase)
   ├─ Backup restoration test
   └─ Data retention policy

4. Monitoring setup
   ├─ Error tracking (Sentry optional)
   ├─ Performance monitoring (logging)
   ├─ Uptime alerts (cron health check)
   └─ Dashboard de métricas


DÍA 23:
────────
1. Deploy a Render

   Steps:
   ──────
   1. Push código a main branch
   2. En Render.com: Create Web Service
   3. Connect GitHub repo
   4. Set build command: pip install -r requirements.txt
   5. Set start command: python api/backend.py
   6. Add environment variables (desde .env.production)
   7. Deploy
   8. Verify: curl https://predicast-api.render.com/api/v1/health
   
   Resultado:
   ├─ API deployado en: https://predicast-api.render.com
   ├─ Database conectada
   ├─ S3 bucket accesible
   └─ Ready for clients

2. Deploy dashboard
   
   Streamlit Cloud deployment:
   ───────────────────────────
   1. Push código a GitHub
   2. Go to share.streamlit.io
   3. Connect repo
   4. Select branch: main
   5. Set main file: src/ui/dashboard.py
   6. Deploy
   7. Share URL con cliente

3. Configurar dominios (opcional)
   ├─ API: api.predicast.company.com
   └─ Dashboard: app.predicast.company.com


DÍA 24:
────────
1. Onboard cliente production

   Steps para cliente:
   ───────────────────
   1. Crear cuenta (POST /api/v1/register)
   2. Recibir token JWT
   3. Enviar datos históricos
   4. Test predicciones
   5. Setup alertas (si desea)
   6. Go-live

2. Entrenamiento cliente
   ├─ Mostrar cómo usar dashboard
   ├─ Explicar predicciones y recomendaciones
   ├─ Cómo interpretar confianza
   ├─ Contact para support
   └─ Roadmap futuro


DÍA 25-28:
──────────
1. Ciclo de feedback (7 días monitoring)
   ├─ Monitor errorología
   ├─ Check performance metrics
   ├─ Responder a cliente feedback
   ├─ Ajustes menores
   └─ Documentar issues

2. Iniciar segunda empresa
   ├─ Register sistema
   ├─ Upload datos
   ├─ Validar predicciones
   ├─ Test model selector
   └─ Go-live

3. Documentación final
   ├─ How-to guides
   ├─ API reference completa
   ├─ FAQ
   ├─ Video tutorial (opcional)
   └─ Troubleshooting

4. Setup for Fase 2 planning
   ├─ Metrics collection
   ├─ Retraining pipeline
   ├─ Strategy FastAPI migration
   └─ Roadmap following 4 weeks


DELIVERABLES FIN DE SEMANA 4 (MVP COMPLETADO):
───────────────────────────────────────────────
✅ Sistema en producción
✅ 2+ clientes activos pagando
✅ Security hardened
✅ Performance monitoreando
✅ Documentación completa
✅ Support channel setup
✅ Roadmap Fase 2 claro

ESTADO FINAL:
MRR: $400-600
Usuarios: 2-3
Predicciones/día: ~100-200
Uptime: 99%+
Next: Agregar más clientes + comenzar migración FastAPI
```

---

## RESUMEN TIMELINE

```
SEMANA 1:   Setup + Integración XGBoost         → ✅ MVP base
SEMANA 2:   Dashboard + API integration         → ✅ Funcional
SEMANA 3:   Multi-tenancy preparation           → ✅ Escalable
SEMANA 4:   Deploy + Hardening + Cliente        → ✅ PRODUCCIÓN

TOTAL:      4 semanas
EQUIPO:     1 Dev full-time
COSTO:      $500 cloud infra
RESULTADO:  Sistema producción 1 empresa, preparado 50+

┌─────────────────────────────────────────────┐
│ MVP COMPLETADO Y LISTO PARA ESCALA          │
├─────────────────────────────────────────────┤
│ 2 clientes pagos                            │
│ $500-600 MRR (expected)                     │
│ Arquitectura sólida para multi-tenancy      │
│ Path claro a Fase 2 (FastAPI migration)     │
│ Documentación lista                         │
│ Monitoring en place                         │
│ Ready para crecer a 50+ empresas            │
└─────────────────────────────────────────────┘
```

---

## PRÓXIMOS PASOS INMEDIATOS

```
👉 ESTA SEMANA:
   1. ✅ Leer esta documentación (hecho)
   2. ⏳ Auditar Sistema_Tesis (¿estado actual?)
   3. ⏳ Recolectar requisitos empresa piloto
   4. ⏳ Setup GitHub repo
   5. ⏳ Setup ambientes cloud (Supabase, Render, AWS)
   
👉 SEMANA 1 (Próxima):
   1. Crear estructura folders
   2. Merge códigos
   3. Integrar XGBoost
   4. Deploy a staging

¿TIENES DUDAS o AJUSTES al plan anterior?
```
