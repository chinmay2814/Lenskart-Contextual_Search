"""
Analytics API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.api.dependencies import get_db_session
from app.services.learning_service import get_learning_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get analytics summary including:
    - Total products and events
    - Event counts by type
    - Top products by behavior score
    - Recent search queries
    """
    learning_service = get_learning_service()
    return learning_service.get_analytics_summary(db)


@router.get("/top-products")
def get_top_products(
    limit: int = 10,
    db: Session = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Get top products ranked by behavior score.
    
    These are products that have:
    - High click rates
    - High add-to-cart rates
    - High conversion rates
    - Good dwell time
    """
    learning_service = get_learning_service()
    return learning_service.get_top_products(db, limit)


@router.post("/recalculate-scores")
def recalculate_behavior_scores(
    db: Session = Depends(get_db_session)
) -> Dict[str, str]:
    """
    Recalculate all behavior scores from raw event data.
    
    Useful for:
    - Fixing inconsistencies
    - After bulk event imports
    - Periodic maintenance
    """
    learning_service = get_learning_service()
    learning_service.recalculate_all_scores(db)
    
    return {"status": "success", "message": "All behavior scores recalculated"}


@router.get("/product/{product_id}/behavior")
def get_product_behavior(
    product_id: str,
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get detailed behavior metrics for a specific product.
    """
    from app.models.event import BehaviorScore
    from app.models.product import Product
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    
    score = db.query(BehaviorScore).filter(
        BehaviorScore.product_id == product_id
    ).first()
    
    if not score:
        return {
            "product_id": product_id,
            "title": product.title,
            "message": "No behavior data yet"
        }
    
    return {
        "product_id": product_id,
        "title": product.title,
        "metrics": {
            "impression_count": score.impression_count,
            "click_count": score.click_count,
            "cart_count": score.cart_count,
            "purchase_count": score.purchase_count,
            "total_dwell_time": score.total_dwell_time,
        },
        "rates": {
            "click_rate": score.click_rate,
            "cart_rate": score.cart_rate,
            "conversion_rate": score.conversion_rate,
            "avg_dwell_time": score.avg_dwell_time,
            "bounce_rate": score.bounce_rate,
        },
        "behavior_score": score.behavior_score,
    }

