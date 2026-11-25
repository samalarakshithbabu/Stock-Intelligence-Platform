"""
Forecasting module initialization.
"""
from backend.forecasting.base_forecaster import (
    BaseForecaster, NaiveForecaster, MovingAverageForecaster,
    LinearRegressionForecaster, RandomForestForecaster, XGBoostForecaster
)
from backend.forecasting.arima_forecaster import ARIMAForecaster
from backend.forecasting.deep_learning import LSTMForecaster, GRUForecaster
from backend.forecasting.forecasting_engine import ForecastingEngine
from backend.forecasting.metrics import calculate_all_metrics, compare_models
from backend.forecasting.time_series_validator import TimeSeriesValidator

__all__ = [
    "BaseForecaster", "NaiveForecaster", "MovingAverageForecaster",
    "LinearRegressionForecaster", "RandomForestForecaster", "XGBoostForecaster",
    "ARIMAForecaster", "LSTMForecaster", "GRUForecaster",
    "ForecastingEngine", "calculate_all_metrics", "compare_models",
    "TimeSeriesValidator"
]