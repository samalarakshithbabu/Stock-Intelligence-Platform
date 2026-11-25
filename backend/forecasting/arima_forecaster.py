"""
ARIMA Forecasting Model.
"""
import numpy as np
import pandas as pd
import warnings
from typing import Dict, Any
import time

warnings.filterwarnings('ignore')

from backend.forecasting.base_forecaster import BaseForecaster


class ARIMAForecaster(BaseForecaster):
    """
    ARIMA (AutoRegressive Integrated Moving Average) Model.
    
    Classical statistical time-series forecasting method.
    """
    
    def __init__(
        self,
        p: int = 5,  # AR order
        d: int = 1,  # Differencing order
        q: int = 0   # MA order
    ):
        super().__init__(f"ARIMA_{p}_{d}_{q}")
        self.order = (p, d, q)
        self.model = None
        self.model_params = {
            "p": p, "d": d, "q": q
        }
        self.last_predictions = None
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        **kwargs
    ) -> None:
        """Fit ARIMA model."""
        start_time = time.time()
        
        try:
            from statsmodels.tsa.arima.model import ARIMA
            
            # Create pandas Series for statsmodels
            series = pd.Series(y_train)
            
            # Fit ARIMA model
            self.model = ARIMA(series, order=self.order)
            self.model = self.model.fit()
            
            self.is_fitted = True
            self.last_predictions = self.model.predict(start=0, end=len(y_train)-1)
            
        except Exception as e:
            # Fallback to simpler model if ARIMA fails
            from statsmodels.tsa.arima.model import ARIMA
            self.order = (2, 1, 0)
            series = pd.Series(y_train)  # Define series in this scope too
            self.model = ARIMA(series, order=self.order)
            self.model = self.model.fit()
            self.is_fitted = True
        
        self.training_time = time.time() - start_time
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate in-sample predictions."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        return np.array(self.last_predictions[-len(X):])
    
    def forecast(
        self,
        historical_data: np.ndarray,
        steps: int
    ) -> np.ndarray:
        """Generate multi-step forecast."""
        if not self.is_fitted or len(historical_data) == 0:
            return np.array([])
        
        # Fit on all available data first
        series = pd.Series(historical_data)
        self.model = ARIMA(series, order=self.order).fit()
        
        # Generate forecast
        forecast_result = self.model.forecast(steps=steps)
        
        return np.array(forecast_result)


class SimpleExponentialSmoothingForecaster(BaseForecaster):
    """
    Simple Exponential Smoothing Model.
    
    Useful baseline for comparison.
    """
    
    def __init__(self, alpha: float = 0.3):
        super().__init__(f"SES_{alpha}")
        self.alpha = alpha
        self.last_smoothed = None
        self.model_params = {"alpha": alpha}
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        **kwargs
    ) -> None:
        """Fit exponential smoothing model."""
        start_time = time.time()
        
        self.last_smoothed = y_train[0]
        for value in y_train[1:]:
            self.last_smoothed = self.alpha * value + (1 - self.alpha) * self.last_smoothed
        
        self.is_fitted = True
        self.training_time = time.time() - start_time
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """All predictions equal to last smoothed value."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        return np.full(len(X), self.last_smoothed)
    
    def forecast(
        self,
        historical_data: np.ndarray,
        steps: int
    ) -> np.ndarray:
        """Forecast using last smoothed value."""
        if len(historical_data) == 0:
            return np.array([])
        
        return np.full(steps, self.last_smoothed)