import { useEffect, useState } from 'react'
import { fetchEcomAnalytics, fetchInsights, createAnalytics, type AnalyticsItem, fetchEcomVideos, type EcomVideo } from '../api/ecom'

const pink = '#FB7299'
const inputStyle: React.CSSProperties = { padding: '10px 12px', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 15, outline: 'none', color: '#232529' }

export default function AnalyticsDashboard() {
  const [items, setItems] = useState<AnalyticsItem[]>([])
  const [agg, setAgg] = useState<Record<string, number>>({})
  const [insights, setInsights] = useState('')
  const [insightSource, setInsightSource] = useState('')
  const [loadingInsights, setLoadingInsights] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [videos, setVideos] = useState<EcomVideo[]>([])
  const [form, setForm] = useState({ video_id: '', impressions: '', clicks: '', conversions: '', revenue: '', completion_rate: '', notes: '' })

  const loadData = () => {
    fetchEcomAnalytics({}).then(res => { setItems(res.items); setAgg(res.aggregated) })
  }

  useEffect(() => {
    loadData()
    fetchEcomVideos({ page_size: 100 }).then(res => setVideos(res.items))
  }, [])

  const handleInsights = async () => {
    setLoadingInsights(true)
    try {
      const res = await fetchInsights()
      setInsights(res.insights)
      setInsightSource(res.source)
    } finally { setLoadingInsights(false) }
  }

  const handleSubmitAnalytics = async (e: React.FormEvent) => {
    e.preventDefault()
    const impressions = parseInt(form.impressions) || 0
    const clicks = parseInt(form.clicks) || 0
    await createAnalytics({
      video_id: Number(form.video_id), impressions, clicks,
      ctr: impressions > 0 ? clicks / impressions : 0,
      conversions: parseInt(form.conversions) || 0, revenue: parseFloat(form.revenue) || 0,
      completion_rate: parseFloat(form.completion_rate) || 0, notes: form.notes,
      recorded_at: new Date().toISOString().slice(0, 10),
    })
    setShowForm(false)
    setForm({ video_id: '', impressions: '', clicks: '', conversions: '', revenue: '', completion_rate: '', notes: '' })
    loadData()
  }

  const metricCards = [
    { label: '总展示量', value: (agg.impressions || 0).toLocaleString(), icon: '👁️' },
    { label: '总点击量', value: (agg.clicks || 0).toLocaleString(), icon: '🖱️' },
    { label: '平均CTR', value: `${((agg.ctr || 0) * 100).toFixed(2)}%`, icon: '📊' },
    { label: '总转化', value: String(agg.conversions || 0), icon: '🎯' },
    { label: '总收入', value: `$${(agg.revenue || 0).toFixed(2)}`, icon: '💰' },
    { label: '平均完播率', value: `${((agg.completion_rate || 0) * 100).toFixed(0)}%`, icon: '⏱️' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#232529' }}>数据分析</h1>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => setShowForm(!showForm)} style={{ padding: '8px 16px', background: '#fff', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 13, cursor: 'pointer', color: '#606773' }}>录入数据</button>
          <button onClick={handleInsights} disabled={loadingInsights} style={{ padding: '8px 16px', background: pink, color: '#fff', border: 'none', borderRadius: 4, fontSize: 13, cursor: 'pointer', fontWeight: 500, opacity: loadingInsights ? 0.6 : 1 }}>
            {loadingInsights ? '分析中...' : 'AI 洞察'}
          </button>
        </div>
      </div>

      {/* 聚合指标 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, marginBottom: 20 }}>
        {metricCards.map(c => (
          <div key={c.label} style={{ background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', padding: '16px', textAlign: 'center' }}>
            <span style={{ fontSize: 20 }}>{c.icon}</span>
            <p style={{ fontSize: 11, color: '#9499A0', marginTop: 4 }}>{c.label}</p>
            <p style={{ fontSize: 22, fontWeight: 700, color: '#232529', marginTop: 2 }}>{c.value}</p>
          </div>
        ))}
      </div>

      {/* AI 洞察 */}
      {insights && (
        <div style={{ background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', padding: 20, marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: '#232529' }}>AI 洞察</h3>
            <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 3, background: 'rgba(251,114,153,0.1)', color: pink }}>{insightSource}</span>
          </div>
          <p style={{ fontSize: 13, color: '#606773', whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{insights}</p>
        </div>
      )}

      {/* 录入表单 */}
      {showForm && (
        <form onSubmit={handleSubmitAnalytics} style={{ background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', padding: 20, marginBottom: 20 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, color: '#232529', marginBottom: 12 }}>录入视频表现数据</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10, marginBottom: 10 }}>
            <select value={form.video_id} onChange={e => setForm(f => ({ ...f, video_id: e.target.value }))} style={inputStyle} required>
              <option value="">选择视频</option>
              {videos.map(v => <option key={v.id} value={v.id}>#{v.id} {v.product_name || '未知商品'}</option>)}
            </select>
            <input placeholder="展示量" type="number" value={form.impressions} onChange={e => setForm(f => ({ ...f, impressions: e.target.value }))} style={inputStyle} />
            <input placeholder="点击量" type="number" value={form.clicks} onChange={e => setForm(f => ({ ...f, clicks: e.target.value }))} style={inputStyle} />
            <input placeholder="转化数" type="number" value={form.conversions} onChange={e => setForm(f => ({ ...f, conversions: e.target.value }))} style={inputStyle} />
            <input placeholder="收入" type="number" step="0.01" value={form.revenue} onChange={e => setForm(f => ({ ...f, revenue: e.target.value }))} style={inputStyle} />
            <input placeholder="完播率 (0-1)" type="number" step="0.01" min="0" max="1" value={form.completion_rate} onChange={e => setForm(f => ({ ...f, completion_rate: e.target.value }))} style={inputStyle} />
            <input placeholder="备注" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} style={inputStyle} />
          </div>
          <button type="submit" style={{ padding: '8px 20px', background: pink, color: '#fff', border: 'none', borderRadius: 4, fontSize: 13, cursor: 'pointer', fontWeight: 500 }}>提交</button>
        </form>
      )}

      {/* 数据明细 */}
      {items.length > 0 ? (
        <div style={{ background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #E3E5E7' }}>
                {['视频', '展示', '点击', 'CTR', '转化', '收入', '完播率', '日期'].map(h => (
                  <th key={h} style={{ padding: '10px 12px', textAlign: h === '视频' || h === '日期' ? 'left' : 'right', color: '#9499A0', fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr key={item.id} style={{ borderBottom: '1px solid #F0F1F3' }}>
                  <td style={{ padding: '10px 12px', color: '#232529', fontWeight: 500 }}>#{item.video_id}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', color: '#606773' }}>{item.impressions.toLocaleString()}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', color: '#606773' }}>{item.clicks.toLocaleString()}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', color: '#606773' }}>{(item.ctr * 100).toFixed(2)}%</td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', color: '#606773' }}>{item.conversions}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', color: '#606773' }}>${item.revenue.toFixed(2)}</td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', color: '#606773' }}>{(item.completion_rate * 100).toFixed(0)}%</td>
                  <td style={{ padding: '10px 12px', color: '#9499A0' }}>{item.recorded_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : !showForm ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#9499A0', background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <p style={{ fontSize: 48, marginBottom: 8 }}>📈</p>
          <p>暂无分析数据，点击"录入数据"添加</p>
        </div>
      ) : null}
    </div>
  )
}
