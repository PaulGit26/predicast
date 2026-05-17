# PREDICAST - Resumen para Exposición
## Carpeta `07_Sistema_Produccion`

---

## 1. ¿Qué es esta carpeta?

La carpeta `07_Sistema_Produccion` contiene la **versión operativa del sistema PREDICAST**. Aquí vive la capa que conecta el modelo con el usuario final: la **API**, el **dashboard**, la **base de datos**, la **lógica de autenticación** y la **capa de ML**.

En otras palabras, esta carpeta convierte el trabajo de análisis y predicción en un **sistema usable en producción**.

---

## 2. Objetivo general

Su objetivo es permitir que el sistema:
- reciba solicitudes de usuarios,
- ejecute o sirva predicciones,
- muestre resultados en un dashboard interactivo,
- y guarde información en base de datos cuando corresponde.

---

## 3. Componentes principales

### `run.py` — Orquestador del sistema
Es el archivo de entrada para arrancar el sistema.

**Funciones principales:**
- Ejecutar la **API Flask**.
- Ejecutar el **dashboard Streamlit**.
- Lanzar ambos servicios por separado o en conjunto.
- Servir como punto de inicio simple para el despliegue local.

**Importancia para la exposición:**
- Es el “botón de arranque” del sistema.
- Hace posible levantar la solución sin entrar a cada módulo manualmente.

---

### `src/api/main.py` — Núcleo de la API
Es el archivo que crea y configura la aplicación Flask.

**Hace lo siguiente:**
- carga variables de entorno,
- habilita CORS,
- intenta cargar el modelo ML,
- inicializa la base de datos,
- registra las rutas,
- y carga las predicciones precalculadas para el sistema de forecasting.

**Punto clave:**
- Si no encuentra el modelo `.joblib`, la API no se cae: usa **predicciones precalculadas desde CSV**.

**Importancia para la exposición:**
- Es el corazón técnico del backend.
- Mantiene el sistema funcional incluso sin el modelo entrenado en archivo.

---

### `src/api/routes.py` — Rutas de negocio y autenticación
Aquí están los endpoints principales del sistema general.

**Incluye:**
- registro de empresa y usuario,
- login,
- validación de token JWT,
- predicción individual,
- predicción por lote,
- consulta de información del modelo.

**Qué resuelve:**
- Seguridad y acceso,
- control de usuarios,
- registro de predicciones,
- y comunicación con la capa ML.

**Importancia para la exposición:**
- Convierte la API en una solución multiusuario.
- No solo predice: también autentica y guarda historial.

---

### `src/api/forecasting_routes.py` — Rutas de forecasting
Es la parte especializada para el dashboard de pronóstico.

**Proporciona endpoints como:**
- resumen de todos los productos,
- predicción de 52 semanas por producto,
- detalle completo por producto,
- información del modelo,
- análisis económico simplificado.

**Cómo funciona:**
- carga CSVs de predicciones ya generadas,
- los mantiene en memoria,
- y los expone por API para que el dashboard los consuma.

**Importancia para la exposición:**
- Es el puente entre el pipeline de predicción y la visualización final.
- Hace que el dashboard responda rápido porque usa datos ya preparados.

---

### `src/db/` — Base de datos y modelos
Esta carpeta contiene la estructura de persistencia del sistema.

#### `config.py`
Define:
- URL de conexión,
- sesión SQLAlchemy,
- `Base` de modelos,
- creación y eliminación de tablas.

#### `models.py`
Define las entidades:
- `Tenant` → empresa o cliente,
- `User` → usuario,
- `Prediction` → predicción guardada,
- `ModelMetadata` → metadata del modelo.

**Importancia para la exposición:**
- Esta carpeta hace que el sistema no sea solo visualización, sino una plataforma con memoria y trazabilidad.

---

### `src/utils/` — Utilidades y seguridad
Contiene lógica de soporte reutilizable.

#### `auth.py`
- crea y valida tokens JWT,
- cifra y verifica contraseñas.

#### `constants.py`
- define features requeridas,
- encodings de categorías,
- catálogos de productos y empresas,
- umbrales y métricas base.

**Importancia para la exposición:**
- Es la base de seguridad y configuración técnica del sistema.
- Centraliza valores que el backend necesita para funcionar de forma consistente.

---

### `src/ml/` — Capa de Machine Learning
Contiene la lógica para cargar y usar el modelo entrenado.

#### `model_loader.py`
- carga el archivo `.joblib`,
- carga la metadata del modelo,
- valida que todo esté consistente.

#### `predictor.py`
- prepara las variables de entrada,
- aplica encodings,
- ejecuta la predicción,
- devuelve resultado, confianza y métricas.

**Importancia para la exposición:**
- Es la capa que conecta el modelo entrenado con la API.
- Permite que el sistema use ML real cuando el modelo está disponible.

**Estado actual del proyecto:**
- en esta ejecución, el modelo no estaba presente,
- por eso la API funciona con predicciones precalculadas.

---

### `src/ui/dashboard_v4.py` — Dashboard ejecutivo
Es la interfaz visual del sistema.

**Muestra:**
- métricas principales,
- análisis por producto,
- comparaciones entre productos,
- gráficos interactivos,
- resumen económico,
- recomendaciones ejecutivas.

**Tecnología:**
- construido con Streamlit,
- enriquecido con Plotly y CSS personalizado,
- diseñado para una presentación profesional.

**Importancia para la exposición:**
- Es la cara visible del sistema.
- Convierte datos técnicos en información entendible para negocio.

---

## 4. Flujo de funcionamiento

El flujo de esta carpeta es el siguiente:

1. `run.py` levanta la solución.
2. `src/api/main.py` inicializa la API.
3. `src/db/` maneja la persistencia.
4. `src/utils/` aporta seguridad y constantes.
5. `src/ml/` carga y usa el modelo si existe.
6. `src/api/forecasting_routes.py` expone predicciones.
7. `src/ui/dashboard_v4.py` consume la API y muestra resultados.

---

## 5. Qué aporta al sistema completo

Esta carpeta aporta tres cosas clave:

- **Operatividad:** convierte el pipeline en un sistema usable.
- **Escalabilidad:** separa API, BD, ML y UI.
- **Presentación ejecutiva:** permite visualizar las predicciones de forma clara.

---

## 6. Resultado visible

Gracias a `07_Sistema_Produccion`, PREDICAST puede:

- arrancar como servicio,
- autenticar usuarios,
- guardar predicciones,
- cargar resultados de forecasting,
- y mostrarlos en un dashboard profesional.

---

## 7. Resumen corto para decir en exposición

> La carpeta `07_Sistema_Produccion` convierte todo el trabajo analítico en una solución operativa. Aquí están la API, el dashboard, la base de datos, la autenticación y la capa ML. En conjunto, esta carpeta hace que PREDICAST pase de ser un modelo de análisis a un sistema real listo para uso.

---

**Estado actual:** sistema funcional con API y dashboard, usando predicciones precalculadas cuando no está disponible el modelo `.joblib`.
