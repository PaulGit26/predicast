from pathlib import Path
from .lib.seleccion_filtrado_features import run_seleccion_filtrado_features


OUTPUT_DIR = Path(r"d:/Desktop/Predicast/04_Scripts_Nuevos/EDA_Outputs")


def main():
    res = run_seleccion_filtrado_features(OUTPUT_DIR)
    print("SELECCIÓN Y FILTRADO ejecutado. Resultados:")
    print(res)


if __name__ == "__main__":
    main()
