"""
PREPARACION DE DATA DESDE BACKUP ORIGINAL
- SIN eliminar registros
- Solo agregar 3 columnas: Empresa_Cliente, Canal_Venta, Punto_Venta
- Con lógica específica basada en Salida y patrones estacionales
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

np.random.seed(42)

# Empresas (las 5 primeras serán las principales)
EMPRESAS_PRINCIPALES = [
    "PROCISA INGENIEROS S.A.C.",
    "NEVADO CONSTRUCTORA",
    "Madrid INMOBILIARIA",
    "ELCONSI",
    "SETECOM AIR"
]

EMPRESAS_SECUNDARIAS = [
    "CIM",
    "DRAGON",
    "JEF",
    "ARCHENGINE CONSULTORA S.A.C.",
    "Consultores en Ingeniería y Mantenimiento General S.A.C.",
    "GCG - GARCIA CONTRATISTAS GENERALES S.A.",
    "H&R ELECTRICAL ENGINEERS S.A.C."
]

ALL_EMPRESAS = EMPRESAS_PRINCIPALES + EMPRESAS_SECUNDARIAS

DATA_DIR = r"d:\Desktop\Predicast\01_Datos_Nuevos"
BACKUP_DIR = os.path.join(DATA_DIR, "backup_original")

print("=" * 80)
print("PREPARACION DE DATA - ENRIQUECIMIENTO ESPECÍFICO")
print("=" * 80)

archivos = sorted([f for f in os.listdir(BACKUP_DIR) 
                   if f.startswith("Movimientos_") and f.endswith(".csv")])

for archivo in archivos:
    print(f"\n[{archivo}]")
    
    ruta_backup = os.path.join(BACKUP_DIR, archivo)
    
    # CARGAR
    df = None
    for header_row in [0, 1]:
        try:
            df = pd.read_csv(ruta_backup, sep=";", encoding="latin-1", header=header_row)
            if len(df) > 0 and any(col in df.columns for col in ["Salida", "salida"]):
                break
        except:
            continue
    
    if df is None:
        print(f"  ERROR: No se pudo cargar")
        continue
    
    # Normalizar columnas
    df.columns = df.columns.str.strip()
    if "salida" in df.columns and "Salida" not in df.columns:
        df.rename(columns={"salida": "Salida"}, inplace=True)
    
    n_total = len(df)
    print(f"  Registros: {n_total}")
    
    # Convertir Salida a numérico
    df["Salida"] = pd.to_numeric(df["Salida"], errors="coerce").fillna(0)
    
    # Convertir Fecha
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce", format='%d/%m/%Y')
    
    # Inicializar columnas nuevas
    df["Empresa_Cliente"] = np.nan
    df["Canal_Venta"] = np.nan
    df["Punto_Venta"] = np.nan
    
    # ========================================================================
    # PASO 1: TOP 10 PRODUCTOS POR SALIDA
    # ========================================================================
    
    if "Código" in df.columns:
        prod_salida = df[df["Salida"] > 0].groupby("Código")["Salida"].sum().nlargest(10)
        top_10_productos = set(prod_salida.index)
        print(f"  Top 10 productos: {len(top_10_productos)} productos identificados")
    else:
        top_10_productos = set()
    
    # ========================================================================
    # PASO 2: CALCULAR PROMEDIO DE SALIDA POR PRODUCTO
    # ========================================================================
    
    promedio_producto = {}
    if "Código" in df.columns:
        for prod in df[df["Salida"] > 0]["Código"].unique():
            data_prod = df[(df["Código"] == prod) & (df["Salida"] > 0)]["Salida"]
            promedio_producto[prod] = data_prod.mean()
    
    # ========================================================================
    # PASO 3: LLENAR EMPRESAS
    # ========================================================================
    
    # Solo cuando Salida > 0
    mask_salida = df["Salida"] > 0
    indices_salida = df[mask_salida].index
    
    print(f"  Registros con Salida > 0: {len(indices_salida)}")
    
    # Para productos en top 10: 80% empresas principales, 20% secundarias
    # Para productos NO en top 10: 40% principales, 60% secundarias
    
    for idx in indices_salida:
        prod = df.loc[idx, "Código"] if "Código" in df.columns else None
        
        if prod in top_10_productos:
            # 80% principales, 20% secundarias
            if np.random.rand() < 0.8:
                df.loc[idx, "Empresa_Cliente"] = np.random.choice(EMPRESAS_PRINCIPALES)
            else:
                df.loc[idx, "Empresa_Cliente"] = np.random.choice(EMPRESAS_SECUNDARIAS)
        else:
            # 40% principales, 60% secundarias
            if np.random.rand() < 0.4:
                df.loc[idx, "Empresa_Cliente"] = np.random.choice(EMPRESAS_PRINCIPALES)
            else:
                df.loc[idx, "Empresa_Cliente"] = np.random.choice(EMPRESAS_SECUNDARIAS)
    
    print(f"  Empresa_Cliente: {df['Empresa_Cliente'].notna().sum()} registros asignados")
    
    # ========================================================================
    # PASO 4: LLENAR CANAL VENTA
    # ========================================================================
    
    # Solo cuando Salida > 0
    for idx in indices_salida:
        prod = df.loc[idx, "Código"] if "Código" in df.columns else None
        salida = df.loc[idx, "Salida"]
        promedio = promedio_producto.get(prod, 0)
        
        # Online más probable si Salida > promedio del producto
        if salida > promedio:
            # 70% online, 30% presencial
            canal = "Online" if np.random.rand() < 0.7 else "Presencial"
        else:
            # 30% online, 70% presencial
            canal = "Online" if np.random.rand() < 0.3 else "Presencial"
        
        df.loc[idx, "Canal_Venta"] = canal
    
    print(f"  Canal_Venta: {df['Canal_Venta'].notna().sum()} registros asignados")
    
    # ========================================================================
    # PASO 5: LLENAR PUNTO VENTA
    # ========================================================================
    
    # Solo cuando Canal = Presencial y Salida > 0
    # Sector A: Q2-Q3 más probable
    # Sector B: Q1-Q4 más probable
    
    mask_presencial = (df["Canal_Venta"] == "Presencial") & (df["Salida"] > 0)
    indices_presencial = df[mask_presencial].index
    
    for idx in indices_presencial:
        if "Fecha" in df.columns and pd.notna(df.loc[idx, "Fecha"]):
            trimestre = ((df.loc[idx, "Fecha"].month - 1) // 3) + 1  # 1-4
        else:
            trimestre = np.random.randint(1, 5)
        
        if trimestre in [2, 3]:  # Q2-Q3
            # 70% Sector A, 30% Sector B
            punto = "Sector A" if np.random.rand() < 0.7 else "Sector B"
        else:  # Q1-Q4
            # 30% Sector A, 70% Sector B
            punto = "Sector A" if np.random.rand() < 0.3 else "Sector B"
        
        df.loc[idx, "Punto_Venta"] = punto
    
    print(f"  Punto_Venta: {df['Punto_Venta'].notna().sum()} registros asignados")
    
    # ========================================================================
    # GUARDAR
    # ========================================================================
    
    ruta_destino = os.path.join(DATA_DIR, archivo)
    df.to_csv(ruta_destino, sep=";", encoding="latin-1", index=False)
    
    print(f"  Guardado: {ruta_destino}")
    print(f"    Total registros (sin cambios): {n_total}")
    print(f"    Empresas únicas: {df['Empresa_Cliente'].nunique()}")
    print(f"    Canales únicos: {df['Canal_Venta'].nunique()}")
    print(f"    Puntos únicos: {df['Punto_Venta'].nunique()}")

print("\n" + "=" * 80)
print("DATA PREPARADA - LISTO PARA EDA v3")
print("=" * 80)
print("\n✓ Ningún registro fue eliminado")
print("✓ 3 columnas nuevas agregadas con lógica específica")
print("✓ Empresas: 5 principales + 7 secundarias (distribución ponderada)")
print("✓ Canal: Presencial/Online (basado en promedio de producto)")
print("✓ Punto: Sector A/B (estacionalidad por trimestre)")
