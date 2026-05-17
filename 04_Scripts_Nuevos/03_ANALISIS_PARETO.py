"""
ANÁLISIS PARETO - DEFINIR PRODUCTOS A ANALIZAR
Identifica cuántos productos generan el 80/20 de impacto
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json

OUTPUT_DIR = r"d:\Desktop\Predicast\04_Scripts_Nuevos\EDA_Outputs"

from lib.analisis_pareto import run_analisis_pareto


def main():
    run_analisis_pareto(OUTPUT_DIR)


if __name__ == "__main__":
    main()
