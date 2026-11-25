"""
Pydantic schemas for API data validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum

# Enums
class ModelType(str, Enum):
    NAIVE = "naive"
    MOVING_AVERAGE = "moving_average"
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    ARIMA = "arima"
    LSTM = "lstm"
    GRU = "gru"

class StrategyType(str, Enum):
    SMA_CROSSOVER = "sma_crossover"
    RSI = "rsi"
    MACD = "macd"
    BUY_AND_HOLD = "buy_and_hold"

class PipelineStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

# Stock Schemas
class StockBase(BaseModel):
    symbol: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "USD"

class StockCreate(StockBase):
    pass

class StockUpdate(BaseModel):
    name: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None

class StockResponse(StockBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Price Schemas
class PriceBase(BaseModel):
    date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    adj_close: Optional[float] = None

class PriceResponse(PriceBase):
    id: int
    stock_id: int
    is_adjusted: bool
    source: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Technical Indicator Schemas
class TechnicalIndicatorBase(BaseModel):
    date: date
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_20: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr: Optional[float] = None
    daily_return: Optional[float] = None
    cumulative_return: Optional[float] = None

class TechnicalIndicatorResponse(TechnicalIndicatorBase):
    id: int
    stock_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Prediction Schemas
class PredictionRequest(BaseModel):
    symbol: str
    model_type: ModelType
    prediction_days: int = 30

class PredictionResponse(BaseModel):
    symbol: str
    model_type: ModelType
    predictions: List[Dict[str, Any]]
    confidence_interval: Optional[Dict[str, List[float]]] = None
    
    class Config:
        from_attributes = True

class PredictionResult(BaseModel):
    date: date
    actual_price: Optional[float] = None
    predicted_price: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None

class ModelEvaluationRequest(BaseModel):
    symbol: str
    model_types: Optional[List[ModelType]] = None
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    use_walk_forward: bool = True

class ModelMetrics(BaseModel):
    model_name: str
    mae: float
    rmse: float
    mape: float
    smape: float
    r_squared: float
    directional_accuracy: float
    training_time_seconds: Optional[float] = None

class ModelComparisonResponse(BaseModel):
    stock_symbol: str
    evaluation_date: datetime
    models: List[ModelMetrics]
    best_model: str
    naive_baseline_metrics: ModelMetrics

# Backtesting Schemas
class BacktestRequest(BaseModel):
    symbol: str
    strategy: StrategyType
    start_date: date
    end_date: date
    initial_capital: float = 100000.0
    transaction_cost: float = 0.001
    parameters: Optional[Dict[str, Any]] = None

class BacktestTrade(BaseModel):
    date: date
    action: str  # buy, sell
    price: float
    quantity: float
    cost: float
    total: float

class BacktestResponse(BaseModel):
    symbol: str
    strategy: str
    start_date: date
    end_date: date
    
    # Returns
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    
    # Risk
    max_drawdown: float
    sharpe_ratio: float
    volatility: float
    
    # Trading
    total_trades: int
    win_rate: float
    avg_trade_return: float
    
    trades: List[BacktestTrade]
    equity_curve: List[Dict[str, Any]]

# Pipeline Schemas
class PipelineExecutionResponse(BaseModel):
    id: int
    pipeline_name: str
    execution_id: str
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    records_processed: int
    records_inserted: int
    error_message: Optional[str] = None

class PipelineSummary(BaseModel):
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_duration_seconds: float
    last_execution: Optional[datetime] = None

# Dashboard Schemas
class DashboardMetrics(BaseModel):
    stocks_count: int
    total_records: int
    last_refresh: Optional[datetime] = None
    data_quality_score: float
    active_predictions: int
    models_trained: int

class DataQualitySummary(BaseModel):
    total_checks: int
    passed_checks: int
    failed_checks: int
    issues_by_type: Dict[str, int]
    missing_data_percentage: float
    duplicate_records: int

# Analytics Schemas
class MonthlyPerformance(BaseModel):
    year: int
    month: int
    symbol: str
    monthly_return: float
    avg_daily_return: float
    volatility: float
    best_day: date
    worst_day: date

class YearlyPerformance(BaseModel):
    year: int
    symbol: str
    yearly_return: float
    total_volume: int
    avg_price: float
    highest_price: float
    lowest_price: float

class SQLQueryRequest(BaseModel):
    query: str

class SQLQueryResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float