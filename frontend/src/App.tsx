import { Routes, Route } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import Dashboard from './pages/Dashboard'
import ProductList from './pages/ProductList'
import ProductInput from './pages/ProductInput'
import GenerateVideo from './pages/GenerateVideo'
import VideoList from './pages/VideoList'
import AnalyticsDashboard from './pages/AnalyticsDashboard'
import TimelineEditor from './pages/TimelineEditor'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/products" element={<ProductList />} />
        <Route path="/products/new" element={<ProductInput />} />
        <Route path="/products/:id" element={<ProductInput />} />
        <Route path="/generate" element={<GenerateVideo />} />
        <Route path="/videos" element={<VideoList />} />
        <Route path="/analytics" element={<AnalyticsDashboard />} />
        <Route path="/editor" element={<TimelineEditor />} />
      </Route>
    </Routes>
  )
}

export default App
