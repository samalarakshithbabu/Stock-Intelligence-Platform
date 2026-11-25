import { useState, useEffect } from 'react'
import { 
  TrendingUp, TrendingDown, Database, Activity, 
  RefreshCw, CheckCircle, AlertCircle, BarChart3,
  LineChart, DollarSign, Clock
} from 'lucide-react'
import { 
  LineChart as ReLineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, AreaChart, Area 
} from 'recharts'
import { getStocks, getLatestPrice, getPipelineSummary } from '../services/api'

interface Stock {
  id: number
  symbol: string
  name: string | null
  exchange: string | null
  is_active: boolean
}

interface PriceData {
  date: string
  close: number
  volume: number
}

interface PipelineStats {
  total_executions: number
  successful_executions: number
  failed_executions: number
  success_rate: number
  avg_duration_seconds: number
  last_execution: string | null
}

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  trend?: 'up' | 'down' | 'neutral'
  color: string
}

function MetricCard({ title, value, subtitle, icon: Icon, trend, color }: MetricCardProps) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
      </div>
      {trend && (
        <div className={`flex items-center gap-1 mt-3 text-sm ${trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-slate-400'}`}>
          {trend === 'up' && <TrendingUp className="w-4 h-4" />}
          {trend === 'down' && <TrendingDown className="w-4 h-4" />}
          <span>{trend === 'up' ? '+' : trend === 'down' ? '-' : ''} vs last period</span>
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [selectedStock, setSelectedStock] = useState('AAPL')
  const [priceData, setPriceData] = useState<PriceData[]>([])
  const [pipelineStats, setPipelineStats] = useState<PipelineStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [stocksRes, pipelineRes] = await Promise.all([
        getStocks(),
        getPipelineSummary()
      ])
      setStocks(stocksRes.data)
      setPipelineStats(pipelineRes.data)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const sampleData = [
    { date: '2024-01', value: 185.5 },
    { date: '2024-02', value: 182.3 },
    { date: '2024-03', value: 178.5 },
    { date: '2024-04', value: 172.5 },
    { date: '2024-05', value: 180.2 },
    { date: '2024-06', value: 185.8 },
    { date: '2024-07', value: 192.3 },
    { date: '2024-08', value: 195.2 },
    { date: '2024-09', value: 188.5 },
    { date: '2024-10', value: 193.8 },
    { date: '2024-11', value: 189.5 },
  ]

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card">
              <div className="skeleton h-4 w-24 mb-3"></div>
              <div className="skeleton h-8 w-32 mb-2"></div>
              <div className="skeleton h-4 w-20"></div>
            </div>
          ))}
        </div>
        <div className="card">
          <div className="skeleton h-64"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Market Overview</h1>
          <p className="text-slate-400">Real-time stock intelligence and analytics</p>
        </div>
        <div className="flex items-center gap-3">
          <select 
            className="select w-40"
            value={selectedStock}
            onChange={(e) => setSelectedStock(e.target.value)}
          >
            {stocks.map(s => (
              <option key={s.id} value={s.symbol}>{s.symbol}</option>
            ))}
            <option value="AAPL">AAPL (Demo)</option>
            <option value="GOOGL">GOOGL (Demo)</option>
            <option value="MSFT">MSFT (Demo)</option>
          </select>
          <button onClick={loadData} className="btn btn-secondary flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="Active Stocks"
          value={stocks.length || 3}
          subtitle="In database"
          icon={Database}
          color="bg-blue-600"
          trend="up"
        />
        <MetricCard 
          title="Latest Price"
          value="$193.85"
          subtitle={selectedStock}
          icon={DollarSign}
          color="bg-emerald-600"
          trend="up"
        />
        <MetricCard 
          title="Data Quality"
          value="95.2%"
          subtitle="Pipeline success rate"
          icon={Activity}
          color="bg-purple-600"
        />
        <MetricCard 
          title="Pipeline Runs"
          value={pipelineStats?.total_executions || 12}
          subtitle={`${pipelineStats?.successful_executions || 11} successful`}
          icon={RefreshCw}
          color="bg-amber-600"
        />
      </div>

      {/* Main Chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-white">{selectedStock} Price History</h2>
            <p className="text-sm text-slate-400">12-month price trend</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-primary-500"></div>
              <span className="text-sm text-slate-400">Close Price</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
              <span className="text-sm text-slate-400">Volume</span>
            </div>
          </div>
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={sampleData}>
              <defs>
                <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                </linearGradient>
              </defs>
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
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#0ea5e9" 
                fill="url(#priceGradient)" 
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {[
              { type: 'success', text: 'Pipeline completed for AAPL', time: '2 min ago' },
              { type: 'info', text: 'Model evaluation completed', time: '15 min ago' },
              { type: 'success', text: 'Data refresh successful', time: '1 hour ago' },
              { type: 'warning', text: 'GOOGL - Low volume detected', time: '2 hours ago' },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-slate-700/30">
                {item.type === 'success' && <CheckCircle className="w-5 h-5 text-emerald-400" />}
                {item.type === 'info' && <Activity className="w-5 h-5 text-blue-400" />}
                {item.type === 'warning' && <AlertCircle className="w-5 h-5 text-amber-400" />}
                <div className="flex-1">
                  <p className="text-sm text-slate-300">{item.text}</p>
                  <p className="text-xs text-slate-500">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">Quick Statistics</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Daily Change</span>
              <span className="text-emerald-400 font-semibold">+2.35%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">52 Week High</span>
              <span className="text-white font-semibold">$199.62</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">52 Week Low</span>
              <span className="text-white font-semibold">$164.08</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Avg Volume</span>
              <span className="text-white font-semibold">58.2M</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Market Cap</span>
              <span className="text-white font-semibold">$3.02T</span>
            </div>
          </div>
        </div>

        {/* Model Status */}
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">AI Models Status</h3>
          <div className="space-y-3">
            {[
              { name: 'LSTM', status: 'ready', accuracy: '87.3%' },
              { name: 'GRU', status: 'ready', accuracy: '86.1%' },
              { name: 'XGBoost', status: 'ready', accuracy: '84.5%' },
              { name: 'ARIMA', status: 'ready', accuracy: '82.9%' },
              { name: 'Naive Baseline', status: 'ready', accuracy: '50.2%' },
            ].map((model) => (
              <div key={model.name} className="flex items-center justify-between p-3 rounded-lg bg-slate-700/30">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${model.status === 'ready' ? 'bg-emerald-400' : 'bg-amber-400'}`}></div>
                  <span className="text-sm text-slate-300">{model.name}</span>
                </div>
                <span className="text-xs text-slate-500">{model.accuracy}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}