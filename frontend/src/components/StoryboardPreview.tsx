import { useEffect, useMemo, useRef, useState } from 'react'

const pink = '#FB7299'

export interface StoryboardScene {
  time?: string
  title?: string
  bullets?: string[]
  subtitle?: string
  duration?: number
  material_url?: string
  style?: 'comic' | 'realistic'
}

interface Props {
  storyboard: StoryboardScene[]
  fullScript: string
  ttsAudioUrl?: string
  ttsDuration?: number
  onUploadMaterial?: (sceneIndex: number, file: File) => void
  onEditScene?: (index: number, field: string, value: string | string[]) => void
  editable?: boolean
  renderMode?: 'contain' | 'side'
  visualStyle?: string
  visualStyles?: Record<string, { name_cn: string }>
}

function buildFallback(script: string): StoryboardScene[] {
  const chunks = script.split(/(?<=[。！？!?])\s*|\n+/).map(s => s.trim()).filter(Boolean)
  const count = Math.max(3, Math.min(8, chunks.length || 3))
  const base = 5
  return Array.from({ length: count }).map((_, i) => {
    const t = chunks[i] || chunks[chunks.length - 1] || '内容介绍'
    return {
      time: `${i * base}-${(i + 1) * base}s`,
      title: i === 0 ? 'Hook' : i === count - 1 ? 'CTA' : `亮点 ${i}`,
      bullets: t.split(/[，。；;、]/).map(x => x.trim()).filter(Boolean).slice(0, 4),
      subtitle: t,
      duration: base,
      style: 'comic',
    }
  })
}

export default function StoryboardPreview({ storyboard, fullScript, ttsAudioUrl, onUploadMaterial, onEditScene, editable = false, renderMode = 'contain', visualStyle, visualStyles }: Props) {
  const scenes = useMemo(() => (storyboard.length ? storyboard : buildFallback(fullScript)), [storyboard, fullScript])
  const [current, setCurrent] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [lightbox, setLightbox] = useState<number | null>(null)
  const [fadeTick, setFadeTick] = useState(0)
  const audioRef = useRef<HTMLAudioElement>(null)
  const autoTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const listRefs = useRef<(HTMLDivElement | null)[]>([])
  const panelRef = useRef<HTMLDivElement>(null)
  const totalDuration = useMemo(() => scenes.reduce((a, s) => a + (s.duration || 5), 0), [scenes])

  useEffect(() => {
    listRefs.current[current]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    setFadeTick(t => t + 1)
  }, [current])

  useEffect(() => () => {
    if (autoTimer.current) clearInterval(autoTimer.current)
  }, [])

  const seekToScene = (idx: number) => {
    if (idx < 0 || idx >= scenes.length) return
    setCurrent(idx)
    if (playing && ttsAudioUrl && audioRef.current) {
      const t = scenes.slice(0, idx).reduce((a, s) => a + (s.duration || 5), 0)
      audioRef.current.currentTime = t
    }
  }

  const startAuto = () => {
    if (autoTimer.current) clearInterval(autoTimer.current)
    autoTimer.current = setInterval(() => {
      setCurrent(prev => {
        const next = prev + 1
        if (next >= scenes.length) {
          setPlaying(false)
          if (autoTimer.current) clearInterval(autoTimer.current)
          return prev
        }
        return next
      })
    }, 250)
  }

  const handlePlay = () => {
    if (playing) {
      setPlaying(false)
      audioRef.current?.pause()
      if (autoTimer.current) clearInterval(autoTimer.current)
      return
    }
    setPlaying(true)
    if (ttsAudioUrl && audioRef.current) {
      const startAt = scenes.slice(0, current).reduce((a, s) => a + (s.duration || 5), 0)
      audioRef.current.currentTime = startAt
      void audioRef.current.play()
      return
    }
    startAuto()
  }

  useEffect(() => {
    if (!ttsAudioUrl || !playing || !audioRef.current) return
    const audio = audioRef.current
    const onTime = () => {
      const t = audio.currentTime
      let acc = 0
      for (let i = 0; i < scenes.length; i++) {
        const d = scenes[i].duration || 5
        if (t >= acc && t < acc + d) {
          if (i !== current) setCurrent(i)
          return
        }
        acc += d
      }
    }
    const onEnd = () => setPlaying(false)
    audio.addEventListener('timeupdate', onTime)
    audio.addEventListener('ended', onEnd)
    return () => {
      audio.removeEventListener('timeupdate', onTime)
      audio.removeEventListener('ended', onEnd)
    }
  }, [ttsAudioUrl, playing, scenes, current])

  const scene = scenes[current]
  const materialScene = scenes[lightbox ?? current]
  const displayUrl = scene.material_url

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16 }}>
      <div style={{ maxHeight: 560, overflowY: 'auto', paddingRight: 6 }}>
        {scenes.map((s, i) => (
          <div
            key={i}
            ref={el => { listRefs.current[i] = el }}
            onClick={() => seekToScene(i)}
            style={{
              border: `1px solid ${i === current ? pink : '#E4E7EC'}`,
              background: i === current ? 'rgba(251,114,153,0.07)' : '#fff',
              borderRadius: 10,
              padding: 10,
              marginBottom: 8,
              cursor: 'pointer',
              boxShadow: i === current ? '0 6px 16px rgba(251,114,153,0.16)' : '0 2px 4px rgba(0,0,0,0.04)',
            }}
          >
            <div style={{ fontSize: 12, color: '#8A8F99' }}>{s.time || `${i}`}</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#1F2328', marginTop: 3 }}>{s.title || `场景 ${i + 1}`}</div>
          </div>
        ))}
      </div>
      <div>
        <div
          ref={panelRef}
          key={fadeTick}
          style={{
            borderRadius: 12,
            border: '2px solid #FFD6E2',
            background: 'linear-gradient(155deg, #FAFBFC 0%, #F5F6F7 100%)',
            padding: 14,
            animation: 'scene-fade .28s ease',
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <div>
              <div style={{ border: '2px solid #FFD6E2', background: '#fff', borderRadius: 10, padding: 10, boxShadow: '0 4px 10px rgba(0,0,0,0.06)' }}>
                {editable
                  ? <input value={scene.title || ''} onChange={e => onEditScene?.(current, 'title', e.target.value)} style={{ width: '100%', fontSize: 20, fontWeight: 800, border: 0, outline: 'none' }} />
                  : <div style={{ fontSize: 20, fontWeight: 800 }}>{scene.title || `场景 ${current + 1}`}</div>}
              </div>
              <div style={{ marginTop: 8, display: 'grid', gap: 8 }}>
                {(scene.bullets || []).map((b, i) => (
                  <div key={i} style={{ border: '1px solid #E8EBF0', background: '#fff', borderRadius: 10, padding: '8px 10px', boxShadow: '0 3px 8px rgba(0,0,0,0.04)' }}>
                    {editable
                      ? <input value={b} onChange={e => onEditScene?.(current, 'bullets', (scene.bullets || []).map((x, bi) => bi === i ? e.target.value : x))} style={{ width: '100%', border: 0, outline: 'none' }} />
                      : <span style={{ color: i === 0 ? '#1F2328' : '#3F4753', fontWeight: i === 0 ? 700 : 500 }}>{`• ${b}`}</span>}
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 8, border: '1px dashed #D7DBE0', background: '#fff', borderRadius: 10, padding: 10 }}>
                {editable
                  ? <textarea value={scene.subtitle || ''} onChange={e => onEditScene?.(current, 'subtitle', e.target.value)} rows={3} style={{ width: '100%', resize: 'vertical', border: 0, outline: 'none' }} />
                  : <div style={{ color: '#5A6472', fontWeight: 600 }}>{scene.subtitle || '辅助说明'}</div>}
              </div>
            </div>
            <div>
              {displayUrl ? (
                <img
                  src={displayUrl}
                  onClick={() => setLightbox(current)}
                  onDragOver={e => e.preventDefault()}
                  onDrop={e => {
                    e.preventDefault()
                    const f = e.dataTransfer.files?.[0]
                    if (f && onUploadMaterial) onUploadMaterial(current, f)
                  }}
                  style={{ width: '100%', height: 340, objectFit: renderMode === 'contain' ? 'contain' : 'cover', background: renderMode === 'contain' ? '#f3f5f7' : 'transparent', borderRadius: 10, cursor: 'zoom-in', transform: 'scale(1.03)', transition: 'transform .35s ease, opacity .28s ease', boxShadow: '0 8px 20px rgba(0,0,0,0.14)' }}
                />
              ) : (
                <div
                  onDragOver={e => e.preventDefault()}
                  onDrop={e => {
                    e.preventDefault()
                    const f = e.dataTransfer.files?.[0]
                    if (f && onUploadMaterial) onUploadMaterial(current, f)
                  }}
                  style={{ height: 340, borderRadius: 10, border: '2px dashed #D8DCE2', display: 'grid', placeItems: 'center', background: '#fff', color: '#7A8494' }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <div>{visualStyles?.[visualStyle ?? '']?.name_cn ?? visualStyle ?? '素材'}占位图</div>
                    {editable && onUploadMaterial && <label style={{ color: pink, cursor: 'pointer', marginTop: 8, display: 'inline-block' }}>替换素材<input type="file" accept="image/*,video/*" style={{ display: 'none' }} onChange={e => { const f = e.target.files?.[0]; if (f) onUploadMaterial(current, f) }} /></label>}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={handlePlay} style={{ width: 36, height: 36, borderRadius: '50%', border: 0, background: pink, color: '#fff', cursor: 'pointer' }}>{playing ? '⏸' : '▶'}</button>
          <div style={{ display: 'flex', flex: 1, gap: 4 }}>
            {scenes.map((s, i) => (
              <div key={i} onClick={() => seekToScene(i)} style={{ flex: (s.duration || 5) / Math.max(1, totalDuration), height: 6, borderRadius: 4, background: i <= current ? pink : '#E5E7EB', cursor: 'pointer' }} />
            ))}
          </div>
          <span style={{ fontSize: 12, color: '#7A8494' }}>{current + 1}/{scenes.length}</span>
        </div>
      </div>
      {ttsAudioUrl && <audio ref={audioRef} src={ttsAudioUrl} preload="auto" />}
      {lightbox !== null && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 2200, background: 'rgba(0,0,0,0.86)', display: 'grid', placeItems: 'center' }} onClick={() => setLightbox(null)}>
          <button onClick={e => { e.stopPropagation(); setLightbox(v => (v === null ? null : (v - 1 + scenes.length) % scenes.length)) }} style={{ position: 'absolute', left: 24, border: 0, background: 'transparent', color: '#fff', fontSize: 28, cursor: 'pointer' }}>‹</button>
          <img src={materialScene.material_url || ''} style={{ maxWidth: '92%', maxHeight: '92%' }} />
          <button onClick={e => { e.stopPropagation(); setLightbox(v => (v === null ? null : (v + 1) % scenes.length)) }} style={{ position: 'absolute', right: 24, border: 0, background: 'transparent', color: '#fff', fontSize: 28, cursor: 'pointer' }}>›</button>
        </div>
      )}
      <style>{`@keyframes scene-fade{from{opacity:.45;transform:scale(1.01)}to{opacity:1;transform:scale(1)}}`}</style>
    </div>
  )
}
