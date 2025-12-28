"""
API Routes
"""
from app.api.routes.products import router as products_router
from app.api.routes.search import router as search_router
from app.api.routes.events import router as events_router
from app.api.routes.analytics import router as analytics_router

__all__ = [
    "products_router",
    "search_router",
    "events_router",
    "analytics_router",
]

