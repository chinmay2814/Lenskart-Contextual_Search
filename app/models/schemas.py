"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============== Product Schemas ==============

class ProductCreate(BaseModel):
    """Schema for creating a product"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=100)
    brand: Optional[str] = None
    frame_type: Optional[str] = None
    frame_material: Optional[str] = None
    lens_type: Optional[str] = None
    color: Optional[str] = None
    gender: Optional[str] = None
    price: float = Field(..., gt=0)
    original_price: Optional[float] = None
    rating: Optional[float] = Field(default=0.0, ge=0, le=5)
    review_count: Optional[int] = Field(default=0, ge=0)
    attributes: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Ray-Ban Aviator Classic",
                "description": "Iconic aviator sunglasses with gold frame and green lenses",
                "category": "sunglasses",
                "brand": "Ray-Ban",
                "frame_type": "aviator",
                "frame_material": "metal",
                "lens_type": "polarized",
                "color": "gold",
                "gender": "unisex",
                "price": 4999.0,
                "original_price": 6999.0,
                "rating": 4.5,
                "review_count": 1250,
                "attributes": {
                    "uv_protection": "100%",
                    "lens_color": "green"
                }
            }
        }


class ProductResponse(BaseModel):
    """Schema for product response"""
    id: str
    title: str
    description: Optional[str]
    category: str
    brand: Optional[str]
    frame_type: Optional[str]
    frame_material: Optional[str]
    lens_type: Optional[str]
    color: Optional[str]
    gender: Optional[str]
    price: float
    original_price: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    attributes: Optional[Dict[str, Any]]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ProductBatchCreate(BaseModel):
    """Schema for batch product creation"""
    products: List[ProductCreate]


# ============== Search Schemas ==============

class SearchQuery(BaseModel):
    """Schema for search request"""
    query: str = Field(..., min_length=1, max_length=500)
    
    # Filters
    min_price: Optional[float] = Field(default=None, ge=0)
    max_price: Optional[float] = Field(default=None, ge=0)
    category: Optional[str] = None
    brand: Optional[str] = None
    frame_type: Optional[str] = None
    lens_type: Optional[str] = None
    gender: Optional[str] = None
    min_rating: Optional[float] = Field(default=None, ge=0, le=5)
    
    # Pagination
    top_k: Optional[int] = Field(default=10, ge=1, le=100)
    
    # AI features
    enable_query_expansion: bool = True
    enable_explanations: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "stylish sunglasses for men under 5000",
                "min_price": 1000,
                "max_price": 5000,
                "gender": "men",
                "top_k": 10,
                "enable_query_expansion": True,
                "enable_explanations": True
            }
        }


class SearchResult(BaseModel):
    """Schema for a single search result"""
    product: ProductResponse
    semantic_score: float = Field(..., ge=0, le=1)
    behavior_score: float = Field(default=0.0, ge=0, le=1)
    final_score: float = Field(..., ge=0, le=1)
    explanation: Optional[str] = None
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Schema for search response"""
    query: str
    expanded_query: Optional[str] = None
    total_results: int
    results: List[SearchResult]
    search_time_ms: float
    filters_applied: Dict[str, Any]


# ============== Event Schemas ==============

class EventTypeEnum(str, Enum):
    """Event types"""
    SEARCH = "search"
    CLICK = "click"
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"
    DWELL_TIME = "dwell_time"


class EventCreate(BaseModel):
    """Schema for creating an event"""
    event_type: EventTypeEnum
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    product_id: Optional[str] = None
    query: Optional[str] = None
    dwell_time_seconds: Optional[float] = Field(default=None, ge=0)
    position: Optional[int] = Field(default=None, ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "click",
                "user_id": "user_123",
                "session_id": "session_456",
                "product_id": "prod_789",
                "query": "aviator sunglasses",
                "position": 2
            }
        }


class EventResponse(BaseModel):
    """Schema for event response"""
    id: str
    event_type: str
    user_id: Optional[str]
    session_id: Optional[str]
    product_id: Optional[str]
    query: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== Analytics Schemas ==============

class ProductAnalytics(BaseModel):
    """Analytics for a single product"""
    product_id: str
    title: str
    impression_count: int
    click_count: int
    cart_count: int
    purchase_count: int
    click_rate: float
    conversion_rate: float
    behavior_score: float


class QueryAnalytics(BaseModel):
    """Analytics for search queries"""
    query: str
    search_count: int
    avg_results_clicked: float
    top_clicked_products: List[str]


class AnalyticsResponse(BaseModel):
    """Schema for analytics response"""
    total_products: int
    total_events: int
    top_products: List[ProductAnalytics]
    recent_queries: List[QueryAnalytics]
    event_counts: Dict[str, int]

