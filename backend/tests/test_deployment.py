"""
Tests for deployment preparation features.

This module tests Docker configuration, health checks, and deployment readiness.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


client = TestClient(app)


class TestHealthCheckEndpoint:
    """Tests for health check endpoint (Requirement 19.7)."""
    
    def test_health_check_all_services_healthy(self):
        """Test health check returns 200 when all services are healthy."""
        with patch('app.main.check_db_health') as mock_db_health, \
             patch('app.main.get_db_info') as mock_db_info, \
             patch('app.core.redis.get_redis_client') as mock_redis:
            
            # Mock healthy services
            mock_db_health.return_value = True
            mock_db_info.return_value = {
                'pool_size': 5,
                'checked_in': 4,
                'checked_out': 1
            }
            
            mock_redis_client = MagicMock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            # Make request
            response = client.get("/health")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            assert data['status'] == 'healthy'
            assert 'timestamp' in data
            assert data['services']['database']['status'] == 'healthy'
            assert data['services']['database']['connected'] is True
            assert data['services']['redis']['status'] == 'healthy'
            assert data['services']['redis']['connected'] is True
    
    def test_health_check_database_unhealthy(self):
        """Test health check returns 503 when database is unhealthy."""
        with patch('app.main.check_db_health') as mock_db_health, \
             patch('app.core.redis.get_redis_client') as mock_redis:
            
            # Mock unhealthy database
            mock_db_health.return_value = False
            
            # Mock healthy Redis
            mock_redis_client = MagicMock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            # Make request
            response = client.get("/health")
            
            # Verify response
            assert response.status_code == 503
            data = response.json()
            
            assert data['status'] == 'unhealthy'
            assert data['services']['database']['status'] == 'unhealthy'
            assert data['services']['database']['connected'] is False
    
    def test_health_check_redis_unhealthy(self):
        """Test health check returns 503 when Redis is unhealthy."""
        with patch('app.main.check_db_health') as mock_db_health, \
             patch('app.main.get_db_info') as mock_db_info, \
             patch('app.core.redis.get_redis_client') as mock_redis:
            
            # Mock healthy database
            mock_db_health.return_value = True
            mock_db_info.return_value = {'pool_size': 5}
            
            # Mock unhealthy Redis
            mock_redis_client = MagicMock()
            mock_redis_client.ping.side_effect = Exception("Connection failed")
            mock_redis.return_value = mock_redis_client
            
            # Make request
            response = client.get("/health")
            
            # Verify response
            assert response.status_code == 503
            data = response.json()
            
            assert data['status'] == 'unhealthy'
            assert data['services']['redis']['status'] == 'unhealthy'
            assert data['services']['redis']['connected'] is False
    
    def test_health_check_all_services_unhealthy(self):
        """Test health check returns 503 when all services are unhealthy."""
        with patch('app.main.check_db_health') as mock_db_health, \
             patch('app.core.redis.get_redis_client') as mock_redis:
            
            # Mock unhealthy services
            mock_db_health.return_value = False
            
            mock_redis_client = MagicMock()
            mock_redis_client.ping.side_effect = Exception("Connection failed")
            mock_redis.return_value = mock_redis_client
            
            # Make request
            response = client.get("/health")
            
            # Verify response
            assert response.status_code == 503
            data = response.json()
            
            assert data['status'] == 'unhealthy'
            assert data['services']['database']['status'] == 'unhealthy'
            assert data['services']['redis']['status'] == 'unhealthy'


class TestCORSConfiguration:
    """Tests for CORS configuration (Requirement 13.4)."""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
    
    def test_cors_allows_configured_origins(self):
        """Test that CORS allows configured origins."""
        # This test depends on CORS_ORIGINS configuration
        # In test environment, it should allow localhost:3000
        response = client.get(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should not be blocked
        assert response.status_code == 200


class TestDockerHealthCheck:
    """Tests for Docker health check compatibility."""
    
    def test_health_endpoint_accessible(self):
        """Test that /health endpoint is accessible without authentication."""
        response = client.get("/health")
        
        # Should be accessible without auth
        assert response.status_code in [200, 503]
        
        # Should return JSON
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'services' in data
    
    def test_health_endpoint_response_format(self):
        """Test that health endpoint returns expected format."""
        with patch('app.main.check_db_health') as mock_db_health, \
             patch('app.main.get_db_info') as mock_db_info, \
             patch('app.core.redis.get_redis_client') as mock_redis:
            
            mock_db_health.return_value = True
            mock_db_info.return_value = {}
            
            mock_redis_client = MagicMock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            response = client.get("/health")
            data = response.json()
            
            # Verify structure
            assert isinstance(data['status'], str)
            assert isinstance(data['timestamp'], str)
            assert isinstance(data['services'], dict)
            assert 'database' in data['services']
            assert 'redis' in data['services']
            
            # Verify service structure
            assert 'status' in data['services']['database']
            assert 'connected' in data['services']['database']
            assert 'status' in data['services']['redis']
            assert 'connected' in data['services']['redis']


class TestProductionReadiness:
    """Tests for production readiness checks."""
    
    def test_root_endpoint_returns_app_info(self):
        """Test that root endpoint returns application information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'name' in data
        assert 'version' in data
        assert 'status' in data
        assert 'environment' in data
    
    def test_api_documentation_accessible(self):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        
        # Should be accessible
        assert response.status_code == 200
    
    def test_openapi_schema_accessible(self):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'openapi' in data
        assert 'info' in data
        assert 'paths' in data
