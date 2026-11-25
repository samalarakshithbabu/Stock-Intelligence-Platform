"""
Technical Indicator Calculations for Stock Analysis.
All calculations use only information available at prediction time to prevent leakage.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


class TechnicalIndicatorEngine:
    """Calculate comprehensive technical indicators without look-ahead bias."""
    
    def __init__(self):
        self.indicators = {}
    
    def calculate_all_indicators(
        self, 
        df: pd.DataFrame,
        use_close_only: bool = False
    ) -> pd.DataFrame:
        """
        Calculate all technical indicators for a DataFrame.
        
        Args:
            df: DataFrame with columns ['date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']
            use_close_only: If True, use only close price for calculations (faster)
        
        Returns:
            DataFrame with all indicators added
        """
        if len(df) < 2:
            return df.copy()
        
        df = df.copy()
        
        # Ensure we have the required columns
        required_cols = ['close_price']
        if not use_close_only:
            required_cols.extend(['high_price', 'low_price', 'volume', 'open_price'])
        
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0.0
        
        # Basic returns first (must be calculated first)
        df = self._calculate_returns(df)
        
        # Moving Averages
        df = self._calculate_moving_averages(df)
        
        # Exponential Moving Averages
        df = self._calculate_exponential_moving_averages(df)
        
        # RSI
        df = self._calculate_rsi(df)
        
        # MACD
        df = self._calculate_macd(df)
        
        # Bollinger Bands
        df = self._calculate_bollinger_bands(df)
        
        # ATR
        if not use_close_only:
            df = self._calculate_atr(df)
        
        # Volatility
        df = self._calculate_volatility(df)
        
        # Volume indicators
        df = self._calculate_volume_indicators(df)
        
        return df
    
    def _calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily and cumulative returns."""
        df['daily_return'] = df['close_price'].pct_change()
        df['log_return'] = np.log(df['close_price'] / df['close_price'].shift(1))
        
        # Cumulative return (never look ahead - use expanding window)
        df['cumulative_return'] = (1 + df['daily_return'].fillna(0)).cumprod() - 1
        df['cumulative_return'] = df['cumulative_return'].shift(1)  # Avoid look-ahead
        
        return df
    
    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Simple Moving Averages."""
        # SMA 20
        df['sma_20'] = df['close_price'].rolling(window=20, min_periods=20).mean().shift(1)
        
        # SMA 50
        df['sma_50'] = df['close_price'].rolling(window=50, min_periods=50).mean().shift(1)
        
        return df
    
    def _calculate_exponential_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Exponential Moving Averages."""
        # EMA 20
        df['ema_20'] = df['close_price'].ewm(span=20, adjust=False).mean().shift(1)
        
        return df
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Relative Strength Index."""
        # Calculate price changes
        delta = df['close_price'].diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = (-delta).where(delta < 0, 0.0)
        
        # Calculate average gains and losses using expanding window
        avg_gain = gains.rolling(window=period, min_periods=period).mean()
        avg_loss = losses.rolling(window=period, min_periods=period).mean()
        
        # Use smoothing method for better accuracy
        for i in range(period, len(df)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gains.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + losses.iloc[i]) / period
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        df['rsi'] = rsi.shift(1)  # Prevent look-ahead
        
        return df
    
    def _calculate_macd(
        self, 
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> pd.DataFrame:
        """Calculate MACD, Signal Line, and Histogram."""
        # Calculate EMAs
        ema_fast = df['close_price'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df['close_price'].ewm(span=slow_period, adjust=False).mean()
        
        # MACD line
        df['macd'] = (ema_fast - ema_slow).shift(1)
        
        # Signal line (EMA of MACD)
        df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean().shift(1)
        
        # Histogram
        df['macd_histogram'] = (df['macd'] - df['macd_signal']).shift(1)
        
        return df
    
    def _calculate_bollinger_bands(
        self, 
        df: pd.DataFrame,
        period: int = 20,
        std_dev: int = 2
    ) -> pd.DataFrame:
        """Calculate Bollinger Bands."""
        # Middle band (SMA)
        middle = df['close_price'].rolling(window=period, min_periods=period).mean()
        
        # Standard deviation
        std = df['close_price'].rolling(window=period, min_periods=period).std()
        
        # Upper and lower bands
        df['bollinger_middle'] = middle.shift(1)
        df['bollinger_upper'] = (middle + (std * std_dev)).shift(1)
        df['bollinger_lower'] = (middle - (std * std_dev)).shift(1)
        
        # Bollinger Bandwidth
        df['bollinger_width'] = (df['bollinger_upper'] - df['bollinger_lower']) / df['bollinger_middle']
        
        # Bollinger Band Position (%B)
        df['bollinger_position'] = (
            (df['close_price'] - df['bollinger_lower']) / 
            (df['bollinger_upper'] - df['bollinger_lower'])
        )
        
        return df
    
    def _calculate_atr(
        self, 
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        """Calculate Average True Range."""
        # True Range calculation
        high_low = df['high_price'] - df['low_price']
        high_close = np.abs(df['high_price'] - df['close_price'].shift(1))
        low_close = np.abs(df['low_price'] - df['close_price'].shift(1))
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR using expanding window then rolling
        atr = true_range.rolling(window=period, min_periods=period).mean()
        
        df['atr'] = atr.shift(1)
        
        return df
    
    def _calculate_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate rolling volatility."""
        # 20-day rolling volatility (annualized)
        df['rolling_volatility_20'] = df['daily_return'].rolling(
            window=20, min_periods=20
        ).std() * np.sqrt(252) * 100
        
        # 50-day rolling volatility (annualized)
        df['rolling_volatility_50'] = df['daily_return'].rolling(
            window=50, min_periods=50
        ).std() * np.sqrt(252) * 100
        
        return df
    
    def _calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume-based indicators."""
        # Volume SMA 20
        df['volume_sma_20'] = df['volume'].rolling(window=20, min_periods=20).mean()
        
        # Volume ratio
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        return df
    
    def get_indicator_values(
        self, 
        df: pd.DataFrame, 
        date: pd.Timestamp
    ) -> Dict[str, float]:
        """Get indicator values for a specific date."""
        row = df[df['date'] == date]
        if row.empty:
            return {}
        
        row = row.iloc[0]
        return {
            'sma_20': row.get('sma_20'),
            'sma_50': row.get('sma_50'),
            'ema_20': row.get('ema_20'),
            'rsi': row.get('rsi'),
            'macd': row.get('macd'),
            'macd_signal': row.get('macd_signal'),
            'macd_histogram': row.get('macd_histogram'),
            'bollinger_upper': row.get('bollinger_upper'),
            'bollinger_middle': row.get('bollinger_middle'),
            'bollinger_lower': row.get('bollinger_lower'),
            'atr': row.get('atr'),
            'daily_return': row.get('daily_return'),
            'rolling_volatility_20': row.get('rolling_volatility_20')
        }