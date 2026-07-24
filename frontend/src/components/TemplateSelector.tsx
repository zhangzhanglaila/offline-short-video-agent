import { useState, useEffect } from 'react'
import { fetchTemplates, type TemplateInfo } from '../api/template'

const cardStyle: React.CSSProperties = {
  background: '#fff',
  borderRadius: 8,
  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  padding: 16,
  cursor: 'pointer',
  transition: 'all 0.2s',
  border: '2px solid transparent',
}

const cardHoverStyle: React.CSSProperties = {
  ...cardStyle,
  boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
  transform: 'translateY(-2px)',
}

const selectedStyle: React.CSSProperties = {
  ...cardStyle,
  borderColor: '#FB7299',
  backgroundColor: '#FFF5F7',
}

const filterGroupStyle: React.CSSProperties = {
  marginBottom: 16,
  display: 'flex',
  alignItems: 'center',
  gap: 12,
}

const labelStyle: React.CSSProperties = {
  fontSize: 14,
  fontWeight: 500,
  color: '#232529',
  minWidth: 80,
}

const selectStyle: React.CSSProperties = {
  padding: '8px 12px',
  border: '1px solid #E3E5E7',
  borderRadius: 4,
  fontSize: 14,
  minWidth: 150,
}

interface TemplateSelectorProps {
  onSelect: (template: TemplateInfo) => void
  selectedTemplate?: string
  aspectRatio?: string
}

export default function TemplateSelector({ onSelect, selectedTemplate, aspectRatio = '1080x1920' }: TemplateSelectorProps) {
  const [templates, setTemplates] = useState<TemplateInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 筛选状态
  const [aspectFilter, setAspectFilter] = useState(aspectRatio)
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [styleFilter, setStyleFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')

  // 可用的筛选选项
  const [availableFilters, setAvailableFilters] = useState<{
    aspect_ratios: string[]
    template_types: string[]
    styles: string[]
  }>({ aspect_ratios: [], template_types: [], styles: [] })

  // 加载模板列表
  const loadTemplates = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchTemplates({
        aspect_ratio: aspectFilter || undefined,
        template_type: typeFilter || undefined,
        style: styleFilter || undefined,
        search: searchQuery || undefined,
      })
      setTemplates(data.templates)
      setAvailableFilters(data.filters)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 初始加载和筛选变化时重新加载
  useEffect(() => {
    loadTemplates()
  }, [aspectFilter, typeFilter, styleFilter, searchQuery])

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px' }}>
      <h2 style={{ fontSize: 24, fontWeight: 600, marginBottom: 24, color: '#232529' }}>
        选择模板
      </h2>

      {/* 筛选器 */}
      <div style={{ background: '#fff', padding: 20, borderRadius: 8, marginBottom: 24, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
        <div style={filterGroupStyle}>
          <span style={labelStyle}>画幅:</span>
          <select
            style={selectStyle}
            value={aspectFilter}
            onChange={(e) => setAspectFilter(e.target.value)}
          >
            <option value="">全部</option>
            {availableFilters.aspect_ratios.map((ratio) => (
              <option key={ratio} value={ratio}>
                {ratio}
              </option>
            ))}
          </select>
        </div>

        <div style={filterGroupStyle}>
          <span style={labelStyle}>类型:</span>
          <select
            style={selectStyle}
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">全部</option>
            {availableFilters.template_types.map((type) => (
              <option key={type} value={type}>
                {type === 'image' ? '图片' : type === 'video' ? '视频' : type === 'static' ? '静态' : '素材'}
              </option>
            ))}
          </select>
        </div>

        <div style={filterGroupStyle}>
          <span style={labelStyle}>风格:</span>
          <select
            style={selectStyle}
            value={styleFilter}
            onChange={(e) => setStyleFilter(e.target.value)}
          >
            <option value="">全部</option>
            {availableFilters.styles.map((style) => (
              <option key={style} value={style}>
                {style}
              </option>
            ))}
          </select>
        </div>

        <div style={filterGroupStyle}>
          <span style={labelStyle}>搜索:</span>
          <input
            type="text"
            placeholder="搜索模板名称..."
            style={{ ...selectStyle, flex: 1 }}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div style={{ background: '#FFE5E5', color: '#D32F2F', padding: 16, borderRadius: 8, marginBottom: 24 }}>
          {error}
        </div>
      )}

      {/* 加载状态 */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
          加载中...
        </div>
      )}

      {/* 模板网格 */}
      {!loading && templates.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
          没有找到匹配的模板
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {templates.map((template) => {
          const isSelected = selectedTemplate === template.name
          const cardCss = isSelected ? selectedStyle : cardStyle

          return (
            <div
              key={template.name}
              style={cardCss}
              onMouseEnter={(e) => {
                if (!isSelected) {
                  Object.assign(e.currentTarget.style, cardHoverStyle)
                }
              }}
              onMouseLeave={(e) => {
                if (!isSelected) {
                  Object.assign(e.currentTarget.style, cardStyle)
                }
              }}
              onClick={() => onSelect(template)}
            >
              {/* 模板预览占位 */}
              <div
                style={{
                  width: '100%',
                  aspectRatio: `${template.width} / ${template.height}`,
                  background: '#F5F5F5',
                  borderRadius: 4,
                  marginBottom: 12,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 48,
                  color: '#E0E0E0',
                }}
              >
                🖼
              </div>

              {/* 模板信息 */}
              <h3 style={{ fontSize: 16, fontWeight: 600, color: '#232529', marginBottom: 4 }}>
                {template.name}
              </h3>

              <div style={{ fontSize: 13, color: '#666', marginBottom: 8 }}>
                {template.width} × {template.height} · {template.template_type}
              </div>

              <div style={{ fontSize: 12, color: '#999' }}>
                风格: {template.style || '默认'}
              </div>
            </div>
          )
        })}
      </div>

      {/* 统计信息 */}
      <div style={{ marginTop: 24, fontSize: 14, color: '#666' }}>
        共 {templates.length} 个模板
      </div>
    </div>
  )
}
