"""
Event and BehaviorScore SQLAlchemy models
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base
import uuid
import enum


class EventType(str, enum.Enum):
    """Types of user events"""
    SEARCH = "search"
    CLICK = "click"
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"
    DWELL_TIME = "dwell_time"


class Event(Base):
    """User interaction event model"""
    
    __tablename__ = "events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Event details
    event_type = Column(String(20), nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)  # Optional user tracking
    session_id = Column(String(36), nullable=True, index=True)
    
    # Related entities
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True, index=True)
    query = Column(String(500), nullable=True)  # For search events
    
    # Event metadata
    dwell_time_seconds = Column(Float, nullable=True)  # For dwell_time events
    position = Column(Integer, nullable=True)  # Position in search results when clicked
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<Event(id={self.id}, type={self.event_type}, product_id={self.product_id})>"


class BehaviorScore(Base):
    """
    Aggregated behavior scores for products.
    Updated by the learning service based on user events.
    """
    
    __tablename__ = "behavior_scores"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), unique=True, nullable=False, index=True)
    
    # Aggregated metrics
    impression_count = Column(Integer, default=0)  # Times shown in search
    click_count = Column(Integer, default=0)
    cart_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    total_dwell_time = Column(Float, default=0.0)
    
    # Calculated rates (updated by learning service)
    click_rate = Column(Float, default=0.0)  # clicks / impressions
    cart_rate = Column(Float, default=0.0)   # carts / clicks
    conversion_rate = Column(Float, default=0.0)  # purchases / clicks
    avg_dwell_time = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)  # clicks with low dwell time
    
    # Final computed score
    behavior_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<BehaviorScore(product_id={self.product_id}, score={self.behavior_score})>"
    
    def calculate_score(self) -> float:
        """
        Calculate behavior score based on aggregated metrics.
        
        Formula:
        behavior_score = (
            click_rate * 0.3 +
            cart_rate * 0.3 +
            conversion_rate * 0.3 +
            normalized_dwell_time * 0.1
        ) - (bounce_rate * 0.2)
        """
        # Normalize dwell time (assume 60 seconds is optimal)
        normalized_dwell = min(self.avg_dwell_time / 60.0, 1.0) if self.avg_dwell_time else 0.0
        
        score = (
            self.click_rate * 0.3 +
            self.cart_rate * 0.3 +
            self.conversion_rate * 0.3 +
            normalized_dwell * 0.1
        ) - (self.bounce_rate * 0.2)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))
    
    def update_rates(self):
        """Update calculated rates based on raw counts"""
        if self.impression_count > 0:
            self.click_rate = self.click_count / self.impression_count
        
        if self.click_count > 0:
            self.cart_rate = self.cart_count / self.click_count
            self.conversion_rate = self.purchase_count / self.click_count
            self.avg_dwell_time = self.total_dwell_time / self.click_count
        
        self.behavior_score = self.calculate_score()

