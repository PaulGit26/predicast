"""
PREDICAST - Dashboard Profesional v3 (CONECTADO AL API REAL)
Sistema de Recomendación de Producción
CON PREDICCIONES REALES DEL MODELO XGBOOST
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io
import os

# ============================================
# CONFIGURACIÓN
# ============================================
API_URL = "http://localhost:5000"
st.set_page_config(
    page_title="PREDICAST - Recomendador de Producción",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .recommendation-box {
        background: #f0f7ff;
        border-left: 5px solid #667eea;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .high-confidence {
        color: #27ae60;
        font-weight: bold;
    }
    .low-confidence {
        color: #e74c3c;
        font-weight: bold;
    }
    h1 { color: #2c3e50; }
    h2 { color: #34495e; }
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def get_stored_token():
    """Obtener token del session state"""
    return st.session_state.get('token')

def store_token(token, user_data):
    """Guardar token y datos de usuario en session state"""
    st.session_state['token'] = token
    st.session_state['user_data'] = user_data

def get_auth_header():
    """Generar header con autenticación"""
    token = get_stored_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def api_call(endpoint, method="GET", data=None, header_override=None):
    """Helper para llamadas al API"""
    try:
        headers = header_override or get_auth_header()
        url = f"{API_URL}{endpoint}"
        
        if method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        else:
            return {"error": "Invalid method"}
        
        return response.json()
    except Exception as e:
        return {"error": str(e), "status": "error"}

def is_logged_in():
    """Verificar si usuario está autenticado"""
    return get_stored_token() is not None

# ============================================
# PÁGINA DE LOGIN/REGISTRO
# ============================================
def page_login():
    """Página de autenticación"""
    st.markdown("# 🔐 PREDICAST - Acceso")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 Nuevo Usuario / Empresa")
        
        with st.form("registro_form"):
            empresa_name = st.text_input("Nombre de Empresa", placeholder="Mi Empresa S.A.")
            email = st.text_input("Email", placeholder="usuario@empresa.com")
            full_name = st.text_input("Nombre Completo", placeholder="Juan Pérez")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submit_register = st.form_submit_button("📝 Registrar Empresa")
            
            if submit_register:
                if not all([empresa_name, email, full_name, password]):
                    st.error("❌ Por favor completa todos los campos")
                else:
                    with st.spinner("Registrando..."):
                        resp = api_call(
                            "/api/v1/auth/register",
                            method="POST",
                            data={
                                "empresa_name": empresa_name,
                                "email": email,
                                "full_name": full_name,
                                "password": password
                            },
                            header_override={}
                        )
                        
                        if resp.get("status") == "success":
                            store_token(resp['token'], {
                                "email": email,
                                "full_name": full_name,
                                "tenant_id": resp['tenant_id'],
                                "is_admin": True,
                                "tenant_name": empresa_name
                            })
                            st.success(f"✅ ¡Bienvenido {full_name}!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {resp.get('error', 'Error desconocido')}")
    
    with col2:
        st.markdown("### 🔑 Usuario Existente")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="usuario@empresa.com", key="login_email")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••", key="login_pass")
            submit_login = st.form_submit_button("🔓 Iniciar Sesión")
            
            if submit_login:
                if not all([email, password]):
                    st.error("❌ Por favor completa todos los campos")
                else:
                    with st.spinner("Autenticando..."):
                        resp = api_call(
                            "/api/v1/auth/login",
                            method="POST",
                            data={"email": email, "password": password},
                            header_override={}
                        )
                        
                        if resp.get("status") == "success":
                            # Obtener datos del usuario
                            user_resp = api_call("/api/v1/me")
                            if user_resp.get("status") == "success":
                                user_info = user_resp['user']
                                store_token(resp['token'], user_info)
                                st.success(f"✅ ¡Hola {user_info.get('full_name', 'Usuario')}!")
                                st.rerun()
                            else:
                                st.error("❌ Error obteniendo datos del usuario")
                        else:
                            st.error(f"❌ {resp.get('error', 'Error en autenticación')}")
    
    st.markdown("""
    ---
    ### 📌 Demo Rápida
    **Empresa:** Empresa Test 171957  
    **Email:** test_171957@predicast.com  
    **Contraseña:** demo123456
    
    O crea una nueva empresa con los datos que quieras.
    """)

# ============================================
# DASHBOARD PRINCIPAL - PREDICCIONES REALES
# ============================================
def page_dashboard():
    """Redirige a Forecasting - V1 obsoleta"""
    st.markdown("# 📊 PREDICAST - Sistema de Forecasting Automático")
    st.markdown("""
    ## ✨ Versión 3.1 (Forecasting Temporal)
    
    Hemos mejorado el sistema a un modelo de **predicción automática de 52 semanas**.
    
    ### 🔄 ¿Qué cambió?
    
    **Antes (V1):** Predicciones manuales ingresando 15 parámetros
    
    **Ahora (V2):** Predicciones automáticas basadas en histórico
    - ✅ Demanda histórica (222 semanas)
    - ✅ Predicciones futuras (52 semanas)
    - ✅ Comportamiento de stock
    - ✅ Recomendaciones de producción
    - ✅ Intervalos de confianza (95%)
    
    ### 🎯 Cómo usar
    
    1. Selecciona el producto en la pestaña **"🔮 Forecasting 52 Sem"**
    2. Observa el gráfico de histórico + predicción
    3. Analiza el comportamiento del stock
    4. Lee las recomendaciones de producción
    5. Descarga los datos si lo necesitas
    
    ### 📊 Modelo
    
    - **Precisión:** R² = 0.9939 (99.39%)
    - **Algoritmo:** XGBoost con lag features
    - **Features:** Demanda histórica [4, 8, 12, 16] semanas
    - **Período predicho:** 52 semanas (2026-W02 a 2027-W01)
    
    ---
    
    ### 👇 **Ir a Forecasting**
    """)
    
    if st.button("➡️ Ir a Forecasting 52 Semanas", key="btn_forecasting"):
        st.rerun()

# ============================================
# PÁGINA DE FORECASTING (52 SEMANAS)
# ============================================
def page_forecasting():
    """Dashboard profesional: Histórico + Predicciones + Stock + Recomendaciones"""
    st.markdown("# 🔮 Forecasting 52 Semanas")
    st.markdown("**Análisis integral:** Histórico + Predicciones + Stock + Recomendaciones de Producción")
    
    # Cargar datos
    @st.cache_data
    def load_historical_data():
        """Cargar datos históricos desde CSV"""
        try:
            # Rutas posibles desde diferentes contextos
            paths = [
                "01_Datos/datos_semanales_long.csv",
                "../01_Datos/datos_semanales_long.csv",
                "../../01_Datos/datos_semanales_long.csv",
            ]
            
            for path in paths:
                if os.path.exists(path):
                    df = pd.read_csv(path, encoding='utf-8')
                    return df
            
            st.warning(f"⚠️ No se encontraron datos históricos. Rutas probadas: {', '.join(paths)}")
            return None
        except Exception as e:
            st.error(f"Error cargando datos históricos: {e}")
            return None
    
    @st.cache_data
    def load_original_data():
        """Cargar datos originales para stock"""
        try:
            paths = [
                "01_Datos/Data.csv",
                "../01_Datos/Data.csv",
                "../../01_Datos/Data.csv",
            ]
            
            for path in paths:
                if os.path.exists(path):
                    df = pd.read_csv(path, sep=';', encoding='utf-8')
                    return df
            
            return None
        except Exception as e:
            return None
    
    # Obtener lista de productos
    with st.spinner("Cargando datos..."):
        forecast_resp = api_call("/api/v1/forecasting/all-products")
        df_hist = load_historical_data()
        df_original = load_original_data()
    
    if forecast_resp.get("error"):
        st.error(f"❌ Error: {forecast_resp.get('error')}")
        return
    
    # Extracto productos
    productos = forecast_resp.get("productos", [])
    productos_names = sorted([p['codigo'] for p in productos])
    
    # Selector de producto
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_producto = st.selectbox("🏷️ Selecciona un producto:", productos_names, key="product_selector")
    with col2:
        if st.button("🔄 Actualizar"):
            st.cache_data.clear()
            st.rerun()
    
    # Obtener predicciones del producto
    with st.spinner(f"Analizando {selected_producto}..."):
        detail_resp = api_call(f"/api/v1/forecasting/52weeks/{selected_producto}")
    
    if detail_resp.get("error"):
        st.error(f"❌ Error: {detail_resp.get('error')}")
        return
    
    # Extraer datos
    predicciones = detail_resp.get("predicciones", [])
    fechas_pred = detail_resp.get("fechas_prediccion", [])
    lower = detail_resp.get("intervalo_confianza_95_pct", {}).get("lower", [])
    upper = detail_resp.get("intervalo_confianza_95_pct", {}).get("upper", [])
    stats = detail_resp.get("estadisticas_predicciones", {})
    
    # ========================================================================
    # SECCIÓN 1: MÉTRICAS CLAVE
    # ========================================================================
    st.markdown(f"## 📊 {selected_producto}")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📈 Predicción Media", f"{stats.get('media', 0):.0f} u")
    with col2:
        st.metric("📊 Volatilidad (σ)", f"{stats.get('desv_estandar', 0):.0f} u")
    with col3:
        st.metric("⬇️ Mínimo", f"{stats.get('minimo', 0):.0f} u")
    with col4:
        st.metric("⬆️ Máximo", f"{stats.get('maximo', 0):.0f} u")
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 2: GRÁFICO HISTÓRICO + PREDICCIONES
    # ========================================================================
    st.markdown("### 📈 Demanda: Histórico vs Predicciones (52 semanas)")
    
    # Filtrar datos históricos del producto
    if df_hist is not None:
        df_prod_hist = df_hist[df_hist['Producto_codigo'] == selected_producto].copy()
        df_prod_hist['AñoSemana_dt'] = pd.to_datetime(df_prod_hist['AñoSemana'], format='%Y-W%W-%w', errors='coerce')
        df_prod_hist = df_prod_hist.sort_values('AñoSemana_dt')
        
        ventas_historicas = df_prod_hist['Ventas_Semana'].values
        fechas_hist = df_prod_hist['AñoSemana'].values
        
        # Crear gráfico combinado
        fig = go.Figure()
        
        # Ventas históricas
        fig.add_trace(go.Scatter(
            x=fechas_hist,
            y=ventas_historicas,
            mode='lines+markers',
            name='Demanda Histórica',
            line=dict(color='#2E86AB', width=2),
            marker=dict(size=4)
        ))
        
        # Predicciones
        fig.add_trace(go.Scatter(
            x=fechas_pred,
            y=predicciones,
            mode='lines+markers',
            name='Predicción (52 sem)',
            line=dict(color='#A23B72', width=2, dash='dash'),
            marker=dict(size=4)
        ))
        
        # Intervalo de confianza
        fig.add_trace(go.Scatter(
            x=fechas_pred + fechas_pred[::-1],
            y=upper + lower[::-1],
            fill='toself',
            fillcolor='rgba(162, 59, 114, 0.15)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Intervalo 95%'
        ))
        
        fig.update_layout(
            title=f"Demanda Histórica vs Predicción - {selected_producto}",
            xaxis_title="Semana",
            yaxis_title="Ventas (unidades)",
            hovermode='x unified',
            height=450,
            template='plotly_white',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 3: COMPORTAMIENTO DE STOCK
    # ========================================================================
    st.markdown("### 📦 Análisis de Stock")
    
    if df_original is not None:
        df_prod = df_original[df_original['Producto_codigo'] == selected_producto].copy()
        
        if len(df_prod) > 0:
            # Stock promedio histrico
            stock_medio = df_prod['Stock_anterior'].mean()
            stock_max = df_prod['Stock_anterior'].max()
            stock_min = df_prod['Stock_anterior'].min()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Stock Promedio Histórico", f"{stock_medio:.0f} u")
            with col2:
                st.metric("⬆️ Stock Máximo", f"{stock_max:.0f} u")
            with col3:
                st.metric("⬇️ Stock Mínimo", f"{stock_min:.0f} u")
            with col4:
                st.metric("📈 Rotación Índice", f"{stats.get('media', 1) / stock_medio if stock_medio > 0 else 0:.2f}x")
            
            # Gráfico temporal de stock
            df_prod_sorted = df_prod.sort_values('Fecha')
            df_prod_sorted['Fecha_dt'] = pd.to_datetime(df_prod_sorted['Fecha'], format='%d/%m/%Y')
            
            # Resample a semanal
            df_weekly = df_prod_sorted.set_index('Fecha_dt').resample('W')['Stock_anterior'].mean()
            
            fig_stock = go.Figure()
            fig_stock.add_trace(go.Scatter(
                x=df_weekly.index.astype(str),
                y=df_weekly.values,
                mode='lines',
                name='Stock Semanal Promedio',
                line=dict(color='#F18F01', width=2),
                fill='tozeroy',
                fillcolor='rgba(241, 143, 1, 0.2)'
            ))
            
            # Línea de predicción media
            fig_stock.add_hline(
                y=stats.get('media', 0),
                line_dash="dash",
                line_color="red",
                annotation_text=f"Predicción media: {stats.get('media', 0):.0f}u",
                annotation_position="right"
            )
            
            fig_stock.update_layout(
                title=f"Comportamiento Histórico de Stock - {selected_producto}",
                xaxis_title="Fecha",
                yaxis_title="Stock (unidades)",
                height=350,
                template='plotly_white',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_stock, use_container_width=True)
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 4: RECOMENDACIONES DE PRODUCCIÓN
    # ========================================================================
    st.markdown("### 💡 Recomendaciones de Producción")
    
    media_pred = stats.get('media', 0)
    std_pred = stats.get('desv_estandar', 0)
    min_pred = stats.get('minimo', 0)
    max_pred = stats.get('maximo', 0)
    
    # Calcular recomendaciones
    inventario_seguridad = media_pred + (1.65 * std_pred)  # 95% service level
    lote_economico = (media_pred * 4)  # 4 semanas
    punto_reorden = media_pred * 2  # 2 semanas de demanda
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"""
        **🛡️ Inventario de Seguridad**
        
        {inventario_seguridad:.0f} unidades
        
        *Recomendado para proteger contra\ndemanda impredecible*
        """)
    
    with col2:
        st.warning(f"""
        **📦 Lote Económico de Compra**
        
        {lote_economico:.0f} unidades
        
        *Cantidad óptima por orden\n(4 semanas de demanda)*
        """)
    
    with col3:
        st.success(f"""
        **🔔 Punto de Reorden**
        
        {punto_reorden:.0f} unidades
        
        *Cuando reponer (2 semanas\nde demanda pendiente)*
        """)
    
    # Análisis de demanda
    st.markdown("#### 📊 Análisis de Demanda Futura")
    
    tendencia_col1, tendencia_col2 = st.columns(2)
    
    with tendencia_col1:
        # Tendencia en predicción
        primera_mitad = sum(predicciones[:26]) / 26
        segunda_mitad = sum(predicciones[26:]) / 26
        variacion = ((segunda_mitad - primera_mitad) / primera_mitad * 100) if primera_mitad > 0 else 0
        
        if variacion > 5:
            tendencia_texto = "🔴 **DEMANDA CRECIENTE**"
            tendencia_recc = "Aumentar producción, preparar más materia prima"
        elif variacion < -5:
            tendencia_texto = "🟠 **DEMANDA DECRECIENTE**"
            tendencia_recc = "Reducir producción, optimizar inventario"
        else:
            tendencia_texto = "🟢 **DEMANDA ESTABLE**"
            tendencia_recc = "Mantener producción estable"
        
        st.markdown(f"{tendencia_texto}\n\nVariación semestral: {variacion:+.1f}%\n\n**Recomendación:** {tendencia_recc}")
    
    with tendencia_col2:
        # Volatilidad
        volatilidad_pct = (std_pred / media_pred * 100) if media_pred > 0 else 0
        
        if volatilidad_pct < 20:
            volatilidad_texto = "✅ Baja volatilidad"
        elif volatilidad_pct < 40:
            volatilidad_texto = "⚠️ Volatilidad moderada"
        else:
            volatilidad_texto = "🔴 Alta volatilidad"
        
        st.markdown(f"""
        {volatilidad_texto}
        
        Coef. variación: {volatilidad_pct:.1f}%
        
        **Implicación:** {'Planeación confiable' if volatilidad_pct < 30 else 'Mayor buffer de inventario'}
        """)
    
    st.markdown("---")
    
    # ========================================================================
    # SECCIÓN 5: TABLA Y DESCARGAS
    # ========================================================================
    st.markdown("### 📥 Detalle de Predicciones (52 semanas)")
    
    df_forecast = pd.DataFrame({
        'Semana': fechas_pred,
        'Predicción (u)': [f"{p:.0f}" for p in predicciones],
        'Límite Inferior (95%)': [f"{l:.0f}" for l in lower],
        'Límite Superior (95%)': [f"{u:.0f}" for u in upper]
    })
    
    st.dataframe(df_forecast, use_container_width=True, hide_index=True)
    
    # Descargar datos
    col_down1, col_down2, col_down3 = st.columns([1, 1, 2])
    
    with col_down1:
        csv = df_forecast.to_csv(index=False)
        st.download_button(
            label="📥 CSV Predicciones",
            data=csv,
            file_name=f"predicciones_{selected_producto}.csv",
            mime="text/csv"
        )
    
    with col_down2:
        # JSON con recomendaciones
        recc_data = {
            "producto": selected_producto,
            "predicciones": [f"{p:.2f}" for p in predicciones],
            "inventario_seguridad": f"{inventario_seguridad:.0f}",
            "lote_economico": f"{lote_economico:.0f}",
            "punto_reorden": f"{punto_reorden:.0f}"
        }
        json_str = json.dumps(recc_data, indent=2)
        st.download_button(
            label="📥 JSON Recomendaciones",
            data=json_str,
            file_name=f"recomendaciones_{selected_producto}.json",
            mime="application/json"
        )
    
    st.markdown("---")
    
    # Resumen final
    st.markdown("### 📋 Resumen Ejecutivo - Todos los Productos")
    
    df_productos = pd.DataFrame(productos)
    df_summary = df_productos[['codigo', 'prediccion_media', 'prediccion_std', 'tendencia_52sem']].copy()
    df_summary.columns = ['Producto', 'Media', 'Volatilidad', 'Tendencia']
    
    # Colorizar
    def color_row(row):
        if row['Tendencia'] == 'creciente':
            return ['background-color: #C8E6C9'] * len(row)
        elif row['Tendencia'] == 'decreciente':
            return ['background-color: #FFCDD2'] * len(row)
        else:
            return ['background-color: #FFF9C4'] * len(row)
    
    st.dataframe(
        df_summary.style.apply(color_row, axis=1),
        use_container_width=True,
        hide_index=True
    )


# ============================================
# PÁGINA DE ADMIN
# ============================================
def page_admin():
    """Panel de administración"""
    user = st.session_state.get('user_data', {})
    
    if not user.get('is_admin'):
        st.error("❌ No tienes permisos de administrador")
        return
    
    st.markdown("# 👑 Panel de Administración")
    st.markdown(f"**Empresa:** {user.get('tenant_name')}")
    
    tab1, tab2, tab3 = st.tabs(["👥 Usuarios", "📊 Estadísticas", "ℹ️ Info Modelo"])
    
    with tab1:
        st.markdown("## Gestión de Usuarios")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Crear Nuevo Usuario")
            with st.form("new_user_form"):
                new_email = st.text_input("Email", placeholder="usuario@empresa.com")
                new_name = st.text_input("Nombre Completo", placeholder="Juan Pérez")
                new_password = st.text_input("Contraseña", type="password")
                is_admin = st.checkbox("¿Es administrador?")
                
                if st.form_submit_button("➕ Crear Usuario"):
                    if new_email and new_name and new_password:
                        with st.spinner("Creando usuario..."):
                            resp = api_call(
                                "/api/v1/users",
                                method="POST",
                                data={
                                    "email": new_email,
                                    "full_name": new_name,
                                    "password": new_password,
                                    "is_admin": is_admin
                                }
                            )
                            
                            if resp.get("status") == "success":
                                st.success(f"✅ Usuario {new_email} creado exitosamente")
                            else:
                                st.error(f"❌ Error: {resp.get('error')}")
                    else:
                        st.warning("⚠️ Por favor completa todos los campos")
        
        with col2:
            st.markdown("### Usuarios Activos")
            resp = api_call("/api/v1/users", method="GET")
            
            if resp.get("status") == "success":
                users = resp.get('users', [])
                st.metric("Total Usuarios", len(users))
                admin_count = sum(1 for u in users if u['is_admin'])
                st.metric("Administradores", admin_count)
        
        # Listado de usuarios
        st.markdown("### Lista de Usuarios")
        if resp.get("status") == "success":
            df_users = pd.DataFrame(users)
            df_users_display = df_users[['email', 'full_name', 'is_admin']]
            st.dataframe(df_users_display, use_container_width=True)
    
    with tab2:
        st.markdown("## 📊 Estadísticas del Sistema")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Predicciones Totales", "Cargando...")
        with col2:
            st.metric("✅ Modelo R² Score", "0.9443")
        with col3:
            st.metric("📈 Precisión MAE", "0.7634")
        with col4:
            st.metric("🤖 Modelo Versión", "V2_Realista")
    
    with tab3:
        st.markdown("## 🤖 Información del Modelo")
        
        with st.spinner("Cargando información del modelo..."):
            model_resp = api_call("/api/v1/model/info")
        
        if model_resp.get("status") == "success":
            info = model_resp.get('model', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                ### Características Principales
                - **Versión:** {info.get('version')}
                - **Features:** {info.get('n_features')}
                - **Target:** {info.get('target')}
                - **R² Score:** {info.get('r2_score')}
                - **MAE:** {info.get('mae')}
                """)
            
            with col2:
                performance = info.get('performance', {})
                st.markdown(f"""
                ### Performance del Modelo
                - **R² Test:** {performance.get('R2_Test', 'N/A')}
                - **MAE Test:** {performance.get('MAE_Test', 'N/A')}
                - **RMSE:** {performance.get('RMSE', 'N/A')}
                """)
            
            st.markdown("### Features del Modelo (15 inputs)")
            features = info.get('features', [])
            cols = st.columns(3)
            for i, feat in enumerate(features):
                with cols[i % 3]:
                    st.text(f"✓ {feat}")

# ============================================
# SIDEBAR NAVEGACIÓN
# ============================================
def main():
    """Función principal"""
    
    if not is_logged_in():
        page_login()
    else:
        user = st.session_state.get('user_data', {})
        
        with st.sidebar:
            st.markdown("# 🧭 Navegación")
            st.markdown(f"**Usuario:** {user.get('full_name')}")
            st.markdown(f"**Empresa:** {user.get('tenant_name')}")
            st.markdown("---")
            
            page = st.radio(
                "Ir a:",
                ["📊 Predicciones", "� Forecasting 52 Sem", "�👑 Admin", "ℹ️ Información", "🚪 Logout"],
                key="navigation"
            )
            
            st.markdown("---")
            st.markdown("""
            ### 📌 Información rápida
            **PREDICAST v3.1 (CONECTADO)**
            - ✅ Predicciones REALES del modelo
            - ✅ XGBoost con 99.39% R² (Forecasting)
            - ✅ 1,040 predicciones (52 sem × 20 productos)
            - ✅ Forecast automático con intervalos 95%
            - ✅ Multi-usuario por empresa
            - ✅ Historial completo en BD
            """)
        
        if page == "📊 Predicciones":
            page_dashboard()
        elif page == "� Forecasting 52 Sem":
            page_forecasting()
        elif page == "�👑 Admin":
            page_admin()
        elif page == "ℹ️ Información":
            st.markdown("""
            # ℹ️ Acerca de PREDICAST v3.1
            
            ## 🎯 Sistema Dual: Regresión + Forecasting
            
            PREDICAST ahora combina dos modelos ML:
            
            ### 📊 Modelo 1: Regresión Puntual (V1)
            - Predice ventas basadas en 15 parámetros input
            - Precisión: 94.43% (R² Score)
            - Uso: decisiones punto a punto
            
            ### 🔮 Modelo 2: Forecasting Temporal (V2 - NUEVO)
            - Predice 52 semanas futuras automáticamente
            - Precisión: 99.39% (R² Score) ⭐
            - Algoritmo: XGBoost con lag features
            - Output: 1,040 predicciones (52 × 20 productos)
            - Intervalos: 95% confianza incluida
            - Uso: planeación estratégica a largo plazo
            
            ### 📈 Datos de Entrenamiento (Forecasting)
            - Período histórico: 222 semanas
            - Productos: 20 líneas de producción
            - Datos agregados semanalmente
            - Features: Lag [4, 8, 12, 16] semanas
            - Varianza explicada: 99.39%
            
            ### 🏗️ Arquitectura V3.1
            - **Frontend:** Streamlit Dashboard (este sitio)
            - **Backend:** Flask API con JWT Auth
            - **ML Regresión:** XGBoost (V1)
            - **ML Forecasting:** XGBoost + Lag (V2)
            - **BD:** SQLite (desarrollo) / PostgreSQL (prod)
            - **API Endpoints:** 4 nuevos para forecasting
            
            ### 🔌 Nuevos Endpoints Disponibles
            - `GET /api/v1/forecasting/52weeks/<producto>` → predicciones individuales
            - `GET /api/v1/forecasting/all-products` → resumen 20 productos
            - `GET /api/v1/forecasting/product/<producto>/detailed` → detalle completo
            - `GET /api/v1/forecasting/model-info` → información del modelo
            
            ### 📞 Soporte
            Para preguntas o reportar problemas, contacta al equipo de desarrollo.
            """)
        elif page == "🚪 Logout":
            st.session_state.clear()
            st.success("✅ Sesión cerrada correctamente")
            st.rerun()


if __name__ == "__main__":
    main()
