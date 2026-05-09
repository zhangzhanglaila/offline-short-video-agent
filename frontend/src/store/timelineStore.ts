import { create } from 'zustand';

/** A single word timing entry from TTS. */
export interface WordTiming {
  word: string;
  start: number;
  end: number;
  start_frame: number;
  end_frame: number;
}

/** A track in the timeline (video, subtitle, audio). */
export interface TrackData {
  track_id: string;
  track_type: 'video' | 'subtitle' | 'audio';
  layer: number;
  start_frame: number;
  end_frame: number;
  scene_id: string;
  content: Record<string, unknown>;
}

/** A scene clip for display. */
export interface SceneClipData {
  scene_id: string;
  scene_type: string;
  text: string;
  start_frame: number;
  end_frame: number;
  layer: number;
}

/** Undo snapshot. */
interface UndoSnapshot {
  tracks: TrackData[];
  description: string;
}

/** Timeline state. */
interface TimelineState {
  // Data
  tracks: TrackData[];
  durationFrames: number;
  fps: number;
  width: number;
  height: number;

  // Playback
  currentFrame: number;
  isPlaying: boolean;
  loop: boolean;
  autoScroll: boolean;

  // View
  framePerPixel: number;
  scrollX: number;

  // Selection
  selectedSceneId: string | null;

  // Word highlight
  activeWordIndex: number;

  // Undo/Redo
  undoStack: UndoSnapshot[];
  redoStack: UndoSnapshot[];

  // Actions
  setTracks: (tracks: TrackData[], duration: number) => void;
  setCurrentFrame: (frame: number) => void;
  seekToFrame: (frame: number) => void;
  nudgeFrame: (delta: number) => void;
  togglePlay: () => void;
  setPlaying: (playing: boolean) => void;
  toggleLoop: () => void;
  toggleAutoScroll: () => void;
  setZoom: (framePerPixel: number) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  setScrollX: (x: number) => void;
  selectScene: (sceneId: string | null) => void;
  setActiveWordIndex: (index: number) => void;

  // Scene editing
  moveScene: (sceneId: string, deltaFrames: number) => void;
  resizeScene: (sceneId: string, newEndFrame: number) => void;
  updateSceneContent: (sceneId: string, field: string, value: unknown) => void;

  // Undo/Redo
  undo: () => void;
  redo: () => void;

  // Persistence
  restoreSession: (tracks: TrackData[], undoStack: UndoSnapshot[], redoStack: UndoSnapshot[], durationFrames?: number) => void;
  getSnapshot: () => { tracks: TrackData[]; undoStack: UndoSnapshot[]; redoStack: UndoSnapshot[] };

  // Derived
  scenes: () => SceneClipData[];
  subtitleTracks: () => TrackData[];
  videoTracks: () => TrackData[];
  audioTracks: () => TrackData[];
  totalWidthPx: () => number;
  currentSeconds: () => number;
  currentWordTimings: () => WordTiming[];
  selectedScene: () => SceneClipData | null;
}

function _snapshot(tracks: TrackData[]): TrackData[] {
  return tracks.map((t) => ({ ...t, content: { ...t.content } }));
}

function _pushUndo(set: (fn: (s: TimelineState) => Partial<TimelineState>) => void, get: () => TimelineState, description: string) {
  const { tracks } = get();
  const snap: UndoSnapshot = { tracks: _snapshot(tracks), description };
  set((s) => ({
    undoStack: [...s.undoStack.slice(-49), snap], // max 50 entries
    redoStack: [], // clear redo on new action
  }));
}

export const useTimelineStore = create<TimelineState>((set, get) => ({
  // Initial state
  tracks: [],
  durationFrames: 900,
  fps: 30,
  width: 1080,
  height: 1920,
  currentFrame: 0,
  isPlaying: false,
  loop: false,
  autoScroll: true,
  framePerPixel: 2,
  scrollX: 0,
  selectedSceneId: null,
  activeWordIndex: -1,
  undoStack: [],
  redoStack: [],

  // Actions
  setTracks: (tracks, duration) => set({ tracks, durationFrames: duration }),

  setCurrentFrame: (frame) => {
    const { durationFrames, loop } = get();
    let clamped = Math.max(0, Math.min(frame, durationFrames));
    if (loop && frame >= durationFrames) {
      clamped = 0;
    }
    set({ currentFrame: clamped });
  },

  seekToFrame: (frame) => {
    const { durationFrames } = get();
    const clamped = Math.max(0, Math.min(frame, durationFrames));
    set({ currentFrame: clamped, isPlaying: false });
  },

  nudgeFrame: (delta) => {
    const { currentFrame, durationFrames } = get();
    const next = Math.max(0, Math.min(currentFrame + delta, durationFrames));
    set({ currentFrame: next, isPlaying: false });
  },

  togglePlay: () => set((s) => ({ isPlaying: !s.isPlaying })),
  setPlaying: (playing) => set({ isPlaying: playing }),
  toggleLoop: () => set((s) => ({ loop: !s.loop })),
  toggleAutoScroll: () => set((s) => ({ autoScroll: !s.autoScroll })),

  setZoom: (fpp) => set({ framePerPixel: Math.max(0.25, Math.min(fpp, 10)) }),
  zoomIn: () => set((s) => ({ framePerPixel: Math.max(0.25, s.framePerPixel / 1.5) })),
  zoomOut: () => set((s) => ({ framePerPixel: Math.min(10, s.framePerPixel * 1.5) })),

  setScrollX: (x) => set({ scrollX: x }),
  selectScene: (id) => set({ selectedSceneId: id }),
  setActiveWordIndex: (i) => set({ activeWordIndex: i }),

  // Scene editing
  moveScene: (sceneId, deltaFrames) => {
    _pushUndo(set, get, `Move ${sceneId}`);
    set((s) => ({
      tracks: s.tracks.map((t) => {
        if (t.scene_id !== sceneId) return t;
        return {
          ...t,
          start_frame: Math.max(0, t.start_frame + deltaFrames),
          end_frame: Math.max(1, t.end_frame + deltaFrames),
        };
      }),
    }));
  },

  resizeScene: (sceneId, newEndFrame) => {
    _pushUndo(set, get, `Resize ${sceneId}`);
    set((s) => ({
      tracks: s.tracks.map((t) => {
        if (t.scene_id !== sceneId) return t;
        return {
          ...t,
          end_frame: Math.max(t.start_frame + 1, newEndFrame),
        };
      }),
    }));
  },

  updateSceneContent: (sceneId, field, value) => {
    _pushUndo(set, get, `Edit ${sceneId}.${field}`);
    set((s) => ({
      tracks: s.tracks.map((t) => {
        if (t.scene_id !== sceneId) return t;
        return {
          ...t,
          content: { ...t.content, [field]: value },
          ...(field === 'text' ? {} : {}),
        };
      }),
    }));
  },

  // Undo/Redo
  undo: () => {
    const { undoStack, tracks } = get();
    if (undoStack.length === 0) return;
    const snap = undoStack[undoStack.length - 1];
    set((s) => ({
      tracks: snap.tracks,
      undoStack: s.undoStack.slice(0, -1),
      redoStack: [...s.redoStack, { tracks: _snapshot(tracks), description: 'undo' }],
    }));
  },

  redo: () => {
    const { redoStack, tracks } = get();
    if (redoStack.length === 0) return;
    const snap = redoStack[redoStack.length - 1];
    set((s) => ({
      tracks: snap.tracks,
      redoStack: s.redoStack.slice(0, -1),
      undoStack: [...s.undoStack, { tracks: _snapshot(tracks), description: 'redo' }],
    }));
  },

  // Persistence
  restoreSession: (tracks, undoStack, redoStack, durationFrames) => {
    const maxEnd = tracks.length > 0 ? Math.max(...tracks.map((t) => t.end_frame)) : 900;
    set({
      tracks,
      undoStack,
      redoStack,
      durationFrames: durationFrames ?? maxEnd,
      currentFrame: 0,
      isPlaying: false,
      selectedSceneId: null,
    });
  },

  getSnapshot: () => {
    const { tracks, undoStack, redoStack } = get();
    return {
      tracks: _snapshot(tracks),
      undoStack,
      redoStack,
    };
  },

  // Derived
  scenes: () => {
    const { tracks } = get();
    const sceneMap = new Map<string, SceneClipData>();
    for (const t of tracks) {
      if (t.track_type === 'video' && !sceneMap.has(t.scene_id)) {
        sceneMap.set(t.scene_id, {
          scene_id: t.scene_id,
          scene_type: (t.content.scene_type as string) || '',
          text: (t.content.text as string) || '',
          start_frame: t.start_frame,
          end_frame: t.end_frame,
          layer: t.layer,
        });
      }
    }
    return Array.from(sceneMap.values()).sort((a, b) => a.start_frame - b.start_frame);
  },

  subtitleTracks: () => get().tracks.filter((t) => t.track_type === 'subtitle'),
  videoTracks: () => get().tracks.filter((t) => t.track_type === 'video'),
  audioTracks: () => get().tracks.filter((t) => t.track_type === 'audio'),
  totalWidthPx: () => Math.ceil(get().durationFrames / get().framePerPixel),
  currentSeconds: () => get().currentFrame / get().fps,

  currentWordTimings: () => {
    const { tracks, currentFrame } = get();
    for (const t of tracks) {
      if (t.track_type === 'subtitle' && currentFrame >= t.start_frame && currentFrame <= t.end_frame) {
        const wt = t.content.word_timings as WordTiming[] | undefined;
        if (wt) return wt;
      }
    }
    return [];
  },

  selectedScene: () => {
    const { selectedSceneId, tracks } = get();
    if (!selectedSceneId) return null;
    const vt = tracks.find((t) => t.scene_id === selectedSceneId && t.track_type === 'video');
    if (!vt) return null;
    return {
      scene_id: vt.scene_id,
      scene_type: (vt.content.scene_type as string) || '',
      text: (vt.content.text as string) || '',
      start_frame: vt.start_frame,
      end_frame: vt.end_frame,
      layer: vt.layer,
    };
  },
}));
