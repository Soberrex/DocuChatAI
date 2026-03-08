import pytest
from fastapi.testclient import TestClient
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import app

client = TestClient(app)

# Test configuration
API_KEY = "dev-test-key-12345"
HEADERS = {"X-API-Key": API_KEY}


# Setup fixture
@pytest.fixture(scope="session", autouse=True)
def setup_indexer():
    """Initialize the indexer before running tests"""
    import api.app as app_module
    from src.indexer import HybridIndexer
    
    if app_module.indexer is None:
        print("\n🔧 Initializing indexer for tests...")
        try:
            app_module.indexer = HybridIndexer()
            print("✅ Indexer initialized successfully")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize indexer: {e}")
    
    yield
    print("\n🧹 Test cleanup complete")


@pytest.fixture(scope="session")
def indexer_available():
    """Check if indexer is loaded"""
    from api.app import indexer
    return indexer is not None


class TestBasicEndpoints:
    """Test basic API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["status"] == "online"
        assert "endpoints" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "indexer_loaded" in data
        assert "api_version" in data


class TestAuthentication:
    """Test API authentication"""
    
    def test_search_without_api_key(self):
        """Test that search fails without API key"""
        response = client.post("/search", json={"query": "test query"})
        assert response.status_code == 422  # Missing header
    
    def test_search_with_invalid_api_key(self):
        """Test that search fails with invalid API key"""
        response = client.post(
            "/search",
            json={"query": "test query"},
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 403
    
    def test_stats_requires_authentication(self):
        """Test that stats endpoint requires authentication"""
        response = client.get("/stats")
        assert response.status_code == 422  # Missing header


class TestSearchEndpoint:
    """Test search functionality"""
    
    def test_search_with_valid_query(self, indexer_available):
        """Test search with valid query and API key"""
        if not indexer_available:
            pytest.skip("Indexer not loaded")
        
        response = client.post(
            "/search",
            json={"query": "calculate taxes"},
            headers=HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "query" in data
        assert "response_time_ms" in data
        assert data["query"] == "calculate taxes"
    
    def test_search_with_top_k(self, indexer_available):
        """Test search with custom top_k parameter"""
        if not indexer_available:
            pytest.skip("Indexer not loaded")
        
        response = client.post(
            "/search",
            json={"query": "payment processing", "top_k": 5},
            headers=HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
    
    def test_search_empty_query(self):
        """Test that empty query is handled"""
        response = client.post(
            "/search",
            json={"query": ""},
            headers=HEADERS
        )
        assert response.status_code in [200, 422]


class TestMetricsEndpoints:
    """Test metrics and statistics endpoints"""
    
    def test_get_stats(self):
        """Test getting statistics"""
        response = client.get("/stats", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "total_queries" in data
        assert "success_rate" in data
        assert "avg_response_time_ms" in data
    
    def test_get_recent_queries(self):
        """Test getting recent queries"""
        response = client.get("/recent-queries", headers=HEADERS)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_recent_queries_with_limit(self):
        """Test recent queries with custom limit"""
        response = client.get("/recent-queries?limit=5", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5


class TestRateLimiting:
    """Test rate limiting behavior"""
    
    def test_rate_limit_not_exceeded_normal_use(self, indexer_available):
        """Test that normal usage doesn't trigger rate limits"""
        if not indexer_available:
            pytest.skip("Indexer not loaded")
        
        for i in range(3):
            response = client.post(
                "/search",
                json={"query": f"test query {i}"},
                headers=HEADERS
            )
            assert response.status_code == 200
            time.sleep(0.3)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
