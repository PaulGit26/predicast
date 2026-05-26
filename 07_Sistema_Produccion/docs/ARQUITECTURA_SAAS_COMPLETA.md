# 🏗️ ARQUITECTURA PREDICAST - SISTEMA SaaS MULTI-EMPRESA

## I. VISIÓN GENERAL DEL PRODUCTO

### 1.1 ¿Qué es PREDICAST?

```
PREDICAST = Plataforma SaaS de Forecasting de Demanda
             + Recomendaciones de Producción
             + Gestión de Inventario Inteligente

Objetivo:    Cada manufactura peruana toma decisiones data-driven
Target:      Pymes manufactureras (5-500 empleados)
Modelo:      SaaS Multi-tenant (Multi-empresa)
Deploy:      Cloud (AWS/GCP)
```

### 1.2 Decisión Crítica: Multi-Tenancy vs Mono-Tenancy

```
OPCIÓN A: MONO-TENANCY (1 modelo per empresa)
├─ Cada empresa su propia instancia
├─ Mejor seguridad y personalización
├─ PERO: Costo operacional 10x más alto
├─ PERO: Escalabilidad limitada
└─ NO RECOMENDADO para SaaS

OPCIÓN B: MULTI-TENANCY (Varias empresas en 1 plataforma) ✅
├─ 1 infraestructura sirve múltiples clientes
├─ Cada empresa: datos aislados pero sistema compartido
├─ Costo operacional optimizado
├─ Escalabilidad automática
├─ Trade-off: Complejidad técnica inicial (pero worth it)
└─ RECOMENDADO - ÉSTA ES NUESTRA ARQUITECTURA

MODELO ECONÓMICO DIFERENCIA:
─────────────────────────────
Mono-tenancy:
├─ Cliente 1: $1,000/mes infra
├─ Cliente 2: $1,000/mes infra
├─ Cliente 3: $1,000/mes infra
└─ Total: $3,000/mes infra para 3 clientes

Multi-tenancy:
├─ Infra compartida: $500/mes
├─ Cliente 1: $200/mes (incluye su parte)
├─ Cliente 2: $200/mes
├─ Cliente 3: $200/mes
└─ Total: $900/mes infra para 3 clientes = 70% ahorro
```

### 1.3 Modelos por Empresa: ¿Necesarios?

```
PREGUNTA: "¿Cada empresa necesita MODELO DISTINTO?"

RESPUESTA CORTA: No inicialmente. Sí eventualmente.

EXPLICACIÓN:
═════════════

Fase 1 (MVP): MODELO GLOBAL
├─ 1 modelo XGBoost entrenado con ALL empresas
├─ Captura tendencias macroprudenciales (del sector)
├─ Accuracy: ~90-92%
├─ Deploy: 3-4 semanas
├─ Mantenimiento: Bajo (1 retraining/mes)
└─ VENTAJA: Simple, escalable, lanzamiento rápido

Fase 2 (Post-launch): MODELOS POR EMPRESA
├─ Cada empresa que tenga 3+ meses histórico →
├─ Entrenar modelo especializado (solo sus datos)
├─ Accuracy: ~94-96% (mejor que global)
├─ Deploy: Automático vía pipeline
├─ Mantenimiento: Alto (retraining diario si quieren)
└─ VENTAJA: Personalización, mejor predicción, lock-in cliente

TRANSICIÓN:
Empresa se registra → usa modelo global (bueno)
        ↓ (3 meses)
Recopila suficientes datos → auto-migra a modelo personal (mejor)


IMPLICACIÓN TÉCNICA:
───────────────────
El sistema necesita ABSTRACCIÓN DE MODELOS:

┌─────────────────────────────────────────┐
│     PREDICAST API REST                  │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│   MODEL SELECTOR (Router)               │
│  "¿Existe modelo empresa-X?"            │
└─────────────────────────────────────────┘
    ↙            ↘
SÍ (personal)    NO (global)
   ↓                ↓
Modelo_X.pkl    Modelo_Global.pkl
   ↓                ↓
└────────────────┬───────────────────┘
                 ↓
        PREDICCIÓN UNIFICADA
```

---

## II. ARQUITECTURA TÉCNICA DETALLADA

### 2.1 Stack Tecnológico Recomendado

```
LAYER              TECNOLOGÍA                      RAZÓN
────────────────────────────────────────────────────────────────
FRONTEND           React + TypeScript              UX moderna, type-safe
                   + Recharts (visualización)
                   
BACKEND API        FastAPI (Python)                ⚡ Rápido, async, docs auto
                   + SQLAlchemy ORM
                   
ML INFERENCE       XGBoost v2.0+                   Probado en nuestro data
                   + sklearn preprocessing
                   
DATABASE           PostgreSQL (SQL)                Relacional, ACID, datos
                   + TimescaleDB extension         estructurados + series temporales
                   
CACHE              Redis                           ⚡ Predicciones cacheadas
                   (optional pero recomendado)
                   
ML OPS             MLflow                          Versionado modelos, tracking
                   + DVC para data
                   
CLOUD INFRA        AWS o GCP                       Escalables, confiables
                   - EC2/GCE (APIs)
                   - RDS (PostgreSQL managed)
                   - S3/GCS (storage modelos)
                   - Lambda (batch retraining)
                   
DEPLOYMENT         Docker + Kubernetes             Orquestación, auto-scaling
                   (en AWS EKS o GCP GKE)
                   
CI/CD              GitHub Actions                  Integración continua
                   + ArgoCD (deployment)
                   
MONITORING         DataDog o Prometheus            Alertas, performance
                   + Grafana (dashboards)
                   
MESSAGE QUEUE      RabbitMQ o AWS SQS              Async jobs (retraining)
```

### 2.2 Diagrama de Arquitectura (Alto Nivel)

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTES FINALES                         │
│  (Empresa A, B, C... desde Perú/Sudamérica via navegador/API)    │
└────────────────────┬────────────────────────────────────────────┘
                     │
         ┌───────────┴────────────┐
         │                        │
   ┌─────▼──────┐         ┌──────▼──────┐
   │ WEB UI      │         │ REST API    │
   │ React       │         │ FastAPI     │
   │ (Frontend)  │         │ (Backend)   │
   └─────┬──────┘         └──────┬──────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼────────────┐
         │   LOAD BALANCER        │
         │   (AWS ALB/GCP LB)     │
         └───────────┬────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐      ┌────▼────┐      ┌───▼────┐
│API Pod1 │      │API Pod2 │      │API Pod3 │
│(FastAPI)│      │(FastAPI)│      │(FastAPI)│
│+XGBoost │      │+XGBoost │      │+XGBoost │
└───┬────┘      └────┬────┘      └───┬────┘
    │                │                │
    └────────────────┬────────────────┘
                     │
         ┌───────────┴────────────┐
         │                        │
    ┌────▼──────┐          ┌─────▼─────┐
    │ PostgreSQL │          │   Redis   │
    │ + Timescale│          │  (Cache)  │
    │ (Multi-DB) │          └───────────┘
    └────┬──────┘
         │
    ┌────┴──────────┐
    │                │
┌───▼────┐      ┌───▼──────┐
│ Tenant A│      │ Tenant B │
│ Data    │      │ Data     │
│(Aislado)│      │(Aislado) │
└────────┘      └──────────┘

JOBS BATCH (Retraining Diario):
────────────────────────────────
┌─────────────────────────────┐
│  Lambda/Cloud Functions     │
│  (Triggered: 2AM UTC)       │
└──────────┬──────────────────┘
           │
      ┌────▼────────┐
      │ Fetch datos  │
      │ nuevos       │
      └────┬─────────┘
           │
      ┌────▼────────────┐
      │ Reentrenar      │
      │ modelos nuevos  │
      └────┬────────────┘
           │
      ┌────▼──────────────┐
      │ Deploy modelo si  │
      │ mejora > 5%       │
      └───────────────────┘

ALMACENAMIENTO MODELOS:
─────────────────────────
┌──────────────────────┐
│ S3 / GCS             │
│ Model Registry       │
├──────────────────────┤
│ modelo_global_v1.pkl │
│ modelo_global_v2.pkl │
│ modelo_A_v1.pkl      │
│ modelo_A_v2.pkl      │
│ modelo_B_v1.pkl      │
│ modelo_B_v2.pkl      │
└──────────────────────┘
```

### 2.3 Flujo de Datos: Request a Predicción

```
USUARIO: "Dame predicción para mañana"
│
├─ POST /api/v1/prediccion
│  └─ headers: { "Authorization": "Bearer token_empresa_A" }
│  └─ body: {
│       "producto_id": "SKU-003",
│       "variante": "XL",
│       "canal": "distribuidor"
│     }
│
├─ PREDICAST API RECIBE
│  ├─ Valida token (¿Empresa autorizada?)
│  ├─ Extrae tenant_id = "empresa_A"
│  └─ Rutetea a handler de predicción
│
├─ MODEL SELECTOR
│  ├─ Query: "¿Existe modelo personal para empresa_A?"
│  ├─ SÍ → Usa modelo_A_v2.pkl
│  └─ NO → Usa modelo_global_v2.pkl
│
├─ PREPROCESSING
│  ├─ Obtiene features recientes (últimas 30 días)
│  ├─ Normaliza según estándares del modelo
│  └─ Construye vector de entrada
│
├─ XGBOOST INFERENCE
│  ├─ Load modelo en memoria
│  ├─ Ejecuta forward pass (<50ms típico)
│  └─ Genera predicción + intervalo confianza
│
├─ ENRIQUECIMIENTO
│  ├─ Recupera stock actual de DB
│  ├─ Aplica recomendador (fórmula)
│  ├─ Genera 3 escenarios (pesimista/normal/optimista)
│  └─ Cache resultado en Redis (TTL: 24h)
│
└─ RESPUESTA
   {
     "producto_id": "SKU-003",
     "demanda_predicha": 650,
     "intervalo_95pct": [450, 830],
     "stock_actual": 120,
     "recomendaciones": {
       "pessimista": 530,
       "normal": 650,
       "optimista": 450
     },
     "confianza": 0.943,
     "timestamp": "2026-04-05T10:30:00Z"
   }

OBSERVACIÓN:
Si ya hizo predicción hace <24h → Redis devuelve cacheado (1ms)
Si es nueva → Calcula desde 0 (50-100ms)
```

---

## III. GESTIÓN DE MULTI-TENANCY

### 3.1 Isolación de Datos (CRÍTICO)

```
PRINCIPIO: Zero cross-contamination between tenants

DATABASE DESIGN:
────────────────

┌─── SCHEMA (PostgreSQL) ───┐
│                            │
│ tenant (table global)      │ ← Tabla maestra
├─ tenant_id  (PK)           │
├─ empresa_nombre            │
├─ created_at                │
├─ subscription_tier         │
└─ api_key                   │


│ productos (per tenant)
├─ producto_id  (PK)
├─ tenant_id    (FK) ← KEY PARA ISOLACIÓN
├─ sku
├─ nombre
└─ ...

│ demandas_historicas (per tenant)
├─ demanda_id (PK)
├─ tenant_id  (FK) ← KEY PARA ISOLACIÓN
├─ producto_id
├─ cantidad
├─ fecha
└─ ...

│ modelos (per tenant)
├─ modelo_id (PK)
├─ tenant_id (FK) ← KEY PARA ISOLACIÓN
├─ tipo (global /  personal)
├─ version
├─ s3_path
└─ metricas

REGLA DE ORO:
─────────────
TODA QUERY incluye: WHERE tenant_id = @current_tenant_id
NUNCA PERMITIR: Queries sin filtro tenant

EJEMPLO SEGURO:
   SELECT * FROM productos
   WHERE tenant_id = 123

EJEMPLO INSEGURO (ERROR):
   SELECT * FROM productos
   -- ¡¡Devolvería datos de TODAS las empresas!!


ROW-LEVEL SECURITY (PostgreSQL):
──────────────────────────────────
Implementar RLS (Row Level Security) adicional:

CREATE POLICY tenant_isolation ON productos
  USING (tenant_id = current_setting('app.current_tenant_id')::int);

=> Incluso si un hacker bypassea filtro de app,
   DB lo bloquea a nivel políticas
```

### 3.2 Autenticación y Autorización

```
FLUJO DE LOGIN:
───────────────

1. CLIENTE PERUANA:
   username: "contacto@empresa-a.com"
   password: "securepass123"
   
2. POST /auth/login
   ├─ Valida credenciales en tabla users
   ├─ Verifica: user.tenant_id = empresa_a
   └─ Genera JWT token
   
3. JWT TOKEN INCLUYE:
   {
     "sub": "user_id_123",
     "tenant_id": 456,
     "empresa": "Empresa A",
     "role": "admin",
     "exp": 1712275200
   }
   
4. CADA REQUEST HTTP:
   headers: { "Authorization": "Bearer eyJ0eXAi..." }
   
5. MIDDLEWARE VALIDA:
   ├─ Token válido?
   ├─ No expirado?
   ├─ tenant_id correcto?
   └─ Si TODO ok → request permite
   
6. CONTEXT SE HEREDA:
   app_context.current_tenant_id = jwt.tenant_id
   => Todas queries usan este tenant_id automáticamente
```

### 3.3 Modelos por Empresa: Storage

```
UBICACIÓN DE MODELOS EN AWS S3:
────────────────────────────────

s3://predicast-models/
├─ global/
│  ├─ modelo_global_v1.pkl
│  ├─ modelo_global_v2.pkl  ← ACTIVE
│  └─ metadata_v2.json
│
├─ tenant-456/  (Empresa A)
│  ├─ modelo_personal_v1.pkl
│  ├─ modelo_personal_v2.pkl  ← ACTIVE
│  └─ metadata_v2.json
│
├─ tenant-789/  (Empresa B)
│  ├─ modelo_personal_v1.pkl
│  └─ metadata_v1.json  ← ACTIVE
│
└─ tenant-999/  (Empresa C)
   └─ (no existe → usa global)


MODEL LOADING STRATEGY:
──────────────────────
En cada Pod de FastAPI:

# En inicio
class ModelCache:
    def __init__(self):
        self.cache = {}  # {model_id → modelo_pkl}
    
    def get_model(self, tenant_id):
        # Primero: ¿existe local?
        if tenant_id in self.cache:
            return self.cache[tenant_id]
        
        # Segundo: ¿existe en S3?
        custom_path = f"s3://predicast-models/tenant-{tenant_id}/modelo_personal_v2.pkl"
        if s3_exists(custom_path):
            model = load_from_s3(custom_path)
            self.cache[tenant_id] = model  # cache en RAM
            return model
        
        # Fallback: usa modelo global
        global_path = "s3://predicast-models/global/modelo_global_v2.pkl"
        model = load_from_s3(global_path)
        self.cache[tenant_id] = model
        return model

VENTAJA:
- Modelos en RAM (Pod local) → <50ms acceso
- Fallback automático a global si no existe
- Updates: redeploy Pod → carga versión nueva
```

---

## IV. FASES DE DESARROLLO

### 4.1 Timeline Realista (Desde 0 a Producción)

```
FASE 1: MVP (4 semanas)
═════════════════════════
Semana 1:
└─ Setup infraestructura AWS (VPC, RDS, S3)
└─ Setup repositorio + CI/CD
└─ Boilerplate FastAPI + React

Semana 2:
└─ Backend: API básica
└─ DB: Schema multi-tenant
└─ Auth: JWT simple

Semana 3:
└─ Modelo: Integración XGBoost
└─ Predictor: wrapper + preprocessing
└─ Recomendador: lógica fórmula

Semana 4:
└─ Frontend: Dashboard básico
└─ Testing: E2E critical paths
└─ Deploy: Staging en AWS

DELIVERABLES:
├─ API REST funcional (3 endpoints min)
├─ Dashboard WYSIWYG (mostrar predicción + recomendación)
├─ 1 modelo global (compartido todas empresas)
└─ 1 cliente beta (Empresa piloto)

COSTO: ~$3K (infraestructura AWS + desarrollo)


FASE 2: Producción Beta (4 semanas)
═══════════════════════════════════
Semana 1:
└─ Onboarding primer cliente
└─ Upload histórico data
└─ Validación predicciones vs realidad

Semana 2:
└─ Monitoreo + ajustes
└─ Retraining job automático
└─ Bug fixes de beta

Semana 3:
└─ Agregar segundo cliente
└─ Entrenar modelo personal para cliente 1 (si 3+ meses data)
└─ Refinar UX basado feedback

Semana 4:
└─ Escalabilidad testing (load test)
└─ Documentación API + onboarding
└─ Go-live decisión

DELIVERABLES:
├─ 3-5 clientes pagando
├─ Modelos personales para clientes con data
├─ Monitoring + alertas
└─ Procesos operacionales documentados

COSTO: ~$5K (infra + atención cliente)


FASE 3: Crecimiento (8 semanas)
═══════════════════════════════
Semana 1-2:
└─ Sales/Marketing
└─ Agregar 10-15 clientes más
└─ Refinar UX basado feedback

Semana 3-4:
└─ Features avanzados
│  ├─ A/B testing modelos
│  ├─ Análisis sensibilidad
│  └─ Forecasting por mix (agrupa productos)
└─ Mejorar precisión (ensemble modelos)

Semana 5-6:
└─ Mobile app (opcional)
└─ Integraciones (Salesforce, SAP, ERPs básicos)
└─ Reportería avanzada

Semana 7-8:
└─ Escalabilidad infraestructura
└─ Kubernetes auto-scaling
└─ Disaster recovery plan

DELIVERABLES:
├─ 50-100 clientes
├─ Features premium
├─ Ecosystem integraciones
└─ Path a profitabilidad

COSTO: ~$15-30K (equipo + marketing + infra)


FASE 4: Enterprise (12+ semanas)
════════════════════════════════
├─ Modelos más complejos (LSTM, Transformers)
├─ API v2 con features enterprise
├─ Multi-idioma (ES, PT, EN)
├─ SSO/SAML para corporativos
├─ Compliance (GDPR, LGPD, normativa peruana)
├─ Data residency (servidores en Perú)
├─ SLA garantizado (99.9% uptime)
└─ Account managers para clientes grandes

COST: Variable ($50-100K+ dependiendo scope)
```

### 4.2 Roadmap de Features

```
MUST HAVE (MVP):
├─ ✅ Predicción demanda (1 día ahead)
├─ ✅ Recomendación producción (3 escenarios)
├─ ✅ Dashboard visualización
├─ ✅ API REST básica
├─ ✅ Multi-tenancy base
└─ ✅ Modelo global

SHOULD HAVE (Fase 2):
├─ Modelos personales (cuando 3+ meses data)
├─ Upload histórico data (CSV)
├─ Alertas (stock bajo, demanda alta)
├─ Predicción 7 días ahead
├─ Análisis variación vs predicción
└─ Export reportes (PDF, Excel)

NICE TO HAVE (Fase 3+):
├─ Forecasting por mix (agrupa productos)
├─ Machine Learning retraining automático
├─ Recomendaciones de compra (insumos)
├─ Análisis de estacionalidad
├─ Predicción de precio (opcional)
├─ Mobile app
├─ Integraciones API (ERP, CRM)
├─ Análisis de elasticidad
├─ A/B testing de modelos
└─ Multi-idioma

ENTERPRISE (Fase 4):
├─ Modelos LSTM/Transformers
├─ Predicción por cliente individual
├─ Análisis de eventos (causas de variación)
├─ SSO empresarial
├─ Data residency local
├─ Compliance regulatorio
└─ SLA 99.9%
```

---

## V. PLAN DE GO-TO-MARKET (GTM)

### 5.1 Estrategia de Lanzamiento

```
SEMANA 1-2 (Pre-Launch):
└─ Beta cerrada: 3-5 clientes piloto (gratis/descuento)
└─ Objetivo: Validar product-market fit
└─ Feedback: Mejoras rápidas

SEMANA 3-4 (Soft Launch):
└─ Disponibilidad: LinkedIn, comunidades maker/emprendedores
└─ Precio: Early-bird $199/mes (vs $299 regular)
└─ Objetivo: Primeros 10-15 clientes pagos

MES 2-3 (Ramp-Up):
├─ Inbound marketing
│  ├─ Blog: "¿Por qué 40% manufactura peruana pierde $$$?"
│  ├─ Case studies: "Cliente X ahorró $$$"
│  └─ Videos: Demo 3-min
├─ Outreach directo
│  ├─ LinkedIn: CEO/Gerentes Operaciones
│  ├─ Email campaigns: "¿Cuánto inventario exceso?"
│  └─ Eventos: Cámaras empresariales
└─ Objetivo: 30-50 clientes

MES 4+ (Growth):
├─ Partnerships
│  ├─ Contadores/CPA (recomiendan a clientes)
│  ├─ Consultores empresariales
│  └─ Plataformas SAAS peruanas
├─ Content marketing
│  └─ "Forecasting demanda: Guía para Pymes"
└─ Objetivo: 100+ clientes


SEGMENTACIÓN DE CLIENTES:
─────────────────────────
TIER 1 - STARTUP ($99/mes):
├─ 1-5 productos
├─ Hasta 1,000 predicciones/mes
├─ Dashboard básico
└─ Soporte email

TIER 2 - STANDARD ($299/mes): ← RECOMENDADO
├─ Hasta 20 productos
├─ Predicciones ilimitadas
├─ Dashboard completo + alertas
├─ Modelos personales
└─ Soporte Slack

TIER 3 - ENTERPRISE (custom pricing):
├─ Unlimited productos
├─ Features premium (ensemble, APIs)
├─ Integraciones custom
├─ Account manager
└─ Soporte prioritario


PROYECCIÓN CLIENTES:
────────────────────
Mes 1:    5 clientes  ×   $100 promedio = $500
Mes 2:   15 clientes  ×   $200 promedio = $3,000
Mes 3:   40 clientes  ×   $250 promedio = $10,000
Mes 6:  100 clientes  ×   $280 promedio = $28,000
Mes 12: 200 clientes  ×   $300 promedio = $60,000

MRR Mes 12: $60,000 USD
ARR Mes 12: $720,000 USD

(CAC: $200, LTV: $3,000, ratio: 15x ✅ Saludable)
```

### 5.2 Canales de Adquisición

```
OWNED (Sin $ invertido):
├─ LinkedIn personal (@tu_nombre) - storytelling
├─ Blog técnico (Medium, Dev.to)
├─ GitHub público (repo showcasing)
├─ Email lista (networking existing)
└─ Referrals (cliente recomienda a otro)

EARNED (Content + PR):
├─ Menciones en newsletters tech peruanas
├─ Interviews (podcasts startup peruano)
├─ Artículos en publicaciones (El Comercio, Gestión)
├─ Comunidades: Y Combinator, Founders IQ, etc.
└─ Awards (startup premios)

PAID (Con inversión):
├─ Google Ads (keywords: "forecast demanda", "inventory")
├─ LinkedIn Ads (targeting: "Operations Manager" Perú)
├─ Facebook Ads (targeting empresas pequeñas)
└─ Sponsorship tech communities

PARTNERSHIP (Leverage):
├─ Convenio contadores (ellos lo recomiendan)
├─ Partnership consultoras empresariales
├─ Integración SAP/ERPs populares
├─ Marketplace cloud (AWS, GCP marketplace)
└─ Reseller agreements

MIX RECOMENDADO (Año 1):
├─ 50% Owned (personal effort, networking)
├─ 30% Partnership (apalancamiento)
├─ 15% Paid (budget limitado)
└─ 5% Earned (hope for best)
```

---

## VI. INFRAESTRUCTURA Y COSTOS OPERACIONALES

### 6.1 Estimado de Costos Mensuales (Año 1)

```
COMPONENTE                          COSTO/MES    NOTAS
──────────────────────────────────────────────────────────

AWS Infrastructure:
├─ EC2 (2 instancias t3.large)        $150     API servers
├─ RDS PostgreSQL (db.t3.large)       $200     Database
├─ S3 storage (modelos, datos)         $50     Models + backups
├─ ALB (Application Load Balancer)    $15      Traffic distribution
├─ NAT Gateway                         $35      Outbound traffic
├─ Lambda (batch jobs)                 $10     Retraining jobs
└─ CloudWatch + logging               $20      Monitoring

Subtotal AWS:                          $480

Third-party Services:
├─ DataDog (monitoring)                $100    Alertas + dashboards
├─ SendGrid (email notif)              $20     Alerts via email
├─ GitHub Actions (CI/CD)              $4      Build jobs (free tier)
└─ Domain DNS                          $1      Zone management

Subtotal Services:                      $125

TOTAL RECURRENTE:                      $605/mes = $7,260/año


ONE-TIME COSTS (Setup):
├─ AWS setup + optimization           $1,000
├─ CI/CD + infrastructure setup       $1,500
├─ Initial model training              $500
└─ Legal + business setup              $1,000

TOTAL INICIAL:                         $4,000

TEAM COST (Contratar / Consultoría):  $25-50K año 1
(Dev senior: $3-5K/mes part-time)
```

### 6.2 Break-Even Analysis

```
SCENARIO: Monthly Recurring Revenue (MRR)

Mes 1-2:
- Clientes: 5
- MRR: $500
- Gastos: $605
- Resultado: -$105/mes LOSS

Mes 3-4:
- Clientes: 20
- MRR: $5,000
- Gastos: $650 (escala lenta)
- Resultado: +$4,350/mes PROFIT

Mes 6:
- Clientes: 100
- MRR: $28,000
- Gastos: $700 (más optimizado)
- Resultado: +$27,300/mes PROFIT

Mes 12:
- Clientes: 200
- MRR: $60,000
- Gastos: $1,000 (soporte, SAC)
- Resultado: +$59,000/mes PROFIT


BREAK-EVEN: Mes 3 con 15-20 clientes

UNIT ECONOMICS:
───────────────
MRR por cliente:    $300 promedio
CAC (Cost Acq):     $200 (marketing + effort)
Payback period:     2.3 meses
LTV (24 meses):     $7,200
LTV/CAC ratio:      36x (excelente!)
```

### 6.3 Escabilidad de Infraestructura

```
ELASTIC SCALING (Automático):

Clientes:  1-50          50-200        200-1000      1000+
┌──────────────────────────────────────────────────────>
│
├─ Compute:   1 t3.large   → 2 t3.large  → 3-4 c5.xlarge → Custom
├─ Database:  t3.large    → t3.xlarge   → t3.2xlarge    → Sharded
├─ Cache:     None needed  → Redis-1gb   → Redis-5gb     → Cluster
├─ CDN:       No           → CloudFront  → CloudFront    → Multi-region
│
└─ Monthly cost: $600 → $1,200 → $3,500 → $8,000+


AUTO-SCALING RULES:
────────────────────
IF cpu_avg > 70% for 5min
  THEN add_compute_instance()

IF memory_avg > 80% for 5min
  THEN increase_cache_tier()

IF db_connections > 80% pool
  THEN scale_rds_read_replicas()

RESULTADO: Crece dinámicamente con demanda
NO downtime durante crecimiento
Pagamos solo por lo que usamos
```

---

## VII. ARQUITECTURA DE RETRAINING (CRÍTICO)

### 7.1 Pipeline de Reentrenamiento Automático

```
TRIGGER: Cada día 2:00 AM UTC (después data cierre)
         O manual: cuando gerente lo solicita

PIPELINE:
─────────

STEP 1: FETCH NEW DATA
├─ Conectar a DB empresa
├─ Query: últimos 7 días observaciones
├─ Validar: calidad datos (nulls, outliers)
└─ Combine: con histórico (últimos 90 días)

STEP 2: FEATURE ENGINEERING
├─ Temporal features (mes, día semana, etc.)
├─ Lags (demanda 1d, 7d, 30d atrás)
├─ Rolling aggregates
├─ Encoding categóricas
└─ Normalización

STEP 3: TRAIN
├─ Split: 80% train, 20% validation
├─ XGBoost.fit(X_train, y_train)
├─ Early stopping: si val_loss no improve
└─ Epoch típico: 5-30 min

STEP 4: EVALUATE
├─ Métrica: MAE nuevo vs anterior
├─ Threshold: ¿Mejora > 5%?
├─ Alert: Si modelo degrada
└─ Log: Todas métricas a MLflow

STEP 5: DECISION
├─ IF mae_nuevo < mae_anterior * 0.95:
│  └─ ACCEPT: Deploy nuevo modelo
├─ ELSE:
│  └─ REJECT: Mantén modelo anterior
└─ Email alert: Status a gerente

STEP 6: DEPLOY
├─ Save modelo: S3://.../modelo_v{version}.pkl
├─ Update model registry (MLflow)
├─ Update DB: active_model_id = new_version
├─ Pods cargan automáticamente versión nueva
└─ Log: Deployment event a Slack

TOTAL TIME: 30-60 minutos promedio
COST: ~$0.50-1.00 por retraining (Lambda + compute)


CODE OUTLINE:
─────────────
@daily_job
def retrain_pipeline(tenant_id):
    """Daily retraining for each tenant"""
    
    # Paso 1: Fetch data
    df_new = fetch_recent_data(tenant_id, days=7)
    df_historical = fetch_historical(tenant_id, days=90)
    df_combined = pd.concat([df_historical, df_new])
    
    # Paso 2: Features
    X, y = engineer_features(df_combined)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
    
    # Paso 3: Train
    model_new = XGBRegressor()
    model_new.fit(X_train, y_train)
    
    # Paso 4: Evaluate
    mae_new = mean_absolute_error(y_val, model_new.predict(X_val))
    mae_old = get_current_model_mae(tenant_id)
    
    # Paso 5: Decision
    if mae_new < mae_old * 0.95:
        # Paso 6: Deploy
        save_model_s3(model_new, tenant_id)
        update_active_model(tenant_id, model_new)
        notify(f"✅ Model deployed for {tenant_id}")
    else:
        notify(f"⚠️ Model not improved for {tenant_id}")
```

---

## VIII. SEGURIDAD Y COMPLIANCE

### 8.1 Consideraciones Críticas

```
DATA SECURITY:
├─ Cifrado en tránsito: HTTPS/TLS 1.3
├─ Cifrado en reposo: AWS KMS encryption
├─ JWT tokens: RS256 algo
├─ Password: bcrypt + salt
├─ Rate limiting: 100 req/min por API key
└─ CORS: Solo dominios autorizados

PRIVACY:
├─ GDPR-ready (aunque no aplica Perú, buena práctica)
├─ Data retention: Configurable por cliente
├─ Derecho a olvido: Purga historico
├─ Términos de servicio claros
└─ Política privacidad transparente

COMPLIANCE PERUANA:
├─ Ley de Protección de Datos (LPDP)
├─ Autoridad: APDP (Autoridad Protección Datos)
├─ Requisitos: Consentimiento, transparencia
├─ Penalties: Hasta S/. 200,000 si viola
└─ Data residency: OPCIONAL (podría ser requerimiento)

AUDITORÍA:
├─ Logs todas queries (tenant_id + timestamp)
├─ Logs acceso modelo
├─ Logs cambios permiso
└─ 90 días retenidos mínimo


ROADMAP COMPLIANCE:
─────────────────
MVP:          Básico (funciona)
Fase 2:       Data privacy + términos
Fase 3:       Compliance peruana
Fase 4:       ISO 27001, SOC 2
```

### 8.2 Disaster Recovery

```
RTO: Recovery Time Objective = 1 hora (máx downtime)
RPO: Recovery Point Objective = 1 día (máx data loss)

BACKUP STRATEGY:
├─ Database backups: Diarios (AWS RDS automated)
├─ Modelos: Versionados en S3 (immutable)
├─ Código: GitHub (version control)
├─ Config: Infrastructure as Code (Terraform)
└─ Documentación: README + runbooks

DISASTER SCENARIOS:
──────────────────
Escenario A: DB corrompida
└─ Acción: Restore from RDS snapshot (15 min)

Escenario B: API servidor down
└─ Acción: Auto-scaling reinicia Pod (3-5 min)

Escenario C: Model corrupted
└─ Acción: Rollback a versión anterior (1 min)

Escenario D: Ataque DDOS
└─ Acción: AWS Shield + rate limiting automático

Escenario E: Falla AWS región
└─ Acción: Multi-region replication (Fase 4)
```

---

## IX. DECISIONES ARQUITECTÓNICAS CLAVE

### 9.1 Trade-offs Justificados

```
DECISIÓN 1: Multi-tenancy vs Mono-tenancy
ELEGIDO: Multi-tenancy
JUSTIFICACIÓN:
├─ Reduce costos operacionales 70%
├─ Permite escalabilidad a 1000+ clientes
├─ Versioning único beneficia todos
└─ Desventaja complejidad técnica vale la pena

DECISIÓN 2: Modelo Global + Per-Tenant vs Solo Global
ELEGIDO: Híbrido
JUSTIFICACIÓN:
├─ MVP rápido (modelo global)
├─ Escalabilidad mantenida (per-tenant opcional)
├─ Clientes pequeños felices con global
├─ Clientes grandes pueden escalar luego

DECISIÓN 3: FastAPI vs Flask vs Django
ELEGIDO: FastAPI
JUSTIFICACIÓN:
├─ Async performance (50-100x más rápido)
├─ Auto-docs (Swagger)
├─ Type hints (desarrollo robusto)
├─ Deployment simple con Uvicorn
└─ Flask sería más lento, Django overkill

DECISIÓN 4: PostgreSQL vs MongoDB
ELEGIDO: PostgreSQL
JUSTIFICACIÓN:
├─ Datos estructurados (relacional ideal)
├─ ACID transactions (consistency crítica)
├─ TimescaleDB extension (series temporales)
├─ Mejor para multi-tenancy
└─ MongoDB worse para queries tenant isolation

DECISIÓN 5: Kubernetes vs Serverless (Lambda)
ELEGIDO: Kubernetes (EKS)
JUSTIFICACIÓN:
├─ Control fino sobre recursos
├─ Costo predecible (vs Lambda por invocación)
├─ Mejor performance consistente
├─ State persistence más fácil
└─ Lambda para batch jobs sí

DECISIÓN 6: Retraining Diario vs Realtime
ELEGIDO: Diario (batch)
JUSTIFICACIÓN:
├─ Costo 10x menor
├─ 94.3% accuracy suficiente daily
├─ Realtime = data stale 23 horas igual
├─ Simplicidad operacional
└─ Option realtime en Fase 4
```

---

## X. RESUMEN EJECUTIVO

### 10.1 The Stack

```
PREDICAST = La solución SaaS para forecast demanda
             Diseñada específicamente para Perú

PILLARS:
1. 🏭 PARA MANUFACTURERS
   └─ Optimización inventario + producción

2. ☁️ CLOUD-NATIVE
   └─ Escalable, confiable, accesible

3. 🤖 ML POTENTE
   └─ XGBoost 94.3% accuracy (probado)

4. 💰 ECONOMÍA CLARA
   └─ $299/mes, ROI 300%+ año 1

5. 📈 CRECIMIENTO LEAN
   └─ Rentable desde mes 3


TIMELINE:
─────────
Fase 1 (4 sem):  MVP desarrollado
Fase 2 (4 sem):  5-10 clientes beta pagos
Fase 3 (8 sem):  50-100 clientes, profit evident
Fase 4 (12 sem): Features enterprise, 200+ clientes


RESOURCES:
──────────
Equipo: 1 Dev Senior + 1 parte-time ML + 1 parte-time Ops
Budget: $30K (MVP) + $5K/mes operación
ARR Potencial: $720K en 12 meses si se ejecuta

RIESGO: MÁS BAJO (problema real, solución validada)
OPORTUNIDAD: ALTO (mercado Perú sin competencia)
```

### 10.2 Go-to-Market Roadmap

```
TIMELINE                ACTION                      EXPECTED RESULT
─────────────────────────────────────────────────────────────────
Week 1-4    Develop MVP                            API + Dashboard
Week 5-8    3 clientes beta (gratis)               Product-market fit validado
Week 9-10   Soft launch ($199/mes early-bird)      10-15 clientes
Week 11-14  Inbound marketing + outreach           30-50 clientes
Month 4-6   Process optimization + support         100+ clientes, MRR $28K
Month 7-12  Growth marketing + enterprise          200+ clientes, Revenue $60K/mes

DECISION POINT: Month 3
├─ IF <10 clientes → Pivote producto o mercado
├─ IF 10-30 clientes → Continue con plan
└─ IF >30 clientes → Accelerate plan, hire team

INVESTMENT REQUIRED:
├─ MVP: $30K (one-time)
├─ Team: $5K/mes (dev senior part-time)
├─ Marketing: $1-2K/mes (Ads + content)
├─ Infra ops: $600/mes (AWS + tools)
└─ Total Year 1: ~$100-120K
```

---

**DOCUMENTO ARQUITECTÓNICO COMPLETADO**

Siguientes pasos:
1. Validar decisiones técnicas ¿Cambios?
2. Confirmar timeline (¿realista para equipo?)
3. Comenzar construcción Fase 1
