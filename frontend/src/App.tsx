import { Routes, Route } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import Dashboard from './pages/Dashboard'
import GenerateVideo from './pages/GenerateVideo'
import VideoList from './pages/VideoList'
import TimelineEditor from './pages/TimelineEditor'
import TemplateGallery from './pages/TemplateGallery'

function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/generate" element={<GenerateVideo />} />
        <Route path="/videos" element={<VideoList />} />
        <Route path="/editor" element={<TimelineEditor />} />
        <Route path="/templates" element={<TemplateGallery />} />
      </Route>
    </Routes>
  )
}

export default App
