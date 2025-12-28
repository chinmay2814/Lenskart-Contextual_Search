"""
Background event processor using asyncio Queue
"""
import asyncio
from typing import Optional
from datetime import datetime

from app.models.event import Event
from app.models.schemas import EventCreate
from app.db.database import get_db_context
from app.services.learning_service import get_learning_service


class EventProcessor:
    """
    Asynchronous event processor using asyncio Queue.
    
    Events are pushed to the queue and processed in the background,
    ensuring non-blocking event tracking.
    """
    
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.learning_service = get_learning_service()
        self.processed_count = 0
    
    async def start(self):
        """Start the event processor"""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._process_events())
        print("[+] Event processor started")
    
    async def stop(self):
        """Stop the event processor"""
        self.is_running = False
        
        if self._task:
            # Wait for remaining events to be processed
            await self.queue.join()
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        print(f"[+] Event processor stopped. Processed {self.processed_count} events.")
    
    async def push_event(self, event_data: EventCreate):
        """Push an event to the queue for processing"""
        await self.queue.put(event_data)
    
    async def _process_events(self):
        """Background task that processes events from the queue"""
        while self.is_running:
            try:
                # Wait for an event with timeout
                try:
                    event_data = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the event
                await self._handle_event(event_data)
                
                self.queue.task_done()
                self.processed_count += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[!] Error processing event: {e}")
    
    async def _handle_event(self, event_data: EventCreate):
        """Handle a single event"""
        try:
            with get_db_context() as db:
                # Create event record
                event = Event(
                    event_type=event_data.event_type.value,
                    user_id=event_data.user_id,
                    session_id=event_data.session_id,
                    product_id=event_data.product_id,
                    query=event_data.query,
                    dwell_time_seconds=event_data.dwell_time_seconds,
                    position=event_data.position,
                )
                db.add(event)
                db.flush()
                
                # Update behavior scores
                self.learning_service.process_event(db, event)
                
        except Exception as e:
            print(f"[!] Failed to handle event: {e}")
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
    
    def get_stats(self) -> dict:
        """Get processor statistics"""
        return {
            "is_running": self.is_running,
            "queue_size": self.queue.qsize(),
            "processed_count": self.processed_count,
        }


# Singleton instance
_event_processor: Optional[EventProcessor] = None


def get_event_processor() -> EventProcessor:
    """Get or create EventProcessor singleton"""
    global _event_processor
    if _event_processor is None:
        _event_processor = EventProcessor()
    return _event_processor

