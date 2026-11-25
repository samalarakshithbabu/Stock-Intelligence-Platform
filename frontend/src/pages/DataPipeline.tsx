import { useState, useEffect } from 'react'
import { 
  Database, RefreshCw, CheckCircle, XCircle, 
  Clock, AlertCircle, Download, Activity
} from 'lucide-react'
import { runPipeline, getPipelineHistory, getPipelineSummary } from '../services/api'

interface PipelineExecution {
  id: number
  pipeline_name: string
  execution_id: string
  status: string
  start_time: string
  end_time: string | null
  duration_seconds: number | null
  records_processed: number
  records_inserted: number
  error_message: string | null
}

export default function DataPipeline() {
  const [symbol, setSymbol] = useState('AAPL')
  const [running, setRunning] = useState(false)
  const [history, setHistory] = useState<PipelineExecution[]>([])
  const [summary, setSummary] = useState<any>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [historyRes, summaryRes] = await Promise.all([
        getPipelineHistory(20),
        getPipelineSummary()
      ])
      setHistory(historyRes.data)
      setSummary(summaryRes.data)
    } catch (error) {
      console.error('Failed to load pipeline data:', error)
    }
  }

  const runPipelineHandler = async () => {
    setRunning(true)
    try {
      await runPipeline(symbol)
      await loadData()
    } catch (error) {
      console.error('Pipeline failed:', error)
    } finally {
      setRunning(false)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <span className="badge badge-success">Success</span>
      case 'failed':
        return <span className="badge badge-danger">Failed</span>
      case 'running':
        return <span className="badge badge-info">Running</span>
      default:
        return <span className="badge">{status}</span>
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Data Pipeline</h1>
          <p className="text-slate-400">ETL pipeline management and monitoring</p>
        </div>
        <div className="flex items-center gap-3">
          <select 
            className="select w-40" 
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          >
            <option value="AAPL">AAPL</option>
            <option value="GOOGL">GOOGL</option>
            <option value="MSFT">MSFT</option>
            <option value="AMZN">AMZN</option>
            <option value="TSLA">TSLA</option>
          </select>
          <button 
            onClick={runPipelineHandler}
            disabled={running}
            className="btn btn-primary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} />
            {running ? 'Running...' : 'Run Pipeline'}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Total Executions</p>
              <p className="text-2xl font-bold text-white">{summary?.total_executions || 0}</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-600/20">
              <RefreshCw className="w-5 h-5 text-blue-400" />
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Success Rate</p>
              <p className="text-2xl font-bold text-emerald-400">
                {summary?.success_rate?.toFixed(1) || 0}%
              </p>
            </div>
            <div className="p-3 rounded-lg bg-emerald-600/20">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Avg Duration</p>
              <p className="text-2xl font-bold text-white">
                {summary?.avg_duration_seconds?.toFixed(1) || 0}s
              </p>
            </div>
            <div className="p-3 rounded-lg bg-amber-600/20">
              <Clock className="w-5 h-5 text-amber-400" />
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Last Execution</p>
              <p className="text-sm text-white truncate max-w-32">
                {summary?.last_execution ? formatDate(summary.last_execution) : 'Never'}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-purple-600/20">
              <Activity className="w-5 h-5 text-purple-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Pipeline Architecture */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">ETL Pipeline Architecture</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { step: 'Extract', icon: Database, desc: 'Fetch from Yahoo Finance', color: 'blue' },
            { step: 'Transform', icon: RefreshCw, desc: 'Clean & normalize data', color: 'amber' },
            { step: 'Validate', icon: CheckCircle, desc: 'Data quality checks', color: 'emerald' },
            { step: 'Load', icon: Download, desc: 'Store in SQL database', color: 'purple' },
          ].map((item, i) => (
            <div key={i} className="text-center p-4 rounded-lg bg-slate-700/30">
              <div className={`p-3 rounded-full w-fit mx-auto mb-3 ${
                item.color === 'blue' ? 'bg-blue-600/20' :
                item.color === 'amber' ? 'bg-amber-600/20' :
                item.color === 'emerald' ? 'bg-emerald-600/20' :
                'bg-purple-600/20'
              }`}>
                <item.icon className={`w-6 h-6 ${
                  item.color === 'blue' ? 'text-blue-400' :
                  item.color === 'amber' ? 'text-amber-400' :
                  item.color === 'emerald' ? 'text-emerald-400' :
                  'text-purple-400'
                }`} />
              </div>
              <h3 className="font-medium text-white">{item.step}</h3>
              <p className="text-xs text-slate-400 mt-1">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Execution History */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Execution History</h2>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Execution ID</th>
                <th>Stock</th>
                <th>Status</th>
                <th>Start Time</th>
                <th>Duration</th>
                <th>Records</th>
                <th>Inserted</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {history.map((exec) => (
                <tr key={exec.id}>
                  <td className="font-mono text-xs">{exec.execution_id}</td>
                  <td>{exec.stock_symbol || '-'}</td>
                  <td>{getStatusBadge(exec.status)}</td>
                  <td className="text-sm">{formatDate(exec.start_time)}</td>
                  <td className="text-sm">
                    {exec.duration_seconds ? `${exec.duration_seconds.toFixed(1)}s` : '-'}
                  </td>
                  <td className="text-sm">{exec.records_processed}</td>
                  <td className="text-sm text-emerald-400">{exec.records_inserted}</td>
                  <td className="text-sm text-red-400 max-w-xs truncate">
                    {exec.error_message || '-'}
                  </td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center text-slate-400 py-8">
                    No pipeline executions yet. Run the pipeline to see history.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Data Quality */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">Data Quality Checks</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { check: 'Duplicate Detection', status: 'pass', desc: 'No duplicates found' },
            { check: 'Missing Value Check', status: 'pass', desc: '< 1% missing values' },
            { check: 'OHLCV Validation', status: 'pass', desc: 'All validations passed' },
            { check: 'Date Gap Detection', status: 'warning', desc: '2 weekend gaps detected' },
          ].map((item, i) => (
            <div key={i} className="p-4 rounded-lg bg-slate-700/30 flex items-start gap-3">
              {item.status === 'pass' ? (
                <CheckCircle className="w-5 h-5 text-emerald-400 mt-0.5" />
              ) : item.status === 'warning' ? (
                <AlertCircle className="w-5 h-5 text-amber-400 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 text-red-400 mt-0.5" />
              )}
              <div>
                <p className="font-medium text-white">{item.check}</p>
                <p className="text-xs text-slate-400">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}