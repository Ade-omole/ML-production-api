"""
ML Model Loading and Prediction Logic

Handles model loading, preprocessing, and prediction operations.
"""

import os
import joblib
import numpy as np
# import pandas as pd
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ModelLoader:
    """Loads and manages the ML model package."""
    
    def __init__(self, model_path: str):
        """
        Initialize the model loader.
        
        Args:
            model_path: Path to the saved model file
        """
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.model_info = {}
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the model package from disk."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model file not found at {self.model_path}. "
                "Please ensure the model file exists."
            )
        
        try:
            model_package = joblib.load(self.model_path)
            self.model = model_package['model']
            self.scaler = model_package['scaler']
            self.feature_names = model_package['feature_names']
            
            self.model_info = {
                'model_type': model_package.get('model_type', 'Unknown'),
                'trained_date': model_package.get('trained_date', 'Unknown'),
                'performance': model_package.get('performance', {}),
                'feature_count': len(self.feature_names)
            }
            
            logger.info(f"Model loaded successfully: {self.model_info['model_type']}")
            logger.info(f"Model has {len(self.feature_names)} features")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise RuntimeError(f"Failed to load model: {str(e)}")
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Make a prediction given input features.
        
        Args:
            features: Dictionary mapping feature names to values
            
        Returns:
            Dictionary with prediction, probability, and metadata
        """
        try:
            feature_array = np.array([features.get(name, 0.0) for name in self.feature_names])
            feature_array = feature_array.reshape(1, -1)
            feature_array_scaled = self.scaler.transform(feature_array)
            
            prediction = self.model.predict(feature_array_scaled)[0]
            probabilities = self.model.predict_proba(feature_array_scaled)[0]
            
            return {
                'prediction': int(prediction),
                'prediction_label': 'Churn' if prediction == 1 else 'No Churn',
                'probability': {
                    'no_churn': float(probabilities[0]),
                    'churn': float(probabilities[1])
                },
                'model_info': {
                    'model_type': self.model_info['model_type'],
                    'feature_count': len(self.feature_names)
                }
            }
            
        except KeyError as e:
            raise ValueError(f"Missing required feature: {str(e)}")
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise RuntimeError(f"Prediction failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return model metadata."""
        return self.model_info


_model_loader: Optional[ModelLoader] = None


def get_model() -> ModelLoader:
    """
    Get the global model instance (singleton pattern).
    Model is loaded once and reused for all requests.
    """
    global _model_loader
    if _model_loader is None:
        model_path = os.getenv('MODEL_PATH', 'churn_prediction_model.pkl')
        _model_loader = ModelLoader(model_path)
    return _model_loader

