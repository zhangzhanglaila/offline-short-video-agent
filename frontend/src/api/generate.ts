/** 通用视频生成 API（主题驱动，替代电商 product 流程）。
 *  下游 script/tts/render 仍复用 ecom.ts 中基于 video_id 的函数。 */

const BASE = ''

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

export interface GenerateMeta {
  categories: string[]
  platforms: string[]
  visual_styles: Record<string, { name_cn: string; paper_color: string; accent_red: string; text_c: string }>
}

export async function fetchGenerateMeta(): Promise<GenerateMeta> {
  const res = await fetch(`${BASE}/api/topic/generate/meta`)
  return safeJson(res) as never
}

export interface GenerateParams {
  topic: string
  category: string
  style?: string
  platform?: string
  duration: number
  animation_style?: 'contain' | 'side'
  orientation?: 'portrait' | 'landscape'
  visual_style?: string
}

export async function generateVideo(
  data: GenerateParams
): Promise<{ success: boolean; video_id: number; script: Record<string, unknown> }> {
  const res = await fetch(`${BASE}/api/topic/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return safeJson(res) as never
}
