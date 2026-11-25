"""
Data Collection and ETL Pipeline for Stock Data.
Handles data extraction, transformation, validation, and loading.
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
import yfinance as yf

from backend.database.models import (
    Stock, HistoricalPrice, TechnicalIndicator, PipelineExecution, 
    DataQualityLog
)
from backend.indicators.technical_indicators import TechnicalIndicatorEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPipeline:
    """Automated ETL pipeline for stock data."""
    
    def __init__(self, db: Session):
        self.db = db
        self.execution_id = None
        self.records_processed = 0
        self.records_inserted = 0
        self.records_updated = 0
        self.records_failed = 0
        self.errors = []
        self.indicator_engine = TechnicalIndicatorEngine()
    
    def run_pipeline(
        self, 
        symbol: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_history_years: int = 20
    ) -> Dict[str, Any]:
        """
        Execute the full ETL pipeline for a stock.
        
        Extract → Transform → Validate → Load → Analyze
        """
        self.execution_id = str(uuid.uuid4())[:8]
        start_time = datetime.utcnow()
        
        # Create pipeline execution record
        execution = PipelineExecution(
            pipeline_name="stock_data_etl",
            execution_id=self.execution_id,
            status="running",
            start_time=start_time,
            stock_symbol=symbol
        )
        self.db.add(execution)
        self.db.commit()
        
        try:
            logger.info(f"Starting ETL pipeline for {symbol}")
            
            # Extract
            df = self._extract_data(symbol, start_date, end_date, max_history_years)
            if df is None or df.empty:
                raise ValueError(f"No data retrieved for {symbol}")
            
            self.records_processed = len(df)
            
            # Transform
            df = self._transform_data(df)
            
            # Validate
            validation_results = self._validate_data(df, symbol)
            if not validation_results["is_valid"]:
                raise ValueError(f"Data validation failed: {validation_results['errors']}")
            
            # Load
            stats = self._load_data(df, symbol)
            self.records_inserted = stats["inserted"]
            self.records_updated = stats["updated"]
            
            # Calculate and store technical indicators
            self._calculate_indicators(symbol)
            
            # Update pipeline execution
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            execution.status = "success"
            execution.end_time = end_time
            execution.duration_seconds = duration
            execution.records_processed = self.records_processed
            execution.records_inserted = self.records_inserted
            execution.records_updated = self.records_updated
            self.db.commit()
            
            logger.info(f"Pipeline completed successfully for {symbol}")
            
            return {
                "success": True,
                "symbol": symbol,
                "execution_id": self.execution_id,
                "records_processed": self.records_processed,
                "records_inserted": self.records_inserted,
                "records_updated": self.records_updated,
                "duration_seconds": duration
            }
            
        except Exception as e:
            self.errors.append(str(e))
            logger.error(f"Pipeline failed for {symbol}: {e}")
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            execution.status = "failed"
            execution.end_time = end_time
            execution.duration_seconds = duration
            execution.error_message = str(e)
            self.db.commit()
            
            return {
                "success": False,
                "symbol": symbol,
                "execution_id": self.execution_id,
                "error": str(e),
                "duration_seconds": duration
            }
    
    def _extract_data(
        self, 
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_history_years: int = 20
    ) -> Optional[pd.DataFrame]:
        """Extract historical stock data from Yahoo Finance."""
        if not os.getenv("YAHOO_FINANCE_ENABLED", "true").lower() == "true":
            logger.warning("Yahoo Finance API is disabled")
            return None
        
        try:
            # Set default date range
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=max_history_years * 365)).strftime("%Y-%m-%d")
            
            logger.info(f"Fetching {symbol} data from {start_date} to {end_date}")
            
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            df.reset_index(inplace=True)
            
            # Rename columns to standard names
            column_mapping = {
                'Date': 'date',
                'Open': 'open_price',
                'High': 'high_price',
                'Low': 'low_price',
                'Close': 'close_price',
                'Volume': 'volume'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            # Convert date to proper format
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            logger.info(f"Retrieved {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Data extraction failed for {symbol}: {e}")
            raise
    
    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and transform raw data."""
        # Ensure correct data types
        df['open_price'] = pd.to_numeric(df['open_price'], errors='coerce')
        df['high_price'] = pd.to_numeric(df['high_price'], errors='coerce')
        df['low_price'] = pd.to_numeric(df['low_price'], errors='coerce')
        df['close_price'] = pd.to_numeric(df['close_price'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)
        
        # Handle missing values - forward fill then backward fill
        price_columns = ['open_price', 'high_price', 'low_price', 'close_price']
        for col in price_columns:
            if df[col].isna().any():
                # Log missing values
                missing_count = df[col].isna().sum()
                logger.warning(f"Found {missing_count} missing values in {col}")
                df[col] = df[col].ffill().bfill()
        
        # Remove any remaining duplicates
        initial_len = len(df)
        df = df.drop_duplicates(subset=['date'], keep='first')
        if len(df) < initial_len:
            logger.info(f"Removed {initial_len - len(df)} duplicate records")
        
        # Remove rows with invalid data (negative prices, zero volume)
        invalid_mask = (
            (df['open_price'] <= 0) | 
            (df['high_price'] <= 0) | 
            (df['low_price'] <= 0) | 
            (df['close_price'] <= 0)
        )
        if invalid_mask.any():
            invalid_count = invalid_mask.sum()
            logger.warning(f"Removing {invalid_count} rows with invalid prices")
            df = df[~invalid_mask]
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def _validate_data(
        self, 
        df: pd.DataFrame, 
        symbol: str
    ) -> Dict[str, Any]:
        """Validate data quality."""
        errors = []
        warnings = []
        
        # Check required columns
        required_columns = ['date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing columns: {missing_columns}")
        
        # Check for required data
        if df.empty:
            errors.append("DataFrame is empty")
        
        # Check OHLCV validity
        ohlcv_checks = [
            (df['open_price'] <= 0, "Open price has non-positive values"),
            (df['high_price'] < df['open_price'], "High price is below open price"),
            (df['low_price'] > df['open_price'], "Low price is above open price"),
            (df['close_price'] <= 0, "Close price has non-positive values"),
        ]
        
        for check, message in ohlcv_checks:
            if check.any():
                issues_found = check.sum()
                warnings.append(f"{message}: {issues_found} occurrences")
        
        # Check for missing data percentage
        total_cells = len(df) * len(required_columns)
        missing_cells = df[required_columns].isna().sum().sum()
        missing_pct = (missing_cells / total_cells) * 100
        
        if missing_pct > 5:
            warnings.append(f"High missing data percentage: {missing_pct:.2f}%")
        
        # Check for trading date gaps
        if len(df) > 1:
            df_sorted = df.sort_values('date')
            date_diffs = df_sorted['date'].diff().dropna()
            expected_diff = pd.Timedelta(days=1)
            weekend_diffs = date_diffs[date_diffs > pd.Timedelta(days=3)]
            if len(weekend_diffs) > 0:
                missing_dates = len(weekend_diffs)
                warnings.append(f"Potential missing trading dates: {missing_dates}")
        
        # Log data quality issues
        for warning in warnings:
            log = DataQualityLog(
                stock_symbol=symbol,
                check_date=datetime.now().date(),
                issue_type="warning",
                issue_details=warning,
                severity="low"
            )
            self.db.add(log)
        
        self.db.commit()
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _load_data(self, df: pd.DataFrame, symbol: str) -> Dict[str, int]:
        """Load data into the database."""
        # Get or create stock
        stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            stock = Stock(
                symbol=symbol,
                name=symbol,
                exchange="Unknown",
                is_active=True
            )
            self.db.add(stock)
            self.db.commit()
            self.db.refresh(stock)
        
        stock_id = stock.id
        inserted = 0
        updated = 0
        
        # Get existing dates
        existing_dates = set(
            date[0] for date in 
            self.db.query(HistoricalPrice.date)
            .filter(HistoricalPrice.stock_id == stock_id)
            .all()
        )
        
        # Process each row
        for _, row in df.iterrows():
            date_val = row['date']
            
            if date_val in existing_dates:
                # Update existing record
                self.db.query(HistoricalPrice).filter(
                    and_(
                        HistoricalPrice.stock_id == stock_id,
                        HistoricalPrice.date == date_val
                    )
                ).update({
                    'open_price': row['open_price'],
                    'high_price': row['high_price'],
                    'low_price': row['low_price'],
                    'close_price': row['close_price'],
                    'volume': row['volume'],
                    'is_adjusted': True
                })
                updated += 1
            else:
                # Insert new record
                price = HistoricalPrice(
                    stock_id=stock_id,
                    date=date_val,
                    open_price=row['open_price'],
                    high_price=row['high_price'],
                    low_price=row['low_price'],
                    close_price=row['close_price'],
                    volume=row['volume'],
                    is_adjusted=True,
                    source="yahoo_finance"
                )
                self.db.add(price)
                inserted += 1
        
        self.db.commit()
        
        logger.info(f"Loaded {inserted} new records, updated {updated} records for {symbol}")
        
        return {"inserted": inserted, "updated": updated}
    
    def _calculate_indicators(self, symbol: str):
        """Calculate and store technical indicators."""
        stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            return
        
        # Get price data
        prices = self.db.query(HistoricalPrice).filter(
            HistoricalPrice.stock_id == stock.id
        ).order_by(HistoricalPrice.date).all()
        
        if len(prices) < 50:
            logger.warning(f"Insufficient data to calculate indicators for {symbol}")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': p.date,
            'open_price': p.open_price,
            'high_price': p.high_price,
            'low_price': p.low_price,
            'close_price': p.close_price,
            'volume': p.volume
        } for p in prices])
        
        # Calculate indicators
        df = self.indicator_engine.calculate_all_indicators(df)
        
        # Store indicators
        existing_dates = set(
            date[0] for date in
            self.db.query(TechnicalIndicator.date)
            .filter(TechnicalIndicator.stock_id == stock.id)
            .all()
        )
        
        for _, row in df.iterrows():
            if row['date'] in existing_dates:
                continue
            
            indicator = TechnicalIndicator(
                stock_id=stock.id,
                date=row['date'],
                sma_20=row.get('sma_20'),
                sma_50=row.get('sma_50'),
                ema_20=row.get('ema_20'),
                rsi=row.get('rsi'),
                macd=row.get('macd'),
                macd_signal=row.get('macd_signal'),
                macd_histogram=row.get('macd_histogram'),
                bollinger_upper=row.get('bollinger_upper'),
                bollinger_middle=row.get('bollinger_middle'),
                bollinger_lower=row.get('bollinger_lower'),
                atr=row.get('atr'),
                rolling_volatility_20=row.get('rolling_volatility_20'),
                daily_return=row.get('daily_return'),
                cumulative_return=row.get('cumulative_return'),
                volume_sma_20=row.get('volume_sma_20')
            )
            self.db.add(indicator)
        
        self.db.commit()
        logger.info(f"Calculated indicators for {symbol}")


class PipelineManager:
    """Manage multiple pipeline executions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def run_all_stocks(
        self, 
        symbols: Optional[List[str]] = None,
        max_history_years: int = 20
    ) -> Dict[str, Any]:
        """Run pipeline for all configured stocks."""
        if symbols is None:
            symbols = os.getenv(
                "STOCK_SYMBOLS", 
                "AAPL,GOOGL,MSFT,AMZN,TSLA"
            ).split(",")
        
        results = {
            "total": len(symbols),
            "successful": 0,
            "failed": 0,
            "executions": []
        }
        
        for symbol in symbols:
            symbol = symbol.strip().upper()
            if not symbol:
                continue
            
            pipeline = DataPipeline(self.db)
            result = pipeline.run_pipeline(symbol, max_history_years=max_history_years)
            results["executions"].append(result)
            
            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def get_pipeline_history(
        self, 
        limit: int = 50
    ) -> List[PipelineExecution]:
        """Get recent pipeline executions."""
        return (
            self.db.query(PipelineExecution)
            .order_by(PipelineExecution.start_time.desc())
            .limit(limit)
            .all()
        )
    
    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get summary statistics for pipeline executions."""
        total = self.db.query(func.count(PipelineExecution.id)).scalar()
        successful = self.db.query(func.count(PipelineExecution.id)).filter(
            PipelineExecution.status == "success"
        ).scalar()
        failed = self.db.query(func.count(PipelineExecution.id)).filter(
            PipelineExecution.status == "failed"
        ).scalar()
        
        avg_duration = (
            self.db.query(func.avg(PipelineExecution.duration_seconds))
            .filter(PipelineExecution.status == "success")
            .scalar()
        ) or 0
        
        last_execution = (
            self.db.query(func.max(PipelineExecution.start_time)).scalar()
        )
        
        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_duration_seconds": round(avg_duration, 2),
            "last_execution": last_execution
        }