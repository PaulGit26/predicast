from pathlib import Path
import subprocess
import sys
import os
from prefect import flow, task

import importlib.util
from types import ModuleType
import warnings

# Suppress sklearn/user warnings produced by programmatic imports
warnings.filterwarnings('ignore')


@task(retries=1, retry_delay_seconds=10)
def run_script(script_path: str) -> str:
    script = Path(script_path).resolve()
    if not script.exists():
        raise FileNotFoundError(f"Script not found: {script}")
    # Run subprocess with warnings suppressed to avoid sklearn feature-name UserWarnings
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"Script failed: {script}\nstdout:{proc.stdout}\nstderr:{proc.stderr}")
    return proc.stdout


@task(retries=0)
def task_seleccion_filtrado(output_dir: str):
    # Dynamically load the wrapper module from the repository to avoid package import issues
    repo_base = Path(__file__).resolve().parents[3]
    mod_path = repo_base / "04_Scripts_Nuevos" / "lib" / "seleccion_filtrado_features.py"
    if not mod_path.exists():
        raise FileNotFoundError(f"Wrapper module not found: {mod_path}")
    spec = importlib.util.spec_from_file_location("seleccion_filtrado_features", str(mod_path))
    mod: ModuleType = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.run_seleccion_filtrado_features(output_dir)


@task(retries=0)
def task_preparar_top20(output_dir: str):
    repo_base = Path(__file__).resolve().parents[3]
    mod_path = repo_base / "04_Scripts_Nuevos" / "lib" / "preparar_top20.py"
    if not mod_path.exists():
        raise FileNotFoundError(f"Wrapper module not found: {mod_path}")
    spec = importlib.util.spec_from_file_location("preparar_top20", str(mod_path))
    mod: ModuleType = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    # preparar_top20 expects (data_dir, output_dir)
    data_dir = str(repo_base / '01_Datos_Nuevos')
    return mod.run_preparar_top20(data_dir, output_dir)


@task(retries=0)
def task_analisis_pareto(output_dir: str):
    repo_base = Path(__file__).resolve().parents[3]
    mod_path = repo_base / "04_Scripts_Nuevos" / "lib" / "analisis_pareto.py"
    if not mod_path.exists():
        raise FileNotFoundError(f"Wrapper module not found: {mod_path}")
    spec = importlib.util.spec_from_file_location("analisis_pareto", str(mod_path))
    mod: ModuleType = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.run_analisis_pareto(output_dir)


@task(retries=0)
def task_agregacion_features(output_dir: str):
    repo_base = Path(__file__).resolve().parents[3]
    mod_path = repo_base / "04_Scripts_Nuevos" / "lib" / "agregacion_features.py"
    if not mod_path.exists():
        raise FileNotFoundError(f"Wrapper module not found: {mod_path}")
    spec = importlib.util.spec_from_file_location("agregacion_features", str(mod_path))
    mod: ModuleType = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.run_agregacion_features(output_dir)


@task(retries=0)
def task_optimizacion(output_dir: str, clustering_metadata: str = None):
    repo_base = Path(__file__).resolve().parents[3]
    mod_path = repo_base / "04_Scripts_Nuevos" / "lib" / "optimizacion_hiperparametros.py"
    if not mod_path.exists():
        raise FileNotFoundError(f"Wrapper module not found: {mod_path}")
    spec = importlib.util.spec_from_file_location("optimizacion_hiperparametros", str(mod_path))
    mod: ModuleType = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.run_optimizacion_hiperparametros(output_dir, output_dir, clustering_metadata)


@task(retries=0)
def task_predicciones_final(features_dir: str, output_dir: str, reporte_path: str):
    repo_base = Path(__file__).resolve().parents[3]
    mod_path = repo_base / "04_Scripts_Nuevos" / "lib" / "predicciones_final.py"
    if not mod_path.exists():
        raise FileNotFoundError(f"Wrapper module not found: {mod_path}")
    spec = importlib.util.spec_from_file_location("predicciones_final", str(mod_path))
    mod: ModuleType = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.run_predicciones_final(features_dir, output_dir, reporte_path)


@flow(name="predicast-pipeline")
def pipeline_flow(base_dir: str = ""):
    base = Path(base_dir) if base_dir else Path(__file__).resolve().parents[3]
    # Execute pipeline steps programmatically using wrapper tasks where available
    out_dir = base / "04_Scripts_Nuevos" / "EDA_Outputs"

    # 1. Preparar Top20
    task_preparar_top20(str(out_dir))

    # 2. Pareto analysis
    task_analisis_pareto(str(out_dir))

    # 3. Weekly aggregation & feature engineering
    task_agregacion_features(str(out_dir))

    # 4. Selection (already a programmatic task)
    task_seleccion_filtrado(str(out_dir))

    # 5. Hyperparameter optimization
    clustering_meta = str(out_dir / 'CLUSTERING_METADATA.json')
    task_optimizacion(str(out_dir), clustering_meta)

    # 6. Final predictions
    features_dir = str(out_dir)
    data_output_dir = str(base / '01_Datos')
    reporte_path = str(base / '04_Scripts_Nuevos' / 'REPORTE_OPTIMIZACION_HIPERPARAMETROS.json')
    task_predicciones_final(features_dir, data_output_dir, reporte_path)


if __name__ == "__main__":
    pipeline_flow()
