"""
Pytest configuration and fixtures.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.database import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(test_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_price_data():
    """Generate sample price data."""
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=252, freq='B')
    
    # Generate prices with some randomness
    returns = np.random.normal(0.0003, 0.01, len(dates))
    prices = 100 * (1 + returns).cumprod()
    
    df = pd.DataFrame({
        'date': dates,
        'open_price': prices * (1 + np.random.uniform(-0.005, 0.005, len(dates))),
        'high_price': prices * (1 + np.abs(np.random.uniform(0, 0.01, len(dates)))),
        'low_price': prices * (1 - np.abs(np.random.uniform(0, 0.01, len(dates)))),
        'close_price': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    })
    
    return df