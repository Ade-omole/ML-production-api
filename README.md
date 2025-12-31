# Customer Churn Prediction API

Production-ready ML inference service for customer churn prediction using FastAPI and Docker.

## Overview

This service provides a REST API for predicting customer churn using a trained Random Forest model. The API is containerized with Docker and follows production best practices including health checks, input validation, and comprehensive error handling.

## Features

- FastAPI-based REST API with automatic OpenAPI documentation
- Model loads once at startup for optimal performance
- Pydantic schemas for request/response validation
- Health check and model info endpoints
- Docker containerization
- CI/CD ready with GitHub Actions
- Comprehensive test suite

## Project Structure

```
ML_Deployment/
├── app/                          # Application code
│   ├── __init__.py
│   ├── main.py                  # FastAPI application and endpoints
│   ├── models.py                # Pydantic schemas for validation
│   └── ml_model.py              # Model loading and prediction logic
├── tests/                        # Automated test suite
│   └── test_api.py
├── churn_prediction_model.pkl   # Trained ML model
├── requirements_api.txt          # Python dependencies
├── Dockerfile                    # Container definition
├── .dockerignore                 # Docker build exclusions
├── .github/                      # CI/CD workflows
│   └── workflows/
│       └── deploy.yml
└── README.md                     # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)

### Local Development

1. **Install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements_api.txt
   ```

2. **Start the server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Model Info: http://localhost:8000/info

### Docker Deployment

1. **Build the image:**
   ```bash
   docker build -t churn-prediction-api:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d --name churn-api -p 8000:8000 churn-prediction-api:latest
   ```

3. **View logs:**
   ```bash
   docker logs churn-api
   ```

## API Endpoints

### `GET /`
Returns basic service information and available endpoints.

### `GET /health`
Health check endpoint. Returns service status and model availability.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_type": "RandomForestClassifier",
  "feature_count": 38
}
```

### `GET /info`
Returns detailed information about the deployed model including performance metrics.

### `POST /predict`
Main prediction endpoint. Accepts customer feature data and returns churn prediction.

**Request:**
```json
{
  "features": {
    "SeniorCitizen": 0,
    "tenure": 12,
    "MonthlyCharges": 70.0,
    ...
  }
}
```

**Response:**
```json
{
  "prediction": 0,
  "prediction_label": "No Churn",
  "probability": {
    "no_churn": 0.85,
    "churn": 0.15
  },
  "model_info": {
    "model_type": "RandomForestClassifier",
    "feature_count": 38
  }
}
```

### `GET /docs`
Interactive API documentation (Swagger UI).

## Testing

Run the automated test suite:

```bash
pytest tests/ -v
```

## Configuration

### Environment Variables

- `MODEL_PATH`: Path to the model file (default: `churn_prediction_model.pkl`)
- `PORT`: Server port (default: 8000)

### Model Requirements

The model file must be a joblib-serialized dictionary containing:
- `model`: Trained scikit-learn model
- `scaler`: Feature scaler (StandardScaler)
- `feature_names`: List of feature names in expected order
- `model_type`: Model type string (optional)
- `trained_date`: Training date string (optional)
- `performance`: Performance metrics dictionary (optional)

## CI/CD

The repository includes a GitHub Actions workflow (`.github/workflows/deploy.yml`) that:
- Runs automated tests on push to main branch
- Builds Docker image if tests pass
- Validates Docker image functionality

## Deployment

See `DEPLOYMENT.md` for detailed deployment instructions including:
- Local deployment
- Docker deployment
- AWS EC2 deployment
- Domain and HTTPS configuration
- Monitoring and logging setup

## Architecture

See `ARCHITECTURE.md` for detailed explanations of:
- Code structure and design decisions
- File-by-file breakdown
- Design patterns and best practices

## License

[Specify your license here]

## Contributing

[Specify contribution guidelines if applicable]
