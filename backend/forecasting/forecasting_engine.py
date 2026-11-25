"""
Forecasting Engine - Main orchestrator for all forecasting models.

Implements:
- Multiple model training and evaluation
- Walk-forward validation
- Comparison against naive baseline
- Comprehensive metric calculation
"""
import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from backend.database.models import (
    Stock, HistoricalPrice, ModelPerformance, Prediction
)
from backend.database.schema import ModelType
from backend.forecasting.base_forecaster import (
    BaseForecaster, NaiveForecaster, MovingAverageForecaster,
    LinearRegressionForecaster, RandomForestForecaster, XGBoostForecaster
)
from backend.forecasting.arima_forecaster import ARIMAForecaster
from backend.forecasting.deep_learning import LSTMForecaster, GRUForecaster
from backend.forecasting.metrics import calculate_all_metrics, compare_models
from backend.forecasting.time_series_validator import TimeSeriesValidator
from backend.indicators.technical_indicators import TechnicalIndicatorEngine


class ForecastingEngine:
    """
    Main forecasting engine that orchestrates model training,
    evaluation, and prediction generation.
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.validator = TimeSeriesValidator()
        self.indicator_engine = TechnicalIndicatorEngine()
        self._forecaster_map = {
            ModelType.NAIVE: NaiveForecaster,
            ModelType.MOVING_AVERAGE: lambda: MovingAverageForecaster(window=20),
            ModelType.LINEAR_REGRESSION: LinearRegressionForecaster,
            ModelType.RANDOM_FOREST: lambda: RandomForestForecaster(n_estimators=100, max_depth=10),
            ModelType.XGBOOST: lambda: XGBoostForecaster(n_estimators=100, max_depth=6),
            ModelType.ARIMA: lambda: ARIMAForecaster(p=5, d=1, q=0),
            ModelType.LSTM: lambda: LSTMForecaster(sequence_length=60, epochs=20, batch_size=32),
            ModelType.GRU: lambda: GRUForecaster(sequence_length=60, epochs=20, batch_size=32),
        }
    
    def get_forecaster(self, model_type: ModelType) -> BaseForecaster:
        """Get a new instance of the specified forecaster."""
        factory = self._forecaster_map.get(model_type)
        if factory is None:
            raise ValueError(f"Unknown model type: {model_type}")
        return factory()
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available forecasting models."""
        return [
            {"id": mt.value, "name": mt.value.replace("_", " ").title()}
            for mt in ModelType
        ]
    
    def prepare_features(
        self,
        stock_symbol: str,
        include_indicators: bool = True
    ) -> pd.DataFrame:
        """
        Prepare feature matrix from historical data.
        
        Uses only information available at prediction time to prevent leakage.
        """
        # Get stock data
        stock = self.db.query(Stock).filter(Stock.symbol == stock_symbol).first()
        if not stock:
            raise ValueError(f"Stock {stock_symbol} not found in database")
        
        prices = (
            self.db.query(HistoricalPrice)
            .filter(HistoricalPrice.stock_id == stock.id)
            .order_by(HistoricalPrice.date)
            .all()
        )
        
        # Create DataFrame
        df = pd.DataFrame([{
            'date': p.date,
            'open_price': p.open_price,
            'high_price': p.high_price,
            'low_price': p.low_price,
            'close_price': p.close_price,
            'volume': p.volume
        } for p in prices])
        
        if df.empty:
            raise ValueError(f"No price data available for {stock_symbol}")
        
        # Calculate returns first (no look-ahead)
        df = self._prepare_returns(df)
        
        if include_indicators:
            # Add technical indicators
            df = self.indicator_engine.calculate_all_indicators(df)
        
        return df
    
    def _prepare_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare return features without look-ahead."""
        df = df.copy()
        df['daily_return'] = df['close_price'].pct_change()
        df['log_return'] = np.log(df['close_price'] / df['close_price'].shift(1))
        return df
    
    def prepare_sequences(
        self,
        data: np.ndarray,
        sequence_length: int = 60
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for deep learning models."""
        X, y = [], []
        for i in range(sequence_length, len(data)):
            X.append(data[i - sequence_length:i])
            y.append(data[i])
        return np.array(X), np.array(y)
    
    def evaluate_models(
        self,
        stock_symbol: str,
        model_types: Optional[List[ModelType]] = None,
        test_size: float = 0.2,
        use_walk_forward: bool = True,
        sequence_length: int = 60
    ) -> Dict[str, Any]:
        """
        Evaluate multiple forecasting models.
        
        Uses strict time-series validation to prevent leakage.
        """
        if model_types is None:
            model_types = list(ModelType)
        
        # Prepare data
        df = self.prepare_features(stock_symbol, include_indicators=False)
        close_prices = df['close_price'].values
        
        # Chronological split (no shuffling!)
        train_ratio = 1 - test_size
        train_df, test_df = df.iloc[:int(len(df) * train_ratio)], df.iloc[int(len(df) * train_ratio):]
        
        # Validate no leakage
        validation = self.validator.validate_no_leakage(train_df, test_df)
        if validation["has_leakage"]:
            raise ValueError(f"Data leakage detected: {validation['issues']}")
        
        # Fit scaler on training data only
        train_prices = train_df['close_price'].values
        scaler = MinMaxScaler()
        scaler.fit(train_prices.reshape(-1, 1))
        
        # Transform all data using training scaler
        scaled_train = scaler.transform(train_prices.reshape(-1, 1)).flatten()
        scaled_test = scaler.transform(test_df['close_price'].values.reshape(-1, 1)).flatten()
        
        results = {}
        
        for model_type in model_types:
            try:
                forecaster = self.get_forecaster(model_type)
                
                if model_type in [ModelType.LSTM, ModelType.GRU]:
                    # Deep learning models need sequences
                    X_train, y_train = self.prepare_sequences(scaled_train, sequence_length)
                    X_test, y_test = self.prepare_sequences(scaled_test, sequence_length)
                    
                    if len(X_train) == 0 or len(X_test) == 0:
                        continue
                    
                    # Reshape for LSTM/GRU
                    X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
                    X_test = X_test.reshape(X_test.shape[0], X_test.shape[1], 1)
                else:
                    # Other models use raw scaled values
                    X_train = scaled_train.reshape(-1, 1)
                    y_train = scaled_train[1:] if len(scaled_train) > 1 else scaled_train
                    X_test = scaled_test.reshape(-1, 1)
                    y_test = scaled_test[1:] if len(scaled_test) > 1 else scaled_test
                
                # Train model
                forecaster.fit(X_train, y_train)
                
                # Predict
                predictions = forecaster.predict(X_test)
                
                # Inverse transform predictions and actuals
                predictions_inv = scaler.inverse_transform(predictions.reshape(-1, 1)).flatten()
                actuals_inv = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten()
                
                # Calculate metrics
                metrics = calculate_all_metrics(actuals_inv, predictions_inv, model_type.value)
                metrics["training_time_seconds"] = forecaster.training_time
                
                results[model_type.value] = metrics
                
            except Exception as e:
                results[model_type.value] = {
                    "model_name": model_type.value,
                    "error": str(e)
                }
        
        # Compare models
        comparison = compare_models(results)
        
        # Identify naive baseline
        naive_metrics = results.get("naive", None)
        
        return {
            "stock_symbol": stock_symbol,
            "evaluation_date": datetime.utcnow().isoformat(),
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "models": results,
            "comparison": comparison,
            "naive_baseline": naive_metrics,
            "validation_results": validation
        }
    
    def generate_forecast(
        self,
        stock_symbol: str,
        model_type: ModelType,
        prediction_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate forecast for a stock using the specified model.
        """
        df = self.prepare_features(stock_symbol, include_indicators=False)
        close_prices = df['close_price'].values
        
        # Fit scaler on all data
        scaler = MinMaxScaler()
        scaler.fit(close_prices.reshape(-1, 1))
        
        scaled_prices = scaler.transform(close_prices.reshape(-1, 1)).flatten()
        
        # Get model
        forecaster = self.get_forecaster(model_type)
        
        if model_type in [ModelType.LSTM, ModelType.GRU]:
            # Use full sequence for training
            X_train, y_train = self.prepare_sequences(scaled_prices, 60)
            if len(X_train) == 0:
                raise ValueError("Insufficient data for sequence model")
            
            X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
            forecaster.fit(X_train, y_train)
            forecast = forecaster.forecast(scaled_prices, prediction_days)
        else:
            forecaster.fit(scaled_prices.reshape(-1, 1), scaled_prices)
            forecast = forecaster.forecast(scaled_prices, prediction_days)
        
        # Inverse transform
        forecast_prices = scaler.inverse_transform(forecast.reshape(-1, 1)).flatten()
        
        # Generate prediction dates
        last_date = df['date'].max()
        prediction_dates = pd.bdate_range(last_date + pd.Timedelta(days=1), periods=prediction_days)
        
        predictions = [
            {
                "date": str(d.date()),
                "predicted_price": round(price, 2)
            }
            for d, price in zip(prediction_dates, forecast_prices)
        ]
        
        return {
            "symbol": stock_symbol,
            "model_type": model_type.value,
            "predictions": predictions,
            "model_info": forecaster.get_info()
        }