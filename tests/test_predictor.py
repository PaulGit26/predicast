"""
Tests para validar sistema
"""

import pytest
import sys
import os
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ml.model_loader import ModelLoader
from src.ml.predictor import XGBoostPredictor


class TestModelLoader:
    """Tests para carga del modelo"""
    
    def test_model_loading(self):
        """Test: Cargar modelo exitosamente"""
        model_path = "../../03_Modelos/xgboost_model_V2_V2_Realista.joblib"
        metadata_path = "../../03_Modelos/xgboost_metadata_V2_V2_Realista.json"
        
        loader = ModelLoader(model_path, metadata_path)
        model, metadata = loader.load()
        
        assert model is not None
        assert metadata is not None
        assert metadata['n_features'] == 15
        assert metadata['target'] == 'Cantidad'
    
    def test_model_metadata_validation(self):
        """Test: Validar metadata"""
        model_path = "../../03_Modelos/xgboost_model_V2_V2_Realista.joblib"
        metadata_path = "../../03_Modelos/xgboost_metadata_V2_V2_Realista.json"
        
        loader = ModelLoader(model_path, metadata_path)
        model, metadata = loader.load()
        
        # Validar performance
        assert metadata['performance']['R2_Test'] > 0.9
        assert metadata['performance']['MAE_Test'] < 2.0


class TestPreddictor:
    """Tests para predictor"""
    
    @pytest.fixture
    def predictor(self):
        """Fixture: crear predictor"""
        model_path = "../../03_Modelos/xgboost_model_V2_V2_Realista.joblib"
        metadata_path = "../../03_Modelos/xgboost_metadata_V2_V2_Realista.json"
        
        loader = ModelLoader(model_path, metadata_path)
        return XGBoostPredictor(loader)
    
    def test_prediction_valid_input(self, predictor):
        """Test: Predicción con input válido"""
        input_data = {
            "Stock_anterior": 100,
            "Stock_posterior": 95,
            "Precio_unitario": 150.0,
            "Año": 2026,
            "Mes": 4,
            "Trimestre": 2,
            "Día_Semana": 2,
            "Canal_Promedio_Demanda": 75.0,
            "Campana_Promedio_Demanda": 60.0,
            "Cliente_Promedio_Demanda": 80.0,
            "Producto_Promedio_Demanda": 85.0,
            "Canal_venta_encoded": 0,
            "Campana_encoded": 3,
            "Empresa_cliente_encoded": 0,
            "Producto_codigo_encoded": 0
        }
        
        result = predictor.predict(input_data)
        
        assert result['status'] == 'success'
        assert result['prediction'] > 0
        assert result['prediction'] < 500
        assert result['confidence'] > 0.9
    
    def test_prediction_missing_feature(self, predictor):
        """Test: Predicción con feature faltante"""
        input_data = {
            "Stock_anterior": 100,
            # Falta Stock_posterior
        }
        
        result = predictor.predict(input_data)
        assert result['status'] == 'error'
        assert 'Faltan features' in result['error']
    
    def test_batch_prediction(self, predictor):
        """Test: Predicción en batch"""
        input_list = [
            {
                "Stock_anterior": 100,
                "Stock_posterior": 95,
                "Precio_unitario": 150.0,
                "Año": 2026,
                "Mes": 4,
                "Trimestre": 2,
                "Día_Semana": 2,
                "Canal_Promedio_Demanda": 75.0,
                "Campana_Promedio_Demanda": 60.0,
                "Cliente_Promedio_Demanda": 80.0,
                "Producto_Promedio_Demanda": 85.0,
                "Canal_venta_encoded": 0,
                "Campana_encoded": 3,
                "Empresa_cliente_encoded": 0,
                "Producto_codigo_encoded": 0
            },
            {
                "Stock_anterior": 200,
                "Stock_posterior": 180,
                "Precio_unitario": 250.0,
                "Año": 2026,
                "Mes": 5,
                "Trimestre": 2,
                "Día_Semana": 3,
                "Canal_Promedio_Demanda": 80.0,
                "Campana_Promedio_Demanda": 70.0,
                "Cliente_Promedio_Demanda": 85.0,
                "Producto_Promedio_Demanda": 90.0,
                "Canal_venta_encoded": 1,
                "Campana_encoded": 0,
                "Empresa_cliente_encoded": 1,
                "Producto_codigo_encoded": 1
            }
        ]
        
        results = predictor.predict_batch(input_list)
        
        assert len(results) == 2
        assert all(r['status'] == 'success' for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
