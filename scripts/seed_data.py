"""
Script to seed the database with sample eyewear data
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import init_db, get_db_context
from app.services.ingestion_service import get_ingestion_service
from app.models.schemas import ProductCreate


def seed_data():
    """Seed the database with sample products"""
    print("[*] Starting data seeding...")
    
    # Initialize database
    init_db()
    
    # Load sample data
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "sample_eyewear.json"
    )
    
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    products_data = data.get("products", data)
    print(f"[*] Found {len(products_data)} products to seed")
    
    # Get ingestion service
    ingestion_service = get_ingestion_service()
    
    # Ingest products
    with get_db_context() as db:
        products = [ProductCreate(**p) for p in products_data]
        created = ingestion_service.ingest_products_batch(db, products)
        print(f"[+] Successfully seeded {len(created)} products")
    
    print("[+] Data seeding complete!")


if __name__ == "__main__":
    seed_data()

