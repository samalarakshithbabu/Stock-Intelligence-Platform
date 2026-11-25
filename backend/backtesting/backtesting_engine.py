"""
Backtesting Engine for Historical Strategy Evaluation.

Implements educational trading strategy simulations:
- Moving Average Crossover
- RSI-based Strategy
- MACD-based Strategy
- Buy-and-Hold Benchmark

Prevents look-ahead bias using chronological data.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import date, datetime
import numpy as np
import pandas as pd

from backend.database.models import Stock, HistoricalPrice, BacktestResult
from backend.indicators.technical_indicators import TechnicalIndicatorEngine


@dataclass
class Trade:
    """Represents a single trade in backtesting."""
    date: date
    action: str  # "buy" or "sell"
    price: float
    quantity: float
    total: float
    cost: float = 0.0
    cumulative_capital: float = 0.0


@dataclass
class BacktestStats:
    """Backtesting statistics."""
    # Returns
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    
    # Risk
    max_drawdown: float
    max_drawdown_duration: int
    sharpe_ratio: float
    sortino_ratio: float
    volatility: float
    
    # Trading stats
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_trade_return: float
    avg_winning_trade: float
    avg_losing_trade: float
    
    # Costs
    total_transaction_costs: float
    
    # Equity curve
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)


class BacktestingEngine:
    """
    Historical strategy evaluation engine.
    
    Important: All strategies are historical simulations only.
    Past performance does not guarantee future results.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        transaction_cost: float = 0.001,
        slippage: float = 0.0005
    ):
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        self.indicator_engine = TechnicalIndicatorEngine()
    
    def run_backtest(
        self,
        stock_symbol: str,
        strategy: str,
        start_date: date,
        end_date: date,
        parameters: Optional[Dict[str, Any]] = None,
        db_session=None
    ) -> Dict[str, Any]:
        """
        Execute backtest for a given strategy.
        
        Args:
            stock_symbol: Stock ticker symbol
            strategy: Strategy name (sma_crossover, rsi, macd, buy_and_hold)
            start_date: Backtest start date
            end_date: Backtest end date
            parameters: Strategy-specific parameters
            db_session: Database session for saving results
        
        Returns:
            Backtest results dictionary
        """
        parameters = parameters or {}
        
        # Get price data
        df = self._get_price_data(stock_symbol, start_date, end_date, db_session)
        
        if df.empty:
            raise ValueError(f"No data available for {stock_symbol}")
        
        # Calculate indicators
        df = self.indicator_engine.calculate_all_indicators(df)
        
        # Apply strategy
        if strategy == "sma_crossover":
            signals = self._sma_crossover_strategy(df, parameters)
        elif strategy == "rsi":
            signals = self._rsi_strategy(df, parameters)
        elif strategy == "macd":
            signals = self._macd_strategy(df, parameters)
        elif strategy == "buy_and_hold":
            signals = self._buy_and_hold_strategy(df)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Execute trades and calculate returns
        stats = self._execute_trades(df, signals)
        
        # Create result
        result = {
            "symbol": stock_symbol,
            "strategy": strategy,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "initial_capital": stats.initial_capital,
            "final_capital": stats.final_capital,
            "total_return": round(stats.total_return * 100, 2),
            "annualized_return": round(stats.annualized_return * 100, 2),
            "max_drawdown": round(stats.max_drawdown * 100, 2),
            "sharpe_ratio": round(stats.sharpe_ratio, 2),
            "volatility": round(stats.volatility * 100, 2),
            "total_trades": stats.total_trades,
            "win_rate": round(stats.win_rate * 100, 2),
            "avg_trade_return": round(stats.avg_trade_return * 100, 2),
            "total_transaction_costs": round(stats.total_transaction_costs, 2),
            "trades": [
                {
                    "date": str(t.date),
                    "action": t.action,
                    "price": round(t.price, 2),
                    "quantity": round(t.quantity, 2),
                    "total": round(t.total, 2)
                }
                for t in stats.trades
            ],
            "equity_curve": stats.equity_curve
        }
        
        # Save to database
        if db_session:
            self._save_result(stock_symbol, strategy, start_date, end_date, parameters, stats, db_session)
        
        return result
    
    def _get_price_data(
        self,
        stock_symbol: str,
        start_date: date,
        end_date: date,
        db_session=None
    ) -> pd.DataFrame:
        """Get price data from database or create sample data."""
        if db_session:
            try:
                from sqlalchemy import and_
                stock = db_session.query(Stock).filter(Stock.symbol == stock_symbol).first()
                if stock:
                    prices = db_session.query(HistoricalPrice).filter(
                        and_(
                            HistoricalPrice.stock_id == stock.id,
                            HistoricalPrice.date >= start_date,
                            HistoricalPrice.date <= end_date
                        )
                    ).order_by(HistoricalPrice.date).all()
                    
                    if prices:
                        return pd.DataFrame([{
                            'date': p.date,
                            'open_price': p.open_price,
                            'high_price': p.high_price,
                            'low_price': p.low_price,
                            'close_price': p.close_price,
                            'volume': p.volume
                        } for p in prices])
            except:
                pass
        
        # Generate sample data for demonstration
        return self._generate_sample_data(start_date, end_date)
    
    def _generate_sample_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Generate sample price data for testing."""
        dates = pd.bdate_range(start_date, end_date)
        n = len(dates)
        
        # Start with a base price and add random walk
        np.random.seed(42)  # Reproducible
        base_price = 100.0
        returns = np.random.normal(0.0003, 0.015, n)  # Slight positive drift
        price_changes = np.cumprod(1 + returns)
        close_prices = base_price * price_changes
        
        # Generate OHLC from close prices
        df = pd.DataFrame({
            'date': dates,
            'close_price': close_prices,
            'open_price': close_prices * (1 + np.random.uniform(-0.005, 0.005, n)),
            'high_price': close_prices * (1 + np.abs(np.random.uniform(0, 0.01, n))),
            'low_price': close_prices * (1 - np.abs(np.random.uniform(0, 0.01, n))),
            'volume': np.random.randint(1000000, 10000000, n)
        })
        
        # Ensure high >= open >= close >= low
        for i, row in df.iterrows():
            o, h, l, c = row['open_price'], row['high_price'], row['low_price'], row['close_price']
            prices = sorted([o, h, l, c])
            df.at[i, 'low_price'] = prices[0]
            df.at[i, 'close_price'] = prices[1]
            df.at[i, 'open_price'] = prices[2]
            df.at[i, 'high_price'] = prices[3]
        
        return df
    
    def _sma_crossover_strategy(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.Series:
        """
        Moving Average Crossover Strategy.
        
        Buy when short SMA crosses above long SMA.
        Sell when short SMA crosses below long SMA.
        """
        short_window = params.get('short_window', 20)
        long_window = params.get('long_window', 50)
        
        sma_short = df['close_price'].rolling(short_window).mean()
        sma_long = df['close_price'].rolling(long_window).mean()
        
        # Generate signals
        signals = pd.Series(0, index=df.index)
        
        # Previous crossover state
        above = sma_short > sma_long
        
        # Signal changes
        for i in range(1, len(df)):
            if above.iloc[i] and not above.iloc[i-1]:
                signals.iloc[i] = 1  # Buy signal
            elif not above.iloc[i] and above.iloc[i-1]:
                signals.iloc[i] = -1  # Sell signal
        
        return signals
    
    def _rsi_strategy(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.Series:
        """
        RSI-based Strategy.
        
        Buy when RSI crosses below oversold threshold.
        Sell when RSI crosses above overbought threshold.
        """
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        
        rsi = df['rsi']
        
        signals = pd.Series(0, index=df.index)
        
        for i in range(1, len(df)):
            # Buy on oversold bounce
            if rsi.iloc[i] > oversold and rsi.iloc[i-1] <= oversold:
                signals.iloc[i] = 1
            # Sell on overbought reversal
            elif rsi.iloc[i] < overbought and rsi.iloc[i-1] >= overbought:
                signals.iloc[i] = -1
        
        return signals
    
    def _macd_strategy(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.Series:
        """
        MACD-based Strategy.
        
        Buy when MACD crosses above signal line.
        Sell when MACD crosses below signal line.
        """
        macd = df['macd']
        signal = df['macd_signal']
        
        signals = pd.Series(0, index=df.index)
        
        for i in range(1, len(df)):
            # Buy when MACD crosses above signal
            if macd.iloc[i] > signal.iloc[i] and macd.iloc[i-1] <= signal.iloc[i-1]:
                signals.iloc[i] = 1
            # Sell when MACD crosses below signal
            elif macd.iloc[i] < signal.iloc[i] and macd.iloc[i-1] >= signal.iloc[i-1]:
                signals.iloc[i] = -1
        
        return signals
    
    def _buy_and_hold_strategy(self, df: pd.DataFrame) -> pd.Series:
        """Buy and Hold Strategy - simple benchmark."""
        signals = pd.Series(0, index=df.index)
        signals.iloc[0] = 1  # Buy on first day
        return signals
    
    def _execute_trades(
        self,
        df: pd.DataFrame,
        signals: pd.Series
    ) -> BacktestStats:
        """Execute trades based on signals and calculate statistics."""
        capital = self.initial_capital
        position = 0  # Number of shares held
        cash = capital
        entry_price = 0
        trades = []
        equity_curve = []
        max_capital = capital
        drawdown_duration = 0
        max_drawdown_duration = 0
        
        # Track drawdown
        peak_capital = capital
        
        for i in range(len(df)):
            date = df['date'].iloc[i]
            price = df['close_price'].iloc[i]
            
            signal = signals.iloc[i]
            
            # Execute trades
            if signal == 1 and position == 0:  # Buy
                # Account for slippage and transaction cost
                buy_price = price * (1 + self.slippage)
                transaction = cash / (1 + self.transaction_cost)
                position = transaction
                cost = transaction * price * self.transaction_cost
                cash = 0
                entry_price = buy_price
                
                trades.append(Trade(
                    date=date,
                    action="buy",
                    price=buy_price,
                    quantity=position,
                    total=position * buy_price,
                    cost=cost,
                    cumulative_capital=capital
                ))
            
            elif signal == -1 and position > 0:  # Sell
                # Account for slippage and transaction cost
                sell_price = price * (1 - self.slippage)
                proceeds = position * sell_price * (1 - self.transaction_cost)
                cost = position * sell_price * self.transaction_cost
                cash = proceeds
                
                trades.append(Trade(
                    date=date,
                    action="sell",
                    price=sell_price,
                    quantity=position,
                    total=proceeds,
                    transaction_cost=cost,
                    cumulative_capital=capital
                ))
                
                position = 0
            
            # Calculate current capital
            if position > 0:
                current_capital = cash + position * price
            else:
                current_capital = cash
            
            # Track max drawdown
            if current_capital > peak_capital:
                peak_capital = current_capital
            
            drawdown = (peak_capital - current_capital) / peak_capital
            
            if drawdown > 0:
                drawdown_duration += 1
            else:
                max_drawdown_duration = max(max_drawdown_duration, drawdown_duration)
                drawdown_duration = 0
            
            equity_curve.append({
                "date": str(date),
                "capital": round(current_capital, 2),
                "drawdown": round(drawdown * 100, 2)
            })
        
        # Final capital
        if position > 0:
            final_capital = cash + position * df['close_price'].iloc[-1]
        else:
            final_capital = cash
        
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        # Calculate trading statistics
        winning_trades = sum(1 for t in trades if t.action == "sell" and t.total > t.quantity * entry_price)
        losing_trades = len([t for t in trades if t.action == "sell"]) - winning_trades
        
        # Calculate trade returns
        trade_returns = []
        for i in range(0, len(trades) - 1, 2):
            if trades[i].action == "buy" and trades[i + 1].action == "sell":
                buy_total = trades[i].total
                sell_total = trades[i + 1].total
                ret = (sell_total - buy_total) / buy_total
                trade_returns.append(ret)
        
        avg_trade_return = np.mean(trade_returns) if trade_returns else 0
        avg_winning_trade = np.mean([r for r in trade_returns if r > 0]) if trade_returns else 0
        avg_losing_trade = np.mean([r for r in trade_returns if r < 0]) if trade_returns else 0
        
        # Calculate Sharpe ratio
        equity_values = [e['capital'] for e in equity_curve]
        returns = np.diff(equity_values) / equity_values[:-1]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Calculate volatility
        volatility = np.std(returns) * np.sqrt(252)
        
        # Calculate max drawdown
        max_drawdown = max(e['drawdown'] for e in equity_curve)
        
        # Annualized return (assuming ~252 trading days)
        days = len(df)
        years = days / 252
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        total_costs = sum(t.transaction_cost for t in trades)
        
        return BacktestStats(
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown / 100,  # Convert from percentage
            max_drawdown_duration=max_drawdown_duration,
            sharpe_ratio=sharpe,
            sortino_ratio=0,  # Simplified
            volatility=volatility,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=winning_trades / (winning_trades + losing_trades) if (winning_trades + losing_trades) > 0 else 0,
            avg_trade_return=avg_trade_return,
            avg_winning_trade=avg_winning_trade,
            avg_losing_trade=avg_losing_trade,
            total_transaction_costs=total_costs,
            equity_curve=equity_curve,
            trades=trades
        )
    
    def _save_result(
        self,
        stock_symbol: str,
        strategy: str,
        start_date: date,
        end_date: date,
        parameters: Dict[str, Any],
        stats: BacktestStats,
        db_session
    ):
        """Save backtest result to database."""
        import json
        
        result = BacktestResult(
            stock_symbol=stock_symbol,
            strategy_name=strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=stats.initial_capital,
            final_capital=stats.final_capital,
            total_return=stats.total_return,
            annualized_return=stats.annualized_return,
            max_drawdown=stats.max_drawdown,
            max_drawdown_duration=stats.max_drawdown_duration,
            sharpe_ratio=stats.sharpe_ratio,
            volatility=stats.volatility,
            total_trades=stats.total_trades,
            winning_trades=stats.winning_trades,
            losing_trades=stats.losing_trades,
            win_rate=stats.win_rate,
            avg_trade_return=stats.avg_trade_return,
            avg_winning_trade=stats.avg_winning_trade,
            avg_losing_trade=stats.avg_losing_trade,
            total_transaction_costs=stats.total_transaction_costs,
            strategy_parameters=json.dumps(parameters)
        )
        
        db_session.add(result)
        db_session.commit()