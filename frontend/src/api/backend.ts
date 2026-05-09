/** API client for Python backend. */

const BASE = 'http://localhost:8000';

export interface TimelineResponse {
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
}

export interface EditRequest {
  artifact_id: string;
  path: string;
  value: unknown;
}

export interface EditResponse {
  recomputed_nodes: string[];
  cache_hits: string[];
  duration: number;
}

export async function fetchTimeline(sessionId: string): Promise<TimelineResponse> {
  const resp = await fetch(`${BASE}/api/thinking/${sessionId}/timeline`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

export async function sendEdit(sessionId: string, edit: EditRequest): Promise<EditResponse> {
  const resp = await fetch(`${BASE}/api/thinking/${sessionId}/edit`, {
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
