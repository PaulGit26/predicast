"""
XGBoost Predictor: Wrapper para realizar predicciones con el modelo
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from .model_loader import ModelLoader
from src.utils.constants import LABEL_ENCODINGS

logger = logging.getLogger(__name__)

class XGBoostPredictor:
    """
    Wrapper para hacer predicciones con XGBoost
    
    Responsabilidades:
    - Preparar features del input
    - Validar input
    - Hacer predicción
    - Retornar resultado con confianza
    """
    
    def __init__(self, model_loader: ModelLoader):
        """
        Args:
            model_loader: Instancia de ModelLoader con modelo cargado
        """
        self.model, self.metadata = model_loader.load()
        self.features = model_loader.get_features()
        self.label_encoders = model_loader.get_label_encoders()
        self.performance = model_loader.get_performance()
        
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hace predicción con los datos de entrada
        
        Args:
            input_data: Dict con features (e.g., {"Stock_anterior": 10, ...})
        
        Returns:
            Dict con predicción, confianza, metadata
        """
        try:
            # 1. Validar input
            self._validate_input(input_data)
            
            # 2. Preparar features
            X = self._prepare_features(input_data)
            
            # 3. Hacer predicción
            prediction = self.model.predict(X)[0]
            prediction = float(np.clip(prediction, 0, 500))  # Clamp a rango realista
            
            # 4. Calcular confianza (basado en R²)
            confidence = float(self.performance['R2_Test'])
            
            # 5. Retornar resultado
            return {
                "prediction": round(prediction, 2),
                "confidence": round(confidence, 4),
                "mae_test": round(self.performance['MAE_Test'], 4),
                "model_version": self.metadata['model_version'],
                "target": self.metadata['target'],
                "input_features": len(self.features),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Error en predicción: {e}")
            return {
                "prediction": None,
                "error": str(e),
                "status": "error"
            }
    
    def predict_batch(self, input_data_list: List[Dict]) -> List[Dict]:
        """
        Hace predicciones en batch
        
        Args:
            input_data_list: Lista de dicts con features
        
        Returns:
            Lista de predicciones
        """
        return [self.predict(data) for data in input_data_list]
    
    def _validate_input(self, input_data: Dict) -> None:
        """
        Valida que el input tenga todas las features requeridas
        
        Raises:
            ValueError: Si faltan features
        """
        missing_features = [f for f in self.features if f not in input_data]
        if missing_features:
            raise ValueError(
                f"Faltan features requeridas: {missing_features}"
            )
    
    def _prepare_features(self, input_data: Dict) -> np.ndarray:
        """
        Prepara los features en el orden correcto para el modelo
        
        Args:
            input_data: Dict con feature values
        
        Returns:
            Array numpy con features en orden correcto
        """
        prepared = []
        
        for feature in self.features:
            value = input_data[feature]
            
            # Si es una feature categórica, hacer encoding
            if feature in self.label_encoders:
                encoder_map = self.label_encoders[feature]
                if value not in encoder_map:
                    logger.warning(f"⚠️ Valor desconocido para {feature}: {value}. "
                                 f"Usando UNKNOWN o primer valor.")
                    # Intentar usar UNKNOWN si existe
                    value = encoder_map.get("UNKNOWN", list(encoder_map.values())[0])
                else:
                    value = encoder_map[value]
            
            prepared.append(value)
        
        # Convertir a array 2D (1 muestra, n features)
        return np.array(prepared).reshape(1, -1)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna información del modelo"""
        return {
            "version": self.metadata['model_version'],
            "features": self.features,
            "n_features": len(self.features),
            "target": self.metadata['target'],
            "performance": self.performance,
            "r2_score": round(self.performance['R2_Test'], 4),
            "mae": round(self.performance['MAE_Test'], 4)
        }
