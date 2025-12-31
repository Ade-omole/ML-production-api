# Architecture Documentation

Technical documentation explaining the system architecture, design decisions, and component interactions.

## Project Structure

```
ML_Deployment/
├── app/                          # Application package
│   ├── __init__.py              # Package initializer
│   ├── main.py                  # FastAPI application (entry point)
│   ├── models.py                # Pydantic schemas (data validation)
│   └── ml_model.py              # Model loading and prediction logic
├── tests/                        # Test suite
│   └── test_api.py
├── churn_prediction_model.pkl   # Trained ML model
├── requirements_api.txt          # Production dependencies
├── Dockerfile                    # Container definition
├── .dockerignore                 # Docker build exclusions
├── .github/                      # CI/CD workflows
│   └── workflows/
│       └── deploy.yml
├── DEPLOYMENT.md                 # Deployment instructions
└── ARCHITECTURE.md               # This file
```

## Core Components

### `app/__init__.py`

Package initializer that defines the application version and enables package imports.

**Purpose:**
- Makes `app` a valid Python package
- Centralizes version management
- Enables clean imports: `from app.models import PredictionRequest`

### `app/ml_model.py`

Handles model loading, preprocessing, and prediction operations.

**Responsibilities:**
1. Load saved model package from disk
2. Manage feature scaler for normalization
3. Preprocess input data (apply scaling)
4. Execute predictions using loaded model
5. Return structured predictions with probabilities

**Design Rationale:**

**Separation of Concerns:**
- ML logic isolated from API logic
- Enables independent testing
- Facilitates model versioning and A/B testing

**Performance:**
- Model loads once at startup (singleton pattern)
- Loading per request would introduce 10-100x latency overhead

**Error Handling:**
- Centralized error handling for model operations
- Graceful degradation when model unavailable

#### ModelLoader Class

Encapsulates model state (model, scaler, feature names) and provides prediction interface.

```python
def __init__(self, model_path: str):
    self.model_path = model_path
    self._load_model()
```

**Model Loading:**
```python
model_package = joblib.load(self.model_path)
self.model = model_package['model']
self.scaler = model_package['scaler']
self.feature_names = model_package['feature_names']
```

The model package is a dictionary containing:
- `model`: Trained scikit-learn estimator
- `scaler`: StandardScaler instance used during training
- `feature_names`: Ordered list of feature names
- Metadata: model_type, trained_date, performance metrics

**Prediction Method:**
```python
def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
    feature_array = np.array([features.get(name, 0.0) for name in self.feature_names])
    feature_array = feature_array.reshape(1, -1)
    feature_array_scaled = self.scaler.transform(feature_array)
    prediction = self.model.predict(feature_array_scaled)[0]
    probabilities = self.model.predict_proba(feature_array_scaled)[0]
```

**Steps:**
1. Feature ordering: Ensure features match model's expected order
2. Reshape: Convert to 2D array (1 sample, N features) for sklearn
3. Scaling: Apply same StandardScaler used during training
4. Prediction: Get binary class (0=No Churn, 1=Churn)
5. Probabilities: Get confidence scores for both classes

**Singleton Pattern:**
```python
_model_loader: Optional[ModelLoader] = None

def get_model() -> ModelLoader:
    global _model_loader
    if _model_loader is None:
        model_path = os.getenv('MODEL_PATH', 'churn_prediction_model.pkl')
        _model_loader = ModelLoader(model_path)
    return _model_loader
```

Model loads on first call and is reused for subsequent requests, ensuring performance and consistency.

### `app/models.py`

Defines Pydantic schemas for request/response validation and automatic API documentation.

**Purpose:**
1. **Automatic Validation**: Type checking, range validation, required field enforcement
2. **API Documentation**: FastAPI generates OpenAPI/Swagger specs from schemas
3. **Type Safety**: Early error detection and improved IDE support
4. **Data Contracts**: Explicit API interface definition

#### Key Schemas

**PredictionRequest:**
```python
class PredictionRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Dictionary of feature names to numeric values")
```

Accepts feature dictionary mapping feature names to float values. Validated automatically by Pydantic before reaching business logic.

**PredictionResponse:**
```python
class PredictionResponse(BaseModel):
    prediction: int
    prediction_label: str
    probability: Probability
    model_info: ModelInfo
```

Defines structured response format with prediction, label, probabilities, and model metadata.

**HealthResponse & InfoResponse:**
Provide standardized responses for health checks and model information endpoints.

### `app/main.py`

FastAPI application entry point that defines HTTP endpoints and request routing.

**Responsibilities:**
1. Initialize FastAPI application
2. Define REST API endpoints
3. Handle HTTP request/response cycle
4. Manage application lifecycle (startup/shutdown)
5. Error handling and HTTP status code management

**Lifespan Context Manager:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up ML inference service...")
    model = get_model()  # Load model at startup
    yield  # Application runs here
    logger.info("Shutting down ML inference service...")
```

Model loading occurs once during startup, not per request, for optimal performance.

**API Endpoints:**

**GET /**: Service metadata and available endpoints

**GET /health**: Health check endpoint for monitoring and load balancers
- Returns 200 if healthy, 503 if service unavailable
- Used by orchestration platforms (Kubernetes liveness/readiness probes)

**GET /info**: Detailed model information including performance metrics

**POST /predict**: Main prediction endpoint
- Accepts PredictionRequest (validated by Pydantic)
- Returns PredictionResponse with prediction and probabilities
- Handles errors with appropriate HTTP status codes (400, 422, 500, 503)

**Error Handling:**
- `ValueError` → 400 Bad Request (invalid input)
- `RuntimeError` → 500 Internal Server Error (model/prediction failure)
- Unhandled exceptions → 500 with error logging

### `requirements_api.txt`

Production dependencies required to run the API service.

**Key Dependencies:**
- `fastapi`: Web framework
- `uvicorn[standard]`: ASGI server
- `pydantic`: Data validation
- `scikit-learn`: ML library for model inference
- `joblib`: Model serialization/deserialization
- `numpy`: Numerical operations

**Best Practices:**
- Separate from training dependencies
- Version pinning for reproducibility
- Minimal dependencies for smaller Docker images

### `Dockerfile`

Container image definition for consistent deployment across environments.

**Key Sections:**

**Base Image:**
```dockerfile
FROM python:3.11-slim
```
Uses slim variant to minimize image size while maintaining functionality.

**Layer Caching Optimization:**
```dockerfile
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt
COPY app/ ./app/
COPY churn_prediction_model.pkl .
```

Dependencies installed before code copy to leverage Docker layer caching. Dependencies change less frequently than code.

**Security:**
```dockerfile
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser
```

Runs as non-root user for security best practices.

**CMD:**
```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Starts FastAPI application. `--host 0.0.0.0` required for container networking.

### `.dockerignore`

Excludes unnecessary files from Docker build context, reducing build time and image size.

**Common Exclusions:**
- `__pycache__/`, `*.pyc`: Python bytecode
- `venv/`: Virtual environments (recreated in container)
- `.git/`: Version control metadata
- `*.ipynb`: Jupyter notebooks
- `*.csv`: Data files (model included separately)

## System Flow

### Request Flow

```
1. HTTP Request → FastAPI (main.py)
2. FastAPI validates request → Pydantic schemas (models.py)
3. Endpoint handler → ModelLoader (ml_model.py)
4. Model makes prediction → Returns result
5. FastAPI validates response → Pydantic schemas (models.py)
6. HTTP Response → Client
```

### Startup Flow

```
1. Container starts → Dockerfile CMD
2. uvicorn launches → main.py
3. lifespan() executes → ml_model.py (loads model)
4. Server ready → Accepts requests
```

## Design Patterns

### 1. Separation of Concerns
- API logic (`main.py`) separate from ML logic (`ml_model.py`)
- Data models (`models.py`) separate from business logic
- Enables independent testing and maintenance

### 2. Singleton Pattern
- Model instance loaded once, reused for all requests
- Critical for performance (avoids repeated disk I/O)

### 3. Dependency Injection
- `get_model()` provides model instance
- Can be extended to explicit FastAPI dependencies for better testability

### 4. Error Handling Strategy
- Early validation (Pydantic schemas)
- Specific exception types map to HTTP status codes
- Comprehensive error logging

### 5. Configuration via Environment
- `MODEL_PATH` configurable via environment variable
- Enables different configurations for dev/staging/prod environments

## Testing

Automated tests in `tests/test_api.py` validate:
- Endpoint functionality
- Request validation
- Error handling
- Response schemas

Tests run automatically in CI/CD pipeline (see `.github/workflows/deploy.yml`).

## Production Considerations

### Current Implementation
- Model loaded at startup (performance)
- Input validation via Pydantic (reliability)
- Health check endpoint (monitoring)
- Docker containerization (portability)
- CI/CD pipeline (automation)

### Future Enhancements
- Structured logging (JSON format)
- Metrics collection (Prometheus)
- Request tracing (distributed tracing)
- Rate limiting
- Authentication/authorization
- Model versioning
- A/B testing support
- Feature store integration
- Database for prediction storage and analytics

## Security

- Non-root container user
- Input validation and sanitization
- Error messages don't expose internal details
- Environment variables for sensitive configuration

## Performance

- Model loaded once at startup
- Async request handling (FastAPI)
- Efficient numpy operations for preprocessing
- Docker layer caching for faster builds
