"""
Stock Intelligence Platform - FastAPI Backend.

A comprehensive stock analysis and forecasting platform.
"""
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.database import init_db, engine, Base
from backend.api.stocks import router as stocks_router
from backend.services.data_service import ExportService
from backend.database.schema import SQLQueryRequest, SQLQueryResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    print("Stock Intelligence Platform is ready!")
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Stock Intelligence Platform API",
    description="""
    ## AI-Powered Stock Intelligence & Forecasting Platform
    
    ### Features:
    - **Multi-Model Forecasting**: Naive, Moving Average, Linear Regression, 
      Random Forest, XGBoost, ARIMA, LSTM, GRU
    - **Strict Time-Series Validation**: Walk-forward validation with no data leakage
    - **Technical Indicators**: SMA, EMA, RSI, MACD, Bollinger Bands, ATR
    - **Backtesting Engine**: Historical strategy simulation
    - **SQL Analytics**: Complex queries, aggregations, window functions
    - **Data Pipeline**: Automated ETL from Yahoo Finance
    
    ### Important Notes:
    - Predictions are for educational purposes only
    - Past performance does not guarantee future results
    - Always verify with official sources before making investment decisions
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stocks_router)


# Root endpoint - serve frontend
@app.get("/")
async def root():
    """Serve the frontend application."""
    return {
        "message": "Stock Intelligence Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


# Export endpoints
from fastapi import Depends
from sqlalchemy.orm import Session
from backend.database.database import get_db


@app.get("/api/export/prices/{symbol}/csv")
def export_prices_csv(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Export price data to CSV."""
    export_service = ExportService(db)
    content = export_service.export_prices_to_csv(symbol)
    
    return JSONResponse(
        content=content,
        headers={
            "Content-Disposition": f"attachment; filename={symbol}_prices.csv",
            "Content-Type": "text/csv"
        }
    )


@app.get("/api/export/prices/{symbol}/excel")
def export_prices_excel(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Export price data to Excel."""
    export_service = ExportService(db)
    content = export_service.export_prices_to_excel(symbol)
    
    return JSONResponse(
        content=content,
        headers={
            "Content-Disposition": f"attachment; filename={symbol}_prices.xlsx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    )


@app.get("/api/export/indicators/{symbol}/csv")
def export_indicators_csv(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Export technical indicators to CSV."""
    export_service = ExportService(db)
    content = export_service.export_indicators_to_csv(symbol)
    
    return JSONResponse(
        content=content,
        headers={
            "Content-Disposition": f"attachment; filename={symbol}_indicators.csv",
            "Content-Type": "text/csv"
        }
    )


@app.get("/api/export/predictions/{symbol}/csv")
def export_predictions_csv(
    symbol: str,
    model: str = None,
    db: Session = Depends(get_db)
):
    """Export predictions to CSV."""
    export_service = ExportService(db)
    content = export_service.export_predictions_to_csv(symbol, model)
    
    return JSONResponse(
        content=content,
        headers={
            "Content-Disposition": f"attachment; filename={symbol}_predictions.csv",
            "Content-Type": "text/csv"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    
    print(f"\n{'='*60}")
    print(f"Stock Intelligence Platform")
    print(f"{'='*60}")
    print(f"API: http://{host}:{port}")
    print(f"Documentation: http://{host}:{port}/docs")
    print(f"{'='*60}\n")
    
    uvicorn.run(app, host=host, port=port)