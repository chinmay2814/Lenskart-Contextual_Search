"""
Product ingestion API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List
import json

from app.api.dependencies import get_db_session
from app.models.schemas import (
    ProductCreate,
    ProductResponse,
    ProductBatchCreate,
)
from app.services.ingestion_service import get_ingestion_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create a single product.
    
    The product will be:
    1. Normalized (fields cleaned and standardized)
    2. Stored in SQLite database
    3. Embedded and stored in ChromaDB for semantic search
    4. Initialized with behavior tracking
    """
    ingestion_service = get_ingestion_service()
    created_product = ingestion_service.ingest_product(db, product)
    return ProductResponse.model_validate(created_product)


@router.post("/batch", response_model=List[ProductResponse], status_code=201)
def create_products_batch(
    batch: ProductBatchCreate,
    db: Session = Depends(get_db_session)
):
    """
    Create multiple products in batch.
    
    More efficient than creating products one by one as embeddings
    are generated in batch.
    """
    ingestion_service = get_ingestion_service()
    created_products = ingestion_service.ingest_products_batch(db, batch.products)
    return [ProductResponse.model_validate(p) for p in created_products]


@router.post("/upload/json", response_model=List[ProductResponse], status_code=201)
async def upload_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session)
):
    """
    Upload products from a JSON file.
    
    Expected format:
    ```json
    {
        "products": [
            {"title": "...", "category": "...", "price": 1000, ...},
            ...
        ]
    }
    ```
    
    Or just an array:
    ```json
    [
        {"title": "...", "category": "...", "price": 1000, ...},
        ...
    ]
    ```
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be a JSON file")
    
    try:
        content = await file.read()
        json_data = content.decode('utf-8')
        
        ingestion_service = get_ingestion_service()
        created_products = ingestion_service.ingest_from_json(db, json_data)
        
        return [ProductResponse.model_validate(p) for p in created_products]
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/upload/csv", response_model=List[ProductResponse], status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session)
):
    """
    Upload products from a CSV file.
    
    Required columns: title, category, price
    Optional columns: description, brand, frame_type, frame_material,
                     lens_type, color, gender, original_price, rating,
                     review_count, attributes (as JSON string)
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    try:
        content = await file.read()
        csv_data = content.decode('utf-8')
        
        ingestion_service = get_ingestion_service()
        created_products = ingestion_service.ingest_from_csv(db, csv_data)
        
        return [ProductResponse.model_validate(p) for p in created_products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/", response_model=List[ProductResponse])
def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db_session)
):
    """
    List all products with pagination.
    """
    ingestion_service = get_ingestion_service()
    products = ingestion_service.get_products(db, skip=skip, limit=limit)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get a single product by ID.
    """
    ingestion_service = get_ingestion_service()
    product = ingestion_service.get_product(db, product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Delete a product by ID.
    
    This will also remove the product from the vector store
    and delete associated behavior scores.
    """
    ingestion_service = get_ingestion_service()
    deleted = ingestion_service.delete_product(db, product_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return None


@router.get("/count/total")
def get_product_count(db: Session = Depends(get_db_session)):
    """
    Get total number of products.
    """
    from app.models.product import Product
    from sqlalchemy import func
    
    count = db.query(func.count(Product.id)).scalar()
    return {"total_products": count}

