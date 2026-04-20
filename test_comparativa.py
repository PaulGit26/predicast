# -*- coding: utf-8 -*-
import sys
import os
os.chdir("d:\\Desktop\\Predicast\\04_Scripts")
sys.path.insert(0, "d:\\Desktop\\Predicast\\04_Scripts")

# Ejecutar primeras líneas para verificar que carga los datos correctamente
exec(open("11_COMPARATIVA_FORECASTING.py").read().split('print("PASO 2:')[0])
