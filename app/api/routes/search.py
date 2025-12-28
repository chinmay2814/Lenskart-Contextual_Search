"""
Search API endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.api.dependencies import get_db_session
from app.models.schemas import SearchQuery, SearchResponse
from app.services.search_service import get_search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/", response_model=SearchResponse)
async def search(
    query: SearchQuery,
    db: Session = Depends(get_db_session)
):
    """
    Perform contextual search with AI features.
    
    Features:
    - **Query Expansion**: Automatically expands your query with related terms
    - **Semantic Search**: Finds products by meaning, not just keywords
    - **Behavioral Ranking**: Boosts popular products based on user behavior
    - **AI Explanations**: Explains why each product was shown
    
    Example queries:
    - "stylish sunglasses for men under 5000"
    - "blue light blocking glasses for computer"
    - "polarized aviator sunglasses"
    """
    search_service = get_search_service()
    return await search_service.search(db, query)


@router.get("/quick")
async def quick_search(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    top_k: int = Query(default=10, ge=1, le=100, description="Number of results"),
    db: Session = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Quick search without AI features.
    
    Faster than the full search endpoint, useful for:
    - Autocomplete suggestions
    - Quick lookups
    - When AI features are not needed
    """
    search_service = get_search_service()
    return await search_service.search_simple(db, q, top_k)


@router.get("/similar/{product_id}")
def get_similar_products(
    product_id: str,
    top_k: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Find products similar to a given product.
    
    Useful for:
    - "You might also like" recommendations
    - Product detail page suggestions
    - Cross-selling
    """
    search_service = get_search_service()
    return search_service.get_similar_products(db, product_id, top_k)


@router.post("/with-filters", response_model=SearchResponse)
async def search_with_filters(
    q: str = Query(..., min_length=1, description="Search query"),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    frame_type: Optional[str] = None,
    lens_type: Optional[str] = None,
    gender: Optional[str] = None,
    min_rating: Optional[float] = Query(default=None, ge=0, le=5),
    top_k: int = Query(default=10, ge=1, le=100),
    enable_query_expansion: bool = True,
    enable_explanations: bool = True,
    db: Session = Depends(get_db_session)
):
    """
    Search with filters as query parameters.
    
    Alternative to POST /search for simpler integration.
    """
    query = SearchQuery(
        query=q,
        min_price=min_price,
        max_price=max_price,
        category=category,
        brand=brand,
        frame_type=frame_type,
        lens_type=lens_type,
        gender=gender,
        min_rating=min_rating,
        top_k=top_k,
        enable_query_expansion=enable_query_expansion,
        enable_explanations=enable_explanations,
    )
    
    search_service = get_search_service()
    return await search_service.search(db, query)

