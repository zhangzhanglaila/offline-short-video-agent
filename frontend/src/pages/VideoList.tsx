import { useEffect, useState, useCallback } from 'react'
import { fetchEcomVideos, deleteEcomVideo, deleteAllEcomVideos, type EcomVideo } from '../api/ecom'

const pink = '#FB7299'
const statusMap: Record<string, { label: string; bg: string; color: string }> = {
  draft: { label: '草稿', bg: '#F5F5F5', color: '#999' },
  generating: { label: '生成中', bg: '#E3F2FD', color: '#1976D2' },
  generated: { label: '已生成', bg: '#E8F5E9', color: '#4CAF50' },
  done: { label: '已完成', bg: '#E8F5E9', color: '#4CAF50' },
  failed: { label: '失败', bg: '#FFF3F0', color: '#FF4D4F' },
}

export default function VideoList() {
  const [videos, setVideos] = useState<EcomVideo[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [playingId, setPlayingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [deletingAll, setDeletingAll] = useState(false)

  const loadVideos = useCallback(() => {
    setLoading(true)
    fetchEcomVideos({ page, status: statusFilter, page_size: 12 }).then(res => {
      setVideos(res.items)
      setTotal(res.total)
      setLoading(false)
    })
  }, [page, statusFilter])

  useEffect(() => { loadVideos() }, [loadVideos])

  const handleDelete = async (id: number) => {
    if (!window.confirm('确认删除该视频？')) return
    setDeletingId(id)
    try {
      await deleteEcomVideo(id)
      loadVideos()
    } catch (e) {
      alert('删除失败: ' + (e as Error).message)
    } finally {
      setDeletingId(null)
    }
  }

  const handleDeleteAll = async () => {
    if (!window.confirm(`确认删除全部 ${total} 个视频？此操作不可撤销！`)) return
    setDeletingAll(true)
    try {
      const res = await deleteAllEcomVideos()
      alert(`已删除 ${res.deleted_count} 个视频`)
      loadVideos()
    } catch (e) {
      alert('删除失败: ' + (e as Error).message)
    } finally {
      setDeletingAll(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#232529' }}>视频列表</h1>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }} style={{ padding: '6px 12px', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 13 }}>
            <option value="">全部状态</option>
            <option value="draft">草稿</option>
            <option value="generating">生成中</option>
            <option value="generated">已生成</option>
            <option value="done">已完成</option>
            <option value="failed">失败</option>
          </select>
          {total > 0 && (
            <button onClick={handleDeleteAll} disabled={deletingAll} style={{ padding: '6px 16px', background: '#FF4D4F', color: '#fff', border: 'none', borderRadius: 4, fontSize: 13, cursor: deletingAll ? 'not-allowed' : 'pointer', opacity: deletingAll ? 0.6 : 1 }}>
              {deletingAll ? '删除中...' : '一键删除全部'}
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}>
          <div style={{ width: 200, height: 4, background: '#E3E5E7', borderRadius: 2, margin: '0 auto 12px', overflow: 'hidden' }}>
            <div style={{ width: '40%', height: '100%', background: pink, borderRadius: 2, animation: 'progress-slide 1.2s ease-in-out infinite' }} />
          </div>
          <p style={{ color: '#9499A0', fontSize: 13 }}>加载中...</p>
          <style>{`@keyframes progress-slide { 0% { transform: translateX(-100%); } 50% { transform: translateX(150%); } 100% { transform: translateX(-100%); } }`}</style>
        </div>
      ) : videos.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#9499A0', background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <p style={{ fontSize: 48, marginBottom: 8 }}>🎥</p>
          <p>暂无视频，请先生成</p>
        </div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
            {videos.map(v => {
              const st = statusMap[v.status] || statusMap.draft
              const isDeleting = deletingId === v.id
              return (
                <div key={v.id} style={{ background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', overflow: 'hidden', transition: 'box-shadow 0.2s', opacity: isDeleting ? 0.5 : 1, pointerEvents: isDeleting ? 'none' : 'auto' }}
                  onMouseEnter={e => (e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.12)')}
                  onMouseLeave={e => (e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)')}
                >
                  {/* 视频预览区 */}
                  <div style={{ aspectRatio: '16/9', background: '#F0F1F3', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                    {v.video_url ? (
                      playingId === v.id ? (
                        <video src={v.video_url} controls autoPlay style={{ width: '100%', height: '100%', objectFit: 'cover' }} onEnded={() => setPlayingId(null)} />
                      ) : (
                        <div onClick={() => setPlayingId(v.id)} style={{ cursor: 'pointer', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #232529, #3a3d42)' }}>
                          <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'rgba(255,255,255,0.9)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <span style={{ fontSize: 20, color: pink, marginLeft: 3 }}>▶</span>
                          </div>
                        </div>
                      )
                    ) : (
                      <span style={{ fontSize: 36 }}>🎬</span>
                    )}
                    {/* 删除按钮 */}
                    <button onClick={() => handleDelete(v.id)} style={{ position: 'absolute', top: 8, right: 8, width: 28, height: 28, borderRadius: '50%', background: 'rgba(0,0,0,0.5)', color: '#fff', border: 'none', cursor: 'pointer', fontSize: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'background 0.2s' }}
                      onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,77,79,0.85)')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'rgba(0,0,0,0.5)')}
                      title="删除视频"
                    >
                      ✕
                    </button>
                  </div>
                  {/* 信息区 */}
                  <div style={{ padding: 14 }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 8 }}>
                      <p style={{ fontSize: 14, fontWeight: 600, color: '#232529', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {v.product_name || `商品 #${v.product_id}`}
                      </p>
                      <span style={{ marginLeft: 8, padding: '2px 8px', borderRadius: 3, fontSize: 11, background: st.bg, color: st.color, flexShrink: 0 }}>
                        {st.label}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: 12, fontSize: 13, color: '#606773' }}>
                      <span>{v.platform}</span>
                      <span>{v.style}</span>
                      {v.duration && <span>{Math.round(v.duration)}s</span>}
                    </div>
                    <p style={{ fontSize: 11, color: '#C9CDD4', marginTop: 8 }}>{v.created_at?.slice(0, 10)}</p>
                  </div>
                </div>
              )
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16, fontSize: 13, color: '#9499A0' }}>
            <span>共 {total} 个视频</span>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} style={{ padding: '6px 16px', background: '#fff', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 13, cursor: 'pointer', opacity: page <= 1 ? 0.4 : 1 }}>上一页</button>
              <span>第 {page} 页</span>
              <button disabled={videos.length < 12} onClick={() => setPage(p => p + 1)} style={{ padding: '6px 16px', background: '#fff', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 13, cursor: 'pointer', opacity: videos.length < 12 ? 0.4 : 1 }}>下一页</button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
