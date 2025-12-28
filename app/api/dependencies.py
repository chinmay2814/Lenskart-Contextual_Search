"""
API dependencies
"""
from typing import Generator
from sqlalchemy.orm import Session

from app.db.database import SessionLocal


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    
    Usage:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db_session)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

