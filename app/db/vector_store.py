"""
ChromaDB vector store for semantic search
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional, Tuple
import os

from app.config import get_settings

settings = get_settings()


class VectorStore:
    """
    ChromaDB wrapper for vector storage and similarity search.
    Runs in embedded mode - no external service required.
    """
    
    COLLECTION_NAME = "products"
    
    def __init__(self):
        # Ensure directory exists
        os.makedirs(settings.chroma_db_path, exist_ok=True)
        
        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        print(f"[+] ChromaDB initialized at {settings.chroma_db_path}")
    
    def add_product(
        self,
        product_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        document: str
    ):
        """Add a single product to the vector store"""
        # Filter out None values from metadata
        clean_metadata = {k: v for k, v in metadata.items() if v is not None}
        
        self.collection.upsert(
            ids=[product_id],
            embeddings=[embedding],
            metadatas=[clean_metadata],
            documents=[document]
        )
    
    def add_products_batch(
        self,
        product_ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: List[str]
    ):
        """Add multiple products in batch"""
        # Clean metadata
        clean_metadatas = [
            {k: v for k, v in m.items() if v is not None}
            for m in metadatas
        ]
        
        self.collection.upsert(
            ids=product_ids,
            embeddings=embeddings,
            metadatas=clean_metadatas,
            documents=documents
        )
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[float], List[Dict[str, Any]]]:
        """
        Search for similar products.
        
        Returns:
            Tuple of (product_ids, distances, metadatas)
        """
        # Build where clause for filtering
        where_clause = None
        if filters:
            conditions = []
            
            # Category filter
            if filters.get("category"):
                conditions.append({"category": {"$eq": filters["category"]}})
            
            # Brand filter
            if filters.get("brand"):
                conditions.append({"brand": {"$eq": filters["brand"]}})
            
            # Frame type filter
            if filters.get("frame_type"):
                conditions.append({"frame_type": {"$eq": filters["frame_type"]}})
            
            # Lens type filter
            if filters.get("lens_type"):
                conditions.append({"lens_type": {"$eq": filters["lens_type"]}})
            
            # Gender filter
            if filters.get("gender"):
                conditions.append({"gender": {"$eq": filters["gender"]}})
            
            # Price range filters
            if filters.get("min_price") is not None:
                conditions.append({"price": {"$gte": filters["min_price"]}})
            
            if filters.get("max_price") is not None:
                conditions.append({"price": {"$lte": filters["max_price"]}})
            
            # Rating filter
            if filters.get("min_rating") is not None:
                conditions.append({"rating": {"$gte": filters["min_rating"]}})
            
            if len(conditions) == 1:
                where_clause = conditions[0]
            elif len(conditions) > 1:
                where_clause = {"$and": conditions}
        
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["distances", "metadatas", "documents"]
        )
        
        # Extract results
        ids = results["ids"][0] if results["ids"] else []
        distances = results["distances"][0] if results["distances"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        
        # Convert distances to similarity scores (1 - distance for cosine)
        similarities = [1 - d for d in distances]
        
        return ids, similarities, metadatas
    
    def delete_product(self, product_id: str):
        """Delete a product from the vector store"""
        self.collection.delete(ids=[product_id])
    
    def get_count(self) -> int:
        """Get total number of products in the store"""
        return self.collection.count()
    
    def reset(self):
        """Reset the collection (delete all data)"""
        self.client.delete_collection(self.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create VectorStore singleton"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

