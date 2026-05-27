import importlib.util
import pytest
import pandas as pd
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent


def _load_module(rel_path, name):
    spec = importlib.util.spec_from_file_location(name, str(repo_root / rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# preparar_top20 — lib/ (root wrapper)
# ---------------------------------------------------------------------------

def test_run_preparar_top20_missing_dir_raises():
    from lib.preparar_top20 import run_preparar_top20
    with pytest.raises(FileNotFoundError):
        run_preparar_top20("non_existent_dir_12345", str(Path("./tmp_out_test")))


def test_run_preparar_top20_empty_dir_raises(tmp_path):
    from lib.preparar_top20 import run_preparar_top20
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="No movimiento files found"):
        run_preparar_top20(str(data_dir), str(tmp_path / "out"))


def test_run_preparar_top20_lowercase_columns(tmp_path):
    """Covers the column-rename branches (lines 30,32,34,36,38) in preparar_top20."""
    mod = _load_module("04_Scripts_Nuevos/lib/preparar_top20.py", "preparar_top20_04")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    df = pd.DataFrame({
        "Fecha": ["2023-01-01", "2023-01-08", "2023-01-15"],
        "código": ["P001", "P001", "P001"],
        "salida": [100.0, 200.0, 150.0],
        "entrada": [0.0, 0.0, 0.0],
        "documento": ["Venta", "Venta", "Venta"],
        "número": [1, 2, 3],
    })
    df.to_csv(data_dir / "Movimientos_test_2023.csv", sep=";", encoding="latin-1", index=False)

    result = mod.run_preparar_top20(str(data_dir), str(tmp_path / "out"))
    assert Path(result["datos_top20"]).exists()
    datos = pd.read_csv(result["datos_top20"], sep=";", encoding="latin-1")
    assert "Código" in datos.columns
    assert "Salida" in datos.columns


def test_run_preparar_top20_guias_remision_excluded(tmp_path):
    """Covers lines 62-65: guías de remisión where Entrada==Salida are excluded."""
    mod = _load_module("04_Scripts_Nuevos/lib/preparar_top20.py", "preparar_top20_04b")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    df = pd.DataFrame([
        # Guía where Entrada == Salida — should be excluded
        {"Fecha": "2023-01-01", "Código": "P001", "Salida": 50.0, "Entrada": 50.0,
         "Documento": "Guía de remisión - R001", "Número": 10},
        # Regular sale — should remain
        {"Fecha": "2023-01-08", "Código": "P001", "Salida": 100.0, "Entrada": 0.0,
         "Documento": "Venta", "Número": 11},
    ])
    df.to_csv(data_dir / "Movimientos_guias_2023.csv", sep=";", encoding="latin-1", index=False)

    result = mod.run_preparar_top20(str(data_dir), str(tmp_path / "out"))
    datos = pd.read_csv(result["datos_top20"], sep=";", encoding="latin-1")
    assert len(datos) == 1
    assert datos.iloc[0]["Salida"] == 100.0


# ---------------------------------------------------------------------------
# analisis_pareto — covers the empty/zero-sales guard (lines 22-25)
# ---------------------------------------------------------------------------

def test_analisis_pareto_zero_sales(tmp_path):
    """Covers lines 22-25: dataset with zero total sales does not crash."""
    mod = _load_module("04_Scripts_Nuevos/lib/analisis_pareto.py", "analisis_pareto")
    out = tmp_path / "out"
    out.mkdir()
    df = pd.DataFrame({"Código": ["P001", "P002"], "Salida": [0.0, 0.0]})
    df.to_csv(out / "DATOS_TOP20_VENTAS.csv", sep=";", encoding="latin-1", index=False)

    result = mod.run_analisis_pareto(str(out))
    assert "reporte" in result
    assert Path(result["reporte"]).exists()


def test_analisis_pareto_single_product(tmp_path):
    """Single product: cumulative % is 100%, productos_80 must be >= 1."""
    mod = _load_module("04_Scripts_Nuevos/lib/analisis_pareto.py", "analisis_pareto_b")
    out = tmp_path / "out"
    out.mkdir()
    df = pd.DataFrame({"Código": ["P001"], "Salida": [500.0]})
    df.to_csv(out / "DATOS_TOP20_VENTAS.csv", sep=";", encoding="latin-1", index=False)

    result = mod.run_analisis_pareto(str(out))
    import json
    with open(result["reporte"], encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["productos_80pct"] >= 1
    assert meta["total_top20"] == 1
