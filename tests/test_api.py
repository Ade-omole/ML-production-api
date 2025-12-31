"""
Basic tests for the API endpoints.
These run automatically in CI/CD pipeline.

To run tests locally:
    pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create a test client (simulates HTTP requests)
client = TestClient(app)


def test_root_endpoint():
    """Test that root endpoint returns correct info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert data["status"] == "running"
    assert "/docs" in data.get("docs", "")
    assert "/health" in data.get("health", "")


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    # Should return 200 if model loaded, 503 if not
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert isinstance(data["model_loaded"], bool)


def test_info_endpoint():
    """Test model info endpoint."""
    response = client.get("/info")
    # Should return 200 if model loaded, 503 if not
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "service_name" in data
        assert "version" in data
        assert "model_type" in data
        assert "feature_count" in data


def test_predict_endpoint_missing_features():
    """Test prediction endpoint with missing features."""
    # Try to predict with empty features
    response = client.post(
        "/predict",
        json={"features": {}}
    )
    # Should return 400 (bad request) or 422 (validation error)
    assert response.status_code in [400, 422]


def test_predict_endpoint_invalid_data():
    """Test prediction endpoint with invalid data type."""
    # Try to predict with wrong data type
    response = client.post(
        "/predict",
        json={"features": "not a dict"}
    )
    # Should return 422 (validation error)
    assert response.status_code == 422


def test_docs_endpoint():
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    # Should return 200 (HTML page)
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_openapi_schema():
    """Test that OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data

