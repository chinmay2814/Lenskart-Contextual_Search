"""
Product SQLAlchemy model
"""
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.db.database import Base
import uuid


class Product(Base):
    """Product model for eyewear catalog"""
    
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Core fields
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, index=True)
    
    # Eyewear-specific attributes
    brand = Column(String(100), nullable=True, index=True)
    frame_type = Column(String(50), nullable=True)  # aviator, wayfarer, round, etc.
    frame_material = Column(String(50), nullable=True)  # metal, plastic, titanium
    lens_type = Column(String(50), nullable=True)  # polarized, photochromic, blue-light
    color = Column(String(50), nullable=True)
    gender = Column(String(20), nullable=True)  # men, women, unisex
    
    # Pricing and rating
    price = Column(Float, nullable=False, index=True)
    original_price = Column(Float, nullable=True)  # For discount calculation
    rating = Column(Float, nullable=True, default=0.0)
    review_count = Column(Integer, nullable=True, default=0)
    
    # Additional attributes as JSON
    attributes = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(id={self.id}, title={self.title}, price={self.price})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "brand": self.brand,
            "frame_type": self.frame_type,
            "frame_material": self.frame_material,
            "lens_type": self.lens_type,
            "color": self.color,
            "gender": self.gender,
            "price": self.price,
            "original_price": self.original_price,
            "rating": self.rating,
            "review_count": self.review_count,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def get_searchable_text(self) -> str:
        """Generate text for embedding"""
        parts = [
            self.title or "",
            self.description or "",
            self.category or "",
            self.brand or "",
            self.frame_type or "",
            self.lens_type or "",
            self.color or "",
            self.gender or "",
        ]
        # Add attributes if present
        if self.attributes:
            for key, value in self.attributes.items():
                if isinstance(value, str):
                    parts.append(value)
                elif isinstance(value, list):
                    parts.extend([str(v) for v in value])
        
        return " ".join(filter(None, parts))

