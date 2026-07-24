import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import TemplateSelector from '../components/TemplateSelector'
import { type TemplateInfo } from '../api/template'

const containerStyle: React.CSSProperties = {
  minHeight: '100vh',
  background: '#F5F7FA',
  padding: '24px',
}

const headerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '24px',
}

const buttonStyle: React.CSSProperties = {
  padding: '10px 24px',
  background: '#FB7299',
  color: '#fff',
  border: 'none',
  borderRadius: 4,
  fontSize: 15,
  fontWeight: 500,
  cursor: 'pointer',
  transition: 'all 0.2s',
}

const selectedInfoStyle: React.CSSProperties = {
  background: '#FFF5F7',
  border: '2px solid #FB7299',
  borderRadius: 8,
  padding: '16px 24px',
  marginBottom: '24px',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
}

export default function TemplateGallery() {
  const navigate = useNavigate()
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateInfo | null>(null)

  const handleSelectTemplate = (template: TemplateInfo) => {
    setSelectedTemplate(template)
  }

  const handleContinue = () => {
    if (!selectedTemplate) return

    // 导航到生成视频页面，带上模板参数
    navigate(`/generate?template=${selectedTemplate.name}`)
  }

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <div>
          <h1 style={{ fontSize: 32, fontWeight: 600, color: '#232529', margin: 0 }}>
            模板库
          </h1>
          <p style={{ fontSize: 15, color: '#666', marginTop: 8 }}>
            选择一个模板开始创作
          </p>
        </div>
      </div>

      {/* 已选择的模板信息 */}
      {selectedTemplate && (
        <div style={selectedInfoStyle}>
          <div>
            <div style={{ fontSize: 14, color: '#666', marginBottom: 4 }}>
              已选择
            </div>
            <div style={{ fontSize: 18, fontWeight: 600, color: '#232529' }}>
              {selectedTemplate.name}
            </div>
            <div style={{ fontSize: 13, color: '#999', marginTop: 4 }}>
              {selectedTemplate.width} × {selectedTemplate.height} · {selectedTemplate.template_type}
            </div>
          </div>
          <button
            style={buttonStyle}
            onClick={handleContinue}
          >
            继续生成 →
          </button>
        </div>
      )}

      {/* 模板选择器 */}
      <TemplateSelector
        onSelect={handleSelectTemplate}
        selectedTemplate={selectedTemplate?.name}
      />
    </div>
  )
}
