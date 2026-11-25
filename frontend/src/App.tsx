import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Forecasting from './pages/Forecasting'
import Analytics from './pages/Analytics'
import Backtesting from './pages/Backtesting'
import DataPipeline from './pages/DataPipeline'
import ModelComparison from './pages/ModelComparison'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="forecasting" element={<Forecasting />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="backtesting" element={<Backtesting />} />
          <Route path="data-pipeline" element={<DataPipeline />} />
          <Route path="model-comparison" element={<ModelComparison />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App