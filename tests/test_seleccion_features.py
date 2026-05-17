import importlib.util
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent


def _load_seleccion():
    path = repo_root / "04_Scripts_Nuevos" / "lib" / "seleccion_filtrado_features.py"
    spec = importlib.util.spec_from_file_location("seleccion_filtrado_features", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_features_csv(out_dir: Path, n_rows: int = 60) -> None:
    rng = np.random.default_rng(42)
    n = n_rows
    df = pd.DataFrame({
        "Código": ["CER001"] * n,
        "Año": [2023] * n,
        "Semana": list(range(1, n + 1)),
        "Fecha": pd.date_range("2023-01-01", periods=n, freq="W").strftime("%Y-%m-%d").tolist(),
        "Salida": rng.integers(100, 1000, n).astype(float),
        "Lag_1": rng.integers(100, 1000, n).astype(float),
        "Lag_2": rng.integers(100, 1000, n).astype(float),
        "MA_2": rng.integers(100, 1000, n).astype(float),
        "MA_13": rng.integers(100, 1000, n).astype(float),
        "Volatilidad_4": rng.uniform(0.1, 1.0, n),
        "Trend_4": rng.uniform(-1.0, 1.0, n),
        "Mes": rng.integers(1, 13, n).astype(float),
        "Trimestre": rng.integers(1, 5, n).astype(float),
    })
    df.to_csv(out_dir / "FEATURES_SEMANAL_PARA_MODELOS.csv", sep=";", encoding="latin-1", index=False)


def test_seleccion_missing_file_raises(tmp_path):
    mod = _load_seleccion()
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(FileNotFoundError):
        mod.run_seleccion_filtrado_features(out)


def test_seleccion_returns_expected_keys(tmp_path):
    mod = _load_seleccion()
    out = tmp_path / "out"
    out.mkdir()
    _make_features_csv(out)
    result = mod.run_seleccion_filtrado_features(out)
    assert set(result.keys()) == {"feature_files", "correlations", "vif", "metadata"}
    assert set(result["feature_files"].keys()) == {"Conservative", "Intermediate", "Aggressive"}


def test_seleccion_output_files_exist(tmp_path):
    mod = _load_seleccion()
    out = tmp_path / "out"
    out.mkdir()
    _make_features_csv(out)
    result = mod.run_seleccion_filtrado_features(out)

    for fpath in result["feature_files"].values():
        assert Path(fpath).exists()
    assert Path(result["correlations"]).exists()
    assert Path(result["vif"]).exists()
    assert Path(result["metadata"]).exists()
    assert (out / "06_CORRELACION_HEATMAP_TOP30.png").exists()
    assert (out / "07_CORRELACION_TARGET_TOP25.png").exists()
    assert (out / "08_VIF_MULTICOLINEALIDAD.png").exists()


def test_seleccion_metadata_content(tmp_path):
    mod = _load_seleccion()
    out = tmp_path / "out"
    out.mkdir()
    _make_features_csv(out)
    result = mod.run_seleccion_filtrado_features(out)

    with open(result["metadata"], encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["total_features_original"] == 8
    assert "feature_sets" in meta
    assert set(meta["feature_sets"].keys()) == {"Conservative", "Intermediate", "Aggressive"}
    assert "clasificacion" in meta
    for key in ("Pasado_Seguro", "Futuro_Conocido", "Temporal"):
        assert key in meta["clasificacion"]


def test_seleccion_feature_files_contain_base_cols(tmp_path):
    mod = _load_seleccion()
    out = tmp_path / "out"
    out.mkdir()
    _make_features_csv(out)
    result = mod.run_seleccion_filtrado_features(out)

    for set_name, fpath in result["feature_files"].items():
        df = pd.read_csv(fpath, sep=";", encoding="latin-1")
        assert "Código" in df.columns, f"{set_name}: missing Código"
        assert "Salida" in df.columns, f"{set_name}: missing Salida"


def test_seleccion_vif_csv_has_expected_columns(tmp_path):
    mod = _load_seleccion()
    out = tmp_path / "out"
    out.mkdir()
    _make_features_csv(out)
    result = mod.run_seleccion_filtrado_features(out)

    vif_df = pd.read_csv(result["vif"], sep=";", encoding="latin-1")
    assert "Feature" in vif_df.columns
    assert "VIF" in vif_df.columns
    assert len(vif_df) == 8
