"""
Ranking service for combining semantic and behavioral scores
"""
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.config import get_settings
from app.services.learning_service import get_learning_service

settings = get_settings()


class RankingService:
    """
    Service for ranking search results.
    
    Combines semantic similarity scores with behavioral scores:
    final_score = (semantic_score * SEMANTIC_WEIGHT) + (behavior_score * BEHAVIOR_WEIGHT)
    """
    
    def __init__(self):
        self.learning_service = get_learning_service()
        self.semantic_weight = settings.semantic_weight
        self.behavior_weight = settings.behavior_weight
    
    def rank_results(
        self,
        db: Session,
        product_ids: List[str],
        semantic_scores: List[float]
    ) -> List[Tuple[str, float, float, float]]:
        """
        Rank products by combining semantic and behavioral scores.
        
        Args:
            db: Database session
            product_ids: List of product IDs
            semantic_scores: List of semantic similarity scores (0-1)
        
        Returns:
            List of tuples: (product_id, semantic_score, behavior_score, final_score)
            Sorted by final_score descending
        """
        # Get behavior scores for all products
        behavior_scores = self.learning_service.get_behavior_scores_batch(db, product_ids)
        
        # Calculate final scores
        results = []
        for product_id, semantic_score in zip(product_ids, semantic_scores):
            behavior_score = behavior_scores.get(product_id, 0.0)
            
            final_score = (
                semantic_score * self.semantic_weight +
                behavior_score * self.behavior_weight
            )
            
            results.append((product_id, semantic_score, behavior_score, final_score))
        
        # Sort by final score descending
        results.sort(key=lambda x: x[3], reverse=True)
        
        return results
    
    def apply_boost(
        self,
        results: List[Tuple[str, float, float, float]],
        boost_product_ids: List[str],
        boost_factor: float = 1.2
    ) -> List[Tuple[str, float, float, float]]:
        """
        Apply a boost to specific products.
        
        Useful for promotions or featured products.
        """
        boosted = []
        for product_id, semantic, behavior, final in results:
            if product_id in boost_product_ids:
                final *= boost_factor
            boosted.append((product_id, semantic, behavior, final))
        
        # Re-sort
        boosted.sort(key=lambda x: x[3], reverse=True)
        
        return boosted
    
    def apply_penalty(
        self,
        results: List[Tuple[str, float, float, float]],
        penalty_product_ids: List[str],
        penalty_factor: float = 0.8
    ) -> List[Tuple[str, float, float, float]]:
        """
        Apply a penalty to specific products.
        
        Useful for products with issues or low quality.
        """
        penalized = []
        for product_id, semantic, behavior, final in results:
            if product_id in penalty_product_ids:
                final *= penalty_factor
            penalized.append((product_id, semantic, behavior, final))
        
        # Re-sort
        penalized.sort(key=lambda x: x[3], reverse=True)
        
        return penalized


# Singleton instance
_ranking_service = None


def get_ranking_service() -> RankingService:
    """Get or create RankingService singleton"""
    global _ranking_service
    if _ranking_service is None:
        _ranking_service = RankingService()
    return _ranking_service

