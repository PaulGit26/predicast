# 🚀 ARQUITECTURA DEL SISTEMA DE RECOMENDACIÓN DE PRODUCCIÓN

**Estado:** 📋 Planificación
**Próximo Paso:** Construir API + Lógica de Recomendación

---

## 🏗️ ARQUITECTURA GENERAL

```
┌─────────────────────────────────────────────────────────────────┐
│                     USUARIO / APLICACIÓN                        │
│                    (Dashboard / Móvil)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓  API REST
┌─────────────────────────────────────────────────────────────────┐
│              07_Sistema_Produccion/api_servidor.py              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  POST /api/v1/predecir_demanda                           │   │
│  │  GET  /api/v1/recomendacion_produccion                   │   │
│  │  GET  /api/v1/escenarios                                 │   │
│  │  POST /api/v1/reentrenar_modelo                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────┬─────────────────────────────────────────────────────────┘
         │
         ├──────────────────┬──────────────────┬──────────────────┐
         ↓                  ↓                  ↓                  ↓
    ┌─────────┐       ┌──────────┐     ┌────────────┐     ┌─────────┐
    │Predictor│       │Recomendador│    │Reentrenador│     │Database │
    │         │       │            │    │            │     │         │
    │ .joblib │       │Fórmula    │    │ Validación │     │ SQLite  │
    │ loader  │       │ Demanda   │    │  MAE       │     │  PostV  │
    │         │       │-Stock+Buf │    │ Histórico  │     │         │
    └────┬────┘       └─────┬──────┘    └─────┬──────┘     └────┬────┘
         │                  │                 │                 │
         └──────────────────┴─────────────────┴─────────────────┘
                            │
                            ↓
         ┌──────────────────────────────────┐
         │  logs/  (registro de predicciones)│
         │  data/  (histórico de recomenda-│
         │  backup/(modelos anteriores)     │
         └──────────────────────────────────┘
```

---

## 📁 ARCHIVOS A CREAR EN 07_Sistema_Produccion/

### **1. api_servidor.py** - API REST

```python
from flask import Flask, request, jsonify
import joblib
import pandas as pd
from datetime import datetime

app = Flask(__name__)
modelo = joblib.load('../03_Modelos/xgboost_model_V2_Realista.joblib')

@app.route('/api/v1/predecir_demanda', methods=['POST'])
def predecir_demanda():
    """
    Input:  {producto_codigo, fecha, stock_actual}
    Output: {cantidad_predicha, confianza, timestamp}
    """
    # Implementar lógica
    pass

@app.route('/api/v1/recomendacion_produccion', methods=['GET'])
def recomendacion_produccion():
    """
    Input:  producto_codigo, fecha, stock_actual, buffer
    Output: {produccion_recomendada, demanda_predicha, reasoning}
    """
    pass
```

### **2. predictor.py** - Clase predictor

```python
class Predictor:
    def __init__(self, modelo_path, metadata_path):
        self.modelo = cargar_modelo(modelo_path)
        self.metadata = cargar_metadata(metadata_path)
        self.features = metadata['features']
    
    def preparar_features(self, datos_producto):
        """Convierte datos raw → features normalizados"""
        pass
    
    def predecir(self, features):
        """Realiza predicción con modelo"""
        # MAE: 0.7683
        # Tiempo: <10ms
        pass
    
    def predecir_con_confianza(self, features):
        """Predice + calcula intervalo de confianza"""
        # Retorna: cantidad, lower_bound, upper_bound
        pass
```

### **3. recomendador.py** - Lógica de recomendación

```python
class Recomendador:
    
    def recomendar_produccion(self, demanda_predicha, stock_actual, buffer=0.5):
        """
        Fórmula base:
        Producción = Demanda_predicha - Stock_actual + Buffer
        
        Output:
        {
            'produccion_recomendada': int,
            'demanda_predicha': float,
            'stock_actual': int,
            'buffer': float,
            'reasoning': str
        }
        """
        pass
    
    def generar_escenarios(self, demanda_predicha):
        """
        Retorna 3 escenarios:
        
        Conservative:  Demanda * 0.85 (sin stock)
        Normal:        Demanda * 1.00 + buffer
        Optimistic:    Demanda * 1.15 + buffer
        """
        pass
    
    def validar_recomendacion(self, recomendacion):
        """
        Valida vs histórico:
        - No > 3x promedio diario
        - No < mínimo histórico
        - Alerta si anomalía
        """
        pass
```

### **4. requirements_prod.txt** - Dependencias

```
flask==2.3.0
xgboost==2.0.3
scikit-learn==1.3.2
pandas==2.1.3
numpy==1.26.2
joblib==1.3.2
python-dotenv==1.0.0
```

### **5. config.py** - Configuración

```python
MODELO_PATH = '../03_Modelos/xgboost_model_V2_Realista.joblib'
METADATA_PATH = '../03_Modelos/xgboost_metadata_V2_Realista.json'
DATABASE_PATH = 'data/predicciones.db'
LOG_PATH = 'logs/'

PORT = 5000
DEBUG = False
```

### **6. README.md** - Instrucciones

```markdown
# Sistema de Recomendación de Producción

## Instalación
pip install -r requirements_prod.txt

## Ejecutar
python api_servidor.py
→ Servidor en http://localhost:5000

## Endpoints
POST /api/v1/predecir_demanda
GET  /api/v1/recomendacion_produccion
POST /api/v1/reentrenar_modelo
```

---

## 📊 FLUJO DE DATOS

### **Caso 1: Predecir Demanda**

```
Usuario solicita:
"¿Cuánta demanda de CP_01 el 2026-04-15?"

┌────────────────────────────────────────────────┐
│ POST /api/v1/predecir_demanda                  │
│ {                                              │
│   "producto_codigo": "CP_01",                  │
│   "fecha": "2026-04-15"                        │
│ }                                              │
└────────────┬───────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────┐
│ Predictor                                      │
│ ├─ Extraer temporal: Año=2026, Mes=4, etc     │
│ ├─ Encode: Producto_codigo → 11 (number)      │
│ ├─ Agregar: Promedio demanda CP_01 = 6.2      │
│ └─ Feed 15 features → Modelo XGBoost          │
└────────────┬───────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────┐
│ Respuesta                                      │
│ {                                              │
│   "cantidad_predicha": 5.8,                    │
│   "confianza": 0.94,  (R²=0.9432)             │
│   "intervalo_95pct": [3.2, 8.4],              │
│   "timestamp": "2026-04-04T14:32:10Z",        │
│   "tiempo_procesamiento_ms": 8.3               │
│ }                                              │
└────────────────────────────────────────────────┘
```

### **Caso 2: Recomendación de Producción**

```
Usuario solicita:
"Recomienda producción para CP_01 hoy"

┌────────────────────────────────────────────────┐
│ GET /api/v1/recomendacion_produccion           │
│ ?producto=CP_01&stock_actual=12&buffer=1.0    │
└────────────┬───────────────────────────────────┘
             │
             ↓  [Predictor]
    Demanda predicha hoy = 5.2
             │
             ↓  [Recomendador]
    Fórmula: 5.2 - 12 + 1.0 = -5.8
    → NO PRODUCIR (hay stock suficiente)
             │
             ↓
┌────────────────────────────────────────────────┐
│ Respuesta                                      │
│ {                                              │
│   "produccion_recomendada": 0,                 │
│   "demanda_predicha": 5.2,                     │
│   "stock_actual": 12,                          │
│   "buffer": 1.0,                               │
│   "reasoning": "Stock suficiente para 2.2 días│
│                de demanda + buffer",           │
│   "escenarios": {                              │
│     "conservative": 0,  (4.4 - 12 + 0)        │
│     "normal": 0,        (5.2 - 12 + 1.0)      │
│     "optimistic": 0     (6.0 - 12 + 1.0)      │
│   }                                            │
│ }                                              │
└────────────────────────────────────────────────┘
```

### **Caso 3: Reentrenamiento Automático**

```
Fin de mes: 2026-05-01

Scheduler ejecuta:
POST /api/v1/reentrenar_modelo

┌────────────────────────────────────────────────┐
│ Reentrenador                                   │
│ ├─ Cargar últimos 30 días de datos             │
│ ├─ Entrenar nuevo modelo XGBoost              │
│ ├─ Evaluar: MAE_nuevo = 0.7512               │
│ ├─ Comparar: 0.7512 < 0.7683? SÍ ✓           │
│ │  Mejora: -0.0171 (-2.2%) → ACEPTAR         │
│ └─ Backup modelo anterior y activar nuevo    │
└────────────┬───────────────────────────────────┘
             │
             ↓
┌────────────────────────────────────────────────┐
│ Respuesta                                      │
│ {                                              │
│   "exito": true,                               │
│   "mae_anterior": 0.7683,                      │
│   "mae_nuevo": 0.7512,                         │
│   "mejora_pct": -2.2,                          │
│   "r2_anterior": 0.9432,                       │
│   "r2_nuevo": 0.9465,                          │
│   "timestamp": "2026-05-01T00:01:00Z",        │
│   "mensaje": "Modelo actualizado con éxito"   │
│ }                                              │
└────────────────────────────────────────────────┘
```

---

## 🎯 INDICADORES CLAVE (KPIs)

### **Modelo**
```
✅ MAE:             0.7683 (error promedio en unidades)
✅ R²:              0.9432 (94.32% varianza explicada)
✅ RMSE:            1.4229 (penaliza errores grandes)
✅ Latencia:        <10ms (requerimiento: <50ms)
```

### **Producción**
```
📊 Cobertura:       "% predicciones que aciertan dentro ±1 unidad"
📊 Stock_out:       "Veces que no hay stock cuando se predice"
📊 Over-production: "Unidades excedentes producidas"
📊 Cost of error:   "Costo promedio de error de predicción"
```

### **Sistema**
```
⏱️ Uptime:           >99.5% (Target)
⏱️ Tiempo respuesta: <100ms (Target)
🔄 Reentrenamiento: Cada 30 días
🔍 Auditable:       100% logs de decisiones
```

---

## 📋 CHECKLIST PARA CONSTRUIR

### **Semana 1: API Base**
- [ ] Estructura de carpetas 07_Sistema_Produccion/
- [ ] api_servidor.py (Flask skeleton)
- [ ] predictor.py (Cargar modelo + predecir)
- [ ] Endpoint: /api/v1/predecir_demanda (GET)
- [ ] Testing con Postman

### **Semana 2: Lógica de Recomendación**
- [ ] recomendador.py (Clase con fórmula)
- [ ] Escenarios (Conservative/Normal/Optimistic)
- [ ] Validación vs histórico
- [ ] Endpoint: /api/v1/recomendacion_produccion
- [ ] Documentación de API

### **Semana 3: Automatización**
- [ ] Reentrenamiento automático (scheduler)
- [ ] Database de predicciones (SQLite)
- [ ] Logging de decisiones
- [ ] Endpoint: /api/v1/reentrenar_modelo
- [ ] Testing end-to-end

### **Semana 4: Producción**
- [ ] Environment variables (.env)
- [ ] Docker container (opcional)
- [ ] Deployment instrucciones
- [ ] Monitoring + alerting
- [ ] Documentación final

---

## 🔗 INTEGRACIÓN CON EXISTENTE

```
Estado Actual:
├─ ✅ Modelo entrenado (03_Modelos/)
├─ ✅ Función reentrenamiento  (04_Scripts/)
├─ ✅ Features validados       (06_Documentacion/)
└─ ✅ Arquitectura definida    (Este documento)

Próximo:
└─ 🚀 Construir Sistema de Recomendación
   ├─ API servidor
   ├─ Lógica de negocio
   ├─ Base de datos
   └─ Automatización
```

---

**¿Listo para construir?** 🚀

Próximo paso: Crear `api_servidor.py` con Flask + endpoints iniciales
