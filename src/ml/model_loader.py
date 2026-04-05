"""
Model Loader: Carga el modelo XGBoost y su metadata
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import joblib

logger = logging.getLogger(__name__)

class ModelLoader:
    """
    Carga y valida el modelo XGBoost y su metadata
    """
    
    def __init__(self, model_path: str, metadata_path: str):
        """
        Args:
            model_path: Ruta al archivo .joblib del modelo
            metadata_path: Ruta al archivo .json con metadata
        """
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)
        self.model = None
        self.metadata = None
        
    def load(self) -> tuple:
        """
        Carga el modelo y metadata
        
        Returns:
            (model, metadata)
            
        Raises:
            FileNotFoundError: Si los archivos no existen
            ValueError: Si hay inconsistencia en metadata
        """
        # Validar archivos existen
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {self.model_path}")
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata no encontrado: {self.metadata_path}")
        
        try:
            # Cargar modelo
            logger.info(f"Cargando modelo desde {self.model_path}")
            self.model = joblib.load(self.model_path)
            
            # Cargar metadata
            logger.info(f"Cargando metadata desde {self.metadata_path}")
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            
            # Validar metadata
            self._validate_metadata()
            
            logger.info(f"✅ Modelo cargado exitosamente. "
                       f"Features: {self.metadata['n_features']}, "
                       f"R²: {self.metadata['performance']['R2_Test']:.4f}")
            
            return self.model, self.metadata
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            raise
    
    def _validate_metadata(self):
        """Valida que el metadata sea válido"""
        required_keys = [
            'model_version',
            'n_features',
            'features',
            'target',
            'label_encoders',
            'performance'
        ]
        
        for key in required_keys:
            if key not in self.metadata:
                raise ValueError(f"Metadata falta clave requerida: {key}")
        
        # Validar features
        if len(self.metadata['features']) != self.metadata['n_features']:
            raise ValueError(
                f"Inconsistencia: n_features={self.metadata['n_features']} "
                f"pero features length={len(self.metadata['features'])}"
            )
        
        logger.info(f"✅ Metadata validado")
    
    def get_features(self) -> list:
        """Retorna lista de features requeridas"""
        return self.metadata['features']
    
    def get_label_encoders(self) -> Dict[str, Dict[str, int]]:
        """Retorna los encoders para variables categóricas"""
        return self.metadata['label_encoders']
    
    def get_performance(self) -> Dict[str, float]:
        """Retorna métricas de performance del modelo"""
        return self.metadata['performance']
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna información completa del modelo"""
        return {
            "version": self.metadata['model_version'],
            "features": self.metadata['features'],
            "n_features": self.metadata['n_features'],
            "target": self.metadata['target'],
            "performance": self.metadata['performance'],
            "excluded_features": self.metadata.get('features_excluded', []),
            "hyperparameters": self.metadata.get('hyperparameters', {})
        }
