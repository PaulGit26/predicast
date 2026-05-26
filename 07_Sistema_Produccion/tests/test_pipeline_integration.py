import importlib.util
import json
import os
from pathlib import Path
import pandas as pd
import numpy as np

repo_root = Path(__file__).resolve().parents[2]


def _load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(module_path))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


_preparar_mod = _load_module(repo_root / '04_Scripts_Nuevos' / 'lib' / 'preparar_top20.py', 'preparar_top20')
run_preparar_top20 = _preparar_mod.run_preparar_top20

_analisis_mod = _load_module(repo_root / '04_Scripts_Nuevos' / 'lib' / 'analisis_pareto.py', 'analisis_pareto')
run_analisis_pareto = _analisis_mod.run_analisis_pareto

_agregacion_mod = _load_module(repo_root / '04_Scripts_Nuevos' / 'lib' / 'agregacion_features.py', 'agregacion_features')
run_agregacion_features = _agregacion_mod.run_agregacion_features

_optimizacion_mod = _load_module(repo_root / '04_Scripts_Nuevos' / 'lib' / 'optimizacion_hiperparametros.py', 'optimizacion_hiperparametros')
run_optimizacion_hiperparametros = _optimizacion_mod.run_optimizacion_hiperparametros

_predicciones_mod = _load_module(repo_root / '04_Scripts_Nuevos' / 'lib' / 'predicciones_final.py', 'predicciones_final')
run_predicciones_final = _predicciones_mod.run_predicciones_final


def _make_movimientos_csv(path: Path, product_code: str = 'P1'):
    dates = pd.date_range(end=pd.Timestamp.today(), periods=24, freq='7D')
    rows = []
    for d in dates:
        rows.append({
            'Fecha': d.strftime('%Y-%m-%d'),
            'Código': product_code,
            'Salida': 10 + int(np.random.rand() * 5),
            'Entrada': 0,
            'Documento': 'Venta',
            'Número': 1,
            'Empresa_Cliente': 'ACME',
            'Canal_Venta': 'Tienda',
            'Punto_Venta': 'Local1'
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, sep=';', encoding='latin-1', index=False)


def test_pipeline_smoke(tmp_path):
    # Directories
    data_new = tmp_path / '01_Datos_Nuevos'
    eda_out = tmp_path / '04_Scripts_Nuevos' / 'EDA_Outputs'
    data_dir = tmp_path / '01_Datos'
    data_new.mkdir(parents=True)
    eda_out.mkdir(parents=True)
    data_dir.mkdir(parents=True)

    # 1) preparar_top20
    mov_file = data_new / 'Movimientos_MayorAuxiliar_2025.csv'
    _make_movimientos_csv(mov_file, product_code='P1')

    res = run_preparar_top20(str(data_new), str(eda_out))
    assert 'datos_top20' in res
    datos_top20 = Path(res['datos_top20'])
    assert datos_top20.exists()

    # 2) analisis pareto
    pareto = run_analisis_pareto(str(eda_out), datos_top20_path=str(datos_top20))
    assert Path(pareto['reporte']).exists()

    # 3) agregacion y features
    agg = run_agregacion_features(str(eda_out))
    assert agg.get('complete', True) or Path(eda_out / 'FEATURES_SEMANAL_PARA_MODELOS.csv').exists()

    # 4) prepare clustering metadata for optimizer
    clustering_meta = eda_out / 'CLUSTERING_METADATA.json'
    clustering = {'grupos': {'GRUPO_1': {'productos': ['P1']}}}
    with open(clustering_meta, 'w', encoding='utf-8') as f:
        json.dump(clustering, f)

    # 5) optimizacion (may be light with small dataset)
    opt = run_optimizacion_hiperparametros(str(eda_out), str(eda_out), str(clustering_meta))
    assert 'reporte' in opt
    assert Path(opt['reporte']).exists()

    # 6) predicciones final
    pred = run_predicciones_final(str(eda_out), str(data_dir), str(opt['reporte']))
    assert Path(pred['largo']).exists()
    assert Path(pred['pivot']).exists()
    assert Path(pred['metadata']).exists()
