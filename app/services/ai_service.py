"""
AI Service using Groq LLM for query expansion and result explanations
"""
from groq import Groq
from typing import List, Dict, Any, Optional
import json
import re

from app.config import get_settings

settings = get_settings()


class AIService:
    """
    Service for AI-powered features using Groq LLM.
    
    Features:
    - Query expansion: Expand search queries with related terms
    - Result explanation: Explain why a product was shown for a query
    """
    
    def __init__(self):
        if not settings.groq_api_key or settings.groq_api_key == "your_groq_api_key_here":
            print("[!] Warning: GROQ_API_KEY not set. AI features will be disabled.")
            self.client = None
        else:
            self.client = Groq(api_key=settings.groq_api_key)
            print(f"[+] Groq AI service initialized with model: {settings.llm_model}")
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.client is not None
    
    async def expand_query(self, query: str) -> str:
        """
        Expand a search query with related terms using LLM.
        
        Example:
        Input: "sunglasses"
        Output: "sunglasses shades UV protection eyewear polarized glasses sun glasses"
        """
        if not self.is_available():
            return query
        
        try:
            prompt = f"""You are a search query expansion assistant for an eyewear e-commerce store (like Lenskart).
Given a user's search query, expand it with related terms, synonyms, and relevant attributes.
Focus on eyewear-specific terms: frame types, lens types, brands, styles, etc.

User Query: "{query}"

Return ONLY the expanded query as a single line of space-separated terms. Do not include explanations or formatting.
Include the original query terms and add 5-10 related terms.

Expanded Query:"""

            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3,
            )
            
            expanded = response.choices[0].message.content.strip()
            # Clean up any quotes or extra formatting
            expanded = expanded.replace('"', '').replace("'", "")
            
            return expanded
            
        except Exception as e:
            print(f"[!] Query expansion failed: {e}")
            return query
    
    async def explain_result(
        self,
        query: str,
        product: Dict[str, Any],
        semantic_score: float,
        behavior_score: float
    ) -> str:
        """
        Generate an explanation for why a product was shown for a query.
        
        Example:
        "Shown because: matches 'aviator style', high customer rating (4.5), 
        frequently purchased with similar searches"
        """
        if not self.is_available():
            return self._generate_fallback_explanation(query, product, semantic_score, behavior_score)
        
        try:
            prompt = f"""You are an AI assistant explaining search results for an eyewear store.
Generate a brief, helpful explanation (1-2 sentences) for why this product matches the user's search.

User Search: "{query}"

Product:
- Title: {product.get('title', 'N/A')}
- Category: {product.get('category', 'N/A')}
- Brand: {product.get('brand', 'N/A')}
- Frame Type: {product.get('frame_type', 'N/A')}
- Lens Type: {product.get('lens_type', 'N/A')}
- Price: ₹{product.get('price', 0)}
- Rating: {product.get('rating', 0)}/5 ({product.get('review_count', 0)} reviews)

Match Quality:
- Semantic similarity: {semantic_score:.0%}
- Popularity score: {behavior_score:.0%}

Generate a concise explanation starting with "Shown because:". Focus on why this product matches the search intent."""

            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.5,
            )
            
            explanation = response.choices[0].message.content.strip()
            
            # Ensure it starts with "Shown because:"
            if not explanation.lower().startswith("shown because"):
                explanation = "Shown because: " + explanation
            
            return explanation
            
        except Exception as e:
            print(f"[!] Explanation generation failed: {e}")
            return self._generate_fallback_explanation(query, product, semantic_score, behavior_score)
    
    def _generate_fallback_explanation(
        self,
        query: str,
        product: Dict[str, Any],
        semantic_score: float,
        behavior_score: float
    ) -> str:
        """Generate a simple explanation without LLM"""
        reasons = []
        
        # Check for keyword matches
        query_lower = query.lower()
        title_lower = product.get('title', '').lower()
        
        if any(word in title_lower for word in query_lower.split()):
            reasons.append("matches your search terms")
        
        # Rating
        rating = product.get('rating', 0)
        if rating >= 4.0:
            reasons.append(f"highly rated ({rating}/5)")
        
        # Semantic score
        if semantic_score > 0.7:
            reasons.append("strong semantic match")
        elif semantic_score > 0.5:
            reasons.append("good relevance to your query")
        
        # Behavior score
        if behavior_score > 0.5:
            reasons.append("popular with similar searches")
        
        if not reasons:
            reasons.append("relevant to your search")
        
        return "Shown because: " + ", ".join(reasons)
    
    async def extract_attributes(self, description: str) -> Dict[str, Any]:
        """
        Extract structured attributes from a product description using LLM.
        
        This is useful for enriching product data during ingestion.
        """
        if not self.is_available():
            return {}
        
        try:
            prompt = f"""Extract eyewear attributes from this product description.
Return a JSON object with these fields (use null if not found):
- frame_material: string (metal, plastic, titanium, acetate, etc.)
- lens_material: string (glass, polycarbonate, CR-39, etc.)
- uv_protection: string (100%, UV400, etc.)
- face_shape: list of strings (round, oval, square, etc.)
- features: list of strings (anti-glare, scratch-resistant, etc.)

Description: "{description}"

JSON:"""

            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return {}
            
        except Exception as e:
            print(f"[!] Attribute extraction failed: {e}")
            return {}


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create AIService singleton"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service

