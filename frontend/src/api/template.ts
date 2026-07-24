/**
 * 模板 API 调用
 */

export interface TemplateInfo {
  name: string
  aspect_ratio: string
  width: number
  height: number
  template_type: 'image' | 'static' | 'video' | 'asset'
  style: string
  parameters: string[]
  path: string
}

export interface TemplateListResponse {
  templates: TemplateInfo[]
  total: number
  filters: {
    aspect_ratios: string[]
    template_types: string[]
    styles: string[]
  }
}

export interface TemplateFiltersResponse {
  aspect_ratios: string[]
  template_types: string[]
  styles: string[]
  total_templates: number
}

const API_BASE = 'http://localhost:5001'

/**
 * 获取模板列表
 */
export async function fetchTemplates(filters?: {
  aspect_ratio?: string
  template_type?: string
  style?: string
  search?: string
}): Promise<TemplateListResponse> {
  const params = new URLSearchParams()
  if (filters?.aspect_ratio) params.set('aspect_ratio', filters.aspect_ratio)
  if (filters?.template_type) params.set('template_type', filters.template_type)
  if (filters?.style) params.set('style', filters.style)
  if (filters?.search) params.set('search', filters.search)

  const response = await fetch(`${API_BASE}/api/templates?${params.toString()}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  return response.json()
}

/**
 * 获取单个模板信息
 */
export async function fetchTemplate(name: string): Promise<TemplateInfo> {
  const response = await fetch(`${API_BASE}/api/templates/${name}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: Template not found: ${name}`)
  }
  return response.json()
}

/**
 * 获取模板筛选器选项
 */
export async function fetchTemplateFilters(): Promise<TemplateFiltersResponse> {
  const response = await fetch(`${API_BASE}/api/templates/filters`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  return response.json()
}

/**
 * 生成模板预览图
 */
export async function generatePreview(
  templateName: string,
  context?: Record<string, any>
): Promise<{ success: boolean; preview_url: string; output_path: string }> {
  const response = await fetch(`${API_BASE}/api/templates/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      template_name: templateName,
      context: context || {},
    }),
  })
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  return response.json()
}
