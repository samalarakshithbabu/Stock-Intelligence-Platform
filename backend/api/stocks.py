"""
FastAPI API Routes for Stock Intelligence Platform.
"""
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import Stock, HistoricalPrice, TechnicalIndicator
from backend.database.schema import (
    StockCreate, StockUpdate, StockResponse, PriceResponse,
    TechnicalIndicatorResponse, DashboardMetrics, DataQualitySummary,
    PipelineExecutionResponse, PipelineSummary, ModelEvaluationRequest,
    ModelComparisonResponse, ModelMetrics, PredictionRequest, PredictionResponse,
    BacktestRequest, BacktestResponse, MonthlyPerformance, YearlyPerformance,
    SQLQueryRequest, SQLQueryResponse
)
from backend.pipelines.data_pipeline import DataPipeline, PipelineManager
from backend.forecasting.forecasting_engine import ForecastingEngine
from backend.database.schema import ModelType
from backend.backtesting.backtesting_engine import BacktestingEngine
from backend.analytics.sql_analytics import SQLAnalyticsEngine

router = APIRouter()


# ==================== STOCK ENDPOINTS ====================

@router.get("/api/stocks", response_model=List[StockResponse])
def get_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get list of all stocks."""
    stocks = db.query(Stock).filter(Stock.is_active == True).offset(skip).limit(limit).all()
    return stocks


@router.get("/api/stocks/{symbol}", response_model=StockResponse)
def get_stock(symbol: str, db: Session = Depends(get_db)):
    """Get a specific stock by symbol."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@router.post("/api/stocks", response_model=StockResponse)
def create_stock(stock: StockCreate, db: Session = Depends(get_db)):
    """Create a new stock entry."""
    existing = db.query(Stock).filter(Stock.symbol == stock.symbol.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock already exists")
    
    db_stock = Stock(**stock.model_dump())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock


@router.put("/api/stocks/{symbol}", response_model=StockResponse)
def update_stock(symbol: str, stock_update: StockUpdate, db: Session = Depends(get_db)):
    """Update stock information."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    for key, value in stock_update.model_dump(exclude_unset=True).items():
        setattr(stock, key, value)
    
    db.commit()
    db.refresh(stock)
    return stock


@router.delete("/api/stocks/{symbol}")
def deactivate_stock(symbol: str, db: Session = Depends(get_db)):
    """Deactivate a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    stock.is_active = False
    db.commit()
    return {"message": "Stock deactivated"}


# ==================== PRICE ENDPOINTS ====================

@router.get("/api/stocks/{symbol}/prices")
def get_prices(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(5000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """Get historical prices for a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    query = db.query(HistoricalPrice).filter(HistoricalPrice.stock_id == stock.id)
    
    if start_date:
        query = query.filter(HistoricalPrice.date >= start_date)
    if end_date:
        query = query.filter(HistoricalPrice.date <= end_date)
    
    prices = query.order_by(HistoricalPrice.date.desc()).limit(limit).all()
    
    return {
        "symbol": symbol,
        "count": len(prices),
        "prices": [
            {
                "date": p.date,
                "open": p.open_price,
                "high": p.high_price,
                "low": p.low_price,
                "close": p.close_price,
                "volume": p.volume
            }
            for p in prices
        ]
    }


@router.get("/api/stocks/{symbol}/prices/latest")
def get_latest_price(symbol: str, db: Session = Depends(get_db)):
    """Get the latest price for a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    price = (
        db.query(HistoricalPrice)
        .filter(HistoricalPrice.stock_id == stock.id)
        .order_by(HistoricalPrice.date.desc())
        .first()
    )
    
    if not price:
        raise HTTPException(status_code=404, detail="No price data available")
    
    return {
        "symbol": symbol,
        "date": price.date,
        "open": price.open_price,
        "high": price.high_price,
        "low": price.low_price,
        "close": price.close_price,
        "volume": price.volume
    }


# ==================== TECHNICAL INDICATORS ====================

@router.get("/api/stocks/{symbol}/indicators")
def get_indicators(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db)
):
    """Get technical indicators for a stock."""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    query = db.query(TechnicalIndicator).filter(TechnicalIndicator.stock_id == stock.id)
    
    if start_date:
        query = query.filter(TechnicalIndicator.date >= start_date)
    if end_date:
        query = query.filter(TechnicalIndicator.date <= end_date)
    
    indicators = query.order_by(TechnicalIndicator.date.desc()).limit(limit).all()
    
    return {
        "symbol": symbol,
        "count": len(indicators),
        "indicators": [
            {
                "date": i.date,
                "sma_20": i.sma_20,
                "sma_50": i.sma_50,
                "ema_20": i.ema_20,
                "rsi": i.rsi,
                "macd": i.macd,
                "macd_signal": i.macd_signal,
                "bollinger_upper": i.bollinger_upper,
                "bollinger_lower": i.bollinger_lower,
                "atr": i.atr,
                "daily_return": i.daily_return
            }
            for i in indicators
        ]
    }


# ==================== PIPELINE ENDPOINTS ====================

@router.post("/api/pipeline/run/{symbol}")
def run_pipeline(symbol: str, db: Session = Depends(get_db)):
    """Run the ETL pipeline for a specific stock."""
    pipeline = DataPipeline(db)
    result = pipeline.run_pipeline(symbol.upper())
    return result


@router.post("/api/pipeline/run-all")
def run_all_pipelines(db: Session = Depends(get_db)):
    """Run the ETL pipeline for all configured stocks."""
    manager = PipelineManager(db)
    result = manager.run_all_stocks()
    return result


@router.get("/api/pipeline/history", response_model=List[PipelineExecutionResponse])
def get_pipeline_history(limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db)):
    """Get pipeline execution history."""
    manager = PipelineManager(db)
    executions = manager.get_pipeline_history(limit)
    return executions


@router.get("/api/pipeline/summary", response_model=PipelineSummary)
def get_pipeline_summary(db: Session = Depends(get_db)):
    """Get pipeline execution summary statistics."""
    manager = PipelineManager(db)
    return manager.get_pipeline_summary()


# ==================== FORECASTING ENDPOINTS ====================

@router.get("/api/models")
def get_available_models():
    """Get list of available forecasting models."""
    engine = ForecastingEngine(None)
    return engine.get_available_models()


@router.post("/api/models/evaluate")
def evaluate_models(request: ModelEvaluationRequest, db: Session = Depends(get_db)):
    """Evaluate all forecasting models."""
    engine = ForecastingEngine(db)
    
    model_types = [ModelType(m) for m in request.model_types] if request.model_types else None
    
    results = engine.evaluate_models(
        stock_symbol=request.symbol,
        model_types=model_types,
        test_size=request.test_size,
        use_walk_forward=request.use_walk_forward
    )
    
    return results


@router.post("/api/models/forecast")
def generate_forecast(request: PredictionRequest, db: Session = Depends(get_db)):
    """Generate forecast using a specific model."""
    engine = ForecastingEngine(db)
    
    result = engine.generate_forecast(
        stock_symbol=request.symbol,
        model_type=ModelType(request.model_type),
        prediction_days=request.prediction_days
    )
    
    return result


# ==================== BACKTESTING ENDPOINTS ====================

@router.post("/api/backtest", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest, db: Session = Depends(get_db)):
    """Run a backtest for a specific strategy."""
    engine = BacktestingEngine(
        initial_capital=request.initial_capital,
        transaction_cost=request.transaction_cost
    )
    
    result = engine.run_backtest(
        stock_symbol=request.symbol,
        strategy=request.strategy.value,
        start_date=request.start_date,
        end_date=request.end_date,
        parameters=request.parameters or {},
        db_session=db
    )
    
    return result


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/api/analytics/monthly/{symbol}")
def get_monthly_performance(
    symbol: str,
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get monthly performance analytics."""
    analytics = SQLAnalyticsEngine(db)
    return analytics.get_monthly_performance(symbol.upper(), year)


@router.get("/api/analytics/yearly/{symbol}")
def get_yearly_performance(symbol: str, db: Session = Depends(get_db)):
    """Get yearly performance analytics."""
    analytics = SQLAnalyticsEngine(db)
    return analytics.get_yearly_performance(symbol.upper())


@router.get("/api/analytics/volatility/{symbol}")
def get_volatility_analysis(
    symbol: str,
    window: int = Query(20, ge=5, le=252),
    db: Session = Depends(get_db)
):
    """Get historical volatility analysis."""
    analytics = SQLAnalyticsEngine(db)
    return analytics.calculate_historical_volatility(symbol.upper(), window)


@router.get("/api/analytics/top-days/{symbol}")
def get_top_days(symbol: str, n: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Get top performing days."""
    analytics = SQLAnalyticsEngine(db)
    return analytics.get_top_performing_days(symbol.upper(), n)


@router.get("/api/analytics/worst-days/{symbol}")
def get_worst_days(symbol: str, n: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Get worst performing days."""
    analytics = SQLAnalyticsEngine(db)
    return analytics.get_worst_performing_days(symbol.upper(), n)


@router.get("/api/analytics/moving-averages/{symbol}")
def get_moving_averages_sql(symbol: str, db: Session = Depends(get_db)):
    """Get moving averages calculated via SQL."""
    analytics = SQLAnalyticsEngine(db)
    return analytics.calculate_sql_moving_averages(symbol.upper())


@router.get("/api/analytics/quality")
def get_data_quality(db: Session = Depends(get_db)):
    """Get data quality summary."""
    analytics = SQLAnalyticsEngine(db)
    return analytics.get_data_quality_summary()


@router.post("/api/analytics/query")
def execute_sql_query(request: SQLQueryRequest, db: Session = Depends(get_db)):
    """Execute a custom SQL query."""
    analytics = SQLAnalyticsEngine(db)
    return analytics.execute_custom_query(request.query)


# ==================== DASHBOARD ENDPOINTS ====================

@router.get("/api/dashboard/metrics", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Get dashboard summary metrics."""
    stocks_count = db.query(Stock).filter(Stock.is_active == True).count()
    
    total_records = db.query(HistoricalPrice).count()
    
    last_refresh = db.query(HistoricalPrice).order_by(
        HistoricalPrice.created_at.desc()
    ).first()
    
    return DashboardMetrics(
        stocks_count=stocks_count,
        total_records=total_records,
        last_refresh=last_refresh.created_at if last_refresh else None,
        data_quality_score=95.0,  # Placeholder
        active_predictions=0,
        models_trained=0
    )


# ==================== HEALTH ENDPOINT ====================

@router.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}