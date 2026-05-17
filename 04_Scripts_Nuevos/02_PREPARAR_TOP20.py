"""
========================================================================
PREPARAR TOP 20 - LIMPIEZA Y FILTRADO
========================================================================
Script simplificado que:
1. Carga datos enriquecidos (de script 01)
2. Aplica reglas de limpieza específicas
3. Filtra a TOP 20 productos por volumen
4. Exporta DATOS_TOP20_VENTAS.csv para script 03 y 04

Entrada: 01_Datos_Nuevos/*.csv (datos enriquecidos por script 01)
Salida:  DATOS_TOP20_VENTAS.csv (limpio, TOP 20)
         TOP20_PRODUCTOS.csv (ranking)
         RESUMEN_LIMPIEZA.json (estadísticas)
========================================================================
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

OUTPUT_DIR = r"d:\Desktop\Predicast\04_Scripts_Nuevos\EDA_Outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("\n" + "="*80)
print("PREPARAR TOP 20 - LIMPIEZA Y FILTRADO")
print("="*80)

from lib.preparar_top20 import run_preparar_top20

OUTPUT_DIR = r"d:\Desktop\Predicast\04_Scripts_Nuevos\EDA_Outputs"
DATA_DIR = r"d:\Desktop\Predicast\01_Datos_Nuevos"


def main():
    print("Running preparar_top20 wrapper...")
    res = run_preparar_top20(DATA_DIR, OUTPUT_DIR)
    print("Result:", res)


if __name__ == "__main__":
    main()
