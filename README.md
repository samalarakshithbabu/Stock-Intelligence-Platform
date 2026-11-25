# Stock Intelligence Platform

A comprehensive AI-powered stock intelligence and forecasting platform built with Python, FastAPI, SQLAlchemy, and React.

---

## Problem Statement

Individual investors and analysts need robust tools for stock forecasting, backtesting strategies, and technical analysis without look-ahead bias. Most platforms either lack rigorous validation methodology or require expensive subscriptions.

## Objectives

- Implement multiple forecasting models with strict time-series validation
- Provide automated data pipeline from Yahoo Finance to SQL database
- Engineer technical indicators without look-ahead bias
- Build backtesting engine with realistic transaction costs
- Create SQL analytics dashboard for custom queries
- Deploy as full-stack application with Docker

## Key Features

### 1. Multi-Model Forecasting Engine
- **Naive Baseline** - Essential benchmark (tomorrow = today)
- **Moving Average** - Simple trend following
- **Linear Regression** - Linear trend modeling
- **Random Forest** - Ensemble tree-based predictions
- **XGBoost** - Gradient boosting algorithm
- **ARIMA** - Classical time-series statistical model
- **LSTM** - Long Short-Term Memory neural network
- **GRU** - Gated Recurrent Unit neural network

### 2. Strict Time-Series Validation
- Chronological train/validation/test splits
- Walk-forward validation
- Scaler fitting only on training data
- No look-ahead bias in technical indicators
- Leakage-free evaluation methodology

### 3. Automated Data Pipeline
- Extract data from Yahoo Finance
- Transform and clean data
- Validate OHLCV data quality
- Load into SQL database
- Track pipeline executions

### 4. Technical Indicator Engineering
- Simple Moving Averages (SMA 20, SMA 50)
- Exponential Moving Averages (EMA 20)
- Relative Strength Index (RSI)
- MACD, Signal Line, Histogram
- Bollinger Bands
- Average True Range (ATR)
- Rolling Volatility
- Volume indicators

### 5. Backtesting Engine
- Moving Average Crossover strategy
- RSI-based strategy
- MACD-based strategy
- Buy-and-Hold benchmark
- Realistic transaction costs
- Drawdown analysis
- Sharpe ratio calculation

### 6. SQL Analytics Dashboard
- Monthly/yearly performance summaries
- Historical volatility analysis
- Top/worst performing days
- Custom SQL query execution
- Window functions and ranking

## Architecture

```
Stock-Intelligence-Platform/
├── backend/
│   ├── api/              # FastAPI routes
│   ├── database/         # SQLAlchemy models & schemas
│   ├── forecasting/      # ML models & evaluation
│   ├── backtesting/      # Strategy simulation
│   ├── indicators/       # Technical indicators
│   ├── pipelines/        # ETL pipelines
│   ├── analytics/        # SQL analytics
│   ├── services/         # Export services
│   └── main.py           # Application entry point
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   └── App.tsx       # Main app
│   └── package.json
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- pip / npm

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/samalarakshithbabu/stock-intelligence-platform.git
cd Stock-Intelligence-Platform

# 2. Set up the backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Set up the frontend
cd frontend
npm install
```

### Running the Application

```bash
# 1. Start the backend
cd backend
python main.py
# API at http://localhost:8000, Docs at http://localhost:8000/docs

# 2. Start the frontend (new terminal)
cd frontend
npm run dev
# App at http://localhost:3000
```

### Using Docker
```bash
docker-compose up -d
```

## API Endpoints

### Stocks
- `GET /api/stocks` - List all stocks
- `GET /api/stocks/{symbol}` - Get stock details
- `GET /api/stocks/{symbol}/prices` - Get historical prices
- `GET /api/stocks/{symbol}/prices/latest` - Get latest price

### Forecasting
- `GET /api/models` - List available models
- `POST /api/models/evaluate` - Evaluate models
- `POST /api/models/forecast` - Generate forecast

### Backtesting
- `POST /api/backtest` - Run backtest

### Analytics
- `GET /api/analytics/monthly/{symbol}` - Monthly performance
- `GET /api/analytics/yearly/{symbol}` - Yearly performance
- `GET /api/analytics/volatility/{symbol}` - Volatility analysis
- `POST /api/analytics/query` - Execute custom SQL

### Pipeline
- `POST /api/pipeline/run/{symbol}` - Run pipeline for a stock
- `GET /api/pipeline/history` - Get execution history
- `GET /api/pipeline/summary` - Get pipeline statistics

## Model Evaluation Methodology

### Preventing Data Leakage
1. **Chronological Splits**: Data split without shuffling
2. **Scaler Isolation**: Scalers fitted only on training data
3. **Walk-Forward**: Rolling window validation
4. **Technical Indicators**: Shifted by 1 to prevent look-ahead

### Evaluation Metrics
- **RMSE** - Root Mean Squared Error
- **MAE** - Mean Absolute Error
- **MAPE** - Mean Absolute Percentage Error
- **sMAPE** - Symmetric MAPE
- **R²** - Coefficient of Determination
- **Directional Accuracy** - % correct price direction predictions

### Naive Baseline
Every model compared against: `Tomorrow's predicted price = Today's actual price`
If sophisticated model can't beat this, it's not adding value!

## Backtesting

### Strategies Available
1. **SMA Crossover**: Buy when short SMA crosses above long SMA
2. **RSI Strategy**: Buy oversold, sell overbought
3. **MACD Strategy**: Trade MACD crossovers
4. **Buy & Hold**: Simple benchmark

### Parameters
- Initial capital
- Transaction costs
- Slippage assumptions

### Metrics
- Total return
- Sharpe ratio
- Max drawdown
- Win rate

## Technology Stack

### Backend
- **FastAPI** - Modern web framework
- **SQLAlchemy** - Database ORM
- **Pandas** - Data manipulation
- **NumPy** - Numerical computing
- **Scikit-learn** - ML algorithms
- **XGBoost** - Gradient boosting
- **Statsmodels** - Statistical models
- **TensorFlow/Keras** - Deep learning
- **yfinance** - Market data

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Recharts** - Charts
- **React Router** - Navigation
- **Axios** - HTTP client
- **Lucide React** - Icons

### Database
- **SQLite** - Development
- **PostgreSQL** - Production (with SQLAlchemy)

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container

## Disclaimer

This platform is for **educational and research purposes only**.

Stock predictions and backtesting results are:
- Not guaranteed future performance
- Based on historical data which may not predict future trends
- Affected by factors not captured in models (market sentiment, news, etc.)

**Never make investment decisions based solely on this platform.**

---

## Author

**SAMALA RAKSHITH BABU**  

**Contact:**  
- Email: samalarakshithbabu7@gmail.com  
- LinkedIn: https://www.linkedin.com/in/samala-rakshith-babu/  
- GitHub: https://github.com/samalarakshithbabu  

---

## License

MIT License