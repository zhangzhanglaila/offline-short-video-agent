import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchEcomVideos } from '../api/ecom'

const s = {
  card: { background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', padding: 20 } as React.CSSProperties,
  pink: '#FB7299',
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [videoCount, setVideoCount] = useState(0)
  const [doneCount, setDoneCount] = useState(0)

  useEffect(() => {
    fetchEcomVideos({ page_size: 1 }).then(res => setVideoCount(res.total)).catch(() => {})
    fetchEcomVideos({ page_size: 1, status: 'done' }).then(res => setDoneCount(res.total)).catch(() => {})
  }, [])

  const metricCards = [
    { label: '视频总数', value: videoCount, icon: '🎬', gradient: 'linear-gradient(135deg, #FB7299, #FFA4C4)' },
    { label: '已完成', value: doneCount, icon: '✅', gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
  ]

  const quickActions = [
    { icon: '🎬', title: '一键生成', desc: '输入主题，AI 自动生成短视频', to: '/generate' },
    { icon: '🎨', title: '模板库', desc: '浏览和选择视频模板', to: '/templates' },
    { icon: '🎥', title: '历史记录', desc: '查看和管理生成的视频', to: '/videos' },
  ]

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, color: '#232529', marginBottom: 24 }}>仪表盘</h1>

      {/* 指标卡片 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16, marginBottom: 24 }}>
        {metricCards.map(c => (
          <div key={c.label} style={{ ...s.card, display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: c.gradient, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, flexShrink: 0 }}>
              {c.icon}
            </div>
            <div>
              <div style={{ fontSize: 13, color: '#9499A0' }}>{c.label}</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: '#232529', lineHeight: 1.2 }}>{c.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* 快速开始 */}
      <div style={s.card}>
        <h2 style={{ fontSize: 16, fontWeight: 600, color: '#232529', marginBottom: 16 }}>快速开始</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {quickActions.map(a => (
            <div
              key={a.to}
              onClick={() => navigate(a.to)}
              style={{ padding: 20, border: '1px solid #E3E5E7', borderRadius: 8, cursor: 'pointer', transition: 'all 0.2s' }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = s.pink; (e.currentTarget as HTMLElement).style.boxShadow = '0 4px 12px rgba(251,114,153,0.15)' }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = '#E3E5E7'; (e.currentTarget as HTMLElement).style.boxShadow = 'none' }}
            >
              <span style={{ fontSize: 28 }}>{a.icon}</span>
              <p style={{ fontSize: 15, fontWeight: 600, color: '#232529', margin: '8px 0 4px' }}>{a.title}</p>
              <p style={{ fontSize: 13, color: '#606773' }}>{a.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
