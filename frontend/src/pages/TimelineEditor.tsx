import { useEffect, useState, useCallback, useRef } from 'react';
import { Timeline } from '../components/Timeline';
import { AssetPanel } from '../components/AssetPanel';
import { ApiConfigModal } from '../components/ApiConfigModal';
import { useTimelineStore } from '../store/timelineStore';
import { useKeyboard } from '../hooks/useKeyboard';
import { fetchTimeline, fetchSessions, saveSession, loadSession as apiLoadSession } from '../api/backend';
import type { TrackData } from '../store/timelineStore';
import '../App.css';

interface Session {
  id: string;
  topic: string;
  status: string;
}

function loadDemoData() {
  const { restoreSession } = useTimelineStore.getState();

  const tracks: TrackData[] = [
    { track_id: 'v_hook', track_type: 'video', layer: 0, start_frame: 0, end_frame: 90, scene_id: 'hook', content: { scene_type: 'hook', text: 'Redis为什么这么快？' } },
    { track_id: 'v_graph', track_type: 'video', layer: 0, start_frame: 82, end_frame: 210, scene_id: 'graph', content: { scene_type: 'graph', text: '单线程+内存模型' } },
    { track_id: 'v_cards', track_type: 'video', layer: 0, start_frame: 202, end_frame: 330, scene_id: 'cards', content: { scene_type: 'cards', text: '关键总结' } },
    { track_id: 's_hook', track_type: 'subtitle', layer: 1, start_frame: 0, end_frame: 90, scene_id: 'hook', content: { text: 'Redis为什么这么快？', word_timings: [
      { word: 'Redis', start: 0.0, end: 0.4, start_frame: 0, end_frame: 12 },
      { word: '为什么', start: 0.4, end: 0.9, start_frame: 12, end_frame: 27 },
      { word: '这么快', start: 0.9, end: 1.5, start_frame: 27, end_frame: 45 },
      { word: '？', start: 1.5, end: 2.0, start_frame: 45, end_frame: 60 },
    ] } },
    { track_id: 's_graph', track_type: 'subtitle', layer: 1, start_frame: 82, end_frame: 210, scene_id: 'graph', content: { text: '单线程加内存模型是关键', word_timings: [
      { word: '单线程', start: 0.0, end: 0.6, start_frame: 82, end_frame: 100 },
      { word: '加', start: 0.6, end: 0.8, start_frame: 100, end_frame: 106 },
      { word: '内存模型', start: 0.8, end: 1.5, start_frame: 106, end_frame: 127 },
      { word: '是关键', start: 1.5, end: 2.2, start_frame: 127, end_frame: 148 },
    ] } },
    { track_id: 's_cards', track_type: 'subtitle', layer: 1, start_frame: 202, end_frame: 330, scene_id: 'cards', content: { text: '关注学习更多技术', word_timings: [
      { word: '关注', start: 0.0, end: 0.4, start_frame: 202, end_frame: 214 },
      { word: '学习', start: 0.4, end: 0.8, start_frame: 214, end_frame: 226 },
      { word: '更多', start: 0.8, end: 1.2, start_frame: 226, end_frame: 238 },
      { word: '技术', start: 1.2, end: 1.8, start_frame: 238, end_frame: 256 },
    ] } },
    { track_id: 'a_hook', track_type: 'audio', layer: 2, start_frame: 0, end_frame: 90, scene_id: 'hook', content: { audio_path: 'tts_hook.mp3' } },
    { track_id: 'a_graph', track_type: 'audio', layer: 2, start_frame: 82, end_frame: 210, scene_id: 'graph', content: { audio_path: 'tts_graph.mp3' } },
    { track_id: 'a_cards', track_type: 'audio', layer: 2, start_frame: 202, end_frame: 330, scene_id: 'cards', content: { audio_path: 'tts_cards.mp3' } },
  ];

  restoreSession(tracks, [], [], 330);
}

export default function TimelineEditor() {
  useKeyboard();

  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAssets, setShowAssets] = useState(false);
  const [showApiConfig, setShowApiConfig] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error' | 'conflict'>('idle');
  const [sessionVersion, setSessionVersion] = useState(0);
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetchSessions()
      .then(setSessions)
      .catch(() => setSessions([]));
  }, []);

  const doSave = useCallback(async () => {
    if (!activeSessionId) return;
    setSaveStatus('saving');
    try {
      const snapshot = useTimelineStore.getState().getSnapshot();
      const result = await saveSession(activeSessionId, {
        tracks: snapshot.tracks as unknown as Array<Record<string, unknown>>,
        undo_stack: snapshot.undoStack as unknown as Array<Record<string, unknown>>,
        redo_stack: snapshot.redoStack as unknown as Array<Record<string, unknown>>,
        expected_version: sessionVersion > 0 ? sessionVersion : undefined,
      });
      if (result.success) {
        setSaveStatus('saved');
        setSessionVersion(result.version);
        setTimeout(() => setSaveStatus('idle'), 2000);
      } else if (result.conflict) {
        setSaveStatus('conflict');
        if (result.current_version) setSessionVersion(result.current_version);
      } else {
        setSaveStatus('error');
      }
    } catch {
      setSaveStatus('error');
    }
  }, [activeSessionId]);

  useEffect(() => {
    const unsub = useTimelineStore.subscribe((state, prev) => {
      if (state.tracks !== prev.tracks && activeSessionId) {
        if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
        autoSaveTimer.current = setTimeout(doSave, 1500);
      }
    });
    return () => {
      unsub();
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    };
  }, [activeSessionId, doSave]);

  const loadSavedSession = useCallback(async (sessionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const saved = await apiLoadSession(sessionId);
      if (saved.success && saved.tracks.length > 0) {
        const tracks = saved.tracks as unknown as TrackData[];
        const undoStack = saved.undo_stack as unknown as Array<{ tracks: TrackData[]; description: string }>;
        const redoStack = saved.redo_stack as unknown as Array<{ tracks: TrackData[]; description: string }>;
        const { restoreSession } = useTimelineStore.getState();
        restoreSession(tracks, undoStack, redoStack);
        setActiveSessionId(sessionId);
        setSessionVersion(saved.version || 0);
        return;
      }

      const data = await fetchTimeline(sessionId);
      const tracks: TrackData[] = data.tracks.map((t) => ({
        track_id: t.track_id,
        track_type: t.track_type as TrackData['track_type'],
        layer: t.layer,
        start_frame: t.start_frame,
        end_frame: t.end_frame,
        scene_id: t.scene_id,
        content: t.content,
      }));
      const { restoreSession } = useTimelineStore.getState();
      restoreSession(tracks, [], [], data.duration_frames);
      setActiveSessionId(sessionId);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load session');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (sessions.length === 0 && !loading) {
      loadDemoData();
    }
  }, [sessions, loading]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Timeline Editor</h1>
        <span className="app-subtitle">时间线编辑器</span>

        <div className="session-selector">
          {sessions.length > 0 ? (
            <select
              value={activeSessionId || ''}
              onChange={(e) => {
                const id = e.target.value;
                if (id) loadSavedSession(id);
                else {
                  setActiveSessionId(null);
                  loadDemoData();
                }
              }}
            >
              <option value="">Demo</option>
              {sessions.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.topic || s.id.slice(0, 8)} ({s.status})
                </option>
              ))}
            </select>
          ) : (
            <span className="session-label">Demo Mode</span>
          )}
        </div>

        {activeSessionId && (
          <div className="save-controls">
            <button className="header-btn" onClick={doSave} disabled={saveStatus === 'saving'}>
              {saveStatus === 'saving' ? 'Saving...' : 'Save'}
            </button>
            {saveStatus === 'saved' && <span className="save-status save-status--ok">Saved</span>}
            {saveStatus === 'conflict' && <span className="save-status save-status--conflict">Conflict — reloaded</span>}
            {saveStatus === 'error' && <span className="save-status save-status--err">Error</span>}
          </div>
        )}

        <button
          className={`header-btn ${showAssets ? 'header-btn--active' : ''}`}
          onClick={() => setShowAssets(!showAssets)}
        >
          Assets
        </button>

        <button className="header-btn" onClick={() => setShowApiConfig(true)} title="API 配置">
          API
        </button>

        {loading && <span className="loading-indicator">Loading...</span>}
        {error && <span className="error-indicator">{error}</span>}
      </header>
      <main className="app-main">
        <div className="app-content">
          <Timeline />
          {showAssets && <AssetPanel sessionId={activeSessionId} />}
        </div>
      </main>

      <ApiConfigModal open={showApiConfig} onClose={() => setShowApiConfig(false)} />
    </div>
  );
}
