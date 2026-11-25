"""
Deep Learning Forecasting Models: LSTM and GRU.
"""
import numpy as np
import warnings
from typing import Dict, Any
import time

warnings.filterwarnings('ignore')

from backend.forecasting.base_forecaster import BaseForecaster


class LSTMForecaster(BaseForecaster):
    """
    LSTM (Long Short-Term Memory) Neural Network.
    
    Deep learning model for sequential data prediction.
    Uses sequence-to-value architecture.
    """
    
    def __init__(
        self,
        sequence_length: int = 60,
        lstm_units: int = 50,
        dropout_rate: float = 0.2,
        epochs: int = 50,
        batch_size: int = 32
    ):
        super().__init__(f"LSTM_{lstm_units}_{dropout_rate}")
        self.sequence_length = sequence_length
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.model_params = {
            "sequence_length": sequence_length,
            "lstm_units": lstm_units,
            "dropout_rate": dropout_rate,
            "epochs": epochs,
            "batch_size": batch_size
        }
    
    def _build_model(self, input_shape: tuple):
        """Build LSTM architecture."""
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        
        model = Sequential([
            LSTM(self.lstm_units, return_sequences=True, 
                 input_shape=input_shape),
            Dropout(self.dropout_rate),
            
            LSTM(self.lstm_units, return_sequences=True),
            Dropout(self.dropout_rate),
            
            LSTM(self.lstm_units),
            Dropout(self.dropout_rate),
            
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        
        return model
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        **kwargs
    ) -> None:
        """Train LSTM model."""
        start_time = time.time()
        
        import tensorflow as tf
        tf.get_logger().setLevel('ERROR')
        
        # Build model
        input_shape = (X_train.shape[1], X_train.shape[2])
        self.model = self._build_model(input_shape)
        
        # Train
        self.model.fit(
            X_train, y_train,
            epochs=self.epochs,
            batch_size=self.batch_size,
            validation_split=0.1,
            verbose=0
        )
        
        self.is_fitted = True
        self.training_time = time.time() - start_time
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        return self.model.predict(X, verbose=0).flatten()
    
    def forecast(
        self,
        historical_data: np.ndarray,
        steps: int
    ) -> np.ndarray:
        """Generate multi-step forecast with recursive prediction."""
        if not self.is_fitted or len(historical_data) == 0:
            return np.array([])
        
        predictions = []
        current_sequence = historical_data[-self.sequence_length:].copy()
        
        for _ in range(steps):
            X_pred = current_sequence.reshape(1, -1, 1)
            pred = self.predict(X_pred)[0]
            predictions.append(pred)
            current_sequence = np.append(current_sequence[1:], pred)
        
        return np.array(predictions)


class GRUForecaster(BaseForecaster):
    """
    GRU (Gated Recurrent Unit) Neural Network.
    
    Simpler alternative to LSTM with fewer parameters.
    """
    
    def __init__(
        self,
        sequence_length: int = 60,
        gru_units: int = 50,
        dropout_rate: float = 0.2,
        epochs: int = 50,
        batch_size: int = 32
    ):
        super().__init__(f"GRU_{gru_units}_{dropout_rate}")
        self.sequence_length = sequence_length
        self.gru_units = gru_units
        self.dropout_rate = dropout_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.model_params = {
            "sequence_length": sequence_length,
            "gru_units": gru_units,
            "dropout_rate": dropout_rate,
            "epochs": epochs,
            "batch_size": batch_size
        }
    
    def _build_model(self, input_shape: tuple):
        """Build GRU architecture."""
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import GRU, Dense, Dropout
        
        model = Sequential([
            GRU(self.gru_units, return_sequences=True,
                input_shape=input_shape),
            Dropout(self.dropout_rate),
            
            GRU(self.gru_units, return_sequences=True),
            Dropout(self.dropout_rate),
            
            GRU(self.gru_units),
            Dropout(self.dropout_rate),
            
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        
        return model
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        **kwargs
    ) -> None:
        """Train GRU model."""
        start_time = time.time()
        
        import tensorflow as tf
        tf.get_logger().setLevel('ERROR')
        
        # Build model
        input_shape = (X_train.shape[1], X_train.shape[2])
        self.model = self._build_model(input_shape)
        
        # Train
        self.model.fit(
            X_train, y_train,
            epochs=self.epochs,
            batch_size=self.batch_size,
            validation_split=0.1,
            verbose=0
        )
        
        self.is_fitted = True
        self.training_time = time.time() - start_time
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        return self.model.predict(X, verbose=0).flatten()
    
    def forecast(
        self,
        historical_data: np.ndarray,
        steps: int
    ) -> np.ndarray:
        """Generate multi-step forecast with recursive prediction."""
        if not self.is_fitted or len(historical_data) == 0:
            return np.array([])
        
        predictions = []
        current_sequence = historical_data[-self.sequence_length:].copy()
        
        for _ in range(steps):
            X_pred = current_sequence.reshape(1, -1, 1)
            pred = self.predict(X_pred)[0]
            predictions.append(pred)
            current_sequence = np.append(current_sequence[1:], pred)
        
        return np.array(predictions)