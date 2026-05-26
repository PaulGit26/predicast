# 🚀 PREDICAST v4.0 - Sistema Inteligente de Planificación de Demanda

**Plataforma profesional de forecasting y planificación inteligente de producción basada en Machine Learning**

---

## 📋 Descripción General

PREDICAST v4.0 es un sistema integral de **predicción de demanda** y **planificación optimizada de producción** que combina:

- 🤖 **Machine Learning avanzado** con XGBoost (R² = 0.9939)
- 📊 **Dashboard ejecutivo** con análisis detallado por producto
- 📈 **Pronósticos de 52 semanas** con intervalos de confianza
- 🏭 **Algoritmo dinámico** de optimización de producción semanal
- 💰 **Análisis de impacto** financiero del exceso de inventario
- 👥 **Análisis comparativo** de múltiples productos

---

## ✨ Características Principales

### 1. **Predicción Inteligente**
- Modelo XGBoost entrenado con datos históricos de 222 semanas
- Lag features de 4, 8, 12 y 16 semanas para capturar patrones temporales
- Intervalo de confianza del 95% para cada pronóstico
- Volatilidad histórica y tendencias a 52 semanas

### 2. **Dashboard Profesional**
- **Demanda y Componentes**: Histórico + pronóstico en tiempo real
- **Stock y Diagnóstico**: Análisis de rotación, volatilidad y tendencias
- **Comparador de Modelos**: Benchmarking entre diferentes algoritmos
- **Recomendación Individual**: Plan optimizado de producción
- **Análisis de Grupo**: Comparativa entre productos
- **Análisis Extendido**: Drill-down técnico y estadísticas

### 3. **Optimización de Producción**
Algoritmo dinámico que calcula semanalmente:
```
IF Stock_Actual >= Stock_Seguridad:
    Producción = 0  (usa stock existente)
ELSE:
    Producción = Déficit_Solo  (repone solo lo necesario)
```

**Calculado como:**
- Stock de Seguridad = μ + 1.65σ (95% service level)
- Garantiza níveis óptimos sin exceso de inventario
- Minimiza capital inmovilizado mientras mantiene disponibilidad

### 4. **Análisis de Impacto Financiero**
- Cuantificación del capital inmovilizado innecesariamente
- Comparación: viejo algoritmo vs optimizado
- ROI potencial de la optimización
- Oportunidad anual en liberación de capital

---

## 🏗️ Arquitectura

```
PREDICAST/
├── src/
│   ├── api/              # Flask API backend
│   │   ├── main.py
│   │   ├── routes.py
│   │   └── forecasting_routes.py
│   ├── ml/               # Machine Learning
│   │   ├── model_loader.py
│   │   └── predictor.py
│   ├── ui/               # Streamlit Dashboard
│   │   ├── dashboard_v4.py  (dashboard principal)
│   │   └── dashboard_v3.py  (versión anterior)
│   ├── db/               # Base de datos
│   └── utils/            # Utilidades y constantes
├── docs/                 # Documentación
├── tests/                # Tests unitarios
├── requirements.txt      # Dependencias Python
└── run.py                # Script de inicio
```

---

## 🛠️ Tecnologías

- **Backend**: Flask
- **Frontend**: Streamlit
- **ML**: XGBoost, Scikit-learn, NumPy, Pandas
- **Visualización**: Plotly
- **Data**: CSV, JSON, SQLite3

---

## 📦 Instalación

### Requisitos Previos
- Python 3.8+
- Git
- pip o conda

### Pasos

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/predicast.git
cd predicast/07_Sistema_Produccion
```

2. **Crear entorno virtual**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Iniciar el sistema**
```bash
python run.py
```

El sistema levantará:
- 🔹 **API Flask**: http://localhost:5000
- 🔹 **Dashboard Streamlit**: http://localhost:8501

---

## 🚀 Uso Rápido

### Ejecutar Dashboard
```bash
streamlit run src/ui/dashboard_v4.py
```

### Ejecutar API
```bash
python src/api/main.py
```

### Hacer Predicción
```bash
curl http://localhost:5000/api/v1/forecasting/52weeks/CP_01
```

---

## 📊 Flujo de Datos

```
CSV Histórico 
    ↓
XGBoost Training
    ↓
Model Serialization (.joblib)
    ↓
API Flask (Predicciones)
    ↓
Dashboard Streamlit (Visualización)
    ↓
Recomendaciones de Producción
```

---

## 📈 Resultados Modelo XGBoost

- **R² Score**: 0.9939
- **MAE**: 17.34 unidades
- **RMSE**: 22.18 unidades
- **Training Set**: 222 semanas de datos históricos
- **Forecast Horizon**: 52 semanas

---

## 🔧 API Endpoints

### Forecasting
- `GET /api/v1/forecasting/all-products` - Todos los productos
- `GET /api/v1/forecasting/52weeks/{product_id}` - Pronóstico 52 semanas
- `POST /api/v1/forecasting/custom` - Pronóstico personalizado

### Datos
- `GET /api/v1/data/historical/{product_id}` - Datos históricos
- `GET /api/v1/data/statistics` - Estadísticas generales

---

## 📚 Documentación

Ver carpeta `/docs` para:
- [Arquitectura del Sistema](docs/ARQUITECTURA.md)
- [Guía de Inicio Rápido](docs/GUIA_INICIO_RAPIDO.md)
- [Plan Ejecutivo](docs/PLAN_EJECUTIVO_FINAL.md)
- [MVP Plan](docs/MVP_PLAN_4_SEMANAS.md)

---

## 🤝 Workflow Git

Este proyecto usa Git para versionado. Flujo recomendado:

```bash
# Crear rama para feature
git checkout -b feature/nombre-feature

# Hacer cambios y commits
git add .
git commit -m "feat: descripción del cambio"

# Subir a GitHub
git push origin feature/nombre-feature

# Crear Pull Request en GitHub
```

Branch principal: `main` (producción)

---

## 📝 Changelog

### v4.0 (Actual)
- ✅ Dashboard profesional completo
- ✅ Algoritmo dinámico de producción
- ✅ Análisis de impacto financiero
- ✅ Sistema de recomendaciones
- ✅ Versionado con Git

### v3.0
- Versión anterior del dashboard
- Interfaz base

---

## 🐛 Reporte de Issues

Para reportar bugs o sugerir features:
1. Abre un issue en GitHub
2. Incluye pasos para reproducir
3. Describe el comportamiento esperado vs actual

---

## 📄 Licencia

Este proyecto está bajo licencia **Propietaria** (Todos los derechos reservados)

---

## 👨‍💻 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el repositorio
2. Crea una rama para tu feature
3. Abre un Pull Request explicando los cambios

---

## 📞 Contacto

- **Email**: dev@predicast.local
- **GitHub**: https://github.com/tu-usuario/predicast

---

**Desarrollado con ❤️ para optimizar la planificación de demanda**
