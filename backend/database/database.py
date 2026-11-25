"""
SQLAlchemy Database Configuration and Connection Management.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

load_dotenv()

# Use synchronous SQLite for better compatibility
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./stock_intelligence.db"
)

# Check if we should use async (for async endpoints)
USE_ASYNC = os.getenv("USE_ASYNC", "false").lower() == "true"

if USE_ASYNC and "sqlite" in DATABASE_URL:
    # Async SQLite configuration
    from sqlalchemy.pool import NullPool
    engine = create_engine(
        DATABASE_URL.replace("sqlite:", "sqlite+aiosqlite:"),
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )
else:
    # Synchronous SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Session:
    """Dependency for FastAPI database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    from backend.database import models
    Base.metadata.create_all(bind=engine)
    
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connection verified successfully")

def get_engine():
    """Get the database engine."""
    return engine