import pytest
from pathlib import Path


def test_run_preparar_top20_missing_dir_raises():
    from lib.preparar_top20 import run_preparar_top20
    missing = Path("non_existent_dir_12345")
    out = Path("./tmp_out_test")
    if out.exists():
        for f in out.iterdir():
            f.unlink()
        out.rmdir()
    with pytest.raises(FileNotFoundError):
        run_preparar_top20(str(missing), str(out))
