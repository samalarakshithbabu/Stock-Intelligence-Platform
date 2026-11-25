"""
Export Services for data export to CSV and Excel.
"""
import io
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session

from backend.database.models import Stock, HistoricalPrice, TechnicalIndicator, Prediction


class ExportService:
    """Service for exporting data to various formats."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_prices_to_csv(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> bytes:
        """Export price data to CSV format."""
        stock = self.db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            raise ValueError(f"Stock {symbol} not found")
        
        query = self.db.query(HistoricalPrice).filter(
            HistoricalPrice.stock_id == stock.id
        ).order_by(HistoricalPrice.date)
        
        prices = query.all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 
            'Adjusted', 'Source', 'Created_At'
        ])
        
        # Data
        for p in prices:
            writer.writerow([
                p.date,
                p.open_price,
                p.high_price,
                p.low_price,
                p.close_price,
                p.volume,
                p.is_adjusted,
                p.source,
                p.created_at
            ])
        
        return output.getvalue().encode('utf-8')
    
    def export_prices_to_excel(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> bytes:
        """Export price data to Excel format."""
        stock = self.db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            raise ValueError(f"Stock {symbol} not found")
        
        prices = (
            self.db.query(HistoricalPrice)
            .filter(HistoricalPrice.stock_id == stock.id)
            .order_by(HistoricalPrice.date)
            .all()
        )
        
        data = [{
            'Date': p.date,
            'Open': p.open_price,
            'High': p.high_price,
            'Low': p.low_price,
            'Close': p.close_price,
            'Volume': p.volume,
            'Adjusted': p.is_adjusted
        } for p in prices]
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=f'{symbol}_Prices')
        
        return output.getvalue()
    
    def export_indicators_to_csv(self, symbol: str) -> bytes:
        """Export technical indicators to CSV."""
        stock = self.db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            raise ValueError(f"Stock {symbol} not found")
        
        indicators = (
            self.db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.stock_id == stock.id)
            .order_by(TechnicalIndicator.date)
            .all()
        )
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Date', 'SMA_20', 'SMA_50', 'EMA_20', 'RSI', 'MACD', 
            'MACD_Signal', 'MACD_Histogram', 'Bollinger_Upper', 
            'Bollinger_Middle', 'Bollinger_Lower', 'ATR', 
            'Daily_Return', 'Cumulative_Return', 'Rolling_Volatility_20'
        ])
        
        for i in indicators:
            writer.writerow([
                i.date,
                i.sma_20,
                i.sma_50,
                i.ema_20,
                i.rsi,
                i.macd,
                i.macd_signal,
                i.macd_histogram,
                i.bollinger_upper,
                i.bollinger_middle,
                i.bollinger_lower,
                i.atr,
                i.daily_return,
                i.cumulative_return,
                i.rolling_volatility_20
            ])
        
        return output.getvalue().encode('utf-8')
    
    def export_predictions_to_csv(
        self,
        symbol: str,
        model_name: Optional[str] = None
    ) -> bytes:
        """Export predictions to CSV."""
        stock = self.db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            raise ValueError(f"Stock {symbol} not found")
        
        query = self.db.query(Prediction).filter(
            Prediction.stock_id == stock.id
        )
        
        if model_name:
            query = query.filter(Prediction.model_name == model_name)
        
        predictions = query.order_by(Prediction.prediction_date.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Model', 'Prediction_Date', 'Target_Date', 
            'Actual_Price', 'Predicted_Price', 'Confidence_Lower',
            'Confidence_Upper', 'MAE', 'RMSE', 'MAPE', 
            'Directional_Accuracy'
        ])
        
        for p in predictions:
            writer.writerow([
                p.model_name,
                p.prediction_date,
                p.target_date,
                p.actual_price,
                p.predicted_price,
                p.confidence_lower,
                p.confidence_upper,
                p.mae,
                p.rmse,
                p.mape,
                p.directional_accuracy
            ])
        
        return output.getvalue().encode('utf-8')
    
    def export_model_comparison_to_csv(
        self,
        symbol: str
    ) -> bytes:
        """Export model comparison results to CSV."""
        from backend.database.models import ModelPerformance
        
        results = (
            self.db.query(ModelPerformance)
            .filter(ModelPerformance.stock_symbol == symbol.upper())
            .order_by(ModelPerformance.created_at.desc())
            .limit(10)
            .all()
        )
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Model', 'MAE', 'RMSE', 'MAPE', 'SMAPE', 
            'R_Squared', 'Directional_Accuracy', 'Training_Samples',
            'Test_Samples', 'Created_At'
        ])
        
        for r in results:
            writer.writerow([
                r.model_name,
                r.mae,
                r.rmse,
                r.mape,
                r.smape,
                r.r_squared,
                r.directional_accuracy,
                r.training_samples,
                r.test_samples,
                r.created_at
            ])
        
        return output.getvalue().encode('utf-8')
    
    def export_backtest_results_to_excel(
        self,
        symbol: str
    ) -> bytes:
        """Export backtest results to Excel."""
        from backend.database.models import BacktestResult
        
        results = (
            self.db.query(BacktestResult)
            .filter(BacktestResult.stock_symbol == symbol.upper())
            .order_by(BacktestResult.created_at.desc())
            .limit(10)
            .all()
        )
        
        data = []
        for r in results:
            data.append({
                'Strategy': r.strategy_name,
                'Start_Date': r.start_date,
                'End_Date': r.end_date,
                'Initial_Capital': r.initial_capital,
                'Final_Capital': r.final_capital,
                'Total_Return_Pct': r.total_return * 100,
                'Annualized_Return_Pct': r.annualized_return * 100,
                'Max_Drawdown_Pct': r.max_drawdown * 100,
                'Sharpe_Ratio': r.sharpe_ratio,
                'Total_Trades': r.total_trades,
                'Win_Rate_Pct': r.win_rate * 100,
                'Total_Transaction_Costs': r.total_transaction_costs
            })
        
        df = pd.DataFrame(data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Backtest_Results')
        
        return output.getvalue()