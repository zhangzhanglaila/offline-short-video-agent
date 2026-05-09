/** API client for Python backend. */

const BASE = 'http://localhost:8000';

export interface TimelineResponse {
  session_id: string;
  topic: string;
  tracks: Array<{
    track_id: string;
    track_type: string;
    layer: number;
    start_frame: number;
    end_frame: number;
    scene_id: string;
    content: Record<string, unknown>;
  }>;
  duration_frames: number;
  fps: number;
  width: number;
  height: number;
}

export interface EditRequest {
  operation: 'moveScene' | 'resizeScene' | 'updateContent';
  scene_id: string;
  delta_frames?: number;
  new_end_frame?: number;
  field?: string;
  value?: string;
}

export interface EditResponse {
  success: boolean;
  recomputed_nodes: string[];
  cache_hits: string[];
  duration: number;
  error?: string;
}

export async function fetchTimeline(sessionId: string): Promise<TimelineResponse> {
  const resp = await fetch(`${BASE}/api/timeline/${sessionId}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function sendEdit(sessionId: string, edit: EditRequest): Promise<EditResponse> {
  const resp = await fetch(`${BASE}/api/timeline/${sessionId}/edit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(edit),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function fetchSessions(): Promise<Array<{ id: string; topic: string; status: string }>> {
  const resp = await fetch(`${BASE}/api/thinking/sessions`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function fetchAssets(sessionId: string, assetType?: string): Promise<{ assets: Array<Record<string, unknown>>; total: number }> {
  const url = new URL(`${BASE}/api/timeline/${sessionId}/assets`);
  if (assetType) url.searchParams.set('asset_type', assetType);
  const resp = await fetch(url.toString());
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export interface SaveRequest {
  tracks: Array<Record<string, unknown>>;
  undo_stack: Array<Record<string, unknown>>;
  redo_stack: Array<Record<string, unknown>>;
  meta?: Record<string, unknown>;
}

export interface SaveResponse {
  success: boolean;
  session_id: string;
  last_saved: number;
  error?: string;
}

export interface LoadResponse {
  success: boolean;
  session_id: string;
  tracks: Array<Record<string, unknown>>;
  undo_stack: Array<Record<string, unknown>>;
  redo_stack: Array<Record<string, unknown>>;
  meta: Record<string, unknown>;
  error?: string;
}

export async function saveSession(sessionId: string, data: SaveRequest): Promise<SaveResponse> {
  const resp = await fetch(`${BASE}/api/timeline/${sessionId}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function loadSession(sessionId: string): Promise<LoadResponse> {
  const resp = await fetch(`${BASE}/api/timeline/${sessionId}/load`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function listSavedSessions(): Promise<{ sessions: Array<Record<string, unknown>>; total: number }> {
  const resp = await fetch(`${BASE}/api/timeline/sessions/list`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}
