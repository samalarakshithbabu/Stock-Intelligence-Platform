import { useState, useEffect } from 'react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
  LineChart, Line
} from 'recharts'
import { 
  BarChart3, TrendingUp, TrendingDown, 
  Calendar, Database, Activity
} from 'lucide-react'
import { getMonthlyPerformance, getYearlyPerformance, getTopDays, getWorstDays } from '../services/api'

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export default function Analytics() {
  const [symbol, setSymbol] = useState('AAPL')
  const [activeTab, setActiveTab] = useState('monthly')

  // Sample data for demonstration
  const monthlyData = [
    { month: 'Jan', return: 5.2, volume: 45000000 },
    { month: 'Feb', return: -2.3, volume: 52000000 },
    { month: 'Mar', return: 8.1, volume: 48000000 },
    { month: 'Apr', return: -1.5, volume: 55000000 },
    { month: 'May', return: 12.4, volume: 62000000 },
    { month: 'Jun', return: 3.2, volume: 58000000 },
    { month: 'Jul', return: -4.1, volume: 49000000 },
    { month: 'Aug', return: 6.8, volume: 53000000 },
    { month: 'Sep', return: 2.9, volume: 50000000 },
    { month: 'Oct', return: -0.8, volume: 56000000 },
    { month: 'Nov', return: 9.5, volume: 61000000 },
    { month: 'Dec', return: 4.2, volume: 54000000 },
  ]

  const yearlyData = [
    { year: '2020', return: 78.5, volatility: 32.1 },
    { year: '2021', return: 34.2, volatility: 24.5 },
    { year: '2022', return: -18.8, volatility: 28.3 },
    { year: '2023', return: 48.2, volatility: 21.7 },
    { year: '2024', return: 32.1, volatility: 18.9 },
  ]

  const topDays = [
    { date: '2024-11-15', return: 4.8, volume: 82000000 },
    { date: '2024-08-22', return: 4.2, volume: 75000000 },
    { date: '2024-05-03', return: 3.9, volume: 68000000 },
    { date: '2024-03-15', return: 3.7, volume: 71000000 },
    { date: '2024-09-10', return: 3.5, volume: 65000000 },
  ]

  const worstDays = [
    { date: '2024-04-19', return: -4.1, volume: 92000000 },
    { date: '2024-07-24', return: -3.8, volume: 85000000 },
    { date: '2024-01-22', return: -3.2, volume: 78000000 },
    { date: '2024-10-15', return: -2.9, volume: 72000000 },
    { date: '2024-06-05', return: -2.7, volume: 69000000 },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">SQL Analytics</h1>
          <p className="text-slate-400">Advanced analytics powered by SQL queries and aggregations</p>
        </div>
        <select 
          className="select w-40"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        >
          <option value="AAPL">AAPL</option>
          <option value="GOOGL">GOOGL</option>
          <option value="MSFT">MSFT</option>
        </select>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-700">
        {[
          { id: 'monthly', label: 'Monthly Performance' },
          { id: 'yearly', label: 'Yearly Performance' },
          { id: 'top', label: 'Top/Worst Days' },
          { id: 'volatility', label: 'Volatility Analysis' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'monthly' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Monthly Returns Chart */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Monthly Returns</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="month" stroke="#64748b" />
                  <YAxis stroke="#64748b" unit="%" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    formatter={(value: number) => [`${value.toFixed(2)}%`, 'Return']}
                  />
                  <Bar 
                    dataKey="return" 
                    fill="#0ea5e9"
                    radius={[4, 4, 0, 0]}
                  >
                    {monthlyData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.return >= 0 ? '#10b981' : '#ef4444'} 
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Monthly Volume */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Trading Volume</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="month" stroke="#64748b" />
                  <YAxis stroke="#64748b" tickFormatter={(v) => `${(v/1000000).toFixed(0)}M`} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    formatter={(value: number) => [`${(value/1000000).toFixed(1)}M`, 'Volume']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="volume" 
                    stroke="#8b5cf6" 
                    strokeWidth={2}
                    dot={{ fill: '#8b5cf6' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'yearly' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Yearly Returns */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Yearly Performance</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={yearlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="year" stroke="#64748b" />
                  <YAxis stroke="#64748b" unit="%" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    formatter={(value: number) => [`${value.toFixed(2)}%`, 'Return']}
                  />
                  <Bar dataKey="return" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Yearly Volatility */}
          <div className="card">
            <h2 className="text-lg font-semibold text-white mb-4">Annualized Volatility</h2>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={yearlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="year" stroke="#64748b" />
                  <YAxis stroke="#64748b" unit="%" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#1e293b', 
                      border: '1px solid #334155',
                      borderRadius: '8px'
                    }}
                    formatter={(value: number) => [`${value.toFixed(2)}%`, 'Volatility']}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="volatility" 
                    stroke="#f59e0b" 
                    strokeWidth={2}
                    dot={{ fill: '#f59e0b' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'top' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Days */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <h2 className="text-lg font-semibold text-white">Top 5 Performing Days</h2>
            </div>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Return</th>
                    <th>Volume</th>
                  </tr>
                </thead>
                <tbody>
                  {topDays.map((day) => (
                    <tr key={day.date}>
                      <td>{day.date}</td>
                      <td className="text-emerald-400">+{day.return}%</td>
                      <td>{(day.volume/1000000).toFixed(1)}M</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Worst Days */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <TrendingDown className="w-5 h-5 text-red-400" />
              <h2 className="text-lg font-semibold text-white">Worst 5 Performing Days</h2>
            </div>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Return</th>
                    <th>Volume</th>
                  </tr>
                </thead>
                <tbody>
                  {worstDays.map((day) => (
                    <tr key={day.date}>
                      <td>{day.date}</td>
                      <td className="text-red-400">{day.return}%</td>
                      <td>{(day.volume/1000000).toFixed(1)}M</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'volatility' && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">Rolling Volatility Analysis</h2>
          <p className="text-slate-400 mb-4">
            Historical volatility calculated using 20-day rolling standard deviation, annualized.
          </p>
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={[
                { date: 'Jan', vol: 18.2 },
                { date: 'Feb', vol: 21.5 },
                { date: 'Mar', vol: 28.3 },
                { date: 'Apr', vol: 24.1 },
                { date: 'May', vol: 19.8 },
                { date: 'Jun', vol: 16.2 },
                { date: 'Jul', vol: 15.5 },
                { date: 'Aug', vol: 22.4 },
                { date: 'Sep', vol: 25.8 },
                { date: 'Oct', vol: 32.1 },
                { date: 'Nov', vol: 18.9 },
                { date: 'Dec', vol: 16.5 },
              ]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" />
                <YAxis stroke="#64748b" unit="%" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #334155',
                    borderRadius: '8px'
                  }}
                  formatter={(value: number) => [`${value.toFixed(2)}%`, 'Volatility']}
                />
                <Line 
                  type="monotone" 
                  dataKey="vol" 
                  stroke="#f59e0b" 
                  strokeWidth={2}
                  dot={{ fill: '#f59e0b' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* SQL Examples */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">
          <Database className="w-5 h-5 inline mr-2" />
          SQL Analytics Queries
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-900 rounded-lg p-4">
            <p className="text-sm text-slate-400 mb-2">Window Function - Moving Average</p>
            <pre className="text-xs text-slate-300 overflow-x-auto">
{`SELECT symbol, date, close_price,
  AVG(close_price) OVER (
    PARTITION BY symbol 
    ORDER BY date 
    ROWS 19 PRECEDING
  ) as sma_20
FROM historical_prices`}
            </pre>
          </div>
          <div className="bg-slate-900 rounded-lg p-4">
            <p className="text-sm text-slate-400 mb-2">Volatility Calculation</p>
            <pre className="text-xs text-slate-300 overflow-x-auto">
{`SELECT date,
  STDDEV(daily_return) OVER (
    ORDER BY date 
    ROWS 19 PRECEDING
  ) * SQRT(252) * 100 as vol_annualized
FROM daily_returns`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}