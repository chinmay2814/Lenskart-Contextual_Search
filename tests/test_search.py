"""
Tests for search functionality
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_quick_search():
    """Test quick search endpoint"""
    response = client.get("/search/quick?q=sunglasses")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_full_search():
    """Test full search with AI features"""
    search_query = {
        "query": "aviator sunglasses for men",
        "top_k": 5,
        "enable_query_expansion": False,  # Disable for faster testing
        "enable_explanations": False,
    }
    
    response = client.post("/search/", json=search_query)
    assert response.status_code == 200
    
    data = response.json()
    assert "query" in data
    assert "results" in data
    assert "search_time_ms" in data


def test_search_with_filters():
    """Test search with price filters"""
    search_query = {
        "query": "glasses",
        "min_price": 1000,
        "max_price": 5000,
        "top_k": 5,
        "enable_query_expansion": False,
        "enable_explanations": False,
    }
    
    response = client.post("/search/", json=search_query)
    assert response.status_code == 200
    
    data = response.json()
    assert "filters_applied" in data


def test_search_with_category():
    """Test search with category filter"""
    response = client.post(
        "/search/with-filters",
        params={
            "q": "glasses",
            "category": "sunglasses",
            "top_k": 5,
            "enable_query_expansion": False,
            "enable_explanations": False,
        }
    )
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

