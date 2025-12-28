"""
Product ingestion service
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json
import csv
import io

from app.models.product import Product
from app.models.event import BehaviorScore
from app.models.schemas import ProductCreate
from app.db.vector_store import get_vector_store
from app.services.embedding_service import get_embedding_service


class IngestionService:
    """
    Service for ingesting products into the system.
    Handles normalization, embedding generation, and storage.
    """
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.embedding_service = get_embedding_service()
    
    def normalize_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize product fields for consistency.
        """
        normalized = {}
        
        # Required fields
        normalized["title"] = str(product_data.get("title", "")).strip()
        normalized["category"] = str(product_data.get("category", "")).lower().strip()
        normalized["price"] = float(product_data.get("price", 0))
        
        # Optional text fields - normalize to lowercase
        for field in ["description", "brand", "frame_type", "frame_material", 
                      "lens_type", "color", "gender"]:
            value = product_data.get(field)
            if value:
                normalized[field] = str(value).strip()
            else:
                normalized[field] = None
        
        # Numeric fields
        normalized["original_price"] = product_data.get("original_price")
        if normalized["original_price"]:
            normalized["original_price"] = float(normalized["original_price"])
        
        normalized["rating"] = float(product_data.get("rating", 0))
        normalized["review_count"] = int(product_data.get("review_count", 0))
        
        # Attributes (JSON field)
        normalized["attributes"] = product_data.get("attributes", {})
        
        return normalized
    
    def ingest_product(self, db: Session, product_data: ProductCreate) -> Product:
        """
        Ingest a single product.
        
        1. Normalize the data
        2. Create database record
        3. Generate embedding
        4. Store in vector database
        5. Initialize behavior score
        """
        # Normalize
        normalized = self.normalize_product(product_data.model_dump())
        
        # Create product record
        product = Product(**normalized)
        db.add(product)
        db.flush()  # Get the ID
        
        # Generate embedding
        searchable_text = product.get_searchable_text()
        embedding = self.embedding_service.embed_text(searchable_text)
        
        # Prepare metadata for vector store
        metadata = {
            "category": product.category,
            "brand": product.brand,
            "frame_type": product.frame_type,
            "lens_type": product.lens_type,
            "color": product.color,
            "gender": product.gender,
            "price": product.price,
            "rating": product.rating,
        }
        
        # Add to vector store
        self.vector_store.add_product(
            product_id=product.id,
            embedding=embedding,
            metadata=metadata,
            document=searchable_text
        )
        
        # Initialize behavior score
        behavior_score = BehaviorScore(product_id=product.id)
        db.add(behavior_score)
        
        db.commit()
        db.refresh(product)
        
        return product
    
    def ingest_products_batch(
        self, 
        db: Session, 
        products_data: List[ProductCreate]
    ) -> List[Product]:
        """
        Ingest multiple products in batch for efficiency.
        """
        products = []
        embeddings = []
        metadatas = []
        documents = []
        
        # Process all products
        for product_data in products_data:
            normalized = self.normalize_product(product_data.model_dump())
            product = Product(**normalized)
            db.add(product)
            products.append(product)
        
        # Flush to get IDs
        db.flush()
        
        # Generate embeddings in batch
        searchable_texts = [p.get_searchable_text() for p in products]
        embeddings = self.embedding_service.embed_texts(searchable_texts)
        
        # Prepare metadata and add to vector store
        product_ids = []
        for i, product in enumerate(products):
            product_ids.append(product.id)
            metadatas.append({
                "category": product.category,
                "brand": product.brand,
                "frame_type": product.frame_type,
                "lens_type": product.lens_type,
                "color": product.color,
                "gender": product.gender,
                "price": product.price,
                "rating": product.rating,
            })
            documents.append(searchable_texts[i])
            
            # Initialize behavior score
            behavior_score = BehaviorScore(product_id=product.id)
            db.add(behavior_score)
        
        # Batch add to vector store
        self.vector_store.add_products_batch(
            product_ids=product_ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        db.commit()
        
        # Refresh all products
        for product in products:
            db.refresh(product)
        
        return products
    
    def ingest_from_json(self, db: Session, json_data: str) -> List[Product]:
        """Ingest products from JSON string"""
        data = json.loads(json_data)
        
        if isinstance(data, dict) and "products" in data:
            data = data["products"]
        
        products_data = [ProductCreate(**item) for item in data]
        return self.ingest_products_batch(db, products_data)
    
    def ingest_from_csv(self, db: Session, csv_data: str) -> List[Product]:
        """Ingest products from CSV string"""
        reader = csv.DictReader(io.StringIO(csv_data))
        
        products_data = []
        for row in reader:
            # Convert numeric fields
            if "price" in row:
                row["price"] = float(row["price"])
            if "original_price" in row and row["original_price"]:
                row["original_price"] = float(row["original_price"])
            if "rating" in row and row["rating"]:
                row["rating"] = float(row["rating"])
            if "review_count" in row and row["review_count"]:
                row["review_count"] = int(row["review_count"])
            if "attributes" in row and row["attributes"]:
                row["attributes"] = json.loads(row["attributes"])
            
            products_data.append(ProductCreate(**row))
        
        return self.ingest_products_batch(db, products_data)
    
    def get_product(self, db: Session, product_id: str) -> Optional[Product]:
        """Get a product by ID"""
        return db.query(Product).filter(Product.id == product_id).first()
    
    def get_products(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Product]:
        """Get all products with pagination"""
        return db.query(Product).offset(skip).limit(limit).all()
    
    def delete_product(self, db: Session, product_id: str) -> bool:
        """Delete a product"""
        product = self.get_product(db, product_id)
        if not product:
            return False
        
        # Delete from vector store
        self.vector_store.delete_product(product_id)
        
        # Delete behavior score
        db.query(BehaviorScore).filter(BehaviorScore.product_id == product_id).delete()
        
        # Delete product
        db.delete(product)
        db.commit()
        
        return True


# Singleton instance
_ingestion_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    """Get or create IngestionService singleton"""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service

