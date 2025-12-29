"""
Lenskart AI-Powered Contextual Search Platform
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.db.database import init_db, get_db_context
from app.api.routes import (
    products_router,
    search_router,
    events_router,
    analytics_router,
)
from app.workers.event_processor import get_event_processor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


async def auto_seed_if_empty():
    """
    Automatically seed sample data if the database is empty.
    This ensures the deployed app has data to search.
    """
    import json
    import os
    from sqlalchemy import func
    from app.models.product import Product
    from app.models.schemas import ProductCreate
    from app.services.ingestion_service import get_ingestion_service
    
    try:
        with get_db_context() as db:
            # Check if products already exist
            product_count = db.query(func.count(Product.id)).scalar() or 0
            
            if product_count > 0:
                logger.info(f"Database already has {product_count} products. Skipping auto-seed.")
                return
            
            logger.info("Database is empty. Auto-seeding sample data...")
            
            # Find sample data file
            possible_paths = [
                "data/sample_eyewear.json",
                "./data/sample_eyewear.json",
                "/app/data/sample_eyewear.json",  # Railway path
            ]
            
            data_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    data_path = path
                    break
            
            if not data_path:
                logger.warning("Sample data file not found. Skipping auto-seed.")
                return
            
            # Load and seed data
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            products_data = data.get("products", data)
            logger.info(f"Found {len(products_data)} products to seed")
            
            ingestion_service = get_ingestion_service()
            products = [ProductCreate(**p) for p in products_data]
            created = ingestion_service.ingest_products_batch(db, products)
            
            logger.info(f"[+] Auto-seeded {len(created)} products successfully!")
            
    except Exception as e:
        logger.error(f"Auto-seed failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Lenskart Contextual Search Platform...")
    
    # Initialize database
    init_db()
    
    # Start event processor
    event_processor = get_event_processor()
    await event_processor.start()
    
    # Pre-load embedding model (warm-up)
    from app.services.embedding_service import get_embedding_service
    get_embedding_service()
    
    # Auto-seed data if database is empty
    await auto_seed_if_empty()
    
    logger.info("Application started successfully!")
    logger.info(f"API Documentation: http://localhost:8000/docs")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await event_processor.stop()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
## 🔍 AI-Powered Contextual Search Platform for Lenskart

This platform provides intelligent product search with:

### Features
- **Semantic Search**: Understands natural language queries
- **Query Expansion**: AI expands queries with related terms
- **Behavioral Learning**: Rankings improve based on user interactions
- **Explainable Results**: AI explains why products are shown

### Architecture
- **Backend**: FastAPI (Python)
- **Database**: SQLite (structured data)
- **Vector Store**: ChromaDB (embeddings)
- **Embeddings**: Sentence Transformers
- **LLM**: Groq (Llama 3.1)

### Quick Start
1. Add products via `/products` endpoints
2. Search with `/search` endpoint
3. Track events via `/events` endpoints
4. View analytics at `/analytics`
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products_router)
app.include_router(search_router)
app.include_router(events_router)
app.include_router(analytics_router)


@app.get("/", tags=["Health"])
def root():
    """
    Root endpoint - API health check
    """
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Detailed health check
    """
    from app.db.vector_store import get_vector_store
    
    vector_store = get_vector_store()
    event_processor = get_event_processor()
    
    return {
        "status": "healthy",
        "components": {
            "database": "connected",
            "vector_store": {
                "status": "connected",
                "product_count": vector_store.get_count()
            },
            "event_processor": event_processor.get_stats(),
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )

