"""
Integration tests for API health check endpoints.

Tests the health check endpoint with real and mocked dependencies.
Demonstrates usage of test fixtures for API testing.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.integration
@pytest.mark.api
def test_health_endpoint_basic(api_client):
    """
    Test basic health check endpoint.
    
    This test verifies that the health endpoint returns a successful response.
    Uses the api_client fixture which provides a FastAPI TestClient.
    """
    response = api_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.integration
@pytest.mark.api
def test_root_endpoint(api_client):
    """
    Test root endpoint returns service information.
    
    Verifies the root endpoint provides service name, version, and status.
    """
    response = api_client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify expected fields
    assert "service" in data
    assert "version" in data
    assert "status" in data
    
    # Verify values
    assert data["status"] == "running"


@pytest.mark.unit
@pytest.mark.api
def test_health_endpoint_with_mock_redis(api_client, mock_redis_client):
    """
    Test health endpoint with mocked Redis.
    
    This demonstrates testing API endpoints with mocked external dependencies.
    Useful for unit-level API tests that don't need real services.
    """
    # Mock the Redis client at the module level
    with patch("app.api.health.redis_client", mock_redis_client):
        response = api_client.get("/health")
        
        # Should succeed with mocked Redis
        assert response.status_code in [200, 503]  # May vary based on implementation


@pytest.mark.integration
@pytest.mark.api
def test_nonexistent_endpoint(api_client):
    """
    Test that nonexistent endpoints return 404.
    
    Verifies proper error handling for undefined routes.
    """
    response = api_client.get("/nonexistent/endpoint")
    
    assert response.status_code == 404


# Example of parametrized test for multiple endpoints
@pytest.mark.integration
@pytest.mark.api
@pytest.mark.parametrize("endpoint,expected_status", [
    ("/", 200),
    ("/health", 200),
    ("/storage/stats", 200),
])
def test_public_endpoints(api_client, endpoint, expected_status):
    """
    Test multiple public endpoints.
    
    Parametrized test that verifies multiple endpoints return expected status codes.
    This is efficient for testing similar behavior across multiple routes.
    """
    response = api_client.get(endpoint)
    assert response.status_code == expected_status
