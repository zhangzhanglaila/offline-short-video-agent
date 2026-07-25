import { useEffect, useState, useRef, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useGenerateStore } from '../stores/generateStore'
import { fetchGenerateMeta } from '../api/generate'
import StoryboardPreview from '../components/StoryboardPreview'
import { fetchConfig, type ApiConfig } from '../api/backend'

const pink = '#FB7299'
const inputStyle: React.CSSProperties = { width: '100%', padding: '10px 12px', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 15, outline: 'none', boxSizing: 'border-box', color: '#232529' }
const labelStyle: React.CSSProperties = { display: 'block', fontSize: 14, fontWeight: 500, color: '#232529', marginBottom: 6 }
const cardStyle: React.CSSProperties = { background: '#fff', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', padding: 24 }

/* ---- Auto-expanding textarea ---- */
function AutoTextarea({ value, onChange, minRows = 2, style = {} }: {
  value: string; onChange: (v: string) => void; minRows?: number; style?: React.CSSProperties
}) {
  const ref = useRef<HTMLTextAreaElement>(null)
  const autoResize = useCallback(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = el.scrollHeight + 'px'
  }, [])
  useEffect(() => { autoResize() }, [value, autoResize])
  return (
    <textarea
      ref={ref}
      value={value}
      onChange={e => onChange(e.target.value)}
      rows={minRows}
      style={{
        ...inputStyle,
        resize: 'none',
        overflow: 'hidden',
        lineHeight: 1.6,
        ...style,
      }}
    />
  )
}

/* ---- Pipeline steps ---- */
const PIPELINE_STEPS = [
  { key: 'script_ready', label: '脚本生成', icon: '✍' },
  { key: 'script_edited', label: '编辑脚本', icon: '✏' },
  { key: 'tts_ready', label: '生成配音', icon: '🎤' },
  { key: 'rendering', label: '渲染视频', icon: '🎬' },
  { key: 'done', label: '完成', icon: '✅' },
]

function stepIndex(step: string): number {
  const idx = PIPELINE_STEPS.findIndex(s => s.key === step)
  return idx >= 0 ? idx : -1
}

/* ---- 当前活动状态文字 ---- */
function getStatusText(pipelineStep: string, generating: boolean, ttsGenerating: boolean): string | null {
  if (generating) return '正在生成脚本...'
  if (ttsGenerating) return '正在生成配音...'
  switch (pipelineStep) {
    case 'script_ready': return '脚本已生成，请编辑'
    case 'script_edited': return '脚本已保存，请生成配音'
    case 'tts_ready': return '配音已就绪，请生成视频'
    case 'rendering': return '正在渲染视频...'
    case 'done': return '视频生成完成'
    case 'failed': return '生成失败'
    default: return null
  }
}

export default function GenerateVideo() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const [topic, setTopic] = useState(searchParams.get('topic') || '')
  const [category, setCategory] = useState('短视频')
  const [categories, setCategories] = useState<string[]>([])
  const [style, setStyle] = useState('soft_sell')
  const [platform, setPlatform] = useState('抖音')
  const [duration, setDuration] = useState(30)
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait')
  const [visualStyle, setVisualStyleLocal] = useState('manga')
  const [visualStyles, setVisualStyles] = useState<Record<string, { name_cn: string; paper_color: string; accent_red: string; text_c: string }>>({})
  const [platforms, setPlatforms] = useState<string[]>([])
  const [showApiConfig, setShowApiConfig] = useState(false)
  const [apiConfig, setApiConfig] = useState<ApiConfig>({ api_key: '', api_base: '', api_model: '' })
  const [ttsPulse, setTtsPulse] = useState(false)

  // 各区域 ref，用于点击进度条跳转
  const scriptSectionRef = useRef<HTMLDivElement>(null)
  const ttsSectionRef = useRef<HTMLDivElement>(null)
  const renderSectionRef = useRef<HTMLDivElement>(null)
  const doneSectionRef = useRef<HTMLDivElement>(null)

  const {
    generating, error, videoId, pipelineStep,
    editedHook, editedBody, editedCta, editedFullScript, storyboard,
    animationStyle,
    ttsAudioUrl, ttsDuration, ttsGenerating,
    videoUrl, successMsg,
    generate, setField, setStoryboardItem, setAnimationStyle, setOrientation: setStoreOrientation, setVisualStyle: setStoreVisualStyle, saveScript, generateTts, uploadMaterial, startRender, reset, stopPolling,
  } = useGenerateStore()

  useEffect(() => {
    fetchGenerateMeta().then(meta => {
      setCategories(meta.categories || [])
      setPlatforms(meta.platforms || [])
      if (meta.visual_styles) setVisualStyles(meta.visual_styles)
    }).catch(() => {})
    fetchConfig().then(setApiConfig).catch(() => {})
  }, [])

  // 保存脚本后自动滚动到 TTS 区并触发按钮脉冲
  useEffect(() => {
    if (pipelineStep === 'script_edited' && videoId) {
      setTimeout(() => {
        ttsSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
        setTtsPulse(true)
        setTimeout(() => setTtsPulse(false), 3000)
      }, 300)
    }
  }, [pipelineStep, videoId])

  // 渲染完成后滚动到视频区
  useEffect(() => {
    if (pipelineStep === 'done' && videoUrl) {
      setTimeout(() => doneSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300)
    }
  }, [pipelineStep, videoUrl])

  const handleGenerate = async () => {
    if (!topic.trim()) return
    try {
      const cfg = await fetchConfig()
      if (!cfg.api_key || cfg.api_key.trim() === '') {
        setShowApiConfig(true)
        return
      }
      setApiConfig(cfg)
    } catch {
      setShowApiConfig(true)
      return
    }
    setStoreOrientation(orientation)
    setStoreVisualStyle(visualStyle)
    generate({ topic: topic.trim(), category, style, platform, duration, animation_style: animationStyle, orientation, visual_style: visualStyle })
  }

  const handleSaveApiConfig = async () => {
    if (!apiConfig.api_key.trim()) return
    const { saveConfig } = await import('../api/backend')
    try {
      const res = await saveConfig(apiConfig)
      if (res.success) {
        setShowApiConfig(false)
        setStoreOrientation(orientation)
        setStoreVisualStyle(visualStyle)
        generate({ topic: topic.trim(), category, style, platform, duration, animation_style: animationStyle, orientation, visual_style: visualStyle })
      }
    } catch (e) {
      alert('保存配置失败: ' + String(e))
    }
  }

  // 点击进度条跳转到对应区域，并回退到该步骤状态
  const goToStep = (stepIdx: number) => {
    // 只允许回退到已完成的步骤
    if (stepIdx >= currentStepIdx && pipelineStep !== 'done') return
    // 如果正在渲染中，先停止轮询
    if (pipelineStep === 'rendering') stopPolling()
    const refs = [scriptSectionRef, scriptSectionRef, ttsSectionRef, renderSectionRef, doneSectionRef]
    const targetStep = PIPELINE_STEPS[stepIdx]?.key
    if (targetStep) {
      setField('pipelineStep', targetStep)
      setTimeout(() => refs[stepIdx]?.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100)
    }
  }

  // 打开添加商品弹窗
  const scrollToStep = (stepIdx: number) => {
    const refs = [scriptSectionRef, scriptSectionRef, ttsSectionRef, renderSectionRef, doneSectionRef]
    setTimeout(() => refs[stepIdx]?.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 100)
  }

  const currentStepIdx = pipelineStep === 'failed' ? PIPELINE_STEPS.length - 2 : stepIndex(pipelineStep)

  // 脚本风格中文映射
  const styleLabel = (key: string) => {
    const map: Record<string, string> = { soft_sell: '温和种草', hard_sell: '硬核带货', story: '故事型', tutorial: '教程型' }
    return map[key] || key.replace('_', ' ')
  }

  // 右下角状态提示
  const statusText = getStatusText(pipelineStep, generating, ttsGenerating)

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 700, color: '#232529', marginBottom: 24 }}>一键生成视频</h1>

      {/* 右下角浮动状态提示 */}
      {statusText && videoId && (
        <div style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 999,
          padding: '12px 20px', borderRadius: 8,
          background: pipelineStep === 'failed' ? '#FFF3F0' : pipelineStep === 'done' ? '#F6FFED' : '#fff',
          border: `1px solid ${pipelineStep === 'failed' ? '#FFCCC7' : pipelineStep === 'done' ? '#B7EB8F' : '#E3E5E7'}`,
          boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
          display: 'flex', alignItems: 'center', gap: 10,
          fontSize: 14, fontWeight: 500,
          color: pipelineStep === 'failed' ? '#CF1322' : pipelineStep === 'done' ? '#52C41A' : '#232529',
          animation: 'toast-slide-in 0.3s ease-out',
          maxWidth: 320,
        }}>
          {(generating || ttsGenerating || pipelineStep === 'rendering') && (
            <div style={{
              width: 16, height: 16, flexShrink: 0,
              border: `2px solid ${pink}`, borderTopColor: 'transparent',
              borderRadius: '50%', animation: 'spin 1s linear infinite',
            }} />
          )}
          {pipelineStep === 'done' && <span style={{ fontSize: 16 }}>✓</span>}
          {pipelineStep === 'failed' && <span style={{ fontSize: 16 }}>✕</span>}
          {pipelineStep === 'script_ready' && <span style={{ fontSize: 16 }}>✍</span>}
          {pipelineStep === 'script_edited' && <span style={{ fontSize: 16 }}>🎤</span>}
          {pipelineStep === 'tts_ready' && <span style={{ fontSize: 16 }}>🎬</span>}
          <span>{statusText}</span>
          <style>{`
            @keyframes toast-slide-in {
              from { transform: translateX(100%); opacity: 0; }
              to { transform: translateX(0); opacity: 1; }
            }
          `}</style>
        </div>
      )}

      {/* 成功提示 */}
      {successMsg && (
        <div style={{ position: 'fixed', top: 20, right: 20, zIndex: 1000, padding: '10px 20px', background: '#F6FFED', border: '1px solid #B7EB8F', borderRadius: 6, fontSize: 14, color: '#52C41A', fontWeight: 500, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
          {successMsg}
        </div>
      )}

      {/* 配置面板：生成前完整表单，生成后折叠为摘要 */}
      {!videoId ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 20, marginBottom: 20 }}>
          <div style={cardStyle}>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>视频主题 / 描述 *</label>
              <AutoTextarea value={topic} onChange={setTopic} minRows={3} style={{ fontSize: 15 }} />
              <p style={{ fontSize: 12, color: '#9499A0', marginTop: 4 }}>例：讲解什么是区块链 / 三分钟看懂黑洞 / 一款降噪耳机的种草短片</p>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>分类</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: 8 }}>
                {(categories.length > 0 ? categories : ['教育讲解', '短视频', '纪录片', '商业宣传']).map(cat => (
                  <div key={cat} onClick={() => setCategory(cat)}
                    style={{ padding: '10px 12px', border: `2px solid ${category === cat ? pink : '#E3E5E7'}`, borderRadius: 8, cursor: 'pointer', background: category === cat ? 'rgba(251,114,153,0.04)' : '#fff', textAlign: 'center', transition: 'all 0.2s', fontSize: 13, fontWeight: 600, color: category === cat ? pink : '#232529' }}>
                    {cat}
                  </div>
                ))}
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>脚本风格</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {[
                  { key: 'soft_sell', desc: '温和种草，娓娓道来' },
                  { key: 'hard_sell', desc: '硬核直给，突出重点' },
                  { key: 'story', desc: '故事型，有代入感' },
                  { key: 'tutorial', desc: '教程型，清晰讲解' },
                ].map(({ key, desc }) => (
                  <div key={key} onClick={() => setStyle(key)}
                    style={{ padding: 12, border: `1px solid ${style === key ? pink : '#E3E5E7'}`, borderRadius: 6, cursor: 'pointer', background: style === key ? 'rgba(251,114,153,0.04)' : '#fff', transition: 'all 0.2s' }}>
                    <p style={{ fontSize: 14, fontWeight: 600, color: style === key ? pink : '#232529' }}>{styleLabel(key)}</p>
                    <p style={{ fontSize: 12, color: '#606773', marginTop: 2 }}>{desc}</p>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={labelStyle}>目标平台</label>
                <select value={platform} onChange={e => setPlatform(e.target.value)} style={inputStyle}>
                  {platforms.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>视频时长（秒）</label>
                <input type="number" min={10} max={120} value={duration} onChange={e => setDuration(Number(e.target.value))} style={inputStyle} />
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>视频方向</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                {[
                  { key: 'portrait', label: '竖屏 (9:16)', icon: '📱', desc: '抖音/小红书' },
                  { key: 'landscape', label: '横屏 (16:9)', icon: '🖥', desc: 'B站/YouTube' },
                ].map(opt => (
                  <div key={opt.key}
                    onClick={() => { setOrientation(opt.key as 'portrait' | 'landscape'); setStoreOrientation(opt.key as 'portrait' | 'landscape') }}
                    style={{ padding: 12, border: `2px solid ${orientation === opt.key ? pink : '#E3E5E7'}`, borderRadius: 8, cursor: 'pointer', background: orientation === opt.key ? 'rgba(251,114,153,0.04)' : '#fff', textAlign: 'center', transition: 'all 0.2s' }}>
                    <span style={{ fontSize: 20, display: 'block', marginBottom: 4 }}>{opt.icon}</span>
                    <span style={{ fontSize: 13, fontWeight: 600, color: orientation === opt.key ? pink : '#232529' }}>{opt.label}</span>
                    <span style={{ fontSize: 11, color: '#9499A0', display: 'block', marginTop: 2 }}>{opt.desc}</span>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>视频视觉风格</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 8 }}>
                {Object.entries(visualStyles).length > 0 ? Object.entries(visualStyles).map(([key, cfg]) => {
                  const isActive = visualStyle === key
                  return (
                    <div key={key}
                      role="button" tabIndex={0}
                      onClick={() => { setVisualStyleLocal(key); setStoreVisualStyle(key) }}
                      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setVisualStyleLocal(key); setStoreVisualStyle(key) } }}
                      style={{
                        padding: 10, border: `2px solid ${isActive ? pink : '#E3E5E7'}`, borderRadius: 8,
                        cursor: 'pointer', background: isActive ? 'rgba(251,114,153,0.04)' : '#fff',
                        transition: 'all 0.2s', textAlign: 'center', outline: 'none',
                      }}>
                      <div style={{
                        height: 32, borderRadius: 4, marginBottom: 6,
                        background: cfg.paper_color,
                        border: `2px solid ${cfg.accent_red}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        <span style={{ fontSize: 11, color: cfg.text_c, fontWeight: 600 }}>Aa</span>
                      </div>
                      <div style={{ fontSize: 13, fontWeight: 600, color: isActive ? pink : '#1F2328' }}>{cfg.name_cn}</div>
                      <div style={{ fontSize: 11, color: '#8A8F99', marginTop: 1 }}>{key}</div>
                    </div>
                  )
                }) : (
                  Object.entries({ manga: { name_cn: '日式漫画', paper_color: '#FFF8F0', accent_red: '#E04040', text_c: '#1A1A2E' } }).map(([key, cfg]) => {
                    const isActive = visualStyle === key
                    return (
                      <div key={key}
                        role="button" tabIndex={0}
                        onClick={() => { setVisualStyleLocal(key); setStoreVisualStyle(key) }}
                        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setVisualStyleLocal(key); setStoreVisualStyle(key) } }}
                        style={{
                          padding: 10, border: `2px solid ${isActive ? pink : '#E3E5E7'}`, borderRadius: 8,
                          cursor: 'pointer', background: isActive ? 'rgba(251,114,153,0.04)' : '#fff',
                          transition: 'all 0.2s', textAlign: 'center', outline: 'none',
                        }}>
                        <div style={{ height: 32, borderRadius: 4, marginBottom: 6, background: cfg.paper_color, border: `2px solid ${cfg.accent_red}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <span style={{ fontSize: 11, color: cfg.text_c, fontWeight: 600 }}>Aa</span>
                        </div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: isActive ? pink : '#1F2328' }}>{cfg.name_cn}</div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>动画模式</label>
              <select value={animationStyle} onChange={e => setAnimationStyle(e.target.value as 'contain' | 'side')} style={inputStyle}>
                <option value="contain">完整显示（默认）</option>
                <option value="side">侧栏裁切</option>
              </select>
            </div>
            <button onClick={handleGenerate} disabled={!topic.trim() || generating}
              style={{ width: '100%', padding: '12px 0', background: pink, color: '#fff', border: 'none', borderRadius: 6, fontSize: 14, fontWeight: 600, cursor: 'pointer', opacity: (!topic.trim() || generating) ? 0.5 : 1 }}>
              {generating ? '脚本生成中...' : '开始生成'}
            </button>
            {generating && (
              <div style={{ marginTop: 12 }}>
                <div style={{ width: '100%', height: 4, background: '#E3E5E7', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ width: '30%', height: '100%', background: `linear-gradient(90deg, ${pink}, #FF9AB5)`, borderRadius: 2, animation: 'gen-progress 1.5s ease-in-out infinite' }} />
                </div>
                <style>{`@keyframes gen-progress { 0% { transform: translateX(-100%); } 50% { transform: translateX(233%); } 100% { transform: translateX(-100%); } }`}</style>
              </div>
            )}
            {error && <p style={{ color: '#FF4D4F', fontSize: 13, marginTop: 12 }}>{error}</p>}
          </div>

          <div style={cardStyle}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: '#232529', marginBottom: 12 }}>配置预览</h3>
            {topic.trim() ? (
              <div>
                <p style={{ fontSize: 13, color: '#9499A0', marginBottom: 4 }}>主题:</p>
                <p style={{ fontSize: 15, fontWeight: 600, color: '#232529', marginBottom: 12, lineHeight: 1.5 }}>{topic.trim()}</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 13, color: '#606773' }}>
                  <span>分类: <b style={{ color: '#232529' }}>{category}</b></span>
                  <span>脚本风格: <b style={{ color: '#232529' }}>{styleLabel(style)}</b></span>
                  <span>视觉风格: <b style={{ color: '#232529' }}>{visualStyles[visualStyle]?.name_cn || visualStyle}</b></span>
                  <span>平台: <b style={{ color: '#232529' }}>{platform}</b></span>
                  <span>时长: <b style={{ color: '#232529' }}>{duration}s</b> · {orientation === 'portrait' ? '竖屏' : '横屏'}</span>
                </div>
              </div>
            ) : (
              <p style={{ color: '#9499A0', fontSize: 13 }}>请先输入视频主题</p>
            )}
          </div>
        </div>
      ) : (
        /* 生成后的折叠摘要 */
        <div style={{ ...cardStyle, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          {topic.trim() && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 200 }}>
              <span style={{ fontSize: 14, color: '#9499A0' }}>主题:</span>
              <span style={{ fontSize: 15, fontWeight: 600, color: '#232529' }}>{topic.trim()}</span>
            </div>
          )}
          <div style={{ display: 'flex', gap: 16 }}>
            <span style={{ fontSize: 13, color: '#606773' }}>分类: <b>{category}</b></span>
            <span style={{ fontSize: 13, color: '#606773' }}>风格: <b>{styleLabel(style)}</b></span>
            <span style={{ fontSize: 13, color: '#606773' }}>视觉: <b>{visualStyles[visualStyle]?.name_cn || visualStyle}</b></span>
            <span style={{ fontSize: 13, color: '#606773' }}>平台: <b>{platform}</b></span>
            <span style={{ fontSize: 13, color: '#606773' }}>时长: <b>{duration}s</b></span>
          </div>
          <button onClick={reset} style={{ padding: '6px 14px', background: '#fff', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 12, cursor: 'pointer', color: '#606773' }}>
            重新配置
          </button>
        </div>
      )}

      {/* 进度条 — 滚动后固定在顶部，点击可跳转到对应区域 */}
      {videoId && (
        <div style={{ ...cardStyle, marginBottom: 20, position: 'sticky', top: -20, zIndex: 100, boxShadow: '0 6px 18px rgba(0,0,0,0.14)', border: '1px solid #E3E5E7' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
              {PIPELINE_STEPS.map((step, i) => {
                const isDone = i <= currentStepIdx || pipelineStep === 'done'
                const isActive = i === currentStepIdx + 1 && pipelineStep !== 'done' && pipelineStep !== 'failed'
                const isFailed = pipelineStep === 'failed' && i === currentStepIdx
                const canClickBack = isDone && i < currentStepIdx
                return (
                  <div key={step.key} style={{ display: 'flex', alignItems: 'center', flex: i < PIPELINE_STEPS.length - 1 ? 1 : undefined }}>
                    <div
                      onClick={() => canClickBack ? goToStep(i) : scrollToStep(i)}
                      style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 80, cursor: canClickBack ? 'pointer' : 'default', opacity: canClickBack ? 1 : 0.7 }}
                    >
                      <div style={{
                        width: 36, height: 36, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
                        background: isFailed ? '#FF4D4F' : isDone ? '#52C41A' : isActive ? pink : '#F0F1F3',
                        color: (isDone || isActive || isFailed) ? '#fff' : '#9499A0',
                        fontWeight: 600, transition: 'all 0.3s',
                      }}>
                        {isDone ? '✓' : step.icon}
                      </div>
                      <span style={{ fontSize: 11, color: isActive ? pink : isDone ? '#52C41A' : '#9499A0', marginTop: 4, fontWeight: isActive ? 600 : 400, textAlign: 'center' }}>
                        {step.label}
                      </span>
                    </div>
                    {i < PIPELINE_STEPS.length - 1 && (
                      <div style={{ flex: 1, height: 2, background: isDone ? '#52C41A' : '#E3E5E7', margin: '0 4px', marginBottom: 20 }} />
                    )}
                  </div>
                )
              })}
            </div>
        </div>
      )}

      {/* 脚本编辑区 */}
      {videoId && (pipelineStep === 'script_ready' || pipelineStep === 'script_edited') && (
        <div ref={scriptSectionRef} style={cardStyle}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: '#232529', marginBottom: 16 }}>编辑脚本</h3>

          <div style={{ marginBottom: 12 }}>
            <label style={labelStyle}>Hook（开头）</label>
            <AutoTextarea value={editedHook} onChange={v => setField('editedHook', v)} minRows={2} />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={labelStyle}>主体内容</label>
            <AutoTextarea value={editedBody} onChange={v => setField('editedBody', v)} minRows={3} />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={labelStyle}>行动号召 (CTA)</label>
            <AutoTextarea value={editedCta} onChange={v => setField('editedCta', v)} minRows={2} />
          </div>
          <div style={{ marginBottom: 20 }}>
            <label style={labelStyle}>完整脚本</label>
            <AutoTextarea value={editedFullScript} onChange={v => setField('editedFullScript', v)} minRows={4} />
          </div>

          {/* 图文对照预览 */}
          <div style={{ marginBottom: 16 }}>
            <label style={labelStyle}>分镜预览（文字 + 素材对照，点击场景可跳转，点击图片可放大）</label>
            <div style={{ background: '#FAFBFC', borderRadius: 8, padding: 16, border: '1px solid #F0F1F3' }}>
              <StoryboardPreview
                storyboard={storyboard}
                fullScript={editedFullScript}
                ttsAudioUrl={ttsAudioUrl || undefined}
                ttsDuration={ttsDuration || undefined}
                renderMode={animationStyle}
                visualStyle={visualStyle}
                visualStyles={visualStyles}
                onUploadMaterial={(idx, file) => uploadMaterial(idx, file)}
                onEditScene={(idx, field, value) => setStoryboardItem(idx, { [field]: value })}
                editable
              />
            </div>
          </div>

          <button onClick={saveScript}
            style={{ padding: '10px 24px', background: pink, color: '#fff', border: 'none', borderRadius: 4, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
            保存脚本
          </button>
        </div>
      )}

      {/* TTS 区 */}
      {videoId && pipelineStep === 'script_edited' && (
        <div ref={ttsSectionRef} style={{ ...cardStyle, marginTop: 20 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: '#232529', marginBottom: 12 }}>生成配音</h3>
          <p style={{ fontSize: 13, color: '#606773', marginBottom: 16 }}>确认脚本无误后，点击下方按钮生成 TTS 配音。</p>
          <button onClick={() => generateTts()} disabled={ttsGenerating}
            style={{
              padding: '12px 32px', background: pink, color: '#fff', border: 'none', borderRadius: 6,
              fontSize: 15, fontWeight: 700, cursor: 'pointer', opacity: ttsGenerating ? 0.5 : 1,
              animation: ttsPulse ? 'tts-pulse 1.2s ease-in-out 3' : 'none',
              boxShadow: ttsPulse ? '0 0 0 0 rgba(251,114,153,0.6)' : 'none',
            }}>
            {ttsGenerating ? '配音生成中...' : '确认生成配音'}
          </button>
          {ttsGenerating && (
            <div style={{ marginTop: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <div style={{ width: 16, height: 16, border: '2px solid #1976D2', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                <span style={{ fontSize: 13, color: '#1565C0' }}>正在生成语音...</span>
              </div>
              <div style={{ width: '100%', maxWidth: 300, height: 4, background: '#E3E5E7', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{ width: '30%', height: '100%', background: 'linear-gradient(90deg, #1976D2, #64B5F6)', borderRadius: 2, animation: 'tts-progress 1.5s ease-in-out infinite' }} />
              </div>
              <style>{`@keyframes tts-progress { 0% { transform: translateX(-100%); } 50% { transform: translateX(233%); } 100% { transform: translateX(-100%); } }`}</style>
            </div>
          )}
          <style>{`
            @keyframes spin { to { transform: rotate(360deg) } }
            @keyframes tts-pulse {
              0% { box-shadow: 0 0 0 0 rgba(251,114,153,0.6); }
              50% { box-shadow: 0 0 0 14px rgba(251,114,153,0); }
              100% { box-shadow: 0 0 0 0 rgba(251,114,153,0); }
            }
          `}</style>
        </div>
      )}

      {/* TTS 预览 + 渲染控制 */}
      {videoId && pipelineStep === 'tts_ready' && (
        <div ref={renderSectionRef} style={{ ...cardStyle, marginTop: 20 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: '#232529', marginBottom: 12 }}>配音预览</h3>
          {ttsAudioUrl && (
            <div style={{ marginBottom: 16 }}>
              <audio src={ttsAudioUrl} controls style={{ width: '100%', maxWidth: 480 }} />
              {ttsDuration > 0 && <p style={{ fontSize: 12, color: '#9499A0', marginTop: 4 }}>时长: {ttsDuration.toFixed(1)}s</p>}
            </div>
          )}
          <p style={{ fontSize: 13, color: '#606773', marginBottom: 16 }}>配音满意后，点击下方按钮开始渲染最终视频。</p>
          <button onClick={() => startRender()}
            style={{ padding: '10px 24px', background: '#52C41A', color: '#fff', border: 'none', borderRadius: 4, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
            生成视频
          </button>
        </div>
      )}

      {/* 渲染中 */}
      {videoId && pipelineStep === 'rendering' && (
        <div ref={renderSectionRef} style={{ ...cardStyle, marginTop: 20, textAlign: 'center', padding: '40px 24px' }}>
          <div style={{ width: 40, height: 40, border: `4px solid ${pink}`, borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
          <p style={{ fontSize: 15, color: '#232529', fontWeight: 500, marginBottom: 16 }}>视频渲染中...</p>
          <div style={{ width: '80%', maxWidth: 400, height: 6, background: '#E3E5E7', borderRadius: 3, margin: '0 auto 12px', overflow: 'hidden' }}>
            <div style={{ width: '33%', height: '100%', background: `linear-gradient(90deg, ${pink}, #FF9AB5)`, borderRadius: 3, animation: 'render-progress 2s ease-in-out infinite' }} />
          </div>
          <p style={{ fontSize: 13, color: '#9499A0' }}>正在进行动画合成、字幕烧录、多轨道混合，请耐心等待</p>
          <style>{`
            @keyframes spin { to { transform: rotate(360deg) } }
            @keyframes render-progress {
              0% { transform: translateX(-100%); }
              50% { transform: translateX(200%); }
              100% { transform: translateX(-100%); }
            }
          `}</style>
        </div>
      )}

      {/* 渲染完成 */}
      {videoId && pipelineStep === 'done' && videoUrl && (
        <div ref={doneSectionRef} style={{ ...cardStyle, marginTop: 20 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, color: '#232529', marginBottom: 16 }}>生成完成</h3>
          <div style={{ background: '#000', borderRadius: 6, overflow: 'hidden', maxWidth: 640, marginBottom: 12 }}>
            <video src={videoUrl} controls style={{ width: '100%', display: 'block' }} />
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <a href={videoUrl} download style={{ padding: '8px 20px', background: '#52C41A', color: '#fff', borderRadius: 4, fontSize: 14, textDecoration: 'none', fontWeight: 500 }}>下载视频</a>
            <button onClick={() => navigate('/videos')} style={{ padding: '8px 20px', background: pink, color: '#fff', border: 'none', borderRadius: 4, fontSize: 14, cursor: 'pointer', fontWeight: 500 }}>查看视频列表</button>
            <button onClick={reset} style={{ padding: '8px 20px', background: '#fff', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 14, cursor: 'pointer', color: '#606773' }}>重新生成</button>
          </div>
        </div>
      )}

      {/* 渲染失败 */}
      {videoId && pipelineStep === 'failed' && (
        <div style={{ ...cardStyle, marginTop: 20 }}>
          <div style={{ padding: 12, background: '#FFF3F0', borderRadius: 6, border: '1px solid #FFCCC7', marginBottom: 12 }}>
            <p style={{ fontSize: 14, color: '#CF1322', fontWeight: 500 }}>视频生成失败</p>
            <p style={{ fontSize: 13, color: '#595959', marginTop: 4 }}>{error || '未知错误'}</p>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={reset} style={{ padding: '8px 20px', background: '#fff', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 14, cursor: 'pointer', color: '#606773' }}>重新开始</button>
            <button onClick={() => navigate('/videos')} style={{ padding: '8px 20px', background: pink, color: '#fff', border: 'none', borderRadius: 4, fontSize: 14, cursor: 'pointer', fontWeight: 500 }}>查看视频列表</button>
          </div>
        </div>
      )}

      {/* API 配置弹窗 */}
      {showApiConfig && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }} onClick={() => setShowApiConfig(false)}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 24, width: 420, boxShadow: '0 8px 24px rgba(0,0,0,0.2)' }} onClick={e => e.stopPropagation()}>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: '#232529', marginBottom: 16 }}>API 配置</h3>
            <p style={{ fontSize: 14, color: '#606773', marginBottom: 16 }}>生成视频需要配置 LLM API，请填写以下信息：</p>
            <div style={{ marginBottom: 12 }}>
              <label style={labelStyle}>API Key</label>
              <input value={apiConfig.api_key} onChange={e => setApiConfig(c => ({ ...c, api_key: e.target.value }))} style={inputStyle} placeholder="sk-..." />
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={labelStyle}>API Base URL</label>
              <input value={apiConfig.api_base} onChange={e => setApiConfig(c => ({ ...c, api_base: e.target.value }))} style={inputStyle} placeholder="https://api.openai.com/v1" />
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={labelStyle}>Model</label>
              <input value={apiConfig.api_model} onChange={e => setApiConfig(c => ({ ...c, api_model: e.target.value }))} style={inputStyle} placeholder="gpt-4o" />
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={handleSaveApiConfig} style={{ flex: 1, padding: '10px 0', background: pink, color: '#fff', border: 'none', borderRadius: 4, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>保存并生成</button>
              <button onClick={() => setShowApiConfig(false)} style={{ padding: '10px 20px', background: '#fff', border: '1px solid #E3E5E7', borderRadius: 4, fontSize: 14, cursor: 'pointer', color: '#606773' }}>取消</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
