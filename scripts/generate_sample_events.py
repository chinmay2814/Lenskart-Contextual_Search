"""
Script to generate sample user events for testing behavioral learning
"""
import sys
import os
import random
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import init_db, get_db_context
from app.models.product import Product
from app.models.schemas import EventCreate, EventTypeEnum
from app.workers.event_processor import get_event_processor
from app.services.learning_service import get_learning_service


# Sample search queries
SAMPLE_QUERIES = [
    "aviator sunglasses",
    "blue light glasses",
    "polarized sunglasses",
    "reading glasses",
    "computer glasses",
    "sports sunglasses",
    "cat eye frames",
    "round glasses",
    "designer sunglasses",
    "kids glasses",
    "progressive lenses",
    "stylish eyewear for men",
    "women's fashion glasses",
    "lightweight frames",
    "titanium glasses",
]


async def generate_events(num_events: int = 100):
    """Generate sample user events"""
    print(f"[*] Generating {num_events} sample events...")
    
    # Initialize database
    init_db()
    
    # Get all products
    with get_db_context() as db:
        products = db.query(Product).all()
        if not products:
            print("[!] No products found. Please run seed_data.py first.")
            return
        
        product_ids = [p.id for p in products]
        print(f"[*] Found {len(products)} products")
    
    # Start event processor
    event_processor = get_event_processor()
    await event_processor.start()
    
    # Generate events
    events_generated = {
        "search": 0,
        "click": 0,
        "add_to_cart": 0,
        "purchase": 0,
        "dwell_time": 0,
    }
    
    for i in range(num_events):
        # Random event type with weighted probability
        event_type = random.choices(
            ["search", "click", "add_to_cart", "purchase", "dwell_time"],
            weights=[0.3, 0.35, 0.15, 0.1, 0.1],
            k=1
        )[0]
        
        # Random user and session
        user_id = f"user_{random.randint(1, 50)}"
        session_id = f"session_{random.randint(1, 200)}"
        
        # Create event based on type
        if event_type == "search":
            event = EventCreate(
                event_type=EventTypeEnum.SEARCH,
                user_id=user_id,
                session_id=session_id,
                query=random.choice(SAMPLE_QUERIES),
            )
        elif event_type == "click":
            event = EventCreate(
                event_type=EventTypeEnum.CLICK,
                user_id=user_id,
                session_id=session_id,
                product_id=random.choice(product_ids),
                query=random.choice(SAMPLE_QUERIES),
                position=random.randint(1, 10),
            )
        elif event_type == "add_to_cart":
            event = EventCreate(
                event_type=EventTypeEnum.ADD_TO_CART,
                user_id=user_id,
                session_id=session_id,
                product_id=random.choice(product_ids),
            )
        elif event_type == "purchase":
            event = EventCreate(
                event_type=EventTypeEnum.PURCHASE,
                user_id=user_id,
                session_id=session_id,
                product_id=random.choice(product_ids),
            )
        else:  # dwell_time
            event = EventCreate(
                event_type=EventTypeEnum.DWELL_TIME,
                user_id=user_id,
                session_id=session_id,
                product_id=random.choice(product_ids),
                dwell_time_seconds=random.uniform(2, 120),
            )
        
        await event_processor.push_event(event)
        events_generated[event_type] += 1
        
        if (i + 1) % 20 == 0:
            print(f"  Generated {i + 1}/{num_events} events...")
    
    # Wait for events to be processed
    print("[*] Waiting for events to be processed...")
    await asyncio.sleep(3)  # Give time for processing
    
    # Stop processor
    await event_processor.stop()
    
    # Recalculate scores
    print("[*] Recalculating behavior scores...")
    learning_service = get_learning_service()
    with get_db_context() as db:
        learning_service.recalculate_all_scores(db)
    
    # Print summary
    print("\n[+] Events generated:")
    for event_type, count in events_generated.items():
        print(f"  - {event_type}: {count}")
    
    print("\n[+] Sample events generation complete!")


if __name__ == "__main__":
    num_events = 100
    if len(sys.argv) > 1:
        num_events = int(sys.argv[1])
    
    asyncio.run(generate_events(num_events))

