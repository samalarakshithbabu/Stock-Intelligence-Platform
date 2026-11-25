"""
SQLAlchemy ORM Models for Stock Intelligence Platform.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.database import Base

class Stock(Base):
    """Stock metadata table."""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255))
    exchange = Column(String(100))
    sector = Column(String(100))
    industry = Column(String(255))
    currency = Column(String(10), default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    prices = relationship("HistoricalPrice", back_populates="stock", cascade="all, delete-orphan")
    indicators = relationship("TechnicalIndicator", back_populates="stock", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="stock", cascade="all, delete-orphan")

class HistoricalPrice(Base):
    """Historical stock price data."""
    __tablename__ = "historical_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    adj_close = Column(Float)
    
    # Data quality fields
    is_adjusted = Column(Boolean, default=False)
    source = Column(String(50), default="yahoo_finance")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stock = relationship("Stock", back_populates="prices")
    
    __table_args__ = (
        Index("idx_stock_date", "stock_id", "date"),
        Index("idx_date", "date"),
    )

class TechnicalIndicator(Base):
    """Technical indicators for stocks."""
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    
    # Moving Averages
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    ema_20 = Column(Float)
    
    # Momentum
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    
    # Bollinger Bands
    bollinger_upper = Column(Float)
    bollinger_middle = Column(Float)
    bollinger_lower = Column(Float)
    bollinger_width = Column(Float)
    bollinger_position = Column(Float)
    
    # Volatility
    atr = Column(Float)
    rolling_volatility_20 = Column(Float)
    rolling_volatility_50 = Column(Float)
    
    # Returns
    daily_return = Column(Float)
    cumulative_return = Column(Float)
    log_return = Column(Float)
    
    # Volume
    volume_sma_20 = Column(Float)
    volume_ratio = Column(Float)
    
    # Support/Resistance
    support_level = Column(Float)
    resistance_level = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stock = relationship("Stock", back_populates="indicators")
    
    __table_args__ = (
        Index("idx_indicator_stock_date", "stock_id", "date"),
    )

class Prediction(Base):
    """Model predictions storage."""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    model_name = Column(String(50), nullable=False, index=True)
    prediction_date = Column(DateTime, nullable=False)
    target_date = Column(Date, nullable=False)
    
    actual_price = Column(Float)
    predicted_price = Column(Float)
    confidence_lower = Column(Float)
    confidence_upper = Column(Float)
    
    # Metrics at prediction time
    mae = Column(Float)
    rmse = Column(Float)
    mape = Column(Float)
    directional_accuracy = Column(Float)
    
    # Model version
    model_version = Column(String(50))
    is_validated = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    stock = relationship("Stock", back_populates="predictions")
    
    __table_args__ = (
        Index("idx_prediction_stock_model", "stock_id", "model_name"),
        Index("idx_prediction_date", "prediction_date"),
    )

class ModelPerformance(Base):
    """Model performance metrics storage."""
    __tablename__ = "model_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False, index=True)
    stock_symbol = Column(String(20), nullable=False, index=True)
    
    # Evaluation metrics
    mae = Column(Float)
    rmse = Column(Float)
    mape = Column(Float)
    smape = Column(Float)
    r_squared = Column(Float)
    directional_accuracy = Column(Float)
    
    # Training info
    training_start_date = Column(Date)
    training_end_date = Column(Date)
    test_start_date = Column(Date)
    test_end_date = Column(Date)
    training_samples = Column(Integer)
    test_samples = Column(Integer)
    
    # Hyperparameters (stored as JSON-like string)
    hyperparameters = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BacktestResult(Base):
    """Backtesting results storage."""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String(20), nullable=False, index=True)
    strategy_name = Column(String(50), nullable=False)
    
    # Period
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Initial conditions
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float)
    total_return = Column(Float)
    annualized_return = Column(Float)
    
    # Risk metrics
    max_drawdown = Column(Float)
    max_drawdown_duration = Column(Integer)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    volatility = Column(Float)
    
    # Trading stats
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)
    avg_trade_return = Column(Float)
    avg_winning_trade = Column(Float)
    avg_losing_trade = Column(Float)
    
    # Transaction costs
    total_transaction_costs = Column(Float)
    
    # Parameters
    strategy_parameters = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class PipelineExecution(Base):
    """ETL pipeline execution tracking."""
    __tablename__ = "pipeline_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    pipeline_name = Column(String(100), nullable=False)
    execution_id = Column(String(50), unique=True, nullable=False)
    
    status = Column(String(20), nullable=False)  # running, success, failed
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Metrics
    records_processed = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text)
    error_details = Column(Text)
    
    # Stock info
    stock_symbol = Column(String(20))
    
    created_at = Column(DateTime, default=datetime.utcnow)

class DataQualityLog(Base):
    """Data quality issue logging."""
    __tablename__ = "data_quality_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String(20), nullable=False, index=True)
    check_date = Column(Date, nullable=False)
    
    issue_type = Column(String(50), nullable=False)  # missing_value, outlier, duplicate, etc.
    issue_details = Column(Text)
    column_name = Column(String(100))
    expected_value = Column(String(100))
    actual_value = Column(String(100))
    severity = Column(String(20))  # low, medium, high, critical
    is_resolved = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)