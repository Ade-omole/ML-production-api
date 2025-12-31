# Deployment Guide

Complete guide for deploying the Customer Churn Prediction API service.

## Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Local Development

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)

### Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_api.txt
```

### Configuration

Set the model path if using a custom location:

```bash
export MODEL_PATH=churn_prediction_model.pkl
```

### Running the Service

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Verification

```bash
# Health check
curl http://localhost:8000/health

# API documentation
# Open http://localhost:8000/docs in browser
```

## Docker Deployment

### Build Image

```bash
docker build -t churn-prediction-api:latest .
```

### Run Container

```bash
# Run in detached mode
docker run -d \
  --name churn-api \
  -p 8000:8000 \
  --restart unless-stopped \
  churn-prediction-api:latest

# View logs
docker logs churn-api

# Follow logs
docker logs -f churn-api
```

### Container Management

```bash
# Stop container
docker stop churn-api

# Start container
docker start churn-api

# Remove container
docker rm churn-api

# Remove image
docker rmi churn-prediction-api:latest
```

## API Endpoints

### `GET /`

Returns service metadata and available endpoints.

**Response:**
```json
{
  "service": "Customer Churn Prediction API",
  "version": "0.1.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health"
}
```

### `GET /health`

Health check endpoint for monitoring and load balancers.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_type": "RandomForestClassifier",
  "feature_count": 38
}
```

**Status Codes:**
- `200`: Service healthy, model loaded
- `503`: Service unhealthy, model not loaded

### `GET /info`

Returns detailed model information including performance metrics.

**Response:**
```json
{
  "service_name": "Customer Churn Prediction API",
  "version": "0.1.0",
  "model_type": "RandomForestClassifier",
  "model_trained_date": "2025-12-22T02:44:48.641353",
  "model_performance": {
    "f1_score": 0.626,
    "roc_auc": 0.841,
    "accuracy": 0.759
  },
  "feature_count": 38
}
```

### `POST /predict`

Main prediction endpoint. Accepts customer feature data and returns churn prediction with probabilities.

**Request:**
```json
{
  "features": {
    "SeniorCitizen": 0,
    "tenure": 12,
    "MonthlyCharges": 70.0,
    "TotalCharges": 840.0,
    "AvgMonthlyCharge": 70.0,
    "ServiceCount": 1,
    "HighValueCustomer": 0,
    "ChargeRatio": 1.0,
    "gender_Male": 1,
    "Partner_Yes": 0,
    "Dependents_Yes": 0,
    "PhoneService_Yes": 1,
    "MultipleLines_No phone service": 0,
    "MultipleLines_Yes": 0,
    "InternetService_Fiber optic": 0,
    "InternetService_No": 1,
    "OnlineSecurity_No internet service": 1,
    "OnlineSecurity_Yes": 0,
    "OnlineBackup_No internet service": 1,
    "OnlineBackup_Yes": 0,
    "DeviceProtection_No internet service": 1,
    "DeviceProtection_Yes": 0,
    "TechSupport_No internet service": 1,
    "TechSupport_Yes": 0,
    "StreamingTV_No internet service": 1,
    "StreamingTV_Yes": 0,
    "StreamingMovies_No internet service": 1,
    "StreamingMovies_Yes": 0,
    "Contract_One year": 0,
    "Contract_Two year": 0,
    "PaperlessBilling_Yes": 1,
    "PaymentMethod_Credit card (automatic)": 0,
    "PaymentMethod_Electronic check": 1,
    "PaymentMethod_Mailed check": 0,
    "TenureGroup_12-24": 1,
    "TenureGroup_24-48": 0,
    "TenureGroup_48-72": 0,
    "TenureGroup_72+": 0
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

**Status Codes:**
- `200`: Prediction successful
- `400`: Invalid input (missing or incorrect features)
- `422`: Validation error (data type mismatch)
- `500`: Internal server error
- `503`: Model not available

### `GET /docs`

Interactive API documentation (Swagger UI).

### `GET /openapi.json`

OpenAPI schema specification.

## Troubleshooting

### Model File Not Found

**Error:** `FileNotFoundError: Model file not found`

**Solution:**
- Verify `churn_prediction_model.pkl` exists in project root
- Set `MODEL_PATH` environment variable if using custom path
- Ensure Dockerfile includes model file in COPY command

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Use different port
uvicorn app.main:app --port 8001

# Or kill process using port 8000
lsof -ti:8000 | xargs kill
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
- Ensure you're in the project root directory
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements_api.txt`

### Docker Build Fails

**Error:** Various build errors

**Solution:**
```bash
# Verify Docker is running
docker ps

# Clear Docker cache and rebuild
docker system prune -a
docker build --no-cache -t churn-prediction-api:latest .
```

### Dependency Version Conflicts

**Error:** Package version conflicts or binary incompatibility

**Solution:**
- Ensure Python version matches requirements (3.11+)
- Update packages: `pip install --upgrade -r requirements_api.txt`
- Use virtual environment to isolate dependencies

## Production Deployment

### CI/CD

The repository includes GitHub Actions workflow (`.github/workflows/deploy.yml`) configured to:
- Run automated tests on push to main branch
- Build Docker image on successful tests
- Validate container functionality

### Cloud Deployment

#### AWS EC2

1. **Launch EC2 Instance:**
   - AMI: Ubuntu Server 22.04 LTS
   - Instance Type: t3.medium or larger
   - Security Group: Open ports 8000 (API) and 22 (SSH)

2. **Install Docker:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **Deploy Application:**
   ```bash
   # Pull image from registry or build on server
   docker pull YOUR_REGISTRY/churn-prediction-api:latest
   
   # Run container
   docker run -d \
     --name churn-api \
     -p 8000:8000 \
     --restart unless-stopped \
     YOUR_REGISTRY/churn-prediction-api:latest
   ```

4. **Configure Reverse Proxy (nginx):**
   - Install nginx and configure as reverse proxy
   - Set up SSL/TLS certificates (Let's Encrypt)
   - Configure domain name and DNS

#### Container Registry

Push Docker image to registry:

```bash
# Tag image
docker tag churn-prediction-api:latest YOUR_REGISTRY/churn-prediction-api:latest

# Push to registry
docker push YOUR_REGISTRY/churn-prediction-api:latest
```

### Production Considerations

- **Monitoring:** Set up application and infrastructure monitoring
- **Logging:** Configure centralized logging (CloudWatch, ELK, etc.)
- **Security:** Implement rate limiting, API authentication, secrets management
- **Scaling:** Configure load balancing and auto-scaling for high traffic
- **High Availability:** Deploy multiple instances across availability zones
- **Model Versioning:** Implement model version management and rollback capability

### Environment Variables

Production environment variables should be managed securely:

- `MODEL_PATH`: Path to model file
- `LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)
- API keys and secrets via AWS Secrets Manager or similar

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Additional Resources

- FastAPI Documentation: https://fastapi.tiangolo.com
- Docker Documentation: https://docs.docker.com
- AWS EC2 Documentation: https://docs.aws.amazon.com/ec2
