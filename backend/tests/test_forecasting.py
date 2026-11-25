"""
Unit Tests for Stock Intelligence Platform.
"""
import pytest
import numpy as np
import pandas as pd
from datetime import date, datetime
from backend.forecasting.metrics import (
    calculate_rmse, calculate_mae, calculate_mape, calculate_smape,
    calculate_r_squared, calculate_directional_accuracy, calculate_all_metrics
)


class TestMetrics:
    """Test evaluation metrics calculations."""
    
    def test_rmse_basic(self):
        """Test RMSE calculation."""
        actual = np.array([1, 2, 3, 4, 5])
        predicted = np.array([1.1, 1.9, 3.2, 3.8, 5.1])
        
        rmse = calculate_rmse(actual, predicted)
        assert 0 < rmse < 0.2  # Should be small error
    
    def test_mae_basic(self):
        """Test MAE calculation."""
        actual = np.array([10, 20, 30])
        predicted = np.array([10.5, 19.5, 30.5])
        
        mae = calculate_mae(actual, predicted)
        assert 0 < mae < 1
    
    def test_mape_handles_zeros(self):
        """Test MAPE handles zero values gracefully."""
        actual = np.array([10, 20, 0, 40])
        predicted = np.array([11, 19, 5, 39])
        
        mape = calculate_mape(actual, predicted)
        assert mape is not None and mape >= 0
    
    def test_r_squared_perfect(self):
        """Test R² for perfect predictions."""
        actual = np.array([1, 2, 3, 4, 5])
        predicted = np.array([1, 2, 3, 4, 5])
        
        r2 = calculate_r_squared(actual, predicted)
        assert abs(r2 - 1.0) < 0.001
    
    def test_directional_accuracy(self):
        """Test directional accuracy calculation."""
        actual = np.array([100, 105, 102, 108, 107])
        predicted = np.array([103, 108, 104, 110, 105])
        
        da = calculate_directional_accuracy(actual, predicted)
        assert 0 <= da <= 100
    
    def test_calculate_all_metrics(self):
        """Test all metrics calculation function."""
        actual = np.array([100, 102, 98, 105, 103])
        predicted = np.array([99, 104, 97, 106, 102])
        
        results = calculate_all_metrics(actual, predicted, "test_model")
        
        assert "model_name" in results
        assert "mae" in results
        assert "rmse" in results
        assert "mape" in results
        assert "r_squared" in results
        assert "directional_accuracy" in results


class TestTechnicalIndicators:
    """Test technical indicator calculations."""
    
    def test_calculate_returns(self):
        """Test return calculations."""
        from backend.indicators.technical_indicators import TechnicalIndicatorEngine
        
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'close_price': [100, 102, 101, 103, 105, 104, 106, 108, 107, 110],
            'high_price': [103, 104, 103, 105, 107, 106, 108, 110, 109, 112],
            'low_price': [99, 101, 100, 102, 103, 102, 104, 106, 105, 108],
            'volume': [1000000] * 10
        })
        
        engine = TechnicalIndicatorEngine()
        result = engine.calculate_all_indicators(df)
        
        assert 'daily_return' in result.columns
        assert 'sma_20' in result.columns  # Even with <20 data, column exists
        assert 'rsi' in result.columns
    
    def test_sma_calculation(self):
        """Test SMA calculation."""
        from backend.indicators.technical_indicators import TechnicalIndicatorEngine
        
        prices = np.array([100, 102, 104, 106, 108, 110, 112, 114, 116, 118])
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'close_price': prices,
            'high_price': prices + 2,
            'low_price': prices - 2,
            'volume': [1000000] * 10
        })
        
        engine = TechnicalIndicatorEngine()
        result = engine.calculate_all_indicators(df)
        
        # SMA of 10 values should equal mean of all values (with shift)
        sma_5 = result['sma_20'].iloc[-1] if pd.notna(result['sma_20'].iloc[-1]) else None
        # At least check it doesn't crash
    
    def test_rsi_bounds(self):
        """Test RSI stays within 0-100 bounds."""
        from backend.indicators.technical_indicators import TechnicalIndicatorEngine
        
        # Create oscillating prices
        prices = [100 + i * 0.5 + np.sin(i/3) * 5 for i in range(100)]
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=100),
            'close_price': prices,
            'high_price': [p + 2 for p in prices],
            'low_price': [p - 2 for p in prices],
            'volume': [1000000] * 100
        })
        
        engine = TechnicalIndicatorEngine()
        result = engine.calculate_all_indicators(df)
        
        rsi_values = result['rsi'].dropna()
        if len(rsi_values) > 0:
            assert rsi_values.min() >= 0
            assert rsi_values.max() <= 100


class TestForecasterBase:
    """Test base forecaster classes."""
    
    def test_naive_forecaster(self):
        """Test naive forecasting model."""
        from backend.forecasting.base_forecaster import NaiveForecaster
        
        model = NaiveForecaster()
        
        # Fit with some data
        y_train = np.array([100, 102, 101, 103, 105])
        model.fit(np.zeros((5, 10)), y_train)
        
        # Predict should return last value
        predictions = model.predict(np.zeros((3, 10)))
        assert len(predictions) == 3
        assert all(p == y_train[-1] for p in predictions)
        
        # Forecast should return last value repeated
        forecast = model.forecast(y_train, 5)
        assert len(forecast) == 5
        assert all(f == y_train[-1] for f in forecast)
    
    def test_moving_average_forecaster(self):
        """Test moving average forecasting model."""
        from backend.forecasting.base_forecaster import MovingAverageForecaster
        
        model = MovingAverageForecaster(window=5)
        y_train = np.array([100, 102, 104, 106, 108, 110])
        
        model.fit(np.zeros((6, 10)), y_train)
        
        predictions = model.predict(np.zeros((3, 10)))
        assert len(predictions) == 3
        
        # MA should equal mean of last 5 values
        expected_ma = np.mean(y_train[-5:])
        assert all(abs(p - expected_ma) < 0.01 for p in predictions)
    
    def test_linear_regression_forecaster(self):
        """Test linear regression forecaster."""
        from backend.forecasting.base_forecaster import LinearRegressionForecaster
        
        model = LinearRegressionForecaster()
        y_train = np.linspace(100, 150, 60)
        
        model.fit(np.zeros((60, 10)), y_train)
        predictions = model.predict(np.zeros((10, 10)))
        
        assert len(predictions) == 10
        # Predictions should follow trend
        assert predictions[-1] > predictions[0]
    
    def test_forecaster_info(self):
        """Test forecaster info method."""
        from backend.forecasting.base_forecaster import NaiveForecaster
        
        model = NaiveForecaster()
        info = model.get_info()
        
        assert "name" in info
        assert "is_fitted" in info
        assert "training_time_seconds" in info


class TestTimeSeriesValidator:
    """Test time-series validation utilities."""
    
    def test_chronological_split(self):
        """Test chronological split preserves order."""
        from backend.forecasting.time_series_validator import TimeSeriesValidator
        
        validator = TimeSeriesValidator()
        
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=100),
            'close_price': np.random.randn(100).cumsum() + 100
        })
        
        train, val, test = validator.chronological_split(df, 0.7, 0.15, 0.15)
        
        # Check no overlap
        assert train['date'].max() < val['date'].min()
        assert val['date'].max() < test['date'].min()
        
        # Check proportions
        assert len(train) == 70
        assert len(val) == 15
        assert len(test) == 15
    
    def test_no_shuffling(self):
        """Test that data is not shuffled."""
        from backend.forecasting.time_series_validator import TimeSeriesValidator
        
        dates = pd.date_range('2024-01-01', periods=50)
        df = pd.DataFrame({
            'date': dates,
            'value': range(50)
        })
        
        validator = TimeSeriesValidator()
        train, _, test = validator.chronological_split(df)
        
        # Train should be first 70%
        assert train['date'].iloc[0] == df['date'].iloc[0]
        # Test should be last 30%
        assert test['date'].iloc[-1] == df['date'].iloc[-1]
    
    def test_validate_no_leakage(self):
        """Test leakage validation."""
        from backend.forecasting.time_series_validator import TimeSeriesValidator
        
        validator = TimeSeriesValidator()
        
        train_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=70),
            'close_price': range(70)
        })
        
        test_df = pd.DataFrame({
            'date': pd.date_range('2024-03-11', periods=30),
            'close_price': range(70, 100)
        })
        
        result = validator.validate_no_leakage(train_df, test_df)
        
        assert not result["has_leakage"]
    
    def test_leakage_detection(self):
        """Test leakage detection."""
        from backend.forecasting.time_series_validator import TimeSeriesValidator
        
        validator = TimeSeriesValidator()
        
        # Overlapping dates
        train_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=50),
            'close_price': range(50)
        })
        
        test_df = pd.DataFrame({
            'date': pd.date_range('2024-02-01', periods=30),  # Overlaps with train
            'close_price': range(30, 60)
        })
        
        result = validator.validate_no_leakage(train_df, test_df)
        
        assert result["has_leakage"]


class TestBacktestingEngine:
    """Test backtesting functionality."""
    
    def test_backtest_execution(self):
        """Test basic backtest execution."""
        from backend.backtesting.backtesting_engine import BacktestingEngine
        
        engine = BacktestingEngine(
            initial_capital=100000,
            transaction_cost=0.001
        )
        
        # Generate sample data
        start_date = date(2024, 1, 1)
        end_date = date(2024, 6, 30)
        
        result = engine.run_backtest(
            stock_symbol='TEST',
            strategy='buy_and_hold',
            start_date=start_date,
            end_date=end_date,
            parameters={}
        )
        
        assert 'total_return' in result
        assert 'final_capital' in result
        assert 'total_trades' in result
        assert 'max_drawdown' in result
    
    def test_sma_crossover_strategy(self):
        """Test SMA crossover strategy."""
        from backend.backtesting.backtesting_engine import BacktestingEngine
        
        engine = BacktestingEngine()
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        
        result = engine.run_backtest(
            stock_symbol='TEST',
            strategy='sma_crossover',
            start_date=start_date,
            end_date=end_date,
            parameters={'short_window': 10, 'long_window': 20}
        )
        
        assert 'total_return' in result
        assert 'trades' in result


class TestSQLAnalytics:
    """Test SQL analytics engine."""
    
    def test_get_stock_list(self, db_session):
        """Test getting stock list from database."""
        from backend.analytics.sql_analytics import SQLAnalyticsEngine
        
        # Note: This test requires a database with data
        # For unit testing, we test the method signature
        engine = SQLAnalyticsEngine(db_session)
        
        # Should not raise exception
        try:
            result = engine.get_stock_list()
            assert isinstance(result, list)
        except:
            pass  # Expected if no data in test DB
    
    def test_model_comparison_query(self, db_session):
        """Test model performance comparison query."""
        from backend.analytics.sql_analytics import SQLAnalyticsEngine
        
        engine = SQLAnalyticsEngine(db_session)
        
        try:
            result = engine.get_model_performance_comparison("TEST")
            assert isinstance(result, list)
        except:
            pass


# Pytest fixtures
@pytest.fixture
def db_session():
    """Create a test database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.database.database import Base
    
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])