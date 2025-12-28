"""
Tests for product ingestion
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_create_product():
    """Test creating a single product"""
    product_data = {
        "title": "Test Sunglasses",
        "description": "A test product for unit testing",
        "category": "sunglasses",
        "brand": "TestBrand",
        "frame_type": "aviator",
        "price": 1999.0,
        "rating": 4.5,
    }
    
    response = client.post("/products/", json=product_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["title"] == product_data["title"]
    assert data["category"] == product_data["category"]
    assert data["price"] == product_data["price"]
    assert "id" in data


def test_list_products():
    """Test listing products"""
    response = client.get("/products/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_get_product_count():
    """Test getting product count"""
    response = client.get("/products/count/total")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_products" in data


def test_create_batch_products():
    """Test batch product creation"""
    products = {
        "products": [
            {
                "title": "Batch Product 1",
                "category": "eyeglasses",
                "price": 999.0,
            },
            {
                "title": "Batch Product 2",
                "category": "sunglasses",
                "price": 1499.0,
            },
        ]
    }
    
    response = client.post("/products/batch", json=products)
    assert response.status_code == 201
    
    data = response.json()
    assert len(data) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

