"""
SQL Analytics Module.

Demonstrates complex SQL operations:
- JOINs
- GROUP BY and HAVING
- Subqueries
- Common Table Expressions (CTEs)
- Window functions
- Ranking queries
- Moving averages via SQL
- Monthly/yearly performance summaries
- Historical volatility analysis
"""
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from sqlalchemy import text, func, and_, case
from sqlalchemy.orm import Session
from sqlalchemy.sql import func as sql_func

from backend.database.models import (
    Stock, HistoricalPrice, TechnicalIndicator, Prediction, 
    ModelPerformance, BacktestResult, DataQualityLog
)


class SQLAnalyticsEngine:
    """
    Advanced SQL analytics for stock data.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== BASIC AGGREGATIONS ====================
    
    def get_stock_list(self) -> List[Dict[str, Any]]:
        """Get all stocks in the database."""
        query = text("""
            SELECT id, symbol, name, exchange, sector, is_active, created_at
            FROM stocks
            WHERE is_active = 1
            ORDER BY symbol
        """)
        result = self.db.execute(query)
        return [dict(row._mapping) for row in result]
    
    def get_price_summary(self, symbol: str) -> Dict[str, Any]:
        """Get price summary statistics for a stock."""
        query = text("""
            SELECT 
                s.symbol,
                COUNT(hp.id) as total_records,
                MIN(hp.close_price) as min_price,
                MAX(hp.close_price) as max_price,
                AVG(hp.close_price) as avg_price,
                AVG(hp.volume) as avg_volume,
                MIN(hp.date) as first_date,
                MAX(hp.date) as last_date
            FROM stocks s
            JOIN historical_prices hp ON s.id = hp.stock_id
            WHERE s.symbol = :symbol
            GROUP BY s.id, s.symbol
        """)
        result = self.db.execute(query, {"symbol": symbol}).fetchone()
        return dict(result._mapping) if result else {}
    
    # ==================== MOVING AVERAGES VIA SQL ====================
    
    def calculate_sql_moving_averages(
        self, 
        symbol: str, 
        windows: List[int] = [20, 50]
    ) -> List[Dict[str, Any]]:
        """
        Calculate moving averages using SQL window functions.
        """
        window_clause = ", ".join([f"{w} PRECEDING" for w in windows])
        
        query = text(f"""
            SELECT 
                symbol,
                date,
                close_price,
                AVG(close_price) OVER (
                    PARTITION BY symbol 
                    ORDER BY date 
                    ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                ) as sma_20,
                AVG(close_price) OVER (
                    PARTITION BY symbol 
                    ORDER BY date 
                    ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
                ) as sma_50
            FROM (
                SELECT s.symbol, hp.date, hp.close_price
                FROM stocks s
                JOIN historical_prices hp ON s.id = hp.stock_id
                WHERE s.symbol = :symbol
            ) sub
            ORDER BY date DESC
            LIMIT 100
        """)
        
        result = self.db.execute(query, {"symbol": symbol})
        return [dict(row._mapping) for row in result]
    
    # ==================== MONTHLY PERFORMANCE ====================
    
    def get_monthly_performance(
        self, 
        symbol: str, 
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate monthly performance using SQL aggregations.
        """
        if year:
            date_filter = "AND YEAR(date) = :year"
        else:
            date_filter = ""
        
        query = text(f"""
            SELECT 
                YEAR(date) as year,
                MONTH(date) as month,
                symbol,
                MIN(close_price) as monthly_low,
                MAX(close_price) as monthly_high,
                FIRST_VALUE(close_price) OVER (
                    PARTITION BY YEAR(date), MONTH(date) 
                    ORDER BY date
                ) as month_open,
                LAST_VALUE(close_price) OVER (
                    PARTITION BY YEAR(date), MONTH(date) 
                    ORDER BY date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) as month_close,
                SUM(volume) as monthly_volume,
                (LAST_VALUE(close_price) OVER (
                    PARTITION BY YEAR(date), MONTH(date) 
                    ORDER BY date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) - FIRST_VALUE(close_price) OVER (
                    PARTITION BY YEAR(date), MONTH(date) 
                    ORDER BY date
                )) / FIRST_VALUE(close_price) OVER (
                    PARTITION BY YEAR(date), MONTH(date) 
                    ORDER BY date
                ) * 100 as monthly_return_pct
            FROM (
                SELECT s.symbol, hp.date, hp.close_price, hp.volume
                FROM stocks s
                JOIN historical_prices hp ON s.id = hp.stock_id
                WHERE s.symbol = :symbol {date_filter}
            ) sub
            GROUP BY YEAR(date), MONTH(date), symbol, date, close_price, volume
            ORDER BY year DESC, month DESC
        """)
        
        params = {"symbol": symbol}
        if year:
            params["year"] = year
        
        result = self.db.execute(query, params)
        return [dict(row._mapping) for row in result]
    
    def get_yearly_performance(self, symbol: str) -> List[Dict[str, Any]]:
        """Calculate yearly performance using SQL."""
        query = text("""
            SELECT 
                YEAR(date) as year,
                symbol,
                MIN(close_price) as yearly_low,
                MAX(close_price) as yearly_high,
                AVG(close_price) as yearly_avg_price,
                SUM(volume) as yearly_volume,
                FIRST_VALUE(close_price) OVER (
                    PARTITION BY YEAR(date) 
                    ORDER BY date
                ) as year_open,
                LAST_VALUE(close_price) OVER (
                    PARTITION BY YEAR(date) 
                    ORDER BY date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) as year_close,
                (LAST_VALUE(close_price) OVER (
                    PARTITION BY YEAR(date) 
                    ORDER BY date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) - FIRST_VALUE(close_price) OVER (
                    PARTITION BY YEAR(date) 
                    ORDER BY date
                )) / FIRST_VALUE(close_price) OVER (
                    PARTITION BY YEAR(date) 
                    ORDER BY date
                ) * 100 as yearly_return_pct
            FROM (
                SELECT s.symbol, hp.date, hp.close_price, hp.volume
                FROM stocks s
                JOIN historical_prices hp ON s.id = hp.stock_id
                WHERE s.symbol = :symbol
            ) sub
            ORDER BY year DESC
        """)
        
        result = self.db.execute(query, {"symbol": symbol})
        return [dict(row._mapping) for row in result]
    
    # ==================== VOLATILITY ANALYSIS ====================
    
    def calculate_historical_volatility(
        self, 
        symbol: str, 
        window: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Calculate historical volatility using SQL.
        """
        query = text("""
            SELECT 
                date,
                close_price,
                daily_return,
                STDDEV(daily_return) OVER (
                    PARTITION BY symbol 
                    ORDER BY date 
                    ROWS BETWEEN :window-1 PRECEDING AND CURRENT ROW
                ) * SQRT(252) * 100 as annualized_volatility
            FROM (
                SELECT 
                    s.symbol,
                    hp.date,
                    hp.close_price,
                    (hp.close_price - LAG(hp.close_price) OVER (
                        PARTITION BY s.symbol ORDER BY hp.date
                    )) / LAG(hp.close_price) OVER (
                        PARTITION BY s.symbol ORDER BY hp.date
                    ) as daily_return
                FROM stocks s
                JOIN historical_prices hp ON s.id = hp.stock_id
                WHERE s.symbol = :symbol
            ) sub
            WHERE daily_return IS NOT NULL
            ORDER BY date DESC
        """)
        
        result = self.db.execute(query, {"symbol": symbol, "window": window})
        return [dict(row._mapping) for row in result]
    
    # ==================== RANKING QUERIES ====================
    
    def get_top_performing_days(
        self, 
        symbol: str, 
        n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top N performing days using ranking functions."""
        query = text("""
            SELECT 
                symbol,
                date,
                close_price,
                daily_return,
                RANK() OVER (
                    PARTITION BY symbol 
                    ORDER BY daily_return DESC
                ) as return_rank
            FROM (
                SELECT 
                    s.symbol,
                    hp.date,
                    hp.close_price,
                    (hp.close_price - LAG(hp.close_price) OVER (
                        PARTITION BY s.symbol ORDER BY hp.date
                    )) / LAG(hp.close_price) OVER (
                        PARTITION BY s.symbol ORDER BY hp.date
                    ) * 100 as daily_return
                FROM stocks s
                JOIN historical_prices hp ON s.id = hp.stock_id
                WHERE s.symbol = :symbol
            ) sub
            ORDER BY daily_return DESC
            LIMIT :n
        """)
        
        result = self.db.execute(query, {"symbol": symbol, "n": n})
        return [dict(row._mapping) for row in result]
    
    def get_worst_performing_days(
        self, 
        symbol: str, 
        n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get worst N performing days."""
        query = text("""
            SELECT 
                symbol,
                date,
                close_price,
                daily_return,
                RANK() OVER (
                    PARTITION BY symbol 
                    ORDER BY daily_return ASC
                ) as return_rank
            FROM (
                SELECT 
                    s.symbol,
                    hp.date,
                    hp.close_price,
                    (hp.close_price - LAG(hp.close_price) OVER (
                        PARTITION BY s.symbol ORDER BY hp.date
                    )) / LAG(hp.close_price) OVER (
                        PARTITION BY s.symbol ORDER BY hp.date
                    ) * 100 as daily_return
                FROM stocks s
                JOIN historical_prices hp ON s.id = hp.stock_id
                WHERE s.symbol = :symbol
            ) sub
            WHERE daily_return IS NOT NULL
            ORDER BY daily_return ASC
            LIMIT :n
        """)
        
        result = self.db.execute(query, {"symbol": symbol, "n": n})
        return [dict(row._mapping) for row in result]
    
    # ==================== STREAK ANALYSIS ====================
    
    def get_consecutive_gains_losses(self, symbol: str) -> List[Dict[str, Any]]:
        """Analyze consecutive gains and losses using window functions."""
        query = text("""
            WITH daily_returns AS (
                SELECT 
                    s.symbol,
                    hp.date,
                    hp.close_price,
                    CASE 
                        WHEN hp.close_price > LAG(hp.close_price) OVER (
                            PARTITION BY s.symbol ORDER BY hp.date
                        ) THEN 1
                        WHEN hp.close_price < LAG(hp.close_price) OVER (
                            PARTITION BY s.symbol ORDER BY hp.date
                        ) THEN -1
                        ELSE 0
                    END as direction
                FROM stocks s
                JOIN historical_prices hp ON s.id = hp.stock_id
                WHERE s.symbol = :symbol
            )
            SELECT * FROM daily_returns WHERE direction != 0
        """)
        
        result = self.db.execute(query, {"symbol": symbol})
        return [dict(row._mapping) for row in result]
    
    # ==================== DATA QUALITY ANALYSIS ====================
    
    def get_data_quality_summary(self) -> Dict[str, Any]:
        """Get data quality metrics using SQL aggregations."""
        query = text("""
            SELECT 
                (SELECT COUNT(*) FROM stocks WHERE is_active = 1) as active_stocks,
                (SELECT COUNT(*) FROM historical_prices) as total_price_records,
                (SELECT COUNT(*) FROM technical_indicators) as total_indicator_records,
                (SELECT COUNT(DISTINCT stock_id) FROM historical_prices) as stocks_with_data,
                (SELECT MIN(date) FROM historical_prices) as earliest_date,
                (SELECT MAX(date) FROM historical_prices) as latest_date
        """)
        
        result = self.db.execute(query).fetchone()
        return dict(result._mapping) if result else {}
    
    def get_missing_dates_analysis(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Identify missing trading dates using SQL.
        """
        query = text("""
            WITH date_series AS (
                SELECT 
                    MIN(date) as start_date,
                    MAX(date) as end_date
                FROM historical_prices hp
                JOIN stocks s ON s.id = hp.stock_id
                WHERE s.symbol = :symbol
            ),
            expected_dates AS (
                SELECT 
                    DATE_ADD(day, INTERVAL n DAY, start_date) as expected_date
                FROM date_series
                CROSS JOIN (
                    SELECT (a.n + b.n * 10 + c.n * 100) as n
                    FROM (SELECT 0 as n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
                          UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
                         (SELECT 0 as n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
                          UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
                         (SELECT 0 as n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
                          UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c
                ) numbers
                WHERE DATE_ADD(day, INTERVAL n DAY, start_date) <= end_date
            )
            SELECT COUNT(*) as missing_weekdays
            FROM expected_dates ed
            LEFT JOIN historical_prices hp ON ed.expected_date = hp.date
            JOIN stocks s ON s.id = hp.stock_id
            WHERE hp.id IS NULL AND DAYOFWEEK(ed.expected_date) NOT IN (1, 7)
            AND s.symbol = :symbol
        """)
        
        # Simplified version
        query = text("""
            SELECT 
                s.symbol,
                COUNT(DISTINCT hp.date) as recorded_days,
                (SELECT COUNT(*) FROM (
                    SELECT ADDDATE(MIN(date), INTERVAL t4*10000 + t3*1000 + t2*100 + t1*10 + t0 DAY) as missing_date
                    FROM (SELECT 0 t0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t0,
                         (SELECT 0 t1 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t1,
                         (SELECT 0 t2 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t2,
                         (SELECT 0 t3 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t3,
                         (SELECT 0 t4 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) t4,
                         (SELECT MIN(date) as start, MAX(date) as end FROM historical_prices hp2 JOIN stocks s2 ON s2.id = hp2.stock_id WHERE s2.symbol = :symbol) dates
                    WHERE ADDDATE(dates.start, INTERVAL t4*10000 + t3*1000 + t2*100 + t1*10 + t0 DAY) <= dates.end
                ) all_dates WHERE DAYOFWEEK(missing_date) NOT IN (1,7)
            ) - COUNT(DISTINCT hp.date) as estimated_missing
            FROM stocks s
            JOIN historical_prices hp ON s.id = hp.stock_id
            WHERE s.symbol = :symbol
            GROUP BY s.id, s.symbol
        """)
        
        result = self.db.execute(query, {"symbol": symbol}).fetchone()
        return dict(result._mapping) if result else {}
    
    # ==================== MODEL PERFORMANCE COMPARISON ====================
    
    def get_model_performance_comparison(self, symbol: str) -> List[Dict[str, Any]]:
        """Compare model performance using SQL aggregations."""
        query = text("""
            SELECT 
                model_name,
                stock_symbol,
                COUNT(*) as evaluations,
                AVG(mae) as avg_mae,
                AVG(rmse) as avg_rmse,
                AVG(mape) as avg_mape,
                AVG(directional_accuracy) as avg_directional_accuracy,
                MIN(created_at) as first_evaluation,
                MAX(created_at) as last_evaluation
            FROM model_performance
            WHERE stock_symbol = :symbol
            GROUP BY model_name, stock_symbol
            ORDER BY avg_rmse ASC
        """)
        
        result = self.db.execute(query, {"symbol": symbol})
        return [dict(row._mapping) for row in result]
    
    # ==================== CUMULATIVE RETURNS ====================
    
    def calculate_cumulative_returns(self, symbol: str) -> List[Dict[str, Any]]:
        """Calculate cumulative returns using window functions."""
        query = text("""
            SELECT 
                symbol,
                date,
                close_price,
                cumulative_return,
                RANK() OVER (
                    PARTITION BY symbol 
                    ORDER BY cumulative_return DESC
                ) as best_rank,
                RANK() OVER (
                    PARTITION BY symbol 
                    ORDER BY cumulative_return ASC
                ) as worst_rank
            FROM (
                SELECT 
                    s.symbol,
                    hp.date,
                    hp.close_price,
                    (hp.close_price / FIRST_VALUE(hp.close_price) OVER (
                        PARTITION BY s.symbol ORDER BY hp.date
                    ) - 1) * 100 as cumulative_return
                FROM stocks s
                JOIN historical_prices hp ON s.id = hp.stock_id
                WHERE s.symbol = :symbol
            ) sub
            ORDER BY date DESC
        """)
        
        result = self.db.execute(query, {"symbol": symbol})
        return [dict(row._mapping) for row in result]
    
    # ==================== EXECUTE CUSTOM SQL ====================
    
    def execute_custom_query(self, query: str) -> Dict[str, Any]:
        """Execute a custom SQL query."""
        try:
            result = self.db.execute(text(query))
            
            if query.strip().upper().startswith("SELECT"):
                rows = [dict(row._mapping) for row in result]
                return {
                    "success": True,
                    "row_count": len(rows),
                    "results": rows
                }
            else:
                self.db.commit()
                return {
                    "success": True,
                    "message": "Query executed successfully"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }