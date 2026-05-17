from pathlib import Path
import subprocess
import sys
from prefect import flow, task


@task(retries=1, retry_delay_seconds=10)
def run_script(script_path: str) -> str:
    script = Path(script_path).resolve()
    if not script.exists():
        raise FileNotFoundError(f"Script not found: {script}")
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Script failed: {script}\nstdout:{proc.stdout}\nstderr:{proc.stderr}")
    return proc.stdout


@flow(name="predicast-pipeline")
def pipeline_flow(base_dir: str = None):
    base = Path(base_dir) if base_dir else Path(__file__).resolve().parents[3]
    scripts = [
        base / "04_Scripts_Nuevos" / "02_PREPARAR_TOP20.py",
        base / "04_Scripts_Nuevos" / "03_ANALISIS_PARETO.py",
        base / "04_Scripts_Nuevos" / "04_AGREGACION_SEMANAL_Y_FEATURES.py",
        base / "04_Scripts_Nuevos" / "05_SELECCION_FILTRADO_FEATURES.py",
        base / "04_Scripts_Nuevos" / "08_OPTIMIZACION_HIPERPARAMETROS_PRODUCCION.py",
        base / "04_Scripts_Nuevos" / "10_PREDICCIONES_FINAL_PRODUCCION.py",
    ]

    for s in scripts:
        run_script(str(s))


if __name__ == "__main__":
    pipeline_flow()
