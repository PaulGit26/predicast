# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
    COMPARATIVA ALGORITMOS DE FORECASTING [V3.0 CON MODELO POR PRODUCTO]
═══════════════════════════════════════════════════════════════════════════════

Objetivo: Comparar algoritmos de forecasting para predecir ventas semanales

Algoritmos evaluados:
  1. Prophet (Facebook) - Robust, maneja estacionalidad bien
  2. SARIMA - Clasico ARIMA con componente estacional
  3. Exponential Smoothing - Media movil ponderada
  4. XGBoost con lags (52 sem) + features exogenos - MEJORADO con Descuento, Precio, Online%
  5. LightGBM con lags (52 sem) + features exogenos - MEJORADO con mismos features que XGBoost
  6. LSTM (Deep Learning) - Red neuronal recurrente

MEJORAS EN V2.0:
  - Lags aumentados: 12 -> 52 semanas (ciclo anual completo)
  - Features exogenos: Descuento(%), Precio unitario, % Online, Indicador Campana
  - Test set: Minimo 52 semanas para validar estacionalidad anual
  - Hiperparametros: Optimizados para mejor generalizacion
  
Metricass: MAE, RMSE, MAPE, R2

Datasets:
  - datos_semanales_pivot.csv - Ventas (cantidad semanal)
  - datos_semanales_descuento.csv - Promedio descuento %
  - datos_semanales_precio.csv - Promedio precio unitario
  - datos_semanales_pct_online.csv - % ventas Online
  - datos_semanales_campana.csv - Indicador de campana (1/0)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import json
import time
from pathlib import Path

warnings.filterwarnings('ignore')

# Configuración
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("=" * 100)
print("COMPARATIVA DE ALGORITMOS DE FORECASTING - VENTAS SEMANALES")
print("=" * 100)

print("\nPASO 1: CARGAR DATOS")
print("-" * 100)

# Cargar datos
df_pivot = pd.read_csv('../01_Datos/datos_semanales_pivot.csv', index_col=0)
print(f"✓ Datos cargados: {df_pivot.shape[0]} semanas × {df_pivot.shape[1]} productos")

# Cargar features adicionales (enriquecimiento 2025)
df_descuento = pd.read_csv('../01_Datos/datos_semanales_descuento.csv', index_col=0)
df_precio = pd.read_csv('../01_Datos/datos_semanales_precio.csv', index_col=0)
df_pct_online = pd.read_csv('../01_Datos/datos_semanales_pct_online.csv', index_col=0)
df_campana = pd.read_csv('../01_Datos/datos_semanales_campana.csv', index_col=0)
print(f"✓ Features adicionales cargados: Descuento, Precio, % Online, Campaña")

# Seleccionar TODOS los 20 productos para comparativa completa
volumes = df_pivot.sum().sort_values(ascending=False)
productos_test = volumes.index.tolist()
print(f"✓ Evaluando TODOS los {len(productos_test)} productos")
print(f"  Productos: {productos_test}")

df_test = df_pivot[productos_test].copy()

# Split temporal: Mínimo 52 semanas de test (1 año) para validar estacionalidad
min_test_weeks = 52
if len(df_test) >= min_test_weeks * 2:  # Asegurar que haya suficiente histórico
    split_idx = len(df_test) - min_test_weeks
else:
    split_idx = int(len(df_test) * 0.7)

train_size = split_idx
test_size = len(df_test) - split_idx
print(f"\n✓ Split temporal: Train {train_size} semanas, Test {test_size} semanas (mínimo {min_test_weeks} para validación anual)")

print("\n" + "=" * 100)
print("PASO 2: IMPORTAR LIBRERÍAS REQUERIDAS")
print("-" * 100)

try:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    print("✓ sklearn importado")
except:
    print("✗ Instalando sklearn...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'scikit-learn', '-q'])
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    print("✓ statsmodels (ARIMA/SARIMA) importado")
except:
    print("✗ Instalando statsmodels...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'statsmodels', '-q'])
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    print("✓ ExponentialSmoothing importado")
except:
    print("✗ ExponentialSmoothing no disponible")

try:
    import xgboost as xgb
    print("✓ XGBoost importado")
except:
    print("✗ Instalando XGBoost...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'xgboost', '-q'])
    import xgboost as xgb

try:
    import lightgbm as lgb
    print("✓ LightGBM importado")
except:
    print("✗ Instalando LightGBM...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'lightgbm', '-q'])
    import lightgbm as lgb

try:
    from fbprophet import Prophet
    print("✓ Prophet (fbprophet) importado")
except:
    try:
        from prophet import Prophet
        print("✓ Prophet (prophet==1.1+) importado")
    except:
        print("✗ Instalando Prophet...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'cmdstanpy', 'prophet', '-q'])
        from prophet import Prophet

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense
    from tensorflow.keras.optimizers import Adam
    print("✓ TensorFlow/LSTM importado")
    LSTM_DISPONIBLE = True
except:
    print("✗ TensorFlow no disponible (saltaremos LSTM)")
    LSTM_DISPONIBLE = False

# Funciones de utilidad
def mape(y_true, y_pred):
    """Mean Absolute Percentage Error"""
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.sum() > 0 else np.nan

def create_lag_features(data, lags=52):
    """Crear features de lag para ML models"""
    X, y = [], []
    for i in range(lags, len(data)):
        X.append(data[i-lags:i])
        y.append(data[i])
    return np.array(X), np.array(y)

def create_lag_features_with_exogenous(data, exog_features, lags=52):
    """Crear features de lag + features exógenos para ML models
    
    Args:
        data: Serie temporal principal (cantidad/ventas)
        exog_features: Dict con DataFrames de features exógenos {nombre: df}
        lags: Número de lags históricos a usar
    
    Returns:
        X: Array (n_samples, lags + n_exog_features)
        y: Array (n_samples,)
    """
    X, y = [], []
    for i in range(lags, len(data)):
        # Lags históricos de la serie principal
        lag_values = data[i-lags:i]
        
        # Features exógenos (usar el valor actual, no lag)
        exog_values = []
        for fname, fdf in exog_features.items():
            if i < len(fdf):
                exog_values.append(fdf[i])
        
        # Combinar lags + features exógenos
        combined = np.concatenate([lag_values, exog_values])
        X.append(combined)
        y.append(data[i])
    
    return np.array(X), np.array(y)

def get_ventajas(modelo):
    """Describe advantages of each model"""
    ventajas = {
        'prophet': 'Maneja bien estacionalidad, robusto',
        'sarima': 'Clasico, interpretable, lida bien con tendencias',
        'exponential_smoothing': 'Rapido, simple',
        'xgboost': 'Flexible, accurate, maneja no-linearidades',
        'lightgbm': 'Muy rapido, eficiente en memoria',
        'lstm': 'Deep learning, captura patrones complejos'
    }
    return ventajas.get(modelo, 'N/A')

# Estructura para guardar resultados
resultados_modelos = {}

print("\n" + "=" * 100)
print("PASO 3: ENTRENAR Y EVALUAR MODELOS")
print("-" * 100)

# Para cada producto
all_predictions = {}
all_metrics = []

for pid, producto in enumerate(productos_test, 1):
    print(f"\n{pid}/{len(productos_test)} Evaluando producto: {producto}")
    
    # Datos del producto
    serie = df_test[producto].values
    train_data = serie[:split_idx]
    test_data = serie[split_idx:]
    
    print(f"  Train: {len(train_data)} semanas | Test: {len(test_data)} semanas")
    
    # Diccionario para guardar predicciones
    predicciones_producto = {'y_true': test_data}
    metricas_producto = {'producto': producto}
    
    # ════════════════════════════════════════════════════════════════════════════
    # 1. PROPHET
    # ════════════════════════════════════════════════════════════════════════════
    try:
        print(f"  → Entrenando Prophet...", end=" ")
        inicio = time.time()
        
        # Preparar datos para Prophet
        df_prophet = pd.DataFrame({
            'ds': pd.date_range(start='2021-01-01', periods=len(train_data), freq='W'),
            'y': train_data
        })
        
        model_prophet = Prophet(yearly_seasonality=True, weekly_seasonality=True, 
                               daily_seasonality=False, interval_width=0.95, 
                               stan_backend='cmdstanpy')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            model_prophet.fit(df_prophet)
        
        # Predecir
        future = pd.DataFrame({
            'ds': pd.date_range(start='2021-01-01', periods=len(train_data) + len(test_data), freq='W')
        })
        forecast = model_prophet.make_future_dataframe(periods=len(test_data))
        forecast = model_prophet.predict(forecast)
        pred_prophet = forecast['yhat'].values[-len(test_data):]
        pred_prophet = np.maximum(pred_prophet, 0)  # No valores negativos
        
        tiempo_prophet = time.time() - inicio
        
        mae_prophet = mean_absolute_error(test_data, pred_prophet)
        rmse_prophet = np.sqrt(mean_squared_error(test_data, pred_prophet))
        mape_prophet = mape(test_data, pred_prophet)
        r2_prophet = r2_score(test_data, pred_prophet)
        
        predicciones_producto['prophet'] = pred_prophet
        metricas_producto['prophet'] = {
            'mae': mae_prophet, 'rmse': rmse_prophet, 'mape': mape_prophet,
            'r2': r2_prophet, 'tiempo': tiempo_prophet
        }
        
        print(f"✓ MAE={mae_prophet:.2f}, RMSE={rmse_prophet:.2f}, MAPE={mape_prophet:.2f}%, R²={r2_prophet:.4f} ({tiempo_prophet:.1f}s)")
        
    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        metricas_producto['prophet'] = None
    
    # ════════════════════════════════════════════════════════════════════════════
    # 2. SARIMA
    # ════════════════════════════════════════════════════════════════════════════
    try:
        print(f"  → Entrenando SARIMA...", end=" ")
        inicio = time.time()
        
        # Convertir a Series si es ndarray
        train_series = pd.Series(train_data) if isinstance(train_data, np.ndarray) else train_data
        
        # Auto ARIMA simple (p,d,q = 1,1,1 como default)
        # Reducido maxiter a 50 para optimizar velocidad
        model_sarima = SARIMAX(train_series, order=(1, 1, 1), 
                              seasonal_order=(1, 1, 1, 52))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            result_sarima = model_sarima.fit(disp=False, maxiter=50)
        
        # Predecir
        pred_sarima = result_sarima.get_forecast(steps=len(test_data)).predicted_mean.values
        pred_sarima = np.maximum(pred_sarima, 0)
        
        tiempo_sarima = time.time() - inicio
        
        mae_sarima = mean_absolute_error(test_data, pred_sarima)
        rmse_sarima = np.sqrt(mean_squared_error(test_data, pred_sarima))
        mape_sarima = mape(test_data, pred_sarima)
        r2_sarima = r2_score(test_data, pred_sarima)
        
        predicciones_producto['sarima'] = pred_sarima
        metricas_producto['sarima'] = {
            'mae': mae_sarima, 'rmse': rmse_sarima, 'mape': mape_sarima,
            'r2': r2_sarima, 'tiempo': tiempo_sarima
        }
        
        print(f"✓ MAE={mae_sarima:.2f}, RMSE={rmse_sarima:.2f}, MAPE={mape_sarima:.2f}%, R²={r2_sarima:.4f} ({tiempo_sarima:.1f}s)")
        
    except (Exception, KeyboardInterrupt) as e:
        print(f"✗ Error: {str(e)[:50]}")
        metricas_producto['sarima'] = None
    
    # ════════════════════════════════════════════════════════════════════════════
    # 3. EXPONENTIAL SMOOTHING
    # ════════════════════════════════════════════════════════════════════════════
    try:
        print(f"  → Entrenando Exponential Smoothing...", end=" ")
        inicio = time.time()
        
        # Convertir a Series si es ndarray
        train_series = pd.Series(train_data) if isinstance(train_data, np.ndarray) else train_data
        
        model_es = ExponentialSmoothing(train_series, seasonal_periods=52, 
                                       trend='add', seasonal='add',
                                       initialization_method='estimated')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            result_es = model_es.fit(optimized=True)
        
        pred_es = result_es.forecast(steps=len(test_data)).values
        pred_es = np.maximum(pred_es, 0)
        
        tiempo_es = time.time() - inicio
        
        mae_es = mean_absolute_error(test_data, pred_es)
        rmse_es = np.sqrt(mean_squared_error(test_data, pred_es))
        mape_es = mape(test_data, pred_es)
        r2_es = r2_score(test_data, pred_es)
        
        predicciones_producto['exponential_smoothing'] = pred_es
        metricas_producto['exponential_smoothing'] = {
            'mae': mae_es, 'rmse': rmse_es, 'mape': mape_es,
            'r2': r2_es, 'tiempo': tiempo_es
        }
        
        print(f"✓ MAE={mae_es:.2f}, RMSE={rmse_es:.2f}, MAPE={mape_es:.2f}%, R²={r2_es:.4f} ({tiempo_es:.1f}s)")
        
    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        metricas_producto['exponential_smoothing'] = None
    
    # ════════════════════════════════════════════════════════════════════════════
    # 4. XGBOOST CON LAG FEATURES + FEATURES EXÓGENOS
    # ════════════════════════════════════════════════════════════════════════════
    try:
        print(f"  → Entrenando XGBoost (lags + features exógenos)...", end=" ")
        inicio = time.time()
        
        # Crear features de lag (52 semanas = ciclo annual) + features exógenos
        lags = 52
        exog_train = {
            'descuento': df_descuento.loc[df_pivot.index[:split_idx], producto].values,
            'precio': df_precio.loc[df_pivot.index[:split_idx], producto].values,
            'pct_online': df_pct_online.loc[df_pivot.index[:split_idx], producto].values,
            'campana': df_campana.loc[df_pivot.index[:split_idx], producto].values
        }
        X_train, y_train = create_lag_features_with_exogenous(train_data, exog_train, lags)
        
        # Usar últimas X_train para predecir
        X_test_list = []
        for i in range(len(test_data)):
            if i == 0:
                X_test_list.append(np.concatenate([train_data[-(lags-1):], [test_data[0]]]))
            else:
                X_test_list.append(np.concatenate([np.array(predicciones_producto.get('xgboost', test_data))[max(0, i-lags):i]]))
        
        model_xgb = xgb.XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, subsample=0.8, random_state=RANDOM_STATE)
        model_xgb.fit(X_train, y_train, verbose=0)
        
        # Predecir recursivamente con features exógenos
        pred_xgb = []
        hist = list(train_data[-lags:])
        exog_test = {
            'descuento': df_descuento.loc[df_pivot.index[split_idx:], producto].values,
            'precio': df_precio.loc[df_pivot.index[split_idx:], producto].values,
            'pct_online': df_pct_online.loc[df_pivot.index[split_idx:], producto].values,
            'campana': df_campana.loc[df_pivot.index[split_idx:], producto].values
        }
        
        for i in range(len(test_data)):
            # Combinar lags históricos con features exógenos actuales
            exog_current = np.array([exog_test['descuento'][i], exog_test['precio'][i], 
                                     exog_test['pct_online'][i], exog_test['campana'][i]])
            X_pred = np.concatenate([hist[-lags:], exog_current]).reshape(1, -1)
            pred = model_xgb.predict(X_pred)[0]
            pred = max(pred, 0)
            pred_xgb.append(pred)
            hist.append(pred)
        pred_xgb = np.array(pred_xgb)
        
        tiempo_xgb = time.time() - inicio
        
        mae_xgb = mean_absolute_error(test_data, pred_xgb)
        rmse_xgb = np.sqrt(mean_squared_error(test_data, pred_xgb))
        mape_xgb = mape(test_data, pred_xgb)
        r2_xgb = r2_score(test_data, pred_xgb)
        
        predicciones_producto['xgboost'] = pred_xgb
        metricas_producto['xgboost'] = {
            'mae': mae_xgb, 'rmse': rmse_xgb, 'mape': mape_xgb,
            'r2': r2_xgb, 'tiempo': tiempo_xgb
        }
        
        print(f"✓ MAE={mae_xgb:.2f}, RMSE={rmse_xgb:.2f}, MAPE={mape_xgb:.2f}%, R²={r2_xgb:.4f} ({tiempo_xgb:.1f}s)")
        
    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        metricas_producto['xgboost'] = None
    
    # ════════════════════════════════════════════════════════════════════════════
    # 5. LIGHTGBM CON LAG FEATURES + FEATURES EXÓGENOS
    # ════════════════════════════════════════════════════════════════════════════
    try:
        print(f"  → Entrenando LightGBM (lags + features exógenos)...", end=" ")
        inicio = time.time()
        
        # Usar mismos features que XGBoost (52 semanas + 4 features exógenos)
        lags = 52
        X_train, y_train = create_lag_features_with_exogenous(train_data, exog_train, lags)
        
        model_lgb = lgb.LGBMRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, 
                                     num_leaves=31, subsample=0.8, random_state=RANDOM_STATE, verbosity=-1)
        model_lgb.fit(X_train, y_train)
        
        # Predecir recursivamente con features exógenos
        pred_lgb = []
        hist = list(train_data[-lags:])
        
        for i in range(len(test_data)):
            # Combinar lags históricos con features exógenos actuales
            exog_current = np.array([exog_test['descuento'][i], exog_test['precio'][i], 
                                     exog_test['pct_online'][i], exog_test['campana'][i]])
            X_pred = np.concatenate([hist[-lags:], exog_current]).reshape(1, -1)
            pred = model_lgb.predict(X_pred)[0]
            pred = max(pred, 0)
            pred_lgb.append(pred)
            hist.append(pred)
        pred_lgb = np.array(pred_lgb)
        
        tiempo_lgb = time.time() - inicio
        
        mae_lgb = mean_absolute_error(test_data, pred_lgb)
        rmse_lgb = np.sqrt(mean_squared_error(test_data, pred_lgb))
        mape_lgb = mape(test_data, pred_lgb)
        r2_lgb = r2_score(test_data, pred_lgb)
        
        predicciones_producto['lightgbm'] = pred_lgb
        metricas_producto['lightgbm'] = {
            'mae': mae_lgb, 'rmse': rmse_lgb, 'mape': mape_lgb,
            'r2': r2_lgb, 'tiempo': tiempo_lgb
        }
        
        print(f"✓ MAE={mae_lgb:.2f}, RMSE={rmse_lgb:.2f}, MAPE={mape_lgb:.2f}%, R²={r2_lgb:.4f} ({tiempo_lgb:.1f}s)")
        
    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        metricas_producto['lightgbm'] = None
    
    # ════════════════════════════════════════════════════════════════════════════
    # 6. LSTM (Si está disponible)
    # ════════════════════════════════════════════════════════════════════════════
    if LSTM_DISPONIBLE:
        try:
            print(f"  → Entrenando LSTM...", end=" ")
            inicio = time.time()
            
            # Preparar datos
            lags = 12
            X_train_lstm, y_train_lstm = create_lag_features(train_data, lags)
            X_train_lstm = X_train_lstm.reshape((X_train_lstm.shape[0], X_train_lstm.shape[1], 1))
            
            # Modelo
            model_lstm = Sequential([
                LSTM(64, activation='relu', input_shape=(lags, 1)),
                Dense(32, activation='relu'),
                Dense(1)
            ])
            model_lstm.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
            model_lstm.fit(X_train_lstm, y_train_lstm, epochs=50, batch_size=16, verbose=0)
            
            # Predecir
            pred_lstm = []
            hist = list(train_data[-lags:])
            for i in range(len(test_data)):
                X_pred = np.array([hist[-lags:]]).reshape(1, lags, 1)
                pred = model_lstm.predict(X_pred, verbose=0)[0, 0]
                pred = max(pred, 0)
                pred_lstm.append(pred)
                hist.append(pred)
            pred_lstm = np.array(pred_lstm)
            
            tiempo_lstm = time.time() - inicio
            
            mae_lstm = mean_absolute_error(test_data, pred_lstm)
            rmse_lstm = np.sqrt(mean_squared_error(test_data, pred_lstm))
            mape_lstm = mape(test_data, pred_lstm)
            r2_lstm = r2_score(test_data, pred_lstm)
            
            predicciones_producto['lstm'] = pred_lstm
            metricas_producto['lstm'] = {
                'mae': mae_lstm, 'rmse': rmse_lstm, 'mape': mape_lstm,
                'r2': r2_lstm, 'tiempo': tiempo_lstm
            }
            
            print(f"✓ MAE={mae_lstm:.2f}, RMSE={rmse_lstm:.2f}, MAPE={mape_lstm:.2f}%, R²={r2_lstm:.4f} ({tiempo_lstm:.1f}s)")
            
        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            metricas_producto['lstm'] = None
    
    # Guardar predicciones
    all_predictions[producto] = predicciones_producto
    all_metrics.append(metricas_producto)

print("\n" + "=" * 100)
print("PASO 4: CONSOLIDAR RESULTADOS GLOBALES")
print("-" * 100)

# Crear tabla resumen
resultados_consolidados = []

for producto in productos_test:
    metrica = next((m for m in all_metrics if m['producto'] == producto), {})
    
    for modelo in ['prophet', 'sarima', 'exponential_smoothing', 'xgboost', 'lightgbm', 'lstm']:
        if modelo in metrica and metrica[modelo] is not None:
            resultados_consolidados.append({
                'Producto': producto,
                'Modelo': modelo.upper(),
                'MAE': metrica[modelo]['mae'],
                'RMSE': metrica[modelo]['rmse'],
                'MAPE': metrica[modelo]['mape'],
                'R²': metrica[modelo]['r2'],
                'Tiempo (s)': metrica[modelo]['tiempo']
            })

df_resultados = pd.DataFrame(resultados_consolidados)

# Resumen por modelo
print(f"\n📊 RESUMEN POR MODELO (Promedio en {len(productos_test)} productos):\n")
resumen_modelo = df_resultados.groupby('Modelo').agg({
    'MAE': ['mean', 'std'],
    'RMSE': ['mean', 'std'],
    'MAPE': ['mean', 'std'],
    'R²': ['mean', 'std'],
    'Tiempo (s)': 'mean'
}).round(2)

print(resumen_modelo)

# Ranqueo
print("\n🏆 RANKING FINAL (por MAE promedio):\n")
ranking = df_resultados.groupby('Modelo')['MAE'].mean().sort_values()
for idx, (modelo, mae) in enumerate(ranking.items(), 1):
    print(f"  {idx}. {modelo:20s} → MAE: {mae:6.2f}")

# Selección del mejor modelo por producto
print("\n" + "=" * 100)
print("SELECCIÓN DE MEJOR MODELO POR PRODUCTO")
print("-" * 100)

# Crear una matriz de mejor modelo por producto considerando todos los indicadores
producto_mejor_modelo = {}

for producto in productos_test:
    df_prod = df_resultados[df_resultados['Producto'] == producto].copy()
    
    # Calcular score normalizado (0-100) para cada métrica
    # Normalizamos: MAE, RMSE, MAPE (menor es mejor) y R² (mayor es mejor)
    
    df_prod['score_mae'] = 100 - ((df_prod['MAE'] - df_prod['MAE'].min()) / (df_prod['MAE'].max() - df_prod['MAE'].min() + 1e-6) * 100)
    df_prod['score_rmse'] = 100 - ((df_prod['RMSE'] - df_prod['RMSE'].min()) / (df_prod['RMSE'].max() - df_prod['RMSE'].min() + 1e-6) * 100)
    df_prod['score_mape'] = 100 - ((df_prod['MAPE'] - df_prod['MAPE'].min()) / (df_prod['MAPE'].max() - df_prod['MAPE'].min() + 1e-6) * 100)
    df_prod['score_r2'] = (df_prod['R²'] - df_prod['R²'].min()) / (df_prod['R²'].max() - df_prod['R²'].min() + 1e-6) * 100
    
    # Score ponderado: MAE (40%), RMSE (20%), MAPE (20%), R² (20%)
    df_prod['score_final'] = (df_prod['score_mae'] * 0.4 + 
                              df_prod['score_rmse'] * 0.2 + 
                              df_prod['score_mape'] * 0.2 + 
                              df_prod['score_r2'] * 0.2)
    
    mejor = df_prod.loc[df_prod['score_final'].idxmax()]
    producto_mejor_modelo[producto] = {
        'modelo': mejor['Modelo'],
        'score_final': mejor['score_final'],
        'mae': mejor['MAE'],
        'rmse': mejor['RMSE'],
        'mape': mejor['MAPE'],
        'r2': mejor['R²']
    }

# Mostrar selección
print("\n🏆 MEJOR MODELO POR PRODUCTO:\n")
for idx, (producto, info) in enumerate(producto_mejor_modelo.items(), 1):
    print(f"{idx:2d}. {producto:15s} → {info['modelo']:15s} (Puntuación: {info['score_final']:5.1f}/100, MAE: {info['mae']:6.2f}, R²: {info['r2']:6.4f})")

# Resumen de modelos ganadores
modelos_ganadores = {}
for info in producto_mejor_modelo.values():
    modelo = info['modelo']
    modelos_ganadores[modelo] = modelos_ganadores.get(modelo, 0) + 1

print("\n📊 RESUMEN DE GANADORES:")
for modelo, count in sorted(modelos_ganadores.items(), key=lambda x: x[1], reverse=True):
    pct = (count / len(productos_test)) * 100
    print(f"  {modelo:15s}: {count:2d} productos ({pct:5.1f}%)")

# Guardar resultados
df_resultados.to_csv('../04_Scripts/comparativa_resultados.csv', index=False)
print(f"\n✓ Guardado: comparativa_resultados.csv")

# Guardar selección de modelos por producto
seleccion_por_producto = {}
for producto, info in producto_mejor_modelo.items():
    seleccion_por_producto[producto] = {
        'modelo_recomendado': info['modelo'],
        'puntuacion': float(info['score_final']),
        'metricas': {
            'mae': float(info['mae']),
            'rmse': float(info['rmse']),
            'mape': float(info['mape']),
            'r2': float(info['r2'])
        }
    }

# Guardar resumen JSON
with open('../04_Scripts/comparativa_resumen.json', 'w') as f:
    
    resumen_dict = {
        'fecha': datetime.now().isoformat(),
        'productos_evaluados': len(productos_test),
        'muestras_test': test_size,
        'ranking_global': ranking.to_dict(),
        'mejor_modelo_global': ranking.index[0],
        'mae_promedio_mejor_global': float(ranking.iloc[0]),
        'modelos_por_producto': seleccion_por_producto,
        'resumen_ganadores': modelos_ganadores,
        'nota': '✅ Evaluación completa de 5 algoritmos en 20 productos. Recomendación: usar modelo específico por producto para máxima precisión.'
    }
    json.dump(resumen_dict, f, indent=2)

print(f"✓ Guardado: comparativa_resumen.json")
print(f"✓ Guardado: comparativa_resultados.csv")

print("\n" + "=" * 100)
print("VISUALIZACIONES")
print("-" * 100)

# Gráficos comparativos
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

# 1. MAE por modelo
ax = axes[0, 0]
df_resultados.boxplot(column='MAE', by='Modelo', ax=ax)
ax.set_title('MAE por Modelo', fontweight='bold')
ax.set_xlabel('')
ax.set_ylabel('Mean Absolute Error')
ax.get_figure().suptitle('')

# 2. RMSE por modelo
ax = axes[0, 1]
df_resultados.boxplot(column='RMSE', by='Modelo', ax=ax)
ax.set_title('RMSE por Modelo', fontweight='bold')
ax.set_xlabel('')
ax.set_ylabel('Root Mean Squared Error')
ax.get_figure().suptitle('')

# 3. MAPE por modelo
ax = axes[1, 0]
df_resultados.boxplot(column='MAPE', by='Modelo', ax=ax)
ax.set_title('MAPE (%) por Modelo', fontweight='bold')
ax.set_xlabel('')
ax.set_ylabel('Mean Absolute Percentage Error')
ax.get_figure().suptitle('')

# 4. R² por modelo
ax = axes[1, 1]
df_resultados.boxplot(column='R²', by='Modelo', ax=ax)
ax.set_title('R² por Modelo', fontweight='bold')
ax.set_xlabel('')
ax.set_ylabel('R² Score')
ax.get_figure().suptitle('')

plt.tight_layout()
plt.savefig('../05_Visualizaciones/04_Comparativa_Modelos_BoxPlot.png', dpi=300, bbox_inches='tight')
print("✓ Gráfico guardado: 04_Comparativa_Modelos_BoxPlot.png")
plt.close()

# Gráfico de predicciones reales vs predichas para el MEJOR MODELO DE CADA PRODUCTO
fig, axes = plt.subplots(4, 5, figsize=(20, 16))
axes = axes.flatten()

for idx, producto in enumerate(productos_test):
    ax = axes[idx]
    preds = all_predictions[producto]
    
    # Obtener el mejor modelo para este producto
    modelo_ganador = producto_mejor_modelo[producto]['modelo'].lower()
    
    y_true = preds['y_true']
    if modelo_ganador in preds:
        y_pred = preds[modelo_ganador]
        
        ax.plot(range(len(y_true)), y_true, 'b-o', label='Real', linewidth=2, markersize=4)
        ax.plot(range(len(y_pred)), y_pred, 'r--s', label=f'{modelo_ganador.upper()}', linewidth=2, markersize=4)
        
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        
        ax.set_title(f'{producto}\n{modelo_ganador.upper()} | MAE: {mae:.2f}, R²: {r2:.3f}', fontweight='bold', fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

plt.suptitle(f'Predicciones Reales vs Modelo Ganador por Producto (20 productos)', fontsize=14, fontweight='bold', y=0.995)
plt.tight_layout()
plt.savefig(f'../05_Visualizaciones/05_Predicciones_Modelos_Por_Producto.png', dpi=300, bbox_inches='tight')
print(f"✓ Gráfico guardado: 05_Predicciones_Modelos_Por_Producto.png")
plt.close()

print("\n" + "=" * 100)
print("✅ COMPARATIVA COMPLETADA")
print("=" * 100)

# Obtener el mejor modelo global
mejor_modelo = ranking.index[0].lower()

mejor_modelo_nombres = {
    'prophet': 'Maneja bien estacionalidad, robusto',
    'sarima': 'Clasico, interpretable, lida bien con tendencias',
    'exponential_smoothing': 'Rapido, simple',
    'xgboost': 'Flexible, accurate, maneja no-linearidades',
    'lightgbm': 'Muy rapido, eficiente en memoria',
    'lstm': 'Deep learning, captura patrones complejos'
}

ventajas_modelo = mejor_modelo_nombres.get(mejor_modelo, 'N/A')

print(f"""

[+] RESUMEN EJECUTIVO:

  [+] Modelos evaluados: 6 (Prophet, SARIMA, Exp.Smoothing, XGBoost, LightGBM, LSTM)
  [+] Productos probados: {len(productos_test)}
  [+] Semanas test por producto: {test_size}
  
  🏆 MEJOR MODELO: {mejor_modelo.upper()}
     - MAE promedio: {ranking.iloc[0]:.2f}
     - Ventajas: {ventajas_modelo}
  
  📊 ARCHIVOS GENERADOS:
     [+] comparativa_resultados.csv - Tabla completa con todas las metricas
     [+] comparativa_resumen.json - Resumen ejecutivo
     [+] 04_Comparativa_Modelos_BoxPlot.png - Graficos boxplot de metricas
     [+] 05_Predicciones_{mejor_modelo.upper()}.png - Predicciones reales vs predichas
  
  ⏭️  PROXIMO PASO:
     > Reentrenar modelo ganador con todos los datos
     > Generar predicciones para 52 semanas futuras
     > Crear API para servir predicciones automaticas

""")
