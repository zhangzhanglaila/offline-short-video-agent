import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: '仪表盘', icon: '📊' },
  { to: '/products', label: '商品管理', icon: '📦' },
  { to: '/products/new', label: '录入商品', icon: '➕' },
  { to: '/generate', label: '一键生成', icon: '🎬' },
  { to: '/videos', label: '视频列表', icon: '🎥' },
  { to: '/analytics', label: '数据分析', icon: '📈' },
  { to: '/editor', label: '时间线编辑', icon: '🎞️' },
]

export default function Sidebar() {
  return (
    <aside style={{ width: 220, background: '#fff', borderRight: '1px solid #E3E5E7', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <div style={{ padding: '20px 16px', borderBottom: '1px solid #E3E5E7' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 36, height: 36, background: 'linear-gradient(135deg, #FB7299, #FFA4C4)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: '#fff' }}>
            🎬
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#232529' }}>AIGC 带货视频</div>
            <div style={{ fontSize: 11, color: '#9499A0' }}>智能短视频生成系统</div>
          </div>
        </div>
      </div>
      <nav style={{ flex: 1, padding: '8px 0' }}>
        {links.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px', fontSize: 14, textDecoration: 'none', transition: 'all 0.2s',
              color: isActive ? '#FB7299' : '#606773',
              background: isActive ? 'rgba(251,114,153,0.06)' : 'transparent',
              borderLeft: isActive ? '3px solid #FB7299' : '3px solid transparent',
              fontWeight: isActive ? 600 : 400,
            })}
          >
            <span style={{ fontSize: 16 }}>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '12px 16px', borderTop: '1px solid #E3E5E7', fontSize: 11, color: '#9499A0' }}>
        v2.0 E-Commerce
      </div>
    </aside>
  )
}
