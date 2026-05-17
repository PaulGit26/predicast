"""Entry script: llama al wrapper de optimización de hiperparámetros.

Este archivo queda como entrypoint ligero para CI/CLI y preserva compatibilidad
con llamadas directas antiguas.
"""

import os
from lib import optimizacion_hiperparametros as optim


FEATURES_DIR = r'04_Scripts_Nuevos\EDA_Outputs'
OUTPUT_DIR = r'04_Scripts_Nuevos'
CLUSTERING_METADATA_FILE = os.path.join(FEATURES_DIR, 'CLUSTERING_METADATA.json')


def main():
    resultado = optim.run_optimizacion_hiperparametros(FEATURES_DIR, OUTPUT_DIR, CLUSTERING_METADATA_FILE)
    print('\n' + '='*80)
    print('Optimizacion finalizada. Reporte:')
    print(resultado.get('reporte'))
    print('='*80 + '\n')


if __name__ == '__main__':
    main()
