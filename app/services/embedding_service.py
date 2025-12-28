"""
Embedding service using Sentence Transformers
"""
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import numpy as np

from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    """
    Service for generating text embeddings using Sentence Transformers.
    Uses all-MiniLM-L6-v2 model - fast and effective for semantic search.
    """
    
    def __init__(self):
        print(f"[*] Loading embedding model: {settings.embedding_model}...")
        self.model = SentenceTransformer(settings.embedding_model)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"[+] Embedding model loaded (dim={self.embedding_dim})")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batch processing)"""
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create EmbeddingService singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

