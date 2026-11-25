import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Stocks
export const getStocks = () => api.get('/stocks')
export const getStock = (symbol: string) => api.get(`/stocks/${symbol}`)
export const getPrices = (symbol: string, limit = 1000) => 
  api.get(`/stocks/${symbol}/prices?limit=${limit}`)
export const getLatestPrice = (symbol: string) => 
  api.get(`/stocks/${symbol}/prices/latest`)
export const getIndicators = (symbol: string, limit = 500) => 
  api.get(`/stocks/${symbol}/indicators?limit=${limit}`)

// Pipeline
export const runPipeline = (symbol: string) => 
  api.post(`/pipeline/run/${symbol}`)
export const runAllPipelines = () => 
  api.post('/pipeline/run-all')
export const getPipelineHistory = (limit = 50) => 
  api.get(`/pipeline/history?limit=${limit}`)
export const getPipelineSummary = () => 
  api.get('/pipeline/summary')

// Models
export const getModels = () => api.get('/models')
export const evaluateModels = (symbol: string, modelTypes?: string[]) =>
  api.post('/models/evaluate', { symbol, model_types: modelTypes })
export const generateForecast = (symbol: string, modelType: string, predictionDays = 30) =>
  api.post('/models/forecast', { symbol, model_type: modelType, prediction_days: predictionDays })

// Backtesting
export const runBacktest = (symbol: string, strategy: string, startDate: string, endDate: string) =>
  api.post('/backtest', { 
    symbol, 
    strategy, 
    start_date: startDate, 
    end_date: endDate,
    initial_capital: 100000,
    transaction_cost: 0.001
  })

// Analytics
export const getMonthlyPerformance = (symbol: string, year?: number) =>
  api.get(`/analytics/monthly/${symbol}${year ? `?year=${year}` : ''}`)
export const getYearlyPerformance = (symbol: string) =>
  api.get(`/analytics/yearly/${symbol}`)
export const getVolatility = (symbol: string, window = 20) =>
  api.get(`/analytics/volatility/${symbol}?window=${window}`)
export const getTopDays = (symbol: string, n = 10) =>
  api.get(`/analytics/top-days/${symbol}?n=${n}`)
export const getWorstDays = (symbol: string, n = 10) =>
  api.get(`/analytics/worst-days/${symbol}?n=${n}`)

// Dashboard
export const getDashboardMetrics = () => api.get('/dashboard/metrics')
export const healthCheck = () => api.get('/health')

// Export
export const exportPrices = (symbol: string) =>
  api.get(`/export/prices/${symbol}/csv`, { responseType: 'blob' })

// Custom query
export const executeSQL = (query: string) =>
  api.post('/analytics/query', { query })

export default api