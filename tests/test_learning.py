"""
Tests for behavioral learning
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_track_event():
    """Test event tracking"""
    event = {
        "event_type": "click",
        "user_id": "test_user",
        "session_id": "test_session",
        "product_id": "test_product",
        "query": "test query",
        "position": 1,
    }
    
    response = client.post("/events/", json=event)
    assert response.status_code == 202
    
    data = response.json()
    assert data["status"] == "accepted"


def test_track_batch_events():
    """Test batch event tracking"""
    events = [
        {
            "event_type": "click",
            "user_id": "test_user",
            "product_id": "product_1",
        },
        {
            "event_type": "add_to_cart",
            "user_id": "test_user",
            "product_id": "product_1",
        },
    ]
    
    response = client.post("/events/batch", json=events)
    assert response.status_code == 202


def test_get_event_stats():
    """Test event processor stats"""
    response = client.get("/events/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "is_running" in data
    assert "processed_count" in data


def test_analytics_summary():
    """Test analytics summary"""
    response = client.get("/analytics/summary")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_products" in data
    assert "total_events" in data
    assert "event_counts" in data


def test_top_products():
    """Test top products by behavior score"""
    response = client.get("/analytics/top-products?limit=5")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

