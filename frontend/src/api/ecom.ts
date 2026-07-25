/** 视频管线 API（脚本编辑 / TTS / 素材 / 渲染 / 列表）。
 *  历史沿革：原为电商模块，现为主题驱动统一流程的下游管线。
 *  路由前缀保留 /api/ecom/videos 以兼容后端与主应用注册。 */

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

export interface EcomVideo {
  id: number
  product_id?: number
  product_name?: string
  topic?: string
  category?: string
  session_id: string
  platform: string
  style: string
  visual_style?: string
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

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ==================== Videos ====================

export async function fetchEcomVideos(params: {
  status?: string; category?: string; page?: number; page_size?: number
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
  data?: { voice?: string; add_bgm?: boolean; animation_style?: 'contain' | 'side'; orientation?: 'portrait' | 'landscape'; visual_style?: string }
): Promise<{ success: boolean; video_id: number }> {
  const res = await fetch(`${BASE}/api/ecom/videos/${videoId}/render`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data || {}),
  })
  return safeJson(res) as never
}
