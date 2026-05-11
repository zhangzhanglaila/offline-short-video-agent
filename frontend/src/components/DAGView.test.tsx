import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DAGView } from './DAGView';

const mockDAG = {
  name: 'test-pipeline',
  total_duration: 2.5,
  is_complete: true,
  nodes: {
    n1: {
      id: 'n1', name: 'Script Gen', status: 'done' as const,
      inputs: { topic: 'Redis' }, outputs: { script: '...' },
      depends_on: [], error: null, cache_hit: true,
      started_at: 1.0, completed_at: 2.0, duration: 1.0,
      metadata: {},
    },
    n2: {
      id: 'n2', name: 'TTS', status: 'running' as const,
      inputs: {}, outputs: {},
      depends_on: ['n1'], error: null, cache_hit: false,
      started_at: 2.0, completed_at: null, duration: null,
      metadata: {},
    },
    n3: {
      id: 'n3', name: 'Render', status: 'error' as const,
      inputs: {}, outputs: {},
      depends_on: ['n2'], error: 'ffmpeg crashed', cache_hit: false,
      started_at: 3.0, completed_at: null, duration: null,
      metadata: {},
    },
  },
  edges: [
    { from: 'n1', to: 'n2' },
    { from: 'n2', to: 'n3' },
  ],
  stats: { done: 1, running: 1, error: 1 },
};

describe('DAGView', () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows empty state when no sessionId', () => {
    render(<DAGView sessionId={null} />);
    expect(screen.getByText('No session')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {}));
    render(<DAGView sessionId="s1" />);
    expect(screen.getByText('Loading DAG...')).toBeInTheDocument();
  });

  it('renders DAG nodes after fetch', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDAG),
    });

    render(<DAGView sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('Script Gen')).toBeInTheDocument();
      expect(screen.getByText('TTS')).toBeInTheDocument();
      expect(screen.getByText('Render')).toBeInTheDocument();
    });
  });

  it('shows pipeline name in header', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDAG),
    });

    render(<DAGView sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('Pipeline: test-pipeline')).toBeInTheDocument();
    });
  });

  it('shows error message on fetch failure', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network error'));
    render(<DAGView sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('shows node detail when clicked', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDAG),
    });

    render(<DAGView sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('Render')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Render'));
    expect(screen.getByText('ffmpeg crashed')).toBeInTheDocument();
  });

  it('shows cache hit indicator', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDAG),
    });

    render(<DAGView sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('⚡cache')).toBeInTheDocument();
    });
  });

  it('shows duration for completed nodes', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDAG),
    });

    render(<DAGView sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText('1000ms')).toBeInTheDocument();
    });
  });

  it('shows stats in header', async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDAG),
    });

    render(<DAGView sessionId="s1" />);
    await waitFor(() => {
      expect(screen.getByText(/2\.5s/)).toBeInTheDocument();
    });
  });
});
