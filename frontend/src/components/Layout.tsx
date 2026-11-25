import { useState } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  LineChart, 
  BarChart3, 
  GitCompare, 
  Database, 
  Settings,
  Menu,
  X,
  TrendingUp,
  Activity
} from 'lucide-react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Forecasting', href: '/forecasting', icon: LineChart },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Backtesting', href: '/backtesting', icon: GitCompare },
  { name: 'Data Pipeline', href: '/data-pipeline', icon: Database },
  { name: 'Model Comparison', href: '/model-comparison', icon: TrendingUp },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="min-h-screen bg-slate-900 flex">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-slate-800 border-r border-slate-700
        transform transition-transform duration-200 ease-in-out
        lg:translate-x-0 lg:static lg:inset-auto
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-slate-700">
            <div className="flex items-center gap-2">
              <Activity className="w-8 h-8 text-primary-500" />
              <span className="text-lg font-bold gradient-text">StockIQ</span>
            </div>
            <button 
              className="lg:hidden text-slate-400 hover:text-white"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg font-medium
                    transition-all duration-200
                    ${isActive 
                      ? 'bg-primary-600/20 text-primary-400 border-l-2 border-primary-500' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                    }
                  `}
                >
                  <item.icon className="w-5 h-5" />
                  {item.name}
                </NavLink>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-slate-700">
            <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-slate-700/50">
              <Settings className="w-5 h-5 text-slate-400" />
              <span className="text-sm text-slate-300">Settings</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-6">
          <button 
            className="lg:hidden text-slate-400 hover:text-white"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-6 h-6" />
          </button>
          
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">
              {new Date().toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </span>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-emerald-500 flex items-center justify-center text-white font-bold text-sm">
              S
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}