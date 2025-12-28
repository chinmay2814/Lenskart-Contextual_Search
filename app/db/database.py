"""
SQLite database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os

from app.config import get_settings

settings = get_settings()

# Ensure data directory exists
os.makedirs(os.path.dirname(settings.sqlite_db_path), exist_ok=True)

# Create SQLite engine
SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.sqlite_db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=settings.debug,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def init_db():
    """Initialize database tables"""
    # Import models to register them with Base
    from app.models.product import Product
    from app.models.event import Event, BehaviorScore
    
    Base.metadata.create_all(bind=engine)
    print("[+] Database tables created successfully")


def get_db():
    """
    Dependency for getting database session.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database session.
    Usage: with get_db_context() as db: ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

