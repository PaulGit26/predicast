"""
Constantes globales del sistema
"""

from enum import Enum

# ============================================
# FEATURES DEL MODELO
# ============================================
REQUIRED_FEATURES = [
    "Stock_anterior",
    "Stock_posterior",
    "Precio_unitario",
    "Año",
    "Mes",
    "Trimestre",
    "Día_Semana",
    "Canal_Promedio_Demanda",
    "Campana_Promedio_Demanda",
    "Cliente_Promedio_Demanda",
    "Producto_Promedio_Demanda",
    "Canal_venta_encoded",
    "Campana_encoded",
    "Empresa_cliente_encoded",
    "Producto_codigo_encoded"
]

# ============================================
# ENUMERABLES PARA ENCODING
# ============================================
class CanalVenta(str, Enum):
    ONLINE = "Online"
    TIENDA_FISICA = "Tienda Física"

class Campana(str, Enum):
    BLACK_FRIDAY = "Black Friday - Matrices & Cajas"
    DESCUENTO_VOLUMEN = "Descuento por Volumen - Mayoristas"
    PROMO_CONSTRUCTOR = "Promo Constructor - Construcción"
    SIN_CAMPANA = "Sin Campaña"

class Productos(str, Enum):
    CP_01 = "CP_01"
    CP_02 = "CP_02"
    CP_03 = "CP_03"
    CP_04 = "CP_04"
    CP_05 = "CP_05"
    CP_06 = "CP_06"
    CP_07 = "CP_07"
    CP_08 = "CP_08"
    CP_09 = "CP_09"
    CP_10 = "CP_10"
    CP_11 = "CP_11"
    CP_12 = "CP_12"
    CP_13 = "CP_13"
    CP_14 = "CP_14"
    CR_01 = "CR_01"
    CR_02 = "CR_02"
    CR_03 = "CR_03"
    CT_01 = "CT_01"
    MECO_01 = "MECO_01"
    MZ_01 = "MZ_01"

class Empresas(str, Enum):
    CONSTRUCTORA_PACIFICO = "Constructora Pacífico Ltda"
    CONSTRUCTORES_ANDES = "Constructores del Andes"
    DESARROLLOS_SUR = "Desarrollos Urbanos del Sur"
    INMOBILIARIA_ANDINA = "Inmobiliaria Andina SRL"
    PROYECTOS_NACIONAL = "Proyectos Inmobiliarios Nacional"
    UNKNOWN = "UNKNOWN"

# ============================================
# LABEL ENCODINGS (del metadata)
# ============================================
LABEL_ENCODINGS = {
    "Canal_venta": {
        "Online": 0,
        "Tienda Física": 1
    },
    "Campana": {
        "Black Friday - Matrices & Cajas": 0,
        "Descuento por Volumen - Mayoristas": 1,
        "Promo Constructor - Construcción": 2,
        "Sin Campaña": 3
    },
    "Empresa_cliente": {
        "Constructora Pacífico Ltda": 0,
        "Constructores del Andes": 1,
        "Desarrollos Urbanos del Sur": 2,
        "Inmobiliaria Andina SRL": 3,
        "Proyectos Inmobiliarios Nacional": 4,
        "UNKNOWN": 5
    },
    "Producto_codigo": {
        "CP_01": 0, "CP_02": 1, "CP_03": 2, "CP_04": 3, "CP_05": 4,
        "CP_06": 5, "CP_07": 6, "CP_08": 7, "CP_09": 8, "CP_10": 9,
        "CP_11": 10, "CP_12": 11, "CP_13": 12, "CP_14": 13,
        "CR_01": 14, "CR_02": 15, "CR_03": 16,
        "CT_01": 17,
        "MECO_01": 18,
        "MZ_01": 19
    }
}

# ============================================
# THRESHOLDS Y CONFIG
# ============================================
MIN_STOCK = 0
MAX_STOCK = 1000
MIN_PRICE = 0.01
MAX_PRICE = 10000
MIN_DEMAND = 0
MAX_DEMAND = 500

# ============================================
# PERFORMANCE METRICS
# ============================================
MODEL_PERFORMANCE = {
    "MAE_Test": 0.7634,
    "RMSE_Test": 1.4091,
    "R2_Test": 0.9443,
    "MAE_Train": 0.6569,
    "R2_Train": 0.9664
}
