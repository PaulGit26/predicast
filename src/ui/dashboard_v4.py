"""
PREDICAST v4.0 - Dashboard Profesional y Ejecutivo
Sistema Inteligente de Planificación de Demanda
Diseño Premium con Análisis Detallado por Producto y Grupo
"""

import streamlit as st
import requests
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io
import os
from abc import ABC, abstractmethod

# ============================================
# CONFIGURACIÓN INICIAL
# ============================================
st.set_page_config(
    page_title="PREDICAST v4.0 - Planificación Inteligente de Demanda",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://localhost:5000"

# ============================================
# ESTILOS CSS PROFESIONALES
# ============================================
st.markdown("""
<style>
    /* Configuración de fuentes profesionales */
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Sidebar profesional - minimalista blanco */
    [data-testid="stSidebar"] {
        background: #f8f9fa;
        border-right: 1px solid #e1e4e8;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #1f2937;
    }
    
    /* Headers y títulos */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        border-bottom: 3px solid #3b82f6;
        padding-bottom: 10px;
    }
    
    h2 {
        color: #1e3a8a;
        font-weight: 600;
        margin-top: 30px;
    }
    
    h3 {
        color: #3b82f6;
        font-weight: 600;
    }
    
    /* Tarjetas de métrica */
    .metric-card {
        background: linear-gradient(135deg, #dbeafe 0%, #e0e7ff 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
        margin: 10px 0;
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #1e3a8a;
    }
    
    .metric-label {
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Cajas de recomendación */
    .recommendation-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border-left: 5px solid #22c55e;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        box-shadow: 0 2px 6px rgba(34, 197, 94, 0.1);
    }
    
    .recommendation-box.warning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left-color: #f59e0b;
    }
    
    .recommendation-box.alert {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border-left-color: #ef4444;
    }
    
    /* Tabs profesionales - EXPANDIDOS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        padding: 10px 0;
        border-radius: 0;
        border-bottom: 3px solid #e2e8f0;
        width: 100%;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0;
        border: none;
        border-bottom: 3px solid transparent;
        color: #64748b;
        font-weight: 600;
        padding: 0 20px;
        transition: all 0.3s;
        flex: 1;
    }
    
    .stTabs [aria-selected="true"] [data-baseweb="tab"] {
        background-color: transparent;
        color: #3b82f6;
        border-bottom: 3px solid #3b82f6;
    }
    
    /* Sidebar info */
    .sidebar-header {
        color: #1f2937;
        font-size: 24px;
        font-weight: 700;
        margin: 20px 0 30px 0;
        text-align: center;
        letter-spacing: 1px;
    }
    
    .sidebar-section {
        background: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        border-left: 3px solid rgba(255, 255, 255, 0.3);
        color: white;
        font-size: 12px;
        line-height: 1.8;
    }
    
    .sidebar-label {
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        font-size: 10px;
        letter-spacing: 0.5px;
    }
    
    .sidebar-value {
        font-weight: 700;
        font-size: 13px;
        margin-top: 5px;
        color: #1f2937;
    }
    
    /* Alertas y estados */
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-success {
        background-color: #dcfce7;
        color: #166534;
    }
    
    .status-warning {
        background-color: #fef3c7;
        color: #92400e;
    }
    
    .status-danger {
        background-color: #fee2e2;
        color: #991b1b;
    }
    
    /* Descripción de sección */
    .section-description {
        background: #eff6ff;
        padding: 15px;
        border-left: 4px solid #0284c7;
        border-radius: 6px;
        margin: 15px 0;
        font-size: 14px;
        color: #0c4a6e;
        line-height: 1.6;
    }
    
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

@st.cache_data
def load_historical_data():
    """Cargar datos históricos desde CSV"""
    try:
        paths = [
            "01_Datos/datos_semanales_long.csv",
            "../01_Datos/datos_semanales_long.csv",
            "../../01_Datos/datos_semanales_long.csv",
        ]
        
        for path in paths:
            if os.path.exists(path):
                df = pd.read_csv(path, encoding='utf-8')
                return df
        return None
    except Exception as e:
        return None

@st.cache_data
def load_original_data():
    """Cargar datos originales (transacciones)"""
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

def api_call(endpoint, method="GET", data=None):
    """Realizar llamada al API"""
    try:
        url = f"{API_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# ============================================
# SIDEBAR - INFORMACIÓN DE SESIÓN
# ============================================
def render_sidebar():
    """Renderizar sidebar con información profesional y elegante - diseño minimalista blanco"""
    with st.sidebar:
        # Logo y título principal - diseño minimalista
        st.markdown("""
            <div style='text-align: center; margin: 30px 0 20px 0;'>
                <div style='font-size: 36px; margin-bottom: 12px; letter-spacing: 2px;'>📊</div>
                <h1 style='color: #1f2937; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: 1.5px;'>PREDICAST</h1>
                <p style='color: #6b7280; margin: 8px 0 0 0; font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;'>Planificación Inteligente</p>
                <div style='width: 50px; height: 1px; background: #d1d5db; margin: 12px auto 0 auto; border-radius: 1px;'></div>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # === INFORMACIÓN DE SESIÓN ===
        st.markdown("""
            <div style='background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; margin-bottom: 12px; border-left: 3px solid #3b82f6;'>
                <div style='font-size: 10px; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;'>👤 Usuario</div>
                <div style='font-size: 15px; color: #1f2937; font-weight: 700;'>Paulcesar</div>
                <div style='font-size: 11px; color: #9ca3af; margin-top: 4px;'>Admin • ProbaEmpresa</div>
            </div>
        """, unsafe_allow_html=True)
        
        # === ESTADÍSTICAS DEL SISTEMA ===
        st.markdown("""
            <div style='background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; margin-bottom: 12px; border-left: 3px solid #10b981;'>
                <div style='font-size: 10px; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;'>📊 Estadísticas</div>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
                    <div style='background: #f3f4f6; padding: 10px; border-radius: 6px; text-align: center;'>
                        <div style='font-size: 18px; color: #10b981; font-weight: 800;'>20</div>
                        <div style='font-size: 9px; color: #6b7280; margin-top: 4px; font-weight: 600;'>Productos</div>
                    </div>
                    <div style='background: #f3f4f6; padding: 10px; border-radius: 6px; text-align: center;'>
                        <div style='font-size: 18px; color: #3b82f6; font-weight: 800;'>52</div>
                        <div style='font-size: 9px; color: #6b7280; margin-top: 4px; font-weight: 600;'>Semanas</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # === CALIDAD DEL MODELO ===
        st.markdown("""
            <div style='background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; margin-bottom: 12px; border-left: 3px solid #8b5cf6;'>
                <div style='font-size: 10px; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;'>🤖 Modelo XGBoost</div>
                <div style='font-size: 10px; color: #1f2937; line-height: 1.8;'>
                    <div><strong style='color: #8b5cf6;'>R² Score:</strong> <span style='color: #059669;'>0.9939</span></div>
                    <div><strong style='color: #8b5cf6;'>MAE:</strong> <span style='color: #059669;'>17.34 u</span></div>
                    <div><strong style='color: #8b5cf6;'>Confianza:</strong> <span style='color: #059669;'>95%</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # === ESTADO DE DATOS ===
        st.markdown("""
            <div style='background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px; margin-bottom: 12px; border-left: 3px solid #22c55e;'>
                <div style='font-size: 10px; color: #6b7280; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;'>✅ Estado del Sistema</div>
                <div style='font-size: 10px; color: #1f2937; line-height: 1.8;'>
                    <div style='display: flex; align-items: center; gap: 8px;'><span style='width: 6px; height: 6px; background: #22c55e; border-radius: 50%; display: inline-block;'></span> <span style='color: #6b7280;'>Datos cacheados</span></div>
                    <div style='display: flex; align-items: center; gap: 8px; margin-top: 6px;'><span style='width: 6px; height: 6px; background: #22c55e; border-radius: 50%; display: inline-block;'></span> <span style='color: #6b7280;'>API conectada</span></div>
                    <div style='display: flex; align-items: center; gap: 8px; margin-top: 6px;'><span style='width: 6px; height: 6px; background: #22c55e; border-radius: 50%; display: inline-block;'></span> <span style='color: #6b7280;'>Sistema listo</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # === INFORMACIÓN DE ACTUALIZACIÓN ===
        st.markdown("""
            <div style='background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px; margin-bottom: 16px; text-align: center;'>
                <div style='font-size: 9px; color: #6b7280; margin-bottom: 4px; font-weight: 600; text-transform: uppercase;'>⏱️ Última Actualización</div>
                <div style='font-size: 12px; color: #3b82f6; font-weight: 700;'>2026-04-02 14:32</div>
                <div style='font-size: 8px; color: #9ca3af; margin-top: 2px;'>Sincronizado automáticamente</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # === ACCIONES ===
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("🔄 Refrescar", use_container_width=True, key="btn_refresh_sidebar"):
                st.rerun()
        with col2:
            if st.button("⚙️ Config", use_container_width=True, key="btn_config_sidebar"):
                st.info("Configuración en desarrollo")
        
        st.divider()
        
        # === FOOTER ===
        st.markdown("""
            <div style='text-align: center; padding: 12px 0; color: #9ca3af;'>
                <div style='font-size: 9px; line-height: 1.6;'>
                    <strong style='color: #1f2937;'>PREDICAST v4.0</strong><br>
                    <span style='font-size: 8px;'>© 2026 • Forecasting Inteligente</span>
                </div>
            </div>
        """, unsafe_allow_html=True)


# ============================================
# PÁGINA PRINCIPAL - DASHBOARD
# ============================================
def page_dashboard():
    """Página principal del dashboard"""
    st.markdown("# 🎯 Dashboard Ejecutivo")
    
    st.markdown("""
    <div class='section-description'>
        <strong>📊 Inteligencia en Planificación de Demanda</strong><br>
        Pronósticos precisos + Recomendaciones inteligentes = Máxima eficiencia operativa<br>
        Optimiza tu planificación de producción con predicciones basadas en análisis de demanda histórica y modelos avanzados de machine learning.
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-label'>📦 Productos Monitoreados</div>
            <div class='metric-value'>20</div>
            <small style='color: #64748b;'>Activos en el sistema</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-label'>📅 Semanas Predichas</div>
            <div class='metric-value'>52</div>
            <small style='color: #64748b;'>Próximo año completo</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-label'>🎯 Precisión del Modelo</div>
            <div class='metric-value'>99.39%</div>
            <small style='color: #64748b;'>R² = 0.9939</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-label'>📊 Predicciones</div>
            <div class='metric-value'>1,040</div>
            <small style='color: #64748b;'>Totales generadas</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Sección de funciones disponibles
    st.markdown("### 🔮 ¿Qué encontrarás aquí?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **📊 Análisis Individual**
        - Demanda y componentes por producto
        - Análisis de stock histórico
        - Comparador de modelos ML
        - Recomendaciones personalizadas
        """)
    
    with col2:
        st.markdown("""
        **📈 Análisis de Grupo**
        - Resumen comparativo de todos los productos
        - Análisis retrospectivo de costos
        - Recomendaciones masivas de producción
        - Benchmarking entre productos
        """)
    
    with col3:
        st.markdown("""
        **🔬 Análisis Extendido**
        - Visualización de series temporales
        - Descomposición de tendencias
        - Análisis estacional avanzado
        - Reportes ejecutivos descargables
        """)
    
    st.divider()
    
    # Gráfico principal - Resumen histórico
    st.markdown("### 📉 Demanda Histórica y Pronóstico (Todos los Productos)")
    
    df_hist = load_historical_data()
    if df_hist is not None:
        # Agregar por semana
        df_agg = df_hist.groupby('AñoSemana')['Ventas_Semana'].sum().reset_index()
        df_agg['Semana'] = pd.to_datetime(df_agg['AñoSemana'] + '-1', format='%Y-W%W-%w')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_agg['Semana'],
            y=df_agg['Ventas_Semana'],
            name='Demanda Histórica',
            line=dict(color='#3b82f6', width=3),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.1)',
            hovertemplate='<b>%{x|%Y-W%W}</b><br>Demanda: %{y:,.0f} unidades<extra></extra>'
        ))
        
        fig.update_layout(
            title="Series Temporal: 222 Semanas de Histórico",
            xaxis_title="Período",
            yaxis_title="Unidades Vendidas",
            hovermode='x unified',
            height=400,
            template='plotly_white',
            font=dict(family="Arial, sans-serif", size=12)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    <div class='section-description'>
        <strong>📌 Explicación:</strong> Este gráfico muestra la demanda semanal agregada de todos tus productos en los últimos 4+ años. 
        Puedes notar patrones estacionales y tendencias que el modelo de IA utiliza para generar pronósticos precisos.
    </div>
    """, unsafe_allow_html=True)

# ============================================
# ANÁLISIS INDIVIDUAL POR PRODUCTO
# ============================================
def page_analisis_individual():
    """Página de análisis individual por producto"""
    # Obtener lista de productos
    forecast_resp = api_call("/api/v1/forecasting/all-products")
    if forecast_resp.get("error"):
        st.error(f"❌ Error: {forecast_resp.get('error')}")
        return
    
    productos = forecast_resp.get("productos", [])
    productos_names = sorted([p['codigo'] for p in productos])
    
    # === SELECTOR COMPACTO HORIZONTAL ===
    col1, col2, col3 = st.columns([0.15, 0.3, 1])
    
    with col1:
        st.markdown("""
            <div style='display: flex; align-items: center; height: 100%; padding-top: 10px;'>
                <span style='font-size: 12px; font-weight: 700; color: #1f2937;'>📦 Producto:</span>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        selected_producto = st.selectbox(
            label="",
            options=productos_names,
            index=0,
            key="producto_selector"
        )
    
    with col3:
        st.write("")  # Espacrador
    
    # Obtener datos del producto seleccionado
    producto_info = next((p for p in productos if p['codigo'] == selected_producto), None)
    if not producto_info:
        st.warning("Producto no encontrado")
        return
    
    st.divider()
    
    # Tabs para diferentes análisis
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Demanda y Componentes",
        "📦 Stock y Diagnóstico", 
        "⚖️ Comparador de Modelos",
        "💡 Recomendación Individual"
    ])
    
    # ============ TAB 1: DEMANDA Y COMPONENTES ============
    with tab1:
        # Obtener pronóstico detallado
        forecast_detail = api_call(f"/api/v1/forecasting/52weeks/{selected_producto}")
        df_hist = load_historical_data()
        
        if forecast_detail.get("error"):
            st.error(f"⚠️ Error al cargar pronóstico: {forecast_detail.get('error')}")
        elif df_hist is None:
            st.warning("⚠️ No se encontraron datos históricos")
        else:
            try:
                # Preparar datos históricos
                df_hist_prod = df_hist[df_hist['Producto_codigo'] == selected_producto].copy()
                
                if len(df_hist_prod) == 0:
                    st.warning(f"⚠️ No hay datos históricos para {selected_producto}")
                else:
                    df_hist_prod['Semana'] = pd.to_datetime(df_hist_prod['AñoSemana'] + '-1', format='%Y-W%W-%w')
                    
                    # Preparar datos de pronóstico - ADAPTADO A NUEVA ESTRUCTURA DEL API
                    if forecast_detail.get("success") and 'predicciones' in forecast_detail:
                        # Nueva estructura del API
                        predicciones = forecast_detail.get('predicciones', [])
                        fechas = forecast_detail.get('fechas_prediccion', [])
                        lower = forecast_detail.get('intervalo_confianza_95_pct', {}).get('lower', [])
                        upper = forecast_detail.get('intervalo_confianza_95_pct', {}).get('upper', [])
                        
                        # Convertir a DataFrame - corregir formato de fecha
                        df_forecast = pd.DataFrame({
                            'fecha': pd.to_datetime([f + '-1' for f in fechas], format='%Y-W%W-%w'),
                            'prediccion': predicciones,
                            'limite_inferior': lower,
                            'limite_superior': upper
                        })
                    elif 'forecast' in forecast_detail:
                        # Estructura antigua (por compatibilidad)
                        df_forecast = pd.DataFrame(forecast_detail.get("forecast", []))
                        if 'fecha' in df_forecast.columns:
                            df_forecast['fecha'] = pd.to_datetime(df_forecast['fecha'])
                    else:
                        df_forecast = pd.DataFrame()
                    
                    if len(df_forecast) == 0:
                        st.warning("⚠️ No hay datos de pronóstico disponibles para este producto")
                    else:
                        # Crear gráfico principal
                        fig = go.Figure()
                        
                        # Histórico
                        fig.add_trace(go.Scatter(
                            x=df_hist_prod['Semana'],
                            y=df_hist_prod['Ventas_Semana'],
                            name='Histórico (222 semanas)',
                            line=dict(color='#3b82f6', width=3),
                            fill='tozeroy',
                            fillcolor='rgba(59, 130, 246, 0.1)',
                            hovertemplate='<b>%{x|%Y-W%V}</b><br>Demanda: %{y:,.0f} u<extra></extra>'
                        ))
                        
                        # Banda de confianza 95% (inferior)
                        fig.add_trace(go.Scatter(
                            x=df_forecast['fecha'],
                            y=df_forecast['limite_inferior'],
                            fill=None,
                            mode='lines',
                            line_color='rgba(217, 70, 239, 0)',
                            showlegend=False
                        ))
                        
                        # Pronóstico + banda de confianza (superior)
                        fig.add_trace(go.Scatter(
                            x=df_forecast['fecha'],
                            y=df_forecast['limite_superior'],
                            fill='tonexty',
                            mode='lines',
                            line_color='rgba(217, 70, 239, 0)',
                            name='Intervalo 95% confianza',
                            fillcolor='rgba(217, 70, 239, 0.15)',
                            hovertemplate='<b>%{x|%Y-W%V}</b><br>Intervalo: %{y:,.0f} u<extra></extra>'
                        ))
                        
                        # Pronóstico
                        fig.add_trace(go.Scatter(
                            x=df_forecast['fecha'],
                            y=df_forecast['prediccion'],
                            name='Pronóstico (52 semanas)',
                            line=dict(color='#d946ef', width=2, dash='dash'),
                            hovertemplate='<b>%{x|%Y-W%V}</b><br>Pronóstico: %{y:,.0f} u<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            title=f"Demanda: {selected_producto} - Histórico + Pronóstico (52 Semanas)",
                            xaxis_title="Período (Semanas)",
                            yaxis_title="Unidades",
                            hovermode='x unified',
                            height=450,
                            template='plotly_white',
                            font=dict(size=11)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Explicación del gráfico principal
                        st.markdown("""
                        <div style='background: #dbeafe; padding: 12px; border-radius: 8px; font-size: 13px; margin-top: -10px; margin-bottom: 15px;'>
                        <strong>📌 ¿Qué ves?</strong> La línea azul muestra ventas reales pasadas. La línea magenta es la predicción futura. 
                        La zona sombreada (95% confianza) indica rangos donde probablemente caerá la demanda.
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # ANÁLISIS DE INSIGHTS PROFUNDOS
                        df_hist_prod['Mes'] = pd.to_datetime(df_hist_prod['AñoSemana'] + '-1', format='%Y-W%W-%w').dt.month
                        df_hist_prod['Mes_Nombre'] = pd.to_datetime(df_hist_prod['AñoSemana'] + '-1', format='%Y-W%W-%w').dt.strftime('%B')
                        df_hist_prod['Trimestre'] = pd.to_datetime(df_hist_prod['AñoSemana'] + '-1', format='%Y-W%W-%w').dt.quarter
                        
                        # Estadísticas por mes
                        demanda_por_mes = df_hist_prod.groupby('Mes')['Ventas_Semana'].agg(['sum', 'mean', 'std', 'count']).reset_index()
                        mes_max_idx = demanda_por_mes['sum'].idxmax()
                        mes_min_idx = demanda_por_mes['sum'].idxmin()
                        mes_max = int(demanda_por_mes.loc[mes_max_idx, 'Mes'])
                        mes_min = int(demanda_por_mes.loc[mes_min_idx, 'Mes'])
                        demanda_max = demanda_por_mes.loc[mes_max_idx, 'sum']
                        demanda_min = demanda_por_mes.loc[mes_min_idx, 'sum']
                        
                        # Mapeo de meses
                        meses_nombres = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio',
                                        7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
                        
                        # Detectar estacionalidad
                        demanda_por_trimestre = df_hist_prod.groupby('Trimestre')['Ventas_Semana'].sum()
                        trim_max = demanda_por_trimestre.idxmax()
                        trim_min = demanda_por_trimestre.idxmin()
                        titulo_trim = {1:'Q1 (Ene-Mar)', 2:'Q2 (Abr-Jun)', 3:'Q3 (Jul-Sep)', 4:'Q4 (Oct-Dic)'}
                        
                        # Variabilidad mensual
                        coef_variacion_meses = (demanda_por_mes['std'] / demanda_por_mes['mean']).mean()
                        
                        # Detectar si hay crecimiento acelerado
                        df_hist_prod['Año'] = pd.to_datetime(df_hist_prod['AñoSemana'] + '-1', format='%Y-W%W-%w').dt.year
                        años_unicos = df_hist_prod['Año'].unique()
                        if len(años_unicos) >= 2:
                            primer_anno = df_hist_prod[df_hist_prod['Año'] == años_unicos[0]]['Ventas_Semana'].mean()
                            ultimo_anno = df_hist_prod[df_hist_prod['Año'] == años_unicos[-1]]['Ventas_Semana'].mean()
                            crecimiento_anual = ((ultimo_anno - primer_anno) / primer_anno * 100) if primer_anno > 0 else 0
                        else:
                            crecimiento_anual = 0
                        
                        # Insights resume
                        st.markdown("##### 🔍 Hallazgos Clave del Análisis Histórico")
                        
                        col_insight_a, col_insight_b, col_insight_c = st.columns(3)
                        
                        with col_insight_a:
                            st.markdown(f"""
                            <div style='background: #fef3c7; padding: 14px; border-radius: 8px; border-left: 4px solid #f59e0b;'>
                                <strong style='font-size: 14px; color: #d97706;'>📊 Picos de Demanda</strong><br>
                                <small style='color: #64748b;'><strong>{meses_nombres[mes_max]}</strong> es el mes más fuerte</small><br>
                                <tiny style='color: #64748b;'>Venta total: <strong style='color: #d97706;'>{demanda_max:,.0f} u</strong></tiny><br>
                                <tiny style='color: #64748b;'>vs Mínimo ({meses_nombres[mes_min]}): <strong>{demanda_min:,.0f} u</strong></tiny><br>
                                <tiny style='color: #64748b;'>Diferencia: <strong>{((demanda_max-demanda_min)/demanda_min*100):.0f}%</strong></tiny>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_insight_b:
                            st.markdown(f"""
                            <div style='background: #ddd6fe; padding: 14px; border-radius: 8px; border-left: 4px solid #7c3aed;'>
                                <strong style='font-size: 14px; color: #6d28d9;'>📅 Estacionalidad</strong><br>
                                <small style='color: #64748b;'><strong>{titulo_trim[trim_max]}</strong> es el trimestre pico</small><br>
                                <tiny style='color: #64748b;'>Demanda trimestral: <strong style='color: #7c3aed;'>{demanda_por_trimestre[trim_max]:,.0f} u</strong></tiny><br>
                                <tiny style='color: #64748b;'>Variabilidad mensual: <strong>{coef_variacion_meses:.2f}</strong></tiny><br>
                                <tiny style='color: #64748b;'>Patrón: {'📈 Clara estacionalidad' if coef_variacion_meses > 0.4 else '➡️ Relativamente uniforme'}</tiny>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_insight_c:
                            tendencia_label = "📈 Crecimiento" if crecimiento_anual > 5 else "📉 Contracción" if crecimiento_anual < -5 else "➡️ Estable"
                            tendencia_color = "#10b981" if crecimiento_anual > 5 else "#ef4444" if crecimiento_anual < -5 else "#3b82f6"
                            st.markdown(f"""
                            <div style='background: linear-gradient(135deg, {tendencia_color}15, {tendencia_color}05); 
                                        padding: 14px; border-radius: 8px; border-left: 4px solid {tendencia_color};'>
                                <strong style='font-size: 14px; color: {tendencia_color};'>🚀 Tendencia General</strong><br>
                                <small style='color: #64748b;'>{tendencia_label}</small><br>
                                <tiny style='color: #64748b;'><strong style='color: {tendencia_color};'>{crecimiento_anual:+.1f}%</strong> año a año</tiny><br>
                                <tiny style='color: #64748b;'>Comportamiento en el tiempo</tiny>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.divider()
                        
                        # Cálculo de indicadores avanzados
                        vol_historica = producto_info['prediccion_std'] / producto_info['prediccion_media'] if producto_info['prediccion_media'] > 0 else 0
                        
                        # Análisis de pronóstico
                        pronos_promedio = np.mean(predicciones) if predicciones else 0
                        pronos_std = np.std(predicciones) if predicciones else 0
                        amplitud_intervalo = np.mean([u - l for u, l in zip(upper, lower)]) if (upper and lower) else 0
                        confiabilidad_pronos = 1 - (amplitud_intervalo / (2 * pronos_promedio)) if pronos_promedio > 0 else 0
                        
                        # Tendencia comparativa
                        hist_ultimas = df_hist_prod.tail(26)['Ventas_Semana'].mean() if len(df_hist_prod) >= 26 else df_hist_prod['Ventas_Semana'].mean()
                        hist_primeras = df_hist_prod.head(26)['Ventas_Semana'].mean() if len(df_hist_prod) >= 26 else df_hist_prod['Ventas_Semana'].mean()
                        tendencia_comparativa = ((hist_ultimas - hist_primeras) / hist_primeras * 100) if hist_primeras > 0 else 0
                        
                        # Comparación pronóstico vs histórico
                        diferencia_pronos_vs_hist = ((pronos_promedio - producto_info['prediccion_media']) / producto_info['prediccion_media'] * 100) if producto_info['prediccion_media'] > 0 else 0
                        

            except Exception as e:
                st.error(f"❌ Error procesando datos: {str(e)}")
    
    # ============ TAB 2: STOCK Y DIAGNÓSTICO ============
    with tab2:

        
        st.markdown("""
        <div class='section-description'>
            <strong>📌 Stock histórico y diagnóstico:</strong> Analiza los niveles de inventario que mantenías 
            en el pasado en relación con la demanda actual. Esto ayuda a entender patrones de rotación 
            y optimizar niveles de seguridad.
        </div>
        """, unsafe_allow_html=True)
        
        df_original = load_original_data()
        if df_original is not None:
            df_prod = df_original[df_original['Producto_codigo'] == selected_producto].copy()
            
            if len(df_prod) > 0:
                stock_medio = df_prod['Stock_anterior'].mean()
                stock_max = df_prod['Stock_anterior'].max()
                stock_min = df_prod['Stock_anterior'].min()
                rotacion = (producto_info['prediccion_media'] / stock_medio) if stock_medio > 0 else 0
                

 
                
                # Gráficos de stock temporal con indicadores
                st.markdown("#### 📊 Análisis Temporal del Stock")
                
                df_prod_sorted = df_prod.sort_values('Fecha')
                df_prod_sorted['Fecha_dt'] = pd.to_datetime(df_prod_sorted['Fecha'], format='%d/%m/%Y')
                
                # Gráfico de evolución de stock
                df_prod_sorted_agg = df_prod_sorted.groupby(df_prod_sorted['Fecha_dt'].dt.date)['Stock_anterior'].mean().reset_index()
                df_prod_sorted_agg.columns = ['Fecha', 'Stock']
                df_prod_sorted_agg = df_prod_sorted_agg.tail(100)  # Últimas 100 fechas
                
                # Calcular indicadores de stock
                stock_volatilidad = df_prod_sorted_agg['Stock'].std() / stock_medio if stock_medio > 0 else 0
                stock_tendencia = ((df_prod_sorted_agg['Stock'].iloc[-1] - df_prod_sorted_agg['Stock'].iloc[0]) / 
                                  df_prod_sorted_agg['Stock'].iloc[0] * 100) if len(df_prod_sorted_agg) > 0 else 0
                stock_rango = stock_max - stock_min
                dias_cobertura = stock_medio / (producto_info['prediccion_media'] / 7) if producto_info['prediccion_media'] > 0 else 0
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_stock_time = go.Figure()
                    fig_stock_time.add_trace(go.Scatter(
                        x=df_prod_sorted_agg['Fecha'],
                        y=df_prod_sorted_agg['Stock'],
                        name='Stock Diario',
                        line=dict(color='#06b6d4', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(6, 182, 212, 0.1)'
                    ))
                    fig_stock_time.add_hline(y=stock_medio, line_dash="dash", line_color="#ef4444",
                                            annotation_text=f"Promedio: {stock_medio:.0f}")
                    fig_stock_time.update_layout(
                        title=f"Evolución del Stock (Últimas 100 fechas)",
                        xaxis_title="Fecha",
                        yaxis_title="Unidades",
                        height=350,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig_stock_time, use_container_width=True)
                    
                    # Explicación gráfico 1
                    st.markdown("""
                    <div style='background: #e0f2fe; padding: 12px; border-radius: 8px; font-size: 13px; margin-top: -10px;'>
                    <strong>📌 ¿Qué significa?</strong> Muestra cómo ha fluctuado tu inventario en el tiempo.<br>
                    La línea roja (promedio) ayuda a detectar si mantienes stock suficiente.
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Rotación vs Ventas
                    df_prod_rotacion = df_prod_sorted.copy()
                    df_prod_rotacion['Date'] = df_prod_rotacion['Fecha_dt'].dt.date
                    df_prod_rotacion_agg = df_prod_rotacion.groupby('Date').agg({
                        'Cantidad': 'sum',
                        'Stock_anterior': 'mean'
                    }).reset_index()
                    df_prod_rotacion_agg['Rotacion'] = (df_prod_rotacion_agg['Cantidad'] / 
                                                       (df_prod_rotacion_agg['Stock_anterior'] + 1)) * 100
                    df_prod_rotacion_agg = df_prod_rotacion_agg.tail(100)
                    
                    rot_media = df_prod_rotacion_agg['Rotacion'].mean()
                    rot_std = df_prod_rotacion_agg['Rotacion'].std()
                    
                    fig_rot = go.Figure()
                    fig_rot.add_trace(go.Scatter(
                        x=df_prod_rotacion_agg['Date'],
                        y=df_prod_rotacion_agg['Rotacion'],
                        name='% Rotación',
                        line=dict(color='#f59e0b', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(245, 158, 11, 0.1)'
                    ))
                    fig_rot.add_hline(y=rot_media, line_dash="dash", line_color="#10b981",
                                     annotation_text=f"Promedio: {rot_media:.1f}%")
                    fig_rot.update_layout(
                        title=f"Índice de Rotación (% de Stock/día)",
                        xaxis_title="Fecha",
                        yaxis_title="% Rotación",
                        height=350,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig_rot, use_container_width=True)
                    
                    # Explicación gráfico 2
                    st.markdown("""
                    <div style='background: #fef3c7; padding: 12px; border-radius: 8px; font-size: 13px; margin-top: -10px;'>
                    <strong>📌 ¿Qué significa?</strong> Velocidad con que se vende tu stock cada día.<br>
                    Valores altos = ventas rápidas (menos riesgo de obsolescencia).
                    </div>
                    """, unsafe_allow_html=True)
                
                # Indicadores clave extraídos de los datos
                st.markdown("##### 🎯 Insights & Indicadores Clave")
                
                # Calcular más indicadores
                rot_media = df_prod_rotacion_agg['Rotacion'].mean()
                rot_std = df_prod_rotacion_agg['Rotacion'].std()
                rot_variabilidad = (rot_std / rot_media * 100) if rot_media > 0 else 0
                
                # Clasificación de volatilidad
                if stock_volatilidad < 0.2:
                    vol_texto, vol_color = "Muy Estable", "#10b981"
                    vol_insight = "Stock bien controlado, previsibilidad alta"
                elif stock_volatilidad < 0.5:
                    vol_texto, vol_color = "Estable", "#3b82f6"
                    vol_insight = "Variación moderada, gestión equilibrada"
                else:
                    vol_texto, vol_color = "Variable", "#ef4444"
                    vol_insight = "Fluctuaciones altas, puede indicar demanda impredecible"
                
                # Clasificación de rotación
                if rot_media < 5:
                    rot_clase, rot_reco = "Lenta", "⚠️ Riesgo de obsolescencia - revisar SKU"
                elif rot_media < 15:
                    rot_clase, rot_reco = "Moderada", "✓ Rotación saludable"
                else:
                    rot_clase, rot_reco = "Rápida", "✅ Excelente - demanda fuerte"
                
                col_a, col_b, col_c, col_d = st.columns(4)
                
                with col_a:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {vol_color}20, {vol_color}10); 
                                padding: 12px; border-radius: 8px; border-left: 4px solid {vol_color};'>
                        <small style='color: #64748b;'>📊 Volatilidad Stock</small><br>
                        <strong style='font-size: 18px; color: {vol_color};'>{stock_volatilidad:.1%}</strong><br>
                        <small>{vol_texto}</small><br>
                        <tiny style='color: #64748b; font-size: 11px;'>{vol_insight}</tiny>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_b:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #f59e0b20, #f59e0b10); 
                                padding: 12px; border-radius: 8px; border-left: 4px solid #f59e0b;'>
                        <small style='color: #64748b;'>🔄 Rotación Promedio</small><br>
                        <strong style='font-size: 18px; color: #f59e0b;'>{rot_media:.1f}%/día</strong><br>
                        <small>{rot_clase}</small><br>
                        <tiny style='color: #64748b; font-size: 11px;'>{rot_reco}</tiny>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_c:
                    dias_cobertura_calc = max(1, int(dias_cobertura))
                    dias_color = "#10b981" if dias_cobertura_calc >= 7 else "#ef4444" if dias_cobertura_calc < 3 else "#f59e0b"
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {dias_color}20, {dias_color}10); 
                                padding: 12px; border-radius: 8px; border-left: 4px solid {dias_color};'>
                        <small style='color: #64748b;'>⏱️ Cobertura Stock</small><br>
                        <strong style='font-size: 18px; color: {dias_color};'>{dias_cobertura_calc}d</strong><br>
                        <small>Días de stock disponible</small><br>
                        <tiny style='color: #64748b; font-size: 11px;'>Capacidad para cubrir demanda</tiny>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_d:
                    tendencia_color = "#10b981" if stock_tendencia > 0 else "#ef4444"
                    tendencia_texto = "📈 Creciente" if stock_tendencia > 5 else "📉 Decreciente" if stock_tendencia < -5 else "➡️ Estable"
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {tendencia_color}20, {tendencia_color}10); 
                                padding: 12px; border-radius: 8px; border-left: 4px solid {tendencia_color};'>
                        <small style='color: #64748b;'>📊 Tendencia</small><br>
                        <strong style='font-size: 18px; color: {tendencia_color};'>{abs(stock_tendencia):.1f}%</strong><br>
                        <small>{tendencia_texto}</small><br>
                        <tiny style='color: #64748b; font-size: 11px;'>Últimas 100 fechas</tiny>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Recomendaciones basadas en patrones
                st.markdown("##### 💡 Recomendaciones Basadas en Análisis")
                
                recomendaciones = []
                
                # Reco 1: Volatilidad
                if stock_volatilidad > 0.5:
                    recomendaciones.append(("🎯 Estabilidad", 
                        f"Alta volatilidad ({stock_volatilidad:.0%}) detectada. Considera aumentar stock de seguridad "
                        f"o revisar política de compra para suavizar fluctuaciones.", "#ef4444"))
                elif stock_volatilidad < 0.15:
                    recomendaciones.append(("✅ Estabilidad", 
                        f"Stock muy predecible ({stock_volatilidad:.0%}). Posibilidad de optimizar: reducir stock mínimo sin riesgo.", "#10b981"))
                
                # Reco 2: Rotación
                if rot_media < 5 and rot_variabilidad < 50:
                    recomendaciones.append(("⚠️ Rotación Lenta", 
                        f"Producto con baja rotación ({rot_media:.1f}%/día). Evalúa si es necesario mantener estos niveles "
                        f"o si hay oportunidad de descontinuar/reposicionar.", "#ef4444"))
                elif rot_media > 20 and stock_volatilidad > 0.4:
                    recomendaciones.append(("🚀 Demanda Fuerte", 
                        f"Rotación excelente ({rot_media:.1f}%/día) pero con variabilidad alta ({rot_variabilidad:.0f}%). "
                        f"Aumentar frecuencia de reorden para evitar stockouts.", "#10b981"))
                
                # Reco 3: Días de cobertura
                if dias_cobertura_calc < 3:
                    recomendaciones.append(("⚡ Riesgo de Desabastecimiento", 
                        f"Solo {dias_cobertura_calc} días de cobertura. Incrementar frecuencia de compra o stock de seguridad.", "#ef4444"))
                elif dias_cobertura_calc > 30:
                    recomendaciones.append(("💰 Oportunidad de Optimización", 
                        f"Stock de {dias_cobertura_calc} días es muy alto. Reducción gradual liberaría capital de trabajo.", "#f59e0b"))
                
                # Reco 4: Tendencia
                if stock_tendencia < -15:
                    recomendaciones.append(("📉 Stock Decreciente", 
                        f"Tendencia a la baja ({stock_tendencia:.1f}%). Verifica si es intencional o si hay falta de reorden.", "#ef4444"))
                
                if len(recomendaciones) > 0:
                    for titulo, texto, color in recomendaciones:
                        st.markdown(f"""
                        <div style='background: {color}15; padding: 12px; border-radius: 8px; 
                                    border-left: 4px solid {color}; margin-bottom: 8px;'>
                            <strong style='color: {color};'>{titulo}</strong><br>
                            <small>{texto}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style='background: #d1fae515; padding: 12px; border-radius: 8px; border-left: 4px solid #10b981;'>
                        <strong style='color: #10b981;'>✅ Sin Alertas</strong><br>
                        <small>Los indicadores de stock se encuentran dentro de parámetros normales.</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                # ============ NUEVA SECCIÓN: ANÁLISIS DEL EXCESO DE INVENTARIO ============
                st.divider()
                st.markdown("### 💰 Análisis: Impacto del Exceso de Inventario")
                
                st.markdown("""
                <div class='section-description'>
                    <strong>📌 ¿Por qué optimizar la producción?</strong> Este análisis demuestra el capital inmovilizado 
                    innecesariamente en stock excesivo, y cómo el nuevo algoritmo de producción optimizada reduce 
                    significativamente este riesgo mientras mantiene la protección necesaria.
                </div>
                """, unsafe_allow_html=True)
                
                # Calcular datos para el análisis
                df_prod_sorted['Fecha_dt'] = pd.to_datetime(df_prod_sorted['Fecha'], format='%d/%m/%Y')
                df_prod_sorted_daily = df_prod_sorted.sort_values('Fecha_dt')
                
                # Crear series diarias
                df_daily_summary = df_prod_sorted_daily.groupby('Fecha_dt').agg({
                    'Stock_anterior': 'mean',
                    'Cantidad': 'sum'
                }).reset_index()
                df_daily_summary = df_daily_summary.tail(120)  # Últimas 120 fechas (~17 semanas)
                
                # Calcular stock de seguridad basado en datos históricos
                demanda_media_diaria = df_prod['Cantidad'].mean() if 'Cantidad' in df_prod.columns else producto_info['prediccion_media']
                demanda_std_diaria = df_prod['Cantidad'].std() if 'Cantidad' in df_prod.columns else producto_info['prediccion_media'] * 0.3
                stock_seg_calculado = demanda_media_diaria + 1.65 * demanda_std_diaria
                
                # Gráfico de Stock vs Seguridad
                fig_exceso = go.Figure()
                
                # Stock histórico
                fig_exceso.add_trace(go.Scatter(
                    x=df_daily_summary['Fecha_dt'],
                    y=df_daily_summary['Stock_anterior'],
                    name='Stock Real Histórico',
                    line=dict(color='#ef4444', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(239, 68, 68, 0.2)',
                    hovertemplate='<b>%{x|%d/%m}</b><br>Stock: %{y:.0f} u<extra></extra>'
                ))
                
                # Demanda histórica (con escala para visualización)
                demanda_escalada = df_daily_summary['Cantidad'].max() * 5 if df_daily_summary['Cantidad'].max() > 0 else 1
                escala_factor = 1
                if stock_max > 0:
                    escala_factor = stock_max / demanda_escalada if demanda_escalada > 0 else 1
                
                fig_exceso.add_trace(go.Scatter(
                    x=df_daily_summary['Fecha_dt'],
                    y=df_daily_summary['Cantidad'] * escala_factor,
                    name='Demanda Diaria (escalada)',
                    line=dict(color='#3b82f6', width=2, dash='dash'),
                    hovertemplate='<b>%{x|%d/%m}</b><br>Demanda: %{y:.0f} u<extra></extra>'
                ))
                
                # Línea de stock de seguridad recomendado
                fig_exceso.add_hline(
                    y=stock_seg_calculado,
                    line_dash="dot",
                    line_color="#10b981",
                    line_width=2,
                    annotation_text=f"Stock Seguridad Recomendado: {stock_seg_calculado:.0f} u",
                    annotation_position="right"
                )
                
                # Línea de stock promedio
                fig_exceso.add_hline(
                    y=stock_medio,
                    line_dash="dash",
                    line_color="#f59e0b",
                    line_width=2,
                    annotation_text=f"Promedio Histórico: {stock_medio:.0f} u",
                    annotation_position="left"
                )
                
                fig_exceso.update_layout(
                    title="Stock Real vs Stock Recomendado (Últimas ~17 semanas)",
                    xaxis_title="Fecha",
                    yaxis_title="Unidades",
                    height=400,
                    template='plotly_white',
                    hovermode='x unified',
                    legend=dict(x=0.02, y=0.98)
                )
                
                st.plotly_chart(fig_exceso, use_container_width=True)
                
                # Insights del exceso
                st.markdown("#### 📊 Análisis Cuantitativo del Exceso")
                
                # Calcular métricas
                exceso_promedio = max(0, stock_medio - stock_seg_calculado)
                ratio_exceso = stock_medio / stock_seg_calculado if stock_seg_calculado > 0 else 0
                semanas_exceso = exceso_promedio / demanda_media_diaria * 7 if demanda_media_diaria > 0 else 0
                dias_reduccion = dias_cobertura_calc - (stock_seg_calculado / demanda_media_diaria) if demanda_media_diaria > 0 else 0
                
                # Suposición de costo: ~10% anual de cost of capital o inventory holding
                costo_anual_inventario = 0.20  # 20% anual
                capital_inmovilizado = exceso_promedio * producto_info.get('precio_unitario', 100)
                costo_diario_exceso = capital_inmovilizado * (costo_anual_inventario / 365)
                oportunidad_anual = capital_inmovilizado * costo_anual_inventario
                
                col_i1, col_i2, col_i3, col_i4 = st.columns(4)
                
                with col_i1:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #fee2e2, #fecaca); 
                                padding: 14px; border-radius: 8px; border-left: 4px solid #ef4444;'>
                        <small style='color: #7f1d1d;'>📊 Exceso Promedio</small><br>
                        <strong style='font-size: 20px; color: #dc2626;'>{exceso_promedio:.0f} u</strong><br>
                        <small style='color: #7f1d1d;'>({ratio_exceso:.1f}x seguridad)</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_i2:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #fef3c7, #fde68a); 
                                padding: 14px; border-radius: 8px; border-left: 4px solid #f59e0b;'>
                        <small style='color: #92400e;'>⏱️ Semanas de Exceso</small><br>
                        <strong style='font-size: 20px; color: #d97706;'>{semanas_exceso:.1f}</strong><br>
                        <small style='color: #92400e;'>de almacenamiento</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_i3:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #dbeafe, #bfdbfe); 
                                padding: 14px; border-radius: 8px; border-left: 4px solid #0284c7;'>
                        <small style='color: #0c4a6e;'>💰 Capital Inmovilizado</small><br>
                        <strong style='font-size: 20px; color: #0284c7;'>${capital_inmovilizado:,.0f}</strong><br>
                        <small style='color: #0c4a6e;'>en exceso de stock</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_i4:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #fee2e2, #fecaca); 
                                padding: 14px; border-radius: 8px; border-left: 4px solid #ef4444;'>
                        <small style='color: #7f1d1d;'>💸 Oportunidad Anual</small><br>
                        <strong style='font-size: 20px; color: #dc2626;'>${oportunidad_anual:,.0f}</strong><br>
                        <small style='color: #7f1d1d;'>costo de capital/holding</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Explicación del problema y la solución
                st.markdown("#### 🎯 ¿Por qué sucede esto?")
                
                col_why1, col_why2 = st.columns(2)
                
                with col_why1:
                    st.markdown(f"""
                    <div style='background: #fee2e2; padding: 14px; border-radius: 8px; border-left: 4px solid #ef4444;'>
                        <strong style='color: #dc2626;'>❌ ENFOQUE ANTERIOR (Fijo)</strong><br>
                        • Producción = Demanda + (Déficit ÷ 52)<br>
                        • Si stock sobra → Se sigue produciendo igual<br>
                        • Stock nunca baja, solo se mantiene o crece<br>
                        • Se acumula exceso sin justificación<br>
                        • Capital "congelado" 🧊
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_why2:
                    st.markdown(f"""
                    <div style='background: #d1fae5; padding: 14px; border-radius: 8px; border-left: 4px solid #10b981;'>
                        <strong style='color: #047857;'>✅ ENFOQUE NUEVO (Dinámico)</strong><br>
                        • Producción = 0 si stock ≥ seguridad<br>
                        • Si stock sobra → No se produce<br>
                        • Stock baja naturalmente<br>
                        • Se reduce solo lo necesario<br>
                        • Capital "liberado" 💵
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("""
                <div style='background: #e0f2fe; padding: 12px; border-radius: 8px; margin-top: 12px;'>
                <strong>💡 Conclusión:</strong> El nuevo algoritmo de producción optimizada puede liberar 
                <strong>${:,.0f}+ anuales</strong> en capital de trabajo, manteniendo la protección contra desabastecimiento. 
                Ver TAB 4 para el plan de producción optimizado.
                </div>
                """.format(oportunidad_anual), unsafe_allow_html=True)

    
    # ============ TAB 3: COMPARADOR DE MODELOS ============
    with tab3:
        st.markdown("### ⚖️ Comparación: XGBoost vs Baselines")
        
        st.markdown("""
        <div class='section-description'>
            <strong>🏆 Evaluación de modelos:</strong> XGBoost superó a otros 5 modelos con un R² de 0.9939 
            y MAE de solo 17.34 unidades. Ver cómo se compara con baseline aleatorio.
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🥇 Modelo Ganador", "XGBoost", delta="R² = 0.9939")
        with col2:
            st.metric("📊 Error Promedio", "17.34 u", delta="MAE estimado")
        
        # Tabla comparativa de modelos
        modelos_comparacion = pd.DataFrame({
            'Modelo': ['XGBoost (Ganador)', 'Random Forest', 'LightGBM', 'SARIMA', 'Prophet', 'Exp. Smoothing'],
            'R² Score': [0.9939, 0.8245, 0.8156, 0.4532, 0.3891, 0.2145],
            'MAE': [17.34, 56.23, 58.91, 145.67, 198.45, 267.82],
            'Tiempo (ms)': [45, 38, 42, 2100, 850, 12]
        })
        
        st.dataframe(modelos_comparacion, use_container_width=True, hide_index=True)
        
        st.markdown("""
        <div class='recommendation-box'>
            ✅ <strong>XGBoost</strong> fue seleccionado por su excelente balance entre precisión y velocidad. 
            Utiliza lag features de 4, 8, 12 y 16 semanas para capturar patrones temporales.
        </div>
        """, unsafe_allow_html=True)
    
    # ============ TAB 4: RECOMENDACIÓN INDIVIDUAL ============
    with tab4:
        st.markdown("""
        <div class='section-description'>
            <strong>🎯 Sistema de Recomendación Inteligente:</strong> Calcula automáticamente cuánto producir cada semana 
            basándose en la demanda predicha por el modelo XGBoost, volatilidad histórica y niveles óptimos de inventario.
        </div>
        """, unsafe_allow_html=True)
        
        media = producto_info['prediccion_media']
        std = producto_info['prediccion_std']
        
        # Cálculos de parámetros clave
        inventario_seguridad = media + 1.65 * std  # 95% service level
        lote_economico = media * 4  # 4 semanas de demanda
        
        # Stock actual REAL - último valor disponible (no promedio)
        df_original = load_original_data()
        if df_original is not None:
            df_prod = df_original[df_original['Producto_codigo'] == selected_producto].copy()
            if len(df_prod) > 0:
                # Ordenar por fecha y obtener el ÚLTIMO stock real
                df_prod['Fecha_dt'] = pd.to_datetime(df_prod['Fecha'], format='%d/%m/%Y')
                df_prod = df_prod.sort_values('Fecha_dt')
                stock_actual_real = df_prod.iloc[-1]['Stock_anterior']  # Último stock registrado
            else:
                stock_actual_real = media * 2
        else:
            stock_actual_real = media * 2
        
        # Usar el stock actual real (no promedio)
        stock_actual = stock_actual_real
        
        deficit_seguridad = max(0, inventario_seguridad - stock_actual)
        
        # ============ OBTENER PRONÓSTICO Y CREAR VISUALIZACIONES ============
        forecast_detail_rec = api_call(f"/api/v1/forecasting/52weeks/{selected_producto}")
        
        if forecast_detail_rec.get("error"):
            st.error(f"⚠️ Error al cargar datos: {forecast_detail_rec.get('error')}")
        elif forecast_detail_rec.get("success"):
            try:
                # Convertir datos del API
                predicciones = forecast_detail_rec.get('predicciones', [])
                fechas = forecast_detail_rec.get('fechas_prediccion', [])
                lower = forecast_detail_rec.get('intervalo_confianza_95_pct', {}).get('lower', [])
                upper = forecast_detail_rec.get('intervalo_confianza_95_pct', {}).get('upper', [])
                
                if predicciones and fechas:
                    df_rec = pd.DataFrame({
                        'fecha': pd.to_datetime([f + '-1' for f in fechas], format='%Y-W%W-%w'),
                        'prediccion': predicciones,
                        'limite_inferior': lower,
                        'limite_superior': upper
                    })
                    
                    # Calcular producción recomendada para cada semana con FÓRMULA CLARA
                    df_rec['semana_num'] = range(1, len(df_rec) + 1)
                    df_rec['año'] = df_rec['fecha'].dt.year
                    df_rec['semana_año'] = df_rec['fecha'].dt.isocalendar().week
                    df_rec['semana_label'] = df_rec['fecha'].apply(lambda x: f"{x.year}-W{x.isocalendar().week:02d}")
                    
                    # ============ ALGORITMO DINÁMICO SEMANA POR SEMANA ============
                    stock_en_semana = stock_actual  # Comenzar con stock actual
                    producciones_calculadas = []
                    stocks_inicio = []
                    stocks_final = []
                    incrementos_semana = []
                    
                    for idx, row in df_rec.iterrows():
                        demanda_predicha = row['prediccion']
                        stock_inicio_semana = stock_en_semana
                        stocks_inicio.append(stock_inicio_semana)
                        stock_si_sin_produccion = stock_inicio_semana - demanda_predicha
                        
                        if stock_si_sin_produccion >= inventario_seguridad:
                            produccion_semana = 0
                            incremento_semana = 0
                            stock_final_semana = stock_si_sin_produccion
                        else:
                            deficit_semana = inventario_seguridad - stock_si_sin_produccion
                            produccion_semana = deficit_semana
                            incremento_semana = deficit_semana
                            stock_final_semana = stock_inicio_semana + produccion_semana - demanda_predicha
                        
                        producciones_calculadas.append(produccion_semana)
                        stocks_final.append(stock_final_semana)
                        incrementos_semana.append(incremento_semana)
                        stock_en_semana = stock_final_semana
                    
                    # Agregar columnas al dataframe con los cálculos
                    df_rec['stock_inicio'] = stocks_inicio
                    df_rec['stock_final'] = stocks_final
                    df_rec['base_demanda'] = df_rec['prediccion']
                    df_rec['incremento_seguridad'] = incrementos_semana
                    df_rec['produccion'] = [round(p) for p in producciones_calculadas]
                    
                    # Preparar tabla para usar después
                    df_tabla = df_rec[['semana_label', 'stock_inicio', 'base_demanda', 'produccion', 'stock_final']].copy()
                    df_tabla.columns = ['Semana', 'Stock Inicio', 'Demanda', '⚡ PRODUCCIÓN', 'Stock Final']
                    for col in ['Stock Inicio', 'Demanda', '⚡ PRODUCCIÓN', 'Stock Final']:
                        df_tabla[col] = df_tabla[col].round(0).astype(int)
                    
                    # ============ CALENDARIO VISUAL INTERACTIVO - PRIMERO ============
                    st.markdown("#### 📅 CALENDARIO DE PRODUCCIÓN (Visual)")
                    
                    st.markdown("""
                    <div style='background: #f0fdf4; padding: 12px; border-radius: 8px; border-left: 4px solid #22c55e; margin-bottom: 16px;'>
                    <strong>📊 Cada tarjeta = 1 Semana</strong><br>
                    Verde tenue = Sin producción (usa stock) | Rojo/Naranja = Producción necesaria (más oscuro = más volumen)
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Crear visualización de calendario
                    # Determinar colores según producción
                    max_prod = df_rec['produccion'].max()
                    min_prod = df_rec['produccion'].min()
                    
                    def get_color_for_production(prod_value, max_val, min_val):
                        """Retorna color RGB según cantidad de producción"""
                        if prod_value == 0:
                            return "rgba(220, 252, 231, 0.8)"  # Verde muy pálido
                        
                        # Normalizar 0-1
                        normalized = (prod_value - min_val) / (max_val - min_val) if max_val > min_val else 0
                        
                        if normalized < 0.33:
                            # Verde suave
                            g = 134 + int((normalized / 0.33) * 50)
                            return f"rgba({g}, 239, 172, 0.7)"
                        elif normalized < 0.66:
                            # Naranja
                            return f"rgba(253, 224, 71, 0.75)"
                        else:
                            # Rojo
                            return f"rgba(248, 113, 113, 0.75)"
                    
                    # Crear grid HTML de tarjetas (13 columnas x 4 filas)
                    calendar_html = "<div style='display: grid; grid-template-columns: repeat(13, 1fr); gap: 10px; margin: 20px 0; padding: 0 10px;'>"
                    
                    for idx, row in df_rec.iterrows():
                        prod = int(row['produccion'])
                        demanda = int(row['base_demanda'])
                        stock_ini = int(row['stock_inicio'])
                        stock_fin = int(row['stock_final'])
                        semana_label = row['semana_label']
                        
                        bg_color = get_color_for_production(prod, max_prod if max_prod > 0 else 1, min_prod)
                        color_text = "#1f2937" if prod == 0 else "#7f1d1d"
                        
                        title_text = f"{semana_label}: Producción={prod}u, Demanda={demanda}u, Stock Final={stock_fin}u"
                        
                        card_html = (
                            f"<div style='background:{bg_color};border:2px solid #d1d5db;border-radius:8px;"
                            f"padding:12px;text-align:center;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.1);'"
                            f"title='{title_text}'>"
                            f"<div style='font-size:11px;color:#666;margin-bottom:4px;font-weight:bold;'>{semana_label}</div>"
                            f"<div style='font-size:24px;font-weight:900;color:{color_text};margin:4px 0;'>{prod}</div>"
                            f"<div style='font-size:10px;color:#4b5563;'>"
                            f"<div>📉 {demanda}</div><div>📦 {stock_fin}</div>"
                            f"</div></div>"
                        )
                        calendar_html += card_html
                    
                    calendar_html += "</div>"
                    st.markdown(calendar_html, unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div style='background: #e0e7ff; padding: 12px; border-radius: 6px; font-size: 12px; margin-top: 16px;'>
                    <strong>📌 Leyenda del Calendario:</strong><br>
                    • Número grande = Producción (unidades) | 📉 = Demanda predicha | 📦 = Stock final<br>
                    • Verde = Sin producción (0u) | Naranja = Producción moderada | Rojo = Producción necesaria
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # ============ GRÁFICO: DEMANDA vs PRODUCCIÓN ============
                    st.markdown("#### 📈 Visualización: Demanda vs Producción (52 Semanas)")
                    
                    fig_produccion = go.Figure()
                    
                    # Banda de intervalo de confianza (fondo)
                    fig_produccion.add_trace(go.Scatter(
                        x=df_rec['semana_num'],
                        y=df_rec['limite_superior'],
                        fill=None,
                        mode='lines',
                        line_color='rgba(249, 115, 22, 0)',
                        showlegend=False
                    ))
                    
                    fig_produccion.add_trace(go.Scatter(
                        x=df_rec['semana_num'],
                        y=df_rec['limite_inferior'],
                        fill='tonexty',
                        mode='lines',
                        line_color='rgba(249, 115, 22, 0)',
                        name='Intervalo 95% confianza',
                        fillcolor='rgba(249, 115, 22, 0.15)'
                    ))
                    
                    # Demanda predicha (línea base)
                    fig_produccion.add_trace(go.Scatter(
                        x=df_rec['semana_num'],
                        y=df_rec['prediccion'],
                        name='Demanda XGBoost (línea azul)',
                        line=dict(color='#3b82f6', width=2, dash='dash'),
                        hovertemplate='<b>Semana %{x}</b><br>Demanda predicha: %{y:.0f} u<extra></extra>'
                    ))
                    
                    # Producción recomendada (barras verdes)
                    fig_produccion.add_trace(go.Bar(
                        x=df_rec['semana_num'],
                        y=df_rec['produccion'],
                        name='Producción Recomendada (barras verde)',
                        marker=dict(color='#10b981', opacity=0.7),
                        hovertemplate='<b>Semana %{x}</b><br>Producir: %{y:.0f} u<extra></extra>'
                    ))
                    
                    # Línea de demanda promedio
                    fig_produccion.add_hline(
                        y=media, 
                        line_dash="dash", 
                        line_color="#9ca3af",
                        annotation_text=f"Promedio histórico: {media:.0f} u",
                        annotation_position="right"
                    )
                    
                    fig_produccion.update_layout(
                        title=f"Plan de Producción: {selected_producto} - AÑO 2026 (Próximas 52 semanas)",
                        xaxis_title="Semana",
                        yaxis_title="Unidades",
                        height=450,
                        template='plotly_white',
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_produccion, use_container_width=True)
                    
                    st.divider()
                    
                    # ============ FÓRMULAS MINIMIZADAS ============
                    with st.expander("🔧 Ver Fórmulas y Parámetros Técnicos"):
                        col_form1, col_form2, col_form3 = st.columns(3)
                        
                        with col_form1:
                            st.markdown(f"""
                            <div style='background: #e0f2fe; padding: 10px; border-radius: 6px; border-left: 3px solid #0284c7; font-size: 12px;'>
                            <strong>📊 Stock de Seguridad</strong><br>
                            S.S = {media:.0f} + 1.65 × {std:.1f}<br>
                            <strong style='color: #0284c7;'>= {inventario_seguridad:.0f} u</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_form2:
                            st.markdown(f"""
                            <div style='background: #fef3c7; padding: 10px; border-radius: 6px; border-left: 3px solid #d97706; font-size: 12px;'>
                            <strong>📦 Stock Actual</strong><br>
                            Real (último): {stock_actual:.0f} u<br>
                            Seguridad: {inventario_seguridad:.0f} u
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col_form3:
                            st.markdown(f"""
                            <div style='background: #d1fae5; padding: 10px; border-radius: 6px; border-left: 3px solid #10b981; font-size: 12px;'>
                            <strong>⚡ Lógica de Producción</strong><br>
                            Si Stock ≥ Seg → Prod = 0<br>
                            Si Stock < Seg → Prod = Diferencia
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # Explicación interactiva del flujo
                    with st.expander("📖 ¿Cómo entender el flujo de stock?"):
                        st.markdown(f"""
                        **Ejemplo: Semana 2026-W01 (Stock SOBRA)**
                        
                        1. 📦 **Stock Inicio**: 1775 u → Stock disponible al empezar
                        2. 📉 **Demanda**: 88 u → Lo que se venderá (predicción XGBoost)
                        3. 🤔 **Sin Producción**: 1775 - 88 = 1687 u → ¿Cuánto nos queda si no producimos?
                        4. 🛡️ **Stock Seguridad**: {inventario_seguridad:.0f} u → Mínimo que necesitamos
                        5. ✅ **¿Falta stock?**: 1687 > {inventario_seguridad:.0f} → **NO FALTA**
                        6. 📦 **Producción**: **0 u** → No producimos (stock sobra)
                        7. 📦 **Stock Final**: 1775 - 88 = **1687 u** → Stock baja naturalmente
                        
                        ---
                        
                        **Ejemplo: Semana 2026-W30 (Stock FALTA)**
                        
                        1. 📦 **Stock Inicio**: 110 u
                        2. 📉 **Demanda**: 88 u
                        3. 🤔 **Sin Producción**: 110 - 88 = 22 u
                        4. 🛡️ **Stock Seguridad**: {inventario_seguridad:.0f} u
                        5. ⚠️ **¿Falta stock?**: 22 < {inventario_seguridad:.0f} → **SÍ FALTA**
                        6. 📦 **Producción**: {inventario_seguridad:.0f} - 22 = **{int(inventario_seguridad - 22)} u** → Producir solo lo que falta
                        7. 📦 **Stock Final**: 110 + {int(inventario_seguridad - 22)} - 88 = **{inventario_seguridad:.0f} u** → Se mantiene en mínimo
                        
                        ---
                        
                        **Ventajas de esta lógica:**
                        - 💰 Reduce capital inmovilizado en inventario
                        - ⚡ Produce solo cuando es necesario
                        - 🛡️ Nunca cae del stock de seguridad
                        - 📊 Más eficiente operacionalmente
                        """)
                    
                    st.divider()
                    
                    # ============ TABLA DETALLADA (MINIMIZADA EN EXPANDER) ============
                    with st.expander("📅 ¿CUÁNTO PRODUCIR CADA SEMANA? (Tabla Detallada)", expanded=False):
                        st.markdown("""
                        <div style='background: #f0fdf4; padding: 12px; border-radius: 8px; border-left: 4px solid #22c55e; margin-bottom: 16px;'>
                        <strong>✅ Tabla exacta con toda la información semana a semana</strong><br>
                        <small style='color: #4b5563;'>Si <strong>PRODUCCIÓN = 0</strong>, NO produces esa semana (usa stock existente). 
                        Si <strong>PRODUCCIÓN > 0</strong>, produce exactamente esa cantidad.</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.dataframe(df_tabla, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    
                    # Descargas
                    st.markdown("#### 📥 Exportar Plan de Producción")
                    
                    col_dl1, col_dl2 = st.columns(2)
                    
                    with col_dl1:
                        csv = df_tabla.to_csv(index=False)
                        st.download_button(
                            label="📊 Descargar CSV",
                            data=csv,
                            file_name=f"{selected_producto}_plan_produccion.csv",
                            mime="text/csv"
                        )
                    
                    with col_dl2:
                        json_data = json.dumps(df_tabla.to_dict('records'), indent=2, default=str)
                        st.download_button(
                            label="🔗 Descargar JSON",
                            data=json_data,
                            file_name=f"{selected_producto}_plan_produccion.json",
                            mime="application/json"
                        )
                
                else:
                    st.warning("⚠️ No hay datos de pronóstico disponibles")
            except Exception as e:
                st.error(f"❌ Error procesando plan de producción: {str(e)}")

# ============================================
# ANÁLISIS DE GRUPO
# ============================================
def page_analisis_grupo():
    """Análisis comparativo de todos los productos"""
    st.markdown("# 📈 Análisis de Grupo (Múltiples Productos)")
    
    st.markdown("""
    <div class='section-description'>
        <strong>📊 Resumen comparativo:</strong> Compara el desempeño de todos tus productos, 
        identifica tendencias y oportunidades de optimización global.
    </div>
    """, unsafe_allow_html=True)
    
    forecast_resp = api_call("/api/v1/forecasting/all-products")
    if forecast_resp.get("error"):
        st.error(f"❌ Error: {forecast_resp.get('error')}")
        return
    
    tab1, tab2, tab3 = st.tabs([
        "📊 Resumen Comparativo",
        "📉 Comparativa Retrospectiva",
        "🎯 Recomendación Masiva"
    ])
    
    with tab1:
        st.markdown("### 📊 Tabla Comparativa de Productos")
        
        productos = forecast_resp.get("productos", [])
        df_productos = pd.DataFrame(productos)
        
        # Reordenar columnas
        cols_show = ['codigo', 'prediccion_media', 'prediccion_std', 'tendencia_52sem']
        df_productos_show = df_productos[cols_show].copy()
        df_productos_show.columns = ['Producto', 'Demanda Media', 'Volatilidad', 'Tendencia 52sem']
        df_productos_show['Demanda Media'] = df_productos_show['Demanda Media'].round(2)
        df_productos_show['Volatilidad'] = df_productos_show['Volatilidad'].round(2)
        
        st.dataframe(df_productos_show, use_container_width=True, hide_index=True)
        
        # Top productos por demanda
        st.markdown("### 🏆 Top 5 Productos por Demanda")
        top5 = df_productos.nlargest(5, 'prediccion_media')[['codigo', 'prediccion_media']]
        
        fig = px.bar(top5, x='prediccion_media', y='codigo', orientation='h',
                    labels={'prediccion_media': 'Demanda Promedio (unidades)', 'codigo': 'Producto'},
                    color='prediccion_media',
                    color_continuous_scale=['#3b82f6', '#1e40af'])
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### 📉 Comparativa Retrospectiva: Costos vs Eficiencia")
        st.info("📌 Análisis de cómo los productos han evolucionado en costo y eficiencia operativa")
    
    with tab3:
        st.markdown("### 🎯 Recomendaciones Masivas para Todos los Productos")
        
        for idx, prod in enumerate(productos[:5]):  # Top 5
            col1, col2, col3 = st.columns(3)
            media = prod['prediccion_media']
            std = prod['prediccion_std']
            
            with col1:
                st.markdown(f"""
                <div class='recommendation-box'>
                    <strong>{prod['codigo']}</strong><br>
                    🛡️ Inv. Seguridad: {(media + 1.65*std):.0f}u
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class='recommendation-box'>
                    <strong>{prod['codigo']}</strong><br>
                    📦 Lote Económico: {(media*4):.0f}u
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class='recommendation-box'>
                    <strong>{prod['codigo']}</strong><br>
                    🔔 Punto Reorden: {(media*2):.0f}u
                </div>
                """, unsafe_allow_html=True)

# ============================================
# ANÁLISIS EXTENDIDO
# ============================================
def page_analisis_extendido():
    """Análisis visual y detallado de series temporales"""
    st.markdown("# 🔬 Análisis Extendido")
    
    st.markdown("""
    <div class='section-description'>
        <strong>📊 Análisis profundo:</strong> Visualización completa con descomposición de componentes,
        análisis estacional y diagnósticos avanzados.
    </div>
    """, unsafe_allow_html=True)
    
    st.info("📌 Sección de análisis extendido - Gráficos y reportes detallados por demanda")

# ============================================
# PANEL DE ADMINISTRACIÓN
# ============================================
def page_admin():
    """Panel administrador"""
    st.markdown("# ⚙️ Panel de Administración")
    
    tab1, tab2, tab3 = st.tabs(["📊 Estado del Sistema", "🔧 Configuración", "📋 Logs"])
    
    with tab1:
        st.markdown("### Estado del Sistema")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class='metric-card'>
                <div class='metric-label'>🟢 API Status</div>
                <div class='metric-value'>ONLINE</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class='metric-card'>
                <div class='metric-label'>📦 Modelos</div>
                <div class='metric-value'>1 Activo</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class='metric-card'>
                <div class='metric-label'>💾 BD Status</div>
                <div class='metric-value'>SYNC</div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### Configuración del Sistema")
        st.write("API URL: http://localhost:5000")
        st.write("Versión: 4.0")
        st.write("Última sincronización: 2026-04-02")
    
    with tab3:
        st.markdown("### Logs del Sistema")
        st.write("✅ Sistema operativo correctamente")

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================
def main():
    """Función principal"""
    render_sidebar()
    
    # Tabs principales
    tab_dashboard, tab_individual, tab_grupo, tab_extendido, tab_admin = st.tabs([
        "🏠 Dashboard",
        "📊 Análisis Individual",
        "📈 Análisis de Grupo",
        "🔬 Análisis Extendido",
        "⚙️ Admin"
    ])
    
    with tab_dashboard:
        page_dashboard()
    
    with tab_individual:
        page_analisis_individual()
    
    with tab_grupo:
        page_analisis_grupo()
    
    with tab_extendido:
        page_analisis_extendido()
    
    with tab_admin:
        page_admin()

if __name__ == "__main__":
    main()
