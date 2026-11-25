"""
Time-Series Validation Module.

Implements strict validation strategies to prevent data leakage:
- Chronological train/validation/test splits
- Walk-forward validation
- Scaler fitting only on training data
- No future information in technical indicators
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from sklearn.preprocessing import MinMaxScaler, StandardScaler


class TimeSeriesValidator:
    """
    Implements leakage-free time-series validation strategies.
    """
    
    def __init__(self):
        self.train_indices = None
        self.val_indices = None
        self.test_indices = None
        self.scaler = None
    
    def chronological_split(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data chronologically without shuffling.
        
        Args:
            data: DataFrame sorted by date
            train_ratio: Proportion of data for training
            val_ratio: Proportion for validation
            test_ratio: Proportion for testing
        
        Returns:
            Tuple of (train, validation, test) DataFrames
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001, \
            "Ratios must sum to 1"
        
        n = len(data)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        train = data.iloc[:train_end].copy()
        val = data.iloc[train_end:val_end].copy()
        test = data.iloc[val_end:].copy()
        
        self.train_indices = (0, train_end)
        self.val_indices = (train_end, val_end)
        self.test_indices = (val_end, n)
        
        return train, val, test
    
    def walk_forward_split(
        self,
        data: pd.DataFrame,
        train_window: int = 252,  # 1 year of trading days
        test_window: int = 21,    # ~1 month
        min_train_samples: int = 252
    ) -> list:
        """
        Generate walk-forward validation splits.
        
        Args:
            data: DataFrame sorted by date
            train_window: Number of training samples
            test_window: Number of test samples per split
            min_train_samples: Minimum training samples required
        
        Returns:
            List of (train, test) tuples
        """
        splits = []
        data = data.reset_index(drop=True)
        
        i = min_train_samples
        while i + test_window <= len(data):
            train = data.iloc[i - train_window:i].copy()
            test = data.iloc[i:i + test_window].copy()
            
            if len(test) >= 1:
                splits.append((train, test))
            
            i += test_window
        
        return splits
    
    def fit_scaler_on_train(
        self,
        train_data: np.ndarray,
        scaler_type: str = "minmax"
    ) -> MinMaxScaler:
        """
        Fit scaler exclusively on training data to prevent leakage.
        
        Args:
            train_data: Training data array
            scaler_type: 'minmax' or 'standard'
        
        Returns:
            Fitted scaler
        """
        if scaler_type == "minmax":
            self.scaler = MinMaxScaler()
        else:
            self.scaler = StandardScaler()
        
        # Reshape for scaler (requires 2D input)
        self.scaler.fit(train_data.reshape(-1, 1))
        
        return self.scaler
    
    def transform_with_train_scaler(
        self, 
        data: np.ndarray
    ) -> np.ndarray:
        """
        Transform data using scaler fitted on training data.
        
        Args:
            data: Data to transform
        
        Returns:
            Transformed data
        """
        if self.scaler is None:
            raise ValueError("Scaler not fitted. Call fit_scaler_on_train first.")
        
        return self.scaler.transform(data.reshape(-1, 1))
    
    def inverse_transform_with_train_scaler(
        self, 
        data: np.ndarray
    ) -> np.ndarray:
        """
        Inverse transform using scaler fitted on training data.
        
        Args:
            data: Data to inverse transform
        
        Returns:
            Inverse transformed data
        """
        if self.scaler is None:
            raise ValueError("Scaler not fitted. Call fit_scaler_on_train first.")
        
        return self.scaler.inverse_transform(data.reshape(-1, 1))
    
    def create_sequences(
        self,
        data: np.ndarray,
        seq_length: int = 60
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM/GRU models without leakage.
        
        Args:
            data: Time series data
            seq_length: Length of input sequences
        
        Returns:
            X (sequences), y (targets)
        """
        X, y = [], []
        for i in range(seq_length, len(data)):
            X.append(data[i - seq_length:i])
            y.append(data[i])
        
        return np.array(X), np.array(y)
    
    def validate_no_leakage(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Verify no data leakage between train and test sets.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "has_leakage": False,
            "issues": [],
            "train_date_range": None,
            "test_date_range": None
        }
        
        if len(train_df) == 0 or len(test_df) == 0:
            results["has_leakage"] = True
            results["issues"].append("Empty train or test set")
            return results
        
        train_dates = train_df['date']
        test_dates = test_df['date']
        
        results["train_date_range"] = {
            "start": str(train_dates.min()),
            "end": str(train_dates.max())
        }
        results["test_date_range"] = {
            "start": str(test_dates.min()),
            "end": str(test_dates.max())
        }
        
        # Check chronological order
        if train_dates.max() >= test_dates.min():
            results["has_leakage"] = True
            results["issues"].append("Test data starts before training data ends")
        
        # Check for overlapping dates
        train_set = set(train_dates)
        test_set = set(test_dates)
        overlap = train_set & test_set
        
        if overlap:
            results["has_leakage"] = True
            results["issues"].append(f"Overlapping dates found: {len(overlap)}")
        
        # Check for future data in test
        if len(test_df) > 0:
            last_train_date = train_dates.max()
            first_test_date = test_dates.min()
            
            if pd.to_datetime(first_test_date) <= pd.to_datetime(last_train_date):
                results["has_leakage"] = True
                results["issues"].append("Test data contains dates from training period")
        
        return results
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get detailed validation report."""
        return {
            "train_indices": self.train_indices,
            "val_indices": self.val_indices,
            "test_indices": self.test_indices,
            "scaler_fitted": self.scaler is not None
        }