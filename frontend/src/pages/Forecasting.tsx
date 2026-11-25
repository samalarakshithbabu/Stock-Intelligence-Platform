import { useState, useEffect } from 'react'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts'
import { 
  TrendingUp, Clock, Target, Zap, 
  RefreshCw, Play, Settings
} from 'lucide-react'
import { getModels, generateForecast, evaluateModels } from '../services/api'

interface Model {
  id: string
  name: string
}

interface Prediction {
  date: string
  predicted_price: number
}

const modelDescriptions: Record<string, string> = {
  naive: 'Predicts tomorrow\'s price equals today\'s price. Essential baseline for comparison.',
  moving_average: 'Uses moving average of recent prices. Simple but effective.',
  linear_regression: 'Fits a linear trend to historical prices.',
  random_forest: 'Ensemble of decision trees for robust predictions.',
  xgboost: 'Gradient boosting with regularization.',
  arima: 'Classical time-series statistical model.',
  lstm: 'Long Short-Term Memory neural network for sequence data.',
  gru: 'Gated Recurrent Unit - simpler alternative to LSTM.',
}

export default function Forecasting() {
  const [symbol, setSymbol] = useState('AAPL')
  const [selectedModel, setSelectedModel] = useState('lstm')
  const [predictionDays, setPredictionDays] = useState(30)
  const [models, setModels] = useState<Model[]>([])
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(false)
  const [forecastData, setForecastData] = useState<any[]>([])

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      const response = await getModels()
      setModels(response.data)
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  }

  const generatePredictions = async () => {
    setLoading(true)
    try {
      const response = await generateForecast(symbol, selectedModel, predictionDays)
      setPredictions(response.data.predictions)
      
      // Create chart data
      const historical = [
        { date: '2024-09', price: 188.5 },
        { date: '2024-10', price: 192.3 },
        { date: '2024-11', price: 189.8 },
      ]
      
      const forecast = response.data.predictions.map((p: any) => ({
        date: p.date.slice(5),
        price: p.predicted_price,
        isForecast: true
      }))
      
      setForecastData([...historical, ...forecast])
    } catch (error) {
      console.error('Failed to generate forecast:', error)
      // Use sample data
      const samplePredictions = Array.from({ length: predictionDays }, (_, i) => ({
        date: `2024-12-${String(i + 1).padStart(2, '0')}`,
        predicted_price: 190 + Math.random() * 10 - 5
      }))
      setPredictions(samplePredictions)
      
      const sampleChart = [
        { date: '2024-09', price: 188.5, isForecast: false },
        { date: '2024-10', price: 192.3, isForecast: false },
        { date: '2024-11', price: 189.8, isForecast: false },
        ...samplePredictions.map(p => ({ ...p, price: p.predicted_price, isForecast: true }))
      ]
      setForecastData(sampleChart)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Forecasting</h1>
          <p className="text-slate-400">Generate price predictions using multiple ML models</p>
        </div>
      </div>

      {/* Configuration */}
      <div className="card">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-40">
            <label className="block text-sm text-slate-400 mb-2">Stock Symbol</label>
            <select 
              className="select" 
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
            >
              <option value="AAPL">AAPL - Apple Inc.</option>
              <option value="GOOGL">GOOGL - Alphabet</option>
              <option value="MSFT">MSFT - Microsoft</option>
              <option value="AMZN">AMZN - Amazon</option>
              <option value="TSLA">TSLA - Tesla</option>
            </select>
          </div>
          <div className="flex-1 min-w-48">
            <label className="block text-sm text-slate-400 mb-2">Model</label>
            <select 
              className="select" 
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
            >
              {models.map(m => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
              <option value="naive">Naive Baseline</option>
              <option value="moving_average">Moving Average</option>
              <option value="linear_regression">Linear Regression</option>
              <option value="random_forest">Random Forest</option>
              <option value="xgboost">XGBoost</option>
              <option value="arima">ARIMA</option>
              <option value="lstm">LSTM</option>
              <option value="gru">GRU</option>
            </select>
          </div>
          <div className="w-40">
            <label className="block text-sm text-slate-400 mb-2">Days</label>
            <select 
              className="select" 
              value={predictionDays}
              onChange={(e) => setPredictionDays(Number(e.target.value))}
            >
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
            </select>
          </div>
          <button 
            onClick={generatePredictions}
            disabled={loading}
            className="btn btn-primary flex items-center gap-2"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {loading ? 'Generating...' : 'Generate Forecast'}
          </button>
        </div>
        
        {/* Model Description */}
        <div className="mt-4 p-3 rounded-lg bg-slate-700/30 border border-slate-700">
          <p className="text-sm text-slate-300">{modelDescriptions[selectedModel]}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-white">{symbol} Price Forecast</h2>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary-500"></div>
              <span className="text-sm text-slate-400">Historical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
              <span className="text-sm text-slate-400">Forecast</span>
            </div>
          </div>
        </div>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} domain={['auto', 'auto']} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#e2e8f0'
                }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="price" 
                stroke="#0ea5e9" 
                strokeWidth={2}
                dot={false}
                name="Price"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Predictions Table */}
      {predictions.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Detailed Predictions</h2>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Predicted Price</th>
                  <th>Change</th>
                </tr>
              </thead>
              <tbody>
                {predictions.slice(0, 15).map((pred, i) => {
                  const prevPrice = i > 0 ? predictions[i - 1].predicted_price : 189.50
                  const change = pred.predicted_price - prevPrice
                  const changePct = (change / prevPrice) * 100
                  return (
                    <tr key={pred.date}>
                      <td>{pred.date}</td>
                      <td className="font-mono">${pred.predicted_price.toFixed(2)}</td>
                      <td className={change >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                        {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePct.toFixed(2)}%)
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Model Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { icon: Target, title: 'Naive Baseline', desc: 'Benchmark model' },
          { icon: TrendingUp, title: 'Traditional ML', desc: 'Linear models' },
          { icon: Zap, title: 'Deep Learning', desc: 'LSTM & GRU' },
          { icon: Clock, title: 'Time Series', desc: 'ARIMA models' },
        ].map((item, i) => (
          <div key={i} className="card">
            <div className="flex items-center gap-3 mb-2">
              <item.icon className="w-5 h-5 text-primary-400" />
              <h3 className="font-medium text-white">{item.title}</h3>
            </div>
            <p className="text-sm text-slate-400">{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}