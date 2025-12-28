"""
Search service orchestrating semantic search, ranking, and AI features
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import time

from app.models.product import Product
from app.models.schemas import SearchQuery, SearchResult, SearchResponse, ProductResponse
from app.db.vector_store import get_vector_store
from app.services.embedding_service import get_embedding_service
from app.services.ranking_service import get_ranking_service
from app.services.learning_service import get_learning_service
from app.services.ai_service import get_ai_service
from app.config import get_settings

settings = get_settings()


class SearchService:
    """
    Main search service that orchestrates:
    1. Query expansion (AI)
    2. Embedding generation
    3. Semantic search
    4. Behavioral ranking
    5. Result explanation (AI)
    """
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.embedding_service = get_embedding_service()
        self.ranking_service = get_ranking_service()
        self.learning_service = get_learning_service()
        self.ai_service = get_ai_service()
    
    async def search(
        self,
        db: Session,
        query: SearchQuery
    ) -> SearchResponse:
        """
        Perform contextual search with all features.
        """
        start_time = time.time()
        
        # 1. Query expansion (optional)
        expanded_query = None
        search_text = query.query
        
        if query.enable_query_expansion and self.ai_service.is_available():
            expanded_query = await self.ai_service.expand_query(query.query)
            search_text = expanded_query
        
        # 2. Generate query embedding
        query_embedding = self.embedding_service.embed_text(search_text)
        
        # 3. Build filters
        filters = {}
        if query.min_price is not None:
            filters["min_price"] = query.min_price
        if query.max_price is not None:
            filters["max_price"] = query.max_price
        if query.category:
            filters["category"] = query.category.lower()
        if query.brand:
            filters["brand"] = query.brand
        if query.frame_type:
            filters["frame_type"] = query.frame_type
        if query.lens_type:
            filters["lens_type"] = query.lens_type
        if query.gender:
            filters["gender"] = query.gender
        if query.min_rating is not None:
            filters["min_rating"] = query.min_rating
        
        # 4. Semantic search
        product_ids, semantic_scores, _ = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=query.top_k * 2,  # Get more for re-ranking
            filters=filters if filters else None
        )
        
        if not product_ids:
            return SearchResponse(
                query=query.query,
                expanded_query=expanded_query,
                total_results=0,
                results=[],
                search_time_ms=(time.time() - start_time) * 1000,
                filters_applied=filters
            )
        
        # 5. Behavioral ranking
        ranked_results = self.ranking_service.rank_results(
            db=db,
            product_ids=product_ids,
            semantic_scores=semantic_scores
        )
        
        # Limit to requested top_k
        ranked_results = ranked_results[:query.top_k]
        
        # 6. Fetch product details
        result_product_ids = [r[0] for r in ranked_results]
        products = db.query(Product).filter(
            Product.id.in_(result_product_ids)
        ).all()
        
        # Create product lookup
        product_lookup = {p.id: p for p in products}
        
        # 7. Record impressions for learning
        self.learning_service.record_impressions_batch(db, result_product_ids)
        
        # 8. Build results with explanations
        results = []
        for product_id, semantic_score, behavior_score, final_score in ranked_results:
            product = product_lookup.get(product_id)
            if not product:
                continue
            
            # Generate explanation (optional)
            explanation = None
            if query.enable_explanations:
                product_dict = product.to_dict()
                explanation = await self.ai_service.explain_result(
                    query=query.query,
                    product=product_dict,
                    semantic_score=semantic_score,
                    behavior_score=behavior_score
                )
            
            results.append(SearchResult(
                product=ProductResponse.model_validate(product),
                semantic_score=semantic_score,
                behavior_score=behavior_score,
                final_score=final_score,
                explanation=explanation
            ))
        
        search_time_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=query.query,
            expanded_query=expanded_query,
            total_results=len(results),
            results=results,
            search_time_ms=search_time_ms,
            filters_applied=filters
        )
    
    async def search_simple(
        self,
        db: Session,
        query_text: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Simple search without AI features.
        Useful for quick searches or when AI is disabled.
        """
        # Generate embedding
        query_embedding = self.embedding_service.embed_text(query_text)
        
        # Search
        product_ids, semantic_scores, _ = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        if not product_ids:
            return []
        
        # Rank
        ranked_results = self.ranking_service.rank_results(
            db=db,
            product_ids=product_ids,
            semantic_scores=semantic_scores
        )
        
        # Fetch products
        result_product_ids = [r[0] for r in ranked_results]
        products = db.query(Product).filter(
            Product.id.in_(result_product_ids)
        ).all()
        
        product_lookup = {p.id: p for p in products}
        
        results = []
        for product_id, semantic_score, behavior_score, final_score in ranked_results:
            product = product_lookup.get(product_id)
            if product:
                results.append({
                    "product": product.to_dict(),
                    "semantic_score": semantic_score,
                    "behavior_score": behavior_score,
                    "final_score": final_score
                })
        
        return results
    
    def get_similar_products(
        self,
        db: Session,
        product_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find products similar to a given product.
        Useful for "You might also like" recommendations.
        """
        # Get the product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return []
        
        # Generate embedding for the product
        searchable_text = product.get_searchable_text()
        product_embedding = self.embedding_service.embed_text(searchable_text)
        
        # Search for similar (exclude the product itself)
        all_ids, all_scores, _ = self.vector_store.search(
            query_embedding=product_embedding,
            top_k=top_k + 1  # +1 to account for the product itself
        )
        
        # Filter out the original product
        filtered = [
            (pid, score) for pid, score in zip(all_ids, all_scores)
            if pid != product_id
        ][:top_k]
        
        if not filtered:
            return []
        
        # Fetch products
        similar_ids = [f[0] for f in filtered]
        products = db.query(Product).filter(
            Product.id.in_(similar_ids)
        ).all()
        
        product_lookup = {p.id: p for p in products}
        
        results = []
        for pid, score in filtered:
            p = product_lookup.get(pid)
            if p:
                results.append({
                    "product": p.to_dict(),
                    "similarity_score": score
                })
        
        return results


# Singleton instance
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """Get or create SearchService singleton"""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service

