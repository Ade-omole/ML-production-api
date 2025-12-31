"""
Pydantic Models for Request/Response Validation

Defines request and response schemas with automatic validation and type conversion.
"""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Dict, Optional
from enum import Enum


class PredictionRequest(BaseModel):
    """Request schema for /predict endpoint."""
    features: Dict[str, float] = Field(
        ...,
        description="Dictionary of feature names to numeric values",
        example={
            "SeniorCitizen": 0,
            "tenure": 12,
            "MonthlyCharges": 70.0,
            "TotalCharges": 840.0
        }
    )
    
    @validator('features')
    def validate_features_not_empty(cls, v):
        """Validate features dictionary is not empty."""
        if not v:
            raise ValueError('Features dictionary cannot be empty')
        return v


class Probability(BaseModel):
    """Probability scores for each class."""
    no_churn: float = Field(..., ge=0.0, le=1.0, description="Probability of no churn")
    churn: float = Field(..., ge=0.0, le=1.0, description="Probability of churn")


class ModelInfo(BaseModel):
    """Model metadata."""
    model_config = ConfigDict(protected_namespaces=())
    
    model_type: str
    feature_count: int


class PredictionResponse(BaseModel):
    """Response schema for /predict endpoint."""
    model_config = ConfigDict(protected_namespaces=())
    
    prediction: int = Field(
        ...,
        description="Predicted class (0 = No Churn, 1 = Churn)",
        example=0
    )
    prediction_label: str = Field(
        ...,
        description="Human-readable prediction label",
        example="No Churn"
    )
    probability: Probability
    model_info: ModelInfo


class HealthResponse(BaseModel):
    """Response schema for /health endpoint."""
    model_config = ConfigDict(protected_namespaces=())
    
    status: str = Field(..., description="Service status", example="healthy")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    model_type: Optional[str] = Field(None, description="Type of loaded model")
    feature_count: Optional[int] = Field(None, description="Number of features expected")


class InfoResponse(BaseModel):
    """Response schema for /info endpoint."""
    model_config = ConfigDict(protected_namespaces=())
    
    service_name: str
    version: str
    model_type: str
    model_trained_date: str
    model_performance: Dict[str, float]
    feature_count: int

