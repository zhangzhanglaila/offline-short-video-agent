const BASE = ''

/** 安全 JSON 解析 — 后端返回非 JSON 时不会崩溃 */
async function safeJson(res: Response): Promise<Record<string, unknown>> {
  const text = await res.text()
  if (!text || text.trim() === '') {
    throw new Error(`服务器返回空响应 (HTTP ${res.status})，请检查后端日志`)
  }
  try {
    return JSON.parse(text)
  } catch {
    throw new Error(`服务器返回非 JSON (HTTP ${res.status}): ${text.slice(0, 200)}`)
  }
}

export interface Product {
  id: number
  name: string
  category: string
  price: number
  currency: string
  description: string
  selling_points: string[]
  images: string[]
  source_url: string
  platform: string
  status: string
  created_at: string
  updated_at: string
}

export interface EcomVideo {
  id: number
  product_id: number
  product_name?: string
  product_price?: number
  session_id: string
  platform: string
  style: string
  script_content: string
  storyboard: Array<{ time: string; scene?: string; title?: string; bullets?: string[]; subtitle: string; duration: number; material_url?: string; style?: 'comic' | 'realistic' }>
  video_path: string
  video_url: string
  thumbnail_path: string
  duration: number
  status: string
  prompt_snapshot: string
  llm_model: string
  created_at: string
}

export interface AnalyticsItem {
  id: number
  video_id: number
  platform: string
  impressions: number
  clicks: number
  ctr: number
  conversions: number
  conversion_rate: number
  revenue: number
  avg_watch_time: number
  completion_rate: number
  engagement_rate: number
  notes: string
  recorded_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ==================== Products ====================

export async function fetchProducts(params: {
  search?: string; category?: string; platform?: string; status?: string; page?: number; page_size?: number
} = {}): Promise<PaginatedResponse<Product>> {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v) qs.set(k, String(v)) })
  const res = await fetch(`${BASE}/api/ecom/products?${qs}`)
  return safeJson(res) as never
}

export async function fetchProduct(id: number): Promise<Product> {
  const res = await fetch(`${BASE}/api/ecom/products/${id}`)
  return safeJson(res) as never
}

export async function createProduct(data: Partial<Product>): Promise<{ id: number; success: boolean }> {
  const res = await fetch(`${BASE}/api/ecom/products`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  })
  return safeJson(res) as never
}

export async function updateProduct(id: number, data: Partial<Product>): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE}/api/ecom/products/${id}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  })
  return safeJson(res) as never
}

export async function deleteProduct(id: number): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE}/api/ecom/products/${id}`, { method: 'DELETE' })
  return safeJson(res) as never
}

export async function fetchProductCategories(): Promise<{ categories: string[] }> {
  const res = await fetch(`${BASE}/api/ecom/products/categories`)
  return safeJson(res) as never
}

export async function fetchProductStats(): Promise<{ total: number; active: number; categories: number }> {
  const res = await fetch(`${BASE}/api/ecom/products/stats`)
  return safeJson(res) as never
}

// ==================== Generate ====================

export async function generateEcomVideo(data: {
  product_id: number; style: string; platform: string; duration: number; animation_style?: 'contain' | 'side'
}): Promise<{ success: boolean; video_id: number; script: Record<string, unknown> }> {
  const res = await fetch(`${BASE}/api/ecom/generate`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  })
  return safeJson(res) as never
}

// ==================== Videos ====================

export async function fetchEcomVideos(params: {
  product_id?: number; status?: string; platform?: string; page?: number; page_size?: number
} = {}): Promise<PaginatedResponse<EcomVideo>> {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v) qs.set(k, String(v)) })
  const res = await fetch(`${BASE}/api/ecom/videos?${qs}`)
  return safeJson(res) as never
}

export async function fetchEcomVideo(id: number): Promise<EcomVideo> {
  const res = await fetch(`${BASE}/api/ecom/videos/${id}`)
  return safeJson(res) as never
}

export interface VideoStatus {
  status: string
  pipeline_step?: string
  video_url?: string
  video_path?: string
  audio_url?: string
  error?: string
}

export async function fetchVideoStatus(videoId: number): Promise<VideoStatus> {
  const res = await fetch(`${BASE}/api/ecom/videos/${videoId}/status`)
  return safeJson(res) as never
}

export async function deleteEcomVideo(id: number): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE}/api/ecom/videos/${id}`, { method: 'DELETE' })
  return safeJson(res) as never
}

export async function deleteAllEcomVideos(): Promise<{ success: boolean; deleted_count: number }> {
  const res = await fetch(`${BASE}/api/ecom/videos/all`, { method: 'DELETE' })
  return safeJson(res) as never
}

// ==================== Pipeline Control ====================

export async function updateVideoScript(
  videoId: number,
  data: { full_script: string; storyboard: Array<Record<string, unknown>> }
): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE}/api/ecom/videos/${videoId}/script`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  })
  return safeJson(res) as never
}

export async function generateVideoTts(
  videoId: number,
  voice?: string
): Promise<{ success: boolean; audio_url: string; audio_path: string; duration: number }> {
  const res = await fetch(`${BASE}/api/ecom/videos/${videoId}/tts`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ voice }),
  })
  return safeJson(res) as never
}

export async function uploadVideoMaterial(
  videoId: number,
  sceneIndex: number,
  file: File
): Promise<{ success: boolean; path: string; scene_index: number; url: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/ecom/videos/${videoId}/materials?scene_index=${sceneIndex}`, {
    method: 'POST', body: form,
  })
  return safeJson(res) as never
}

export async function renderVideo(
  videoId: number,
  data?: { voice?: string; add_bgm?: boolean; animation_style?: 'contain' | 'side' }
): Promise<{ success: boolean; video_id: number }> {
  const res = await fetch(`${BASE}/api/ecom/videos/${videoId}/render`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data || {}),
  })
  return safeJson(res) as never
}

// ==================== Analytics ====================

export async function fetchEcomAnalytics(params: {
  video_id?: number; product_id?: number
} = {}): Promise<{ items: AnalyticsItem[]; aggregated: Record<string, number> }> {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v) qs.set(k, String(v)) })
  const res = await fetch(`${BASE}/api/ecom/analytics?${qs}`)
  return safeJson(res) as never
}

export async function createAnalytics(data: Partial<AnalyticsItem>): Promise<{ id: number; success: boolean }> {
  const res = await fetch(`${BASE}/api/ecom/analytics`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data),
  })
  return safeJson(res) as never
}

export async function fetchInsights(product_id?: number): Promise<{ insights: string; source: string }> {
  const qs = product_id ? `?product_id=${product_id}` : ''
  const res = await fetch(`${BASE}/api/ecom/analytics/insights${qs}`)
  return safeJson(res) as never
}

// ==================== Meta ====================

export async function fetchEcomMeta(): Promise<{ styles: Record<string, string>; platforms: string[] }> {
  const res = await fetch(`${BASE}/api/ecom/meta`)
  return safeJson(res) as never
}
