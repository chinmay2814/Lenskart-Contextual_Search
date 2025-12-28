"""
Learning service for behavioral learning from user events
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models.event import Event, BehaviorScore
from app.models.product import Product


class LearningService:
    """
    Service for learning from user behavior and updating product rankings.
    
    Implements the behavioral scoring formula:
    behavior_score = (
        click_rate * 0.3 +
        cart_rate * 0.3 +
        conversion_rate * 0.3 +
        normalized_dwell_time * 0.1
    ) - (bounce_rate * 0.2)
    """
    
    # Dwell time threshold for bounce (seconds)
    BOUNCE_THRESHOLD = 5.0
    
    def get_behavior_score(self, db: Session, product_id: str) -> float:
        """Get the behavior score for a product"""
        score = db.query(BehaviorScore).filter(
            BehaviorScore.product_id == product_id
        ).first()
        
        if score:
            return score.behavior_score
        return 0.0
    
    def get_behavior_scores_batch(
        self, 
        db: Session, 
        product_ids: List[str]
    ) -> Dict[str, float]:
        """Get behavior scores for multiple products"""
        scores = db.query(BehaviorScore).filter(
            BehaviorScore.product_id.in_(product_ids)
        ).all()
        
        return {s.product_id: s.behavior_score for s in scores}
    
    def record_impression(self, db: Session, product_id: str):
        """Record that a product was shown in search results"""
        score = self._get_or_create_score(db, product_id)
        score.impression_count += 1
        score.update_rates()
        db.commit()
    
    def record_impressions_batch(self, db: Session, product_ids: List[str]):
        """Record impressions for multiple products"""
        for product_id in product_ids:
            score = self._get_or_create_score(db, product_id)
            score.impression_count += 1
            score.update_rates()
        db.commit()
    
    def process_event(self, db: Session, event: Event):
        """
        Process a user event and update behavior scores.
        
        This is called by the event processor worker.
        """
        if not event.product_id:
            return
        
        score = self._get_or_create_score(db, event.product_id)
        
        if event.event_type == "click":
            score.click_count += 1
            
        elif event.event_type == "add_to_cart":
            score.cart_count += 1
            
        elif event.event_type == "purchase":
            score.purchase_count += 1
            
        elif event.event_type == "dwell_time":
            if event.dwell_time_seconds:
                score.total_dwell_time += event.dwell_time_seconds
                
                # Check for bounce
                if event.dwell_time_seconds < self.BOUNCE_THRESHOLD:
                    # Increment bounce count (stored in a derived way)
                    pass
        
        # Recalculate rates and score
        score.update_rates()
        db.commit()
    
    def recalculate_all_scores(self, db: Session):
        """
        Recalculate all behavior scores from raw event data.
        Useful for batch recalculation or fixing inconsistencies.
        """
        # Get all products
        products = db.query(Product).all()
        
        for product in products:
            score = self._get_or_create_score(db, product.id)
            
            # Count events
            score.impression_count = db.query(func.count(Event.id)).filter(
                Event.product_id == product.id,
                Event.event_type == "search"
            ).scalar() or 0
            
            score.click_count = db.query(func.count(Event.id)).filter(
                Event.product_id == product.id,
                Event.event_type == "click"
            ).scalar() or 0
            
            score.cart_count = db.query(func.count(Event.id)).filter(
                Event.product_id == product.id,
                Event.event_type == "add_to_cart"
            ).scalar() or 0
            
            score.purchase_count = db.query(func.count(Event.id)).filter(
                Event.product_id == product.id,
                Event.event_type == "purchase"
            ).scalar() or 0
            
            # Sum dwell time
            total_dwell = db.query(func.sum(Event.dwell_time_seconds)).filter(
                Event.product_id == product.id,
                Event.event_type == "dwell_time"
            ).scalar() or 0.0
            score.total_dwell_time = total_dwell
            
            # Calculate bounce rate
            low_dwell_count = db.query(func.count(Event.id)).filter(
                Event.product_id == product.id,
                Event.event_type == "dwell_time",
                Event.dwell_time_seconds < self.BOUNCE_THRESHOLD
            ).scalar() or 0
            
            dwell_events = db.query(func.count(Event.id)).filter(
                Event.product_id == product.id,
                Event.event_type == "dwell_time"
            ).scalar() or 0
            
            if dwell_events > 0:
                score.bounce_rate = low_dwell_count / dwell_events
            
            score.update_rates()
        
        db.commit()
        print(f"[+] Recalculated behavior scores for {len(products)} products")
    
    def get_top_products(
        self, 
        db: Session, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top products by behavior score"""
        scores = db.query(BehaviorScore).order_by(
            BehaviorScore.behavior_score.desc()
        ).limit(limit).all()
        
        results = []
        for score in scores:
            product = db.query(Product).filter(
                Product.id == score.product_id
            ).first()
            
            if product:
                results.append({
                    "product_id": product.id,
                    "title": product.title,
                    "impression_count": score.impression_count,
                    "click_count": score.click_count,
                    "cart_count": score.cart_count,
                    "purchase_count": score.purchase_count,
                    "click_rate": score.click_rate,
                    "conversion_rate": score.conversion_rate,
                    "behavior_score": score.behavior_score,
                })
        
        return results
    
    def get_analytics_summary(self, db: Session) -> Dict[str, Any]:
        """Get analytics summary"""
        # Total counts
        total_products = db.query(func.count(Product.id)).scalar() or 0
        total_events = db.query(func.count(Event.id)).scalar() or 0
        
        # Event counts by type
        event_counts = {}
        for event_type in ["search", "click", "add_to_cart", "purchase", "dwell_time"]:
            count = db.query(func.count(Event.id)).filter(
                Event.event_type == event_type
            ).scalar() or 0
            event_counts[event_type] = count
        
        # Top products
        top_products = self.get_top_products(db, limit=10)
        
        # Recent queries
        recent_queries = db.query(
            Event.query,
            func.count(Event.id).label("count")
        ).filter(
            Event.event_type == "search",
            Event.query.isnot(None)
        ).group_by(Event.query).order_by(
            func.count(Event.id).desc()
        ).limit(10).all()
        
        return {
            "total_products": total_products,
            "total_events": total_events,
            "event_counts": event_counts,
            "top_products": top_products,
            "recent_queries": [
                {"query": q, "count": c} for q, c in recent_queries
            ],
        }
    
    def _get_or_create_score(self, db: Session, product_id: str) -> BehaviorScore:
        """Get or create a behavior score record"""
        score = db.query(BehaviorScore).filter(
            BehaviorScore.product_id == product_id
        ).first()
        
        if not score:
            score = BehaviorScore(product_id=product_id)
            db.add(score)
            db.flush()
        
        return score


# Singleton instance
_learning_service: Optional[LearningService] = None


def get_learning_service() -> LearningService:
    """Get or create LearningService singleton"""
    global _learning_service
    if _learning_service is None:
        _learning_service = LearningService()
    return _learning_service

