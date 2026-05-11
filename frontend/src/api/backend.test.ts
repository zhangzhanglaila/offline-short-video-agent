import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchTimeline, sendEdit, fetchSessions, fetchAssets } from './backend';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function jsonResponse(data: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    json: () => Promise.resolve(data),
  };
}

describe('fetchTimeline', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('fetches timeline data for a session', async () => {
    const data = {
      session_id: 's1',
      topic: 'Redis',
      tracks: [{ track_id: 'v1', track_type: 'video', layer: 0, start_frame: 0, end_frame: 90, scene_id: 'sc1', content: {} }],
      duration_frames: 900,
      fps: 30,
      width: 1080,
      height: 1920,
    };
    mockFetch.mockResolvedValue(jsonResponse(data));

    const result = await fetchTimeline('s1');
    expect(result.tracks).toHaveLength(1);
    expect(result.fps).toBe(30);
    expect(result.topic).toBe('Redis');
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:5001/api/timeline/s1');
  });

  it('throws on HTTP error', async () => {
    mockFetch.mockResolvedValue(jsonResponse(null, false, 404));
    await expect(fetchTimeline('bad')).rejects.toThrow('HTTP 404');
  });
});

describe('sendEdit', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('sends moveScene edit request', async () => {
    const data = { success: true, recomputed_nodes: ['r1'], cache_hits: [], duration: 0.05 };
    mockFetch.mockResolvedValue(jsonResponse(data));

    const result = await sendEdit('s1', {
      operation: 'moveScene',
      scene_id: 'sc1',
      delta_frames: 10,
    });

    expect(result.success).toBe(true);
    expect(result.recomputed_nodes).toContain('r1');
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:5001/api/timeline/s1/edit',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('sends resizeScene edit request', async () => {
    const data = { success: true, recomputed_nodes: [], cache_hits: [], duration: 0.01 };
    mockFetch.mockResolvedValue(jsonResponse(data));

    const result = await sendEdit('s1', {
      operation: 'resizeScene',
      scene_id: 'sc1',
      new_end_frame: 150,
    });

    expect(result.success).toBe(true);
  });

  it('sends updateContent edit request', async () => {
    const data = { success: true, recomputed_nodes: [], cache_hits: [], duration: 0.01 };
    mockFetch.mockResolvedValue(jsonResponse(data));

    const result = await sendEdit('s1', {
      operation: 'updateContent',
      scene_id: 'sc1',
      field: 'text',
      value: 'New text',
    });

    expect(result.success).toBe(true);
  });

  it('throws on HTTP error', async () => {
    mockFetch.mockResolvedValue(jsonResponse(null, false, 500));
    await expect(sendEdit('s1', { operation: 'moveScene', scene_id: 'sc1' })).rejects.toThrow('HTTP 500');
  });
});

describe('fetchSessions', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('fetches session list', async () => {
    const data = [{ id: 's1', topic: 'Redis', status: 'done' }];
    mockFetch.mockResolvedValue(jsonResponse(data));

    const result = await fetchSessions();
    expect(result).toHaveLength(1);
    expect(result[0].topic).toBe('Redis');
  });
});

describe('fetchAssets', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('fetches assets for a session', async () => {
    const data = { assets: [{ id: 'a1', type: 'image' }], total: 1 };
    mockFetch.mockResolvedValue(jsonResponse(data));

    const result = await fetchAssets('s1');
    expect(result.assets).toHaveLength(1);
    expect(result.total).toBe(1);
  });

  it('passes asset_type filter', async () => {
    const data = { assets: [], total: 0 };
    mockFetch.mockResolvedValue(jsonResponse(data));

    await fetchAssets('s1', 'video');
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:5001/api/timeline/s1/assets?asset_type=video',
    );
  });
});
