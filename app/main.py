"""
FastAPI Application: Customer Churn Prediction Inference Service

Main entry point for the ML inference API.
Exposes REST endpoints for predictions and service health monitoring.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from typing import Dict

from app.ml_model import get_model, ModelLoader
from app.models import (
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    InfoResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    Loads model at startup for optimal performance.
    """
    logger.info("Starting up ML inference service...")
    try:
        model = get_model()
        logger.info(f"Model loaded: {model.model_info['model_type']}")
        logger.info("Service ready to accept requests")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        pass
    
    yield
    
    logger.info("Shutting down ML inference service...")


# Create FastAPI app with metadata
app = FastAPI(
    title="Customer Churn Prediction API",
    description="ML inference service for predicting customer churn",
    version="0.1.0",
    lifespan=lifespan  # Handles startup/shutdown
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint providing basic API information."""
    return {
        "service": "Customer Churn Prediction API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns 200 if healthy, 503 if service unavailable.
    """
    try:
        model = get_model()
        return HealthResponse(
            status="healthy",
            model_loaded=True,
            model_type=model.model_info.get('model_type'),
            feature_count=len(model.feature_names) if model.feature_names else None
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        # Return 503 Service Unavailable if model not loaded
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )


@app.get("/info", response_model=InfoResponse, tags=["Info"])
async def model_info():
    """Returns detailed information about the loaded model."""
    try:
        model = get_model()
        model_info = model.model_info
        
        return InfoResponse(
            service_name="Customer Churn Prediction API",
            version="0.1.0",
            model_type=model_info.get('model_type', 'Unknown'),
            model_trained_date=model_info.get('trained_date', 'Unknown'),
            model_performance=model_info.get('performance', {}),
            feature_count=model_info.get('feature_count', 0)
        )
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model not available: {str(e)}"
        )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest):
    """
    Main prediction endpoint.
    Accepts customer feature data and returns churn prediction with probabilities.
    """
    try:
        model = get_model()
        result = model.predict(request.features)
        return PredictionResponse(**result)
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except RuntimeError as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

