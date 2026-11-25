"""
Base Forecaster Class.

Abstract base class for all forecasting models.
Ensures consistent interface and leakage prevention.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
import time


class BaseForecaster(ABC):
    """Abstract base class for stock price forecasting models."""
    
    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False
        self.training_time = 0
        self.feature_importance = None
        self.model_params = {}
    
    @abstractmethod
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        **kwargs
    ) -> None:
        """Train the model on training data."""
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions."""
        pass
    
    @abstractmethod
    def forecast(
        self,
        historical_data: np.ndarray,
        steps: int
    ) -> np.ndarray:
        """Generate multi-step forecast."""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "name": self.name,
            "is_fitted": self.is_fitted,
            "training_time_seconds": self.training_time,
            "parameters": self.model_params
        }


class NaiveForecaster(BaseForecaster):
    """
    Naive Forecasting Model.
    
    Tomorrow's predicted price = Today's actual price.
    
    This is the essential baseline - if your sophisticated model
    can't beat this, it's not adding value.
    """
    
    def __init__(self):
        super().__init__("Naive")
        self.last_value = None
    
    def fit(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        **kwargs
    ) -> None:
        """Naive model requires no training - just stores last known value."""
        start_time = time.time()
        
        self.last_value = y_train[-1] if len(y_train) > 0 else None
        self.is_fitted = True
        
        self.training_time = time.time() - start_time
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using last known value."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        if self.last_value is None:
            raise ValueError("No historical data available")
        
        return np.full(len(X), self.last_value)
    
    def forecast(
        self,
        historical_data: np.ndarray,
        steps: int
    ) -> np.ndarray:
        """
        Generate forecast using naive method.
        
        All future predictions equal to the last observed value.
        """
        if len(historical_data) == 0:
            return np.array([])
        
        last_value = historical_data[-1]
        return np.full(steps, last_value)


class MovingAverageForecaster(BaseForecaster):
    """
    Moving Average Forecasting Model.
    
    Predicts future prices based on the moving average of recent observations.
    """
    
    def __init__(self, window: int = 20):
        super().__init__(f"MovingAverage_{window}")
        self.window = window
        self.ma_value = None
    
    def fit(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        **kwargs
    ) -> None:
        """Calculate moving average from training data."""
        start_time = time.time()
        
        self.ma_value = np.mean(y_train[-self.window:]) if len(y_train) >= self.window else np.mean(y_train)
        self.is_fitted = True
        
        self.training_time = time.time() - start_time
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the calculated moving average."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        return np.full(len(X), self.ma_value)
    
    def forecast(
        self,
        historical_data: np.ndarray,
        steps: int
    ) -> np.ndarray:
        """Forecast using moving average."""
        if len(historical_data) == 0:
            return np.array([])
        
        # Use last 'window' observations for MA
        window_data = historical_data[-self.window:]
        ma = np.mean(window_data)
        
        return np.full(steps, ma)


class LinearRegressionForecaster(BaseForecaster):
    """
    Linear Regression Forecasting Model.
    
    Uses linear regression with time-based features.
    """
    
    def __init__(self):
        super().__init__("LinearRegression")
        from sklearn.linear_model import LinearRegression as LR
        self.model = LR()
    
    def fit(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        **kwargs
    ) -> None:
        """Train linear regression model."""
        start_time = time.time()
        
        self.model.fit(X_train.reshape(-1, 1) if X_train.ndim == 1 else X_train, y_train)
        self.is_fitted = True
        self.training_time = time.time() - start_time
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        X_input = X.reshape(-1, 1) if X.ndim == 1 else X
        return self.model.predict(X_input)
    
    def forecast(
        self,
        historical_data: np.ndarray,
        steps: int
    ) -> np.ndarray:
        """Generate multi-step forecast using trend extrapolation."""
        if not self.is_fitted or len(historical_data) == 0:
            return np.array([])
        
        # Create time indices for extrapolation
        X_train = np.arange(len(historical_data)).reshape(-1, 1)
        
        # Fit on actual historical data
        self.model.fit(X_train, historical_data)
        
        # Predict future steps
        X_future = np.arange(len(historical_data), len(historical_data) + steps).reshape(-1, 1)
        return self.model.predict(X_future).flatten()


class RandomForestForecaster(BaseForecaster):
    """
    Random Forest Forecasting Model.
    
    Uses ensemble of decision trees for prediction.
    """
    
    def __init__(
        self, 
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42
    ):
        super().__init__(f"RandomForest_{n_estimators}_{max_depth}")
        self.model_params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "random_state": random_state
        }
        
        from sklearn.ensemble import RandomForestRegressor
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )
    
    def fit(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        **kwargs
    ) -> None:
        """Train random forest model."""
        start_time = time.time()
        
        X_flat = X_train.reshape(X_train.shape[0], -1)
        self.model.fit(X_flat, y_train)
        
        self.is_fitted = True
        self.training_time = time.time() - start_time
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        X_flat = X.reshape(X.shape[0], -1)
        return self.model.predict(X_flat)
    
    def forecast(
        self,
        historical_data: np.ndarray,
        steps: int
    ) -> np.ndarray:
        """Generate forecast using recursive prediction."""
        if not self.is_fitted or len(historical_data) == 0:
            return np.array([])
        
        predictions = []
        current_sequence = historical_data[-60:].tolist()  # Assume 60-day window
        
        for _ in range(steps):
            X_pred = np.array(current_sequence[-60:]).reshape(1, -1)
            pred = self.predict(X_pred)[0]
            predictions.append(pred)
            current_sequence.append(pred)
        
        return np.array(predictions)


class XGBoostForecaster(BaseForecaster):
    """
    XGBoost Forecasting Model.
    
    Uses gradient boosting for prediction.
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        random_state: int = 42
    ):
        super().__init__(f"XGBoost_{n_estimators}_{max_depth}")
        self.model_params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "random_state": random_state
        }
        
        import xgboost as xgb
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            n_jobs=-1
        )
    
    def fit(
        self, 
        X_train: np.ndarray, 
        y_train: np.ndarray,
        **kwargs
    ) -> None:
        """Train XGBoost model."""
        start_time = time.time()
        
        X_flat = X_train.reshape(X_train.shape[0], -1)
        self.model.fit(X_flat, y_train)
        
        self.is_fitted = True
        self.training_time = time.time() - start_time
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        X_flat = X.reshape(X.shape[0], -1)
        return self.model.predict(X_flat)
    
    def forecast(
        self,
        historical_data: np.ndarray,
        steps: int
    ) -> np.ndarray:
        """Generate forecast using recursive prediction."""
        if not self.is_fitted or len(historical_data) == 0:
            return np.array([])
        
        predictions = []
        current_sequence = historical_data[-60:].tolist()
        
        for _ in range(steps):
            X_pred = np.array(current_sequence[-60:]).reshape(1, -1)
            pred = self.predict(X_pred)[0]
            predictions.append(pred)
            current_sequence.append(pred)
        
        return np.array(predictions)