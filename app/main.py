"""
Lenskart AI-Powered Contextual Search Platform
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.db.database import init_db
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

