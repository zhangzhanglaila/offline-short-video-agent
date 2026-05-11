import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import GenerateVideo from './GenerateVideo'
import { useGenerateStore } from '../stores/generateStore'

function jsonResponse(data: unknown): Response {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('GenerateVideo long text rendering', () => {
  beforeEach(() => {
    HTMLElement.prototype.scrollIntoView = vi.fn()

    const longParagraph = Array.from({ length: 80 }, (_, i) => (
      `Long product explanation sentence ${i + 1} with feature details, usage context, proof point, and a concise takeaway.`
    )).join(' ')

    useGenerateStore.setState({
      generating: false,
      error: '',
      videoId: 1001,
      pipelineStep: 'script_ready',
      editedHook: 'LONG_HOOK_TEXT_' + longParagraph.slice(0, 400),
      editedBody: longParagraph,
      editedCta: 'LONG_CTA_TEXT Buy now after reviewing the full explanation.',
      editedFullScript: longParagraph,
      storyboard: Array.from({ length: 8 }, (_, i) => ({
        time: `${i * 5}-${(i + 1) * 5}s`,
        title: `LONG_SCENE_TITLE_${i + 1}_` + longParagraph.slice(0, 180),
        bullets: [
          `LONG_BULLET_A_${i + 1}_` + longParagraph.slice(0, 220),
          `LONG_BULLET_B_${i + 1}_` + longParagraph.slice(220, 440),
          `LONG_BULLET_C_${i + 1}_` + longParagraph.slice(440, 660),
        ],
        subtitle: `LONG_SUBTITLE_${i + 1}_` + longParagraph.slice(0, 700),
        duration: 5,
        material_url: '',
        style: 'comic',
      })),
      animationStyle: 'contain',
      ttsAudioUrl: '',
      ttsDuration: 0,
      ttsGenerating: false,
      videoUrl: '',
      polling: false,
      successMsg: '',
      _pollTimer: null,
    })

    globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.startsWith('/api/ecom/products?')) {
        return jsonResponse({
          total: 1,
          page: 1,
          page_size: 100,
          items: [{
            id: 1,
            name: 'Long Text Test Product',
            category: 'test',
            price: 9.99,
            currency: 'USD',
            description: 'A product used for long text rendering validation.',
            selling_points: ['Long copy support'],
            images: [],
            source_url: '',
            platform: 'TikTok Shop',
            status: 'active',
            created_at: '',
            updated_at: '',
          }],
        })
      }
      if (url === '/api/ecom/meta') {
        return jsonResponse({ styles: { soft_sell: 'Soft sell' }, platforms: ['TikTok'] })
      }
      if (url === '/api/system/config') {
        return jsonResponse({ api_key: 'test-key', api_base: 'http://example.test', api_model: 'test-model' })
      }
      return jsonResponse({})
    }) as typeof fetch
  })

  afterEach(() => {
    vi.restoreAllMocks()
    useGenerateStore.getState().reset()
  })

  it('renders the comic storyboard editor with large generated copy instead of blanking', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/generate?product_id=1']}>
        <GenerateVideo />
      </MemoryRouter>
    )

    expect(await screen.findByDisplayValue(/LONG_HOOK_TEXT_/)).toBeInTheDocument()
    expect(screen.getByDisplayValue(/LONG_SCENE_TITLE_1_/)).toBeInTheDocument()
    expect(screen.getByDisplayValue(/LONG_SUBTITLE_1_/)).toBeInTheDocument()
    expect(container.textContent).toContain('1/8')
    expect(container.textContent).not.toEqual('')
  })
})
