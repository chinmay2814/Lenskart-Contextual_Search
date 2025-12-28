"""
Event tracking API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db_session
from app.models.schemas import EventCreate, EventResponse
from app.models.event import Event
from app.workers.event_processor import get_event_processor

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/", response_model=dict, status_code=202)
async def track_event(event: EventCreate):
    """
    Track a user event asynchronously.
    
    Events are queued for background processing to ensure
    non-blocking operation.
    
    Event types:
    - **search**: User performed a search
    - **click**: User clicked on a product
    - **add_to_cart**: User added product to cart
    - **purchase**: User purchased a product
    - **dwell_time**: Time spent viewing a product
    
    Example:
    ```json
    {
        "event_type": "click",
        "user_id": "user_123",
        "session_id": "session_456",
        "product_id": "prod_789",
        "query": "aviator sunglasses",
        "position": 2
    }
    ```
    """
    event_processor = get_event_processor()
    await event_processor.push_event(event)
    
    return {
        "status": "accepted",
        "message": "Event queued for processing",
        "queue_size": event_processor.get_queue_size()
    }


@router.post("/batch", response_model=dict, status_code=202)
async def track_events_batch(events: List[EventCreate]):
    """
    Track multiple events in batch.
    
    All events are queued for background processing.
    """
    event_processor = get_event_processor()
    
    for event in events:
        await event_processor.push_event(event)
    
    return {
        "status": "accepted",
        "message": f"{len(events)} events queued for processing",
        "queue_size": event_processor.get_queue_size()
    }


@router.get("/recent", response_model=List[EventResponse])
def get_recent_events(
    limit: int = 100,
    event_type: str = None,
    db: Session = Depends(get_db_session)
):
    """
    Get recent events from the database.
    
    Useful for debugging and monitoring.
    """
    query = db.query(Event).order_by(Event.created_at.desc())
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    events = query.limit(limit).all()
    
    return [EventResponse.model_validate(e) for e in events]


@router.get("/stats")
def get_event_stats():
    """
    Get event processor statistics.
    """
    event_processor = get_event_processor()
    return event_processor.get_stats()


@router.post("/click")
async def track_click(
    product_id: str,
    query: str = None,
    position: int = None,
    user_id: str = None,
    session_id: str = None
):
    """
    Convenience endpoint for tracking clicks.
    """
    event = EventCreate(
        event_type="click",
        product_id=product_id,
        query=query,
        position=position,
        user_id=user_id,
        session_id=session_id,
    )
    
    event_processor = get_event_processor()
    await event_processor.push_event(event)
    
    return {"status": "accepted"}


@router.post("/cart")
async def track_add_to_cart(
    product_id: str,
    user_id: str = None,
    session_id: str = None
):
    """
    Convenience endpoint for tracking add-to-cart events.
    """
    event = EventCreate(
        event_type="add_to_cart",
        product_id=product_id,
        user_id=user_id,
        session_id=session_id,
    )
    
    event_processor = get_event_processor()
    await event_processor.push_event(event)
    
    return {"status": "accepted"}


@router.post("/purchase")
async def track_purchase(
    product_id: str,
    user_id: str = None,
    session_id: str = None
):
    """
    Convenience endpoint for tracking purchases.
    """
    event = EventCreate(
        event_type="purchase",
        product_id=product_id,
        user_id=user_id,
        session_id=session_id,
    )
    
    event_processor = get_event_processor()
    await event_processor.push_event(event)
    
    return {"status": "accepted"}


@router.post("/dwell")
async def track_dwell_time(
    product_id: str,
    dwell_time_seconds: float,
    user_id: str = None,
    session_id: str = None
):
    """
    Convenience endpoint for tracking dwell time.
    """
    event = EventCreate(
        event_type="dwell_time",
        product_id=product_id,
        dwell_time_seconds=dwell_time_seconds,
        user_id=user_id,
        session_id=session_id,
    )
    
    event_processor = get_event_processor()
    await event_processor.push_event(event)
    
    return {"status": "accepted"}

