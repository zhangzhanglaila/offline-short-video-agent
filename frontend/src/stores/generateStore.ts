import { create } from 'zustand'
import {
  generateEcomVideo, fetchVideoStatus,
  updateVideoScript, generateVideoTts, uploadVideoMaterial, renderVideo,
} from '../api/ecom'

/** 清洗 LLM 返回的可能带 JSON 转义的字符串 */
function cleanStr(v: unknown): string {
  if (typeof v !== 'string') return String(v ?? '')
  // 去除外层引号
  let s = v.trim()
  if (s.startsWith('"') && s.endsWith('"') && s.length > 2) {
    try { s = JSON.parse(s) } catch { /* ignore */ }
  }
  // 还原常见转义
  s = s.replace(/\\n/g, '\n').replace(/\\t/g, '  ').replace(/\\"/g, '"').replace(/\\\\/g, '\\')
  return s
}

function parseJsonLikeScript(input: unknown): Record<string, unknown> | null {
  const s = cleanStr(input)
  const m = s.match(/\{[\s\S]*\}/)
  if (!m) return null
  try {
    return JSON.parse(m[0]) as Record<string, unknown>
  } catch {
    return null
  }
}

interface StoryboardItem {
  time?: string
  scene?: string
  title?: string
  bullets?: string[]
  subtitle?: string
  duration?: number
  material_path?: string
  material_url?: string
  style?: 'comic' | 'realistic'
}

interface GenerateState {
  // 配置阶段
  generating: boolean
  error: string

  // 视频记录
  videoId: number | null
  pipelineStep: string // init | script_ready | script_edited | tts_ready | rendering | done | failed

  // 可编辑脚本
  editedHook: string
  editedBody: string
  editedCta: string
  editedFullScript: string
  storyboard: StoryboardItem[]
  animationStyle: 'contain' | 'side'
  orientation: 'portrait' | 'landscape'

  // TTS
  ttsAudioUrl: string
  ttsDuration: number
  ttsGenerating: boolean

  // 渲染
  videoUrl: string
  polling: boolean
  successMsg: string
  _pollTimer: ReturnType<typeof setInterval> | null

  // Actions
  generate: (data: { product_id: number; style: string; platform: string; duration: number; animation_style?: 'contain' | 'side'; orientation?: 'portrait' | 'landscape' }) => Promise<void>
  setAnimationStyle: (value: 'contain' | 'side') => void
  setOrientation: (value: 'portrait' | 'landscape') => void
  setField: (field: string, value: string) => void
  setStoryboardItem: (index: number, item: Partial<StoryboardItem>) => void
  saveScript: () => Promise<void>
  generateTts: (voice?: string) => Promise<void>
  uploadMaterial: (sceneIndex: number, file: File) => Promise<void>
  startRender: (voice?: string) => Promise<void>
  startPolling: () => void
  stopPolling: () => void
  reset: () => void
}

export const useGenerateStore = create<GenerateState>((set, get) => ({
  generating: false,
  error: '',
  videoId: null,
  pipelineStep: 'init',
  editedHook: '',
  editedBody: '',
  editedCta: '',
  editedFullScript: '',
  storyboard: [],
  ttsAudioUrl: '',
  ttsDuration: 0,
  ttsGenerating: false,
  videoUrl: '',
  polling: false,
  successMsg: '',
  _pollTimer: null,
  animationStyle: 'contain',
  orientation: 'portrait',

  generate: async (data) => {
    set({ generating: true, error: '', videoId: null, pipelineStep: 'init', videoUrl: '', ttsAudioUrl: '' })
    try {
      const res = await generateEcomVideo(data)
      if (res.success) {
        const script = res.script as Record<string, unknown>
        const mergedParsed =
          parseJsonLikeScript(script.full_script) ||
          parseJsonLikeScript(script.body) ||
          parseJsonLikeScript(script.hook) ||
          null
        const hook = mergedParsed?.hook ?? script.hook ?? ''
        const body = mergedParsed?.body ?? script.body ?? ''
        const cta = mergedParsed?.cta ?? script.cta ?? ''
        const fullScript = mergedParsed?.full_script ?? script.full_script ?? ''
        const sb = (script.storyboard || []) as StoryboardItem[]
        set({
          generating: false,
          videoId: res.video_id,
          pipelineStep: 'script_ready',
          editedHook: cleanStr(hook),
          editedBody: cleanStr(body),
          editedCta: cleanStr(cta),
          editedFullScript: cleanStr(fullScript),
          storyboard: sb,
        })
      } else {
        set({ error: '生成失败', generating: false })
      }
    } catch (e) {
      set({ error: String(e), generating: false })
    }
  },

  setField: (field, value) => {
    set({ [field]: value } as never)
  },
  setAnimationStyle: (value) => set({ animationStyle: value }),
  setOrientation: (value) => set({ orientation: value }),

  setStoryboardItem: (index, item) => {
    const sb = [...get().storyboard]
    if (sb[index]) {
      sb[index] = { ...sb[index], ...item }
      set({ storyboard: sb })
    }
  },

  saveScript: async () => {
    const { videoId, editedFullScript, storyboard } = get()
    if (!videoId) return
    set({ error: '' })
    try {
      const res = await updateVideoScript(videoId, {
        full_script: editedFullScript,
        storyboard: storyboard as Array<Record<string, unknown>>,
      })
      if (res.success) {
        set({ pipelineStep: 'script_edited', successMsg: '脚本保存成功！' })
        setTimeout(() => set({ successMsg: '' }), 3000)
      } else {
        set({ error: '保存失败' })
      }
    } catch (e) {
      set({ error: String(e) })
    }
  },

  generateTts: async (voice) => {
    const { videoId } = get()
    if (!videoId) return
    set({ ttsGenerating: true, error: '' })
    try {
      const res = await generateVideoTts(videoId, voice)
      if (res.success) {
        set({
          ttsAudioUrl: res.audio_url,
          ttsDuration: res.duration || 0,
          ttsGenerating: false,
          pipelineStep: 'tts_ready',
          successMsg: '配音生成成功！',
        })
        setTimeout(() => set({ successMsg: '' }), 3000)
      } else {
        set({ error: 'TTS 生成失败', ttsGenerating: false })
      }
    } catch (e) {
      set({ error: String(e), ttsGenerating: false })
    }
  },

  uploadMaterial: async (sceneIndex, file) => {
    const { videoId } = get()
    if (!videoId) return
    try {
      const res = await uploadVideoMaterial(videoId, sceneIndex, file)
      if (res.success) {
        const sb = [...get().storyboard]
        if (sb[sceneIndex]) {
          sb[sceneIndex] = { ...sb[sceneIndex], material_path: res.path, material_url: res.url }
          set({ storyboard: sb })
        }
      }
    } catch (e) {
      set({ error: String(e) })
    }
  },

  startRender: async (voice) => {
    const { videoId, animationStyle, orientation } = get()
    if (!videoId) return
    set({ error: '' })
    try {
      const res = await renderVideo(videoId, { voice, animation_style: animationStyle, orientation })
      if (res.success) {
        set({ pipelineStep: 'rendering' })
        get().startPolling()
      } else {
        set({ error: '启动渲染失败' })
      }
    } catch (e) {
      set({ error: String(e) })
    }
  },

  startPolling: () => {
    const state = get()
    if (state._pollTimer) clearInterval(state._pollTimer)
    set({ polling: true })

    const timer = setInterval(async () => {
      const { videoId } = get()
      if (!videoId) return
      try {
        const status = await fetchVideoStatus(videoId)
        const step = status.pipeline_step || status.status
        if (step === 'done') {
          set({ pipelineStep: 'done', videoUrl: status.video_url || '', polling: false })
          get().stopPolling()
        } else if (step === 'failed') {
          set({ pipelineStep: 'failed', error: status.error || '视频生成失败', polling: false })
          get().stopPolling()
        } else {
          set({ pipelineStep: step })
        }
      } catch { /* ignore transient errors */ }
    }, 3000)

    set({ _pollTimer: timer })
  },

  stopPolling: () => {
    const state = get()
    if (state._pollTimer) {
      clearInterval(state._pollTimer)
      set({ _pollTimer: null, polling: false })
    }
  },

  reset: () => {
    const state = get()
    if (state._pollTimer) clearInterval(state._pollTimer)
    set({
      generating: false, error: '', videoId: null, pipelineStep: 'init',
      editedHook: '', editedBody: '', editedCta: '', editedFullScript: '',
      storyboard: [], animationStyle: 'contain', ttsAudioUrl: '', ttsDuration: 0, ttsGenerating: false,
      videoUrl: '', polling: false, successMsg: '', _pollTimer: null,
    })
  },
}))
