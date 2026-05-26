import sys
import os
import importlib.util
from pathlib import Path
from datetime import datetime, timezone

SCRIPTS_DIR = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

DATA_DIR  = os.environ.get('DATA_DIR',  '/data/01_Datos_Nuevos')
EDA_DIR   = os.environ.get('EDA_DIR',   '/data/EDA_Outputs')
PRED_DIR  = os.environ.get('PRED_DIR',  '/data/01_Datos')

from lib.preparar_top20            import run_preparar_top20
from lib.analisis_pareto           import run_analisis_pareto
from lib.agregacion_features       import run_agregacion_features
from lib.seleccion_filtrado_features import run_seleccion_filtrado_features
from lib.optimizacion_hiperparametros import run_optimizacion_hiperparametros
from lib.predicciones_final        import run_predicciones_final


def _run_clustering():
    os.environ['EDA_DIR'] = EDA_DIR
    spec = importlib.util.spec_from_file_location(
        'clustering', SCRIPTS_DIR / '05B_ANALISIS_CLUSTERING_ADI_CV.py'
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)


def main(log_callback=print):
    os.makedirs(EDA_DIR,  exist_ok=True)
    os.makedirs(PRED_DIR, exist_ok=True)

    clustering_meta = os.path.join(EDA_DIR, 'CLUSTERING_METADATA.json')
    reporte_path    = os.path.join(EDA_DIR, 'REPORTE_OPTIMIZACION_HIPERPARAMETROS.json')

    stages = [
        ('Preparar TOP20',               lambda: run_preparar_top20(DATA_DIR, EDA_DIR)),
        ('Análisis Pareto',              lambda: run_analisis_pareto(EDA_DIR)),
        ('Agregación + Features',        lambda: run_agregacion_features(EDA_DIR)),
        ('Clustering ADI/CV²',           _run_clustering),
        ('Selección de Features',        lambda: run_seleccion_filtrado_features(EDA_DIR)),
        ('Optimización Hiperparámetros', lambda: run_optimizacion_hiperparametros(EDA_DIR, EDA_DIR, clustering_meta)),
        ('Predicciones Finales',         lambda: run_predicciones_final(EDA_DIR, PRED_DIR, reporte_path)),
    ]

    for name, fn in stages:
        ts = datetime.now(timezone.utc).isoformat()
        log_callback(f'[{ts}] START {name}')
        fn()
        ts = datetime.now(timezone.utc).isoformat()
        log_callback(f'[{ts}] DONE  {name}')

    log_callback('Pipeline completado exitosamente.')


if __name__ == '__main__':
    main()
