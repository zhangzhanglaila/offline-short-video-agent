import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'

export default function AppLayout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#F5F6F7' }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: 'auto' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '20px 24px' }}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
