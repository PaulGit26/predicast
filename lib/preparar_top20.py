from importlib.machinery import SourceFileLoader
from pathlib import Path

_src = Path(__file__).resolve().parent / '..' / '04_Scripts_Nuevos' / 'lib' / 'preparar_top20.py'
_loader = SourceFileLoader('preparar_top20_src', str(_src))
_mod = _loader.load_module()

# Re-export function
run_preparar_top20 = getattr(_mod, 'run_preparar_top20')
