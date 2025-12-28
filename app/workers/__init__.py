"""
Background workers
"""
from app.workers.event_processor import EventProcessor, get_event_processor

__all__ = ["EventProcessor", "get_event_processor"]

