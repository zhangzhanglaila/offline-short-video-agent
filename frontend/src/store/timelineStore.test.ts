import { describe, it, expect, beforeEach } from 'vitest';
import { useTimelineStore } from './timelineStore';
import type { TrackData } from './timelineStore';

function makeTrack(overrides: Partial<TrackData> = {}): TrackData {
  return {
    track_id: 'track_1',
    track_type: 'video',
    layer: 0,
    start_frame: 0,
    end_frame: 90,
    scene_id: 'scene_1',
    content: { text: 'Hello', scene_type: 'hook' },
    ...overrides,
  };
}

function makeTracks(): TrackData[] {
  return [
    makeTrack({ track_id: 'v1', scene_id: 'scene_1', start_frame: 0, end_frame: 90 }),
    makeTrack({ track_id: 'v2', scene_id: 'scene_2', start_frame: 90, end_frame: 200 }),
    makeTrack({ track_id: 'sub1', track_type: 'subtitle', scene_id: 'scene_1', start_frame: 0, end_frame: 90, content: { text: 'Hello', word_timings: [{ word: 'Hello', start: 0, end: 0.5, start_frame: 0, end_frame: 15 }] } }),
    makeTrack({ track_id: 'aud1', track_type: 'audio', scene_id: 'scene_1', start_frame: 0, end_frame: 90, content: { audio_path: '/tmp/a.mp3' } }),
  ];
}

describe('timelineStore', () => {
  beforeEach(() => {
    useTimelineStore.setState({
      loop: false,
      autoScroll: true,
      isPlaying: false,
      currentFrame: 0,
      selectedSceneId: null,
      undoStack: [],
      redoStack: [],
      framePerPixel: 2,
    });
    useTimelineStore.getState().setTracks(makeTracks(), 200);
  });

  describe('setTracks', () => {
    it('stores tracks and duration', () => {
      const { tracks, durationFrames } = useTimelineStore.getState();
      expect(tracks).toHaveLength(4);
      expect(durationFrames).toBe(200);
    });
  });

  describe('setCurrentFrame', () => {
    it('clamps to 0', () => {
      useTimelineStore.getState().setCurrentFrame(-10);
      expect(useTimelineStore.getState().currentFrame).toBe(0);
    });

    it('clamps to durationFrames', () => {
      useTimelineStore.getState().setCurrentFrame(999);
      expect(useTimelineStore.getState().currentFrame).toBe(200);
    });

    it('wraps to 0 when looping and past end', () => {
      useTimelineStore.setState({ loop: true });
      useTimelineStore.getState().setCurrentFrame(250);
      expect(useTimelineStore.getState().currentFrame).toBe(0);
    });
  });

  describe('seekToFrame', () => {
    it('seeks and stops playback', () => {
      useTimelineStore.setState({ isPlaying: true });
      useTimelineStore.getState().seekToFrame(100);
      const { currentFrame, isPlaying } = useTimelineStore.getState();
      expect(currentFrame).toBe(100);
      expect(isPlaying).toBe(false);
    });
  });

  describe('nudgeFrame', () => {
    it('nudges forward by 1', () => {
      useTimelineStore.getState().nudgeFrame(1);
      expect(useTimelineStore.getState().currentFrame).toBe(1);
    });

    it('nudges backward by 1', () => {
      useTimelineStore.setState({ currentFrame: 10 });
      useTimelineStore.getState().nudgeFrame(-1);
      expect(useTimelineStore.getState().currentFrame).toBe(9);
    });

    it('clamps at 0', () => {
      useTimelineStore.getState().nudgeFrame(-1);
      expect(useTimelineStore.getState().currentFrame).toBe(0);
    });

    it('stops playback', () => {
      useTimelineStore.setState({ isPlaying: true });
      useTimelineStore.getState().nudgeFrame(1);
      expect(useTimelineStore.getState().isPlaying).toBe(false);
    });
  });

  describe('togglePlay', () => {
    it('toggles isPlaying', () => {
      expect(useTimelineStore.getState().isPlaying).toBe(false);
      useTimelineStore.getState().togglePlay();
      expect(useTimelineStore.getState().isPlaying).toBe(true);
      useTimelineStore.getState().togglePlay();
      expect(useTimelineStore.getState().isPlaying).toBe(false);
    });
  });

  describe('toggleLoop', () => {
    it('toggles loop', () => {
      expect(useTimelineStore.getState().loop).toBe(false);
      useTimelineStore.getState().toggleLoop();
      expect(useTimelineStore.getState().loop).toBe(true);
    });
  });

  describe('zoom', () => {
    it('setZoom clamps to range', () => {
      useTimelineStore.getState().setZoom(0.01);
      expect(useTimelineStore.getState().framePerPixel).toBe(0.25);
      useTimelineStore.getState().setZoom(100);
      expect(useTimelineStore.getState().framePerPixel).toBe(10);
    });

    it('zoomIn decreases framePerPixel', () => {
      useTimelineStore.setState({ framePerPixel: 4 });
      useTimelineStore.getState().zoomIn();
      expect(useTimelineStore.getState().framePerPixel).toBeCloseTo(4 / 1.5);
    });

    it('zoomOut increases framePerPixel', () => {
      useTimelineStore.setState({ framePerPixel: 4 });
      useTimelineStore.getState().zoomOut();
      expect(useTimelineStore.getState().framePerPixel).toBeCloseTo(4 * 1.5);
    });
  });

  describe('selectScene', () => {
    it('selects a scene', () => {
      useTimelineStore.getState().selectScene('scene_1');
      expect(useTimelineStore.getState().selectedSceneId).toBe('scene_1');
    });

    it('deselects with null', () => {
      useTimelineStore.getState().selectScene('scene_1');
      useTimelineStore.getState().selectScene(null);
      expect(useTimelineStore.getState().selectedSceneId).toBeNull();
    });
  });

  describe('moveScene', () => {
    it('moves all tracks for a scene by delta', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      const tracks = useTimelineStore.getState().tracks;
      const v1 = tracks.find((t) => t.track_id === 'v1')!;
      expect(v1.start_frame).toBe(10);
      expect(v1.end_frame).toBe(100);
    });

    it('does not move unrelated tracks', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      const tracks = useTimelineStore.getState().tracks;
      const v2 = tracks.find((t) => t.track_id === 'v2')!;
      expect(v2.start_frame).toBe(90);
    });

    it('clamps start_frame to 0', () => {
      useTimelineStore.getState().moveScene('scene_1', -50);
      const tracks = useTimelineStore.getState().tracks;
      const v1 = tracks.find((t) => t.track_id === 'v1')!;
      expect(v1.start_frame).toBe(0);
    });
  });

  describe('resizeScene', () => {
    it('resizes end_frame', () => {
      useTimelineStore.getState().resizeScene('scene_1', 150);
      const tracks = useTimelineStore.getState().tracks;
      const v1 = tracks.find((t) => t.track_id === 'v1')!;
      expect(v1.end_frame).toBe(150);
    });

    it('enforces minimum (start_frame + 1)', () => {
      useTimelineStore.getState().resizeScene('scene_1', -10);
      const tracks = useTimelineStore.getState().tracks;
      const v1 = tracks.find((t) => t.track_id === 'v1')!;
      expect(v1.end_frame).toBeGreaterThanOrEqual(v1.start_frame + 1);
    });
  });

  describe('updateSceneContent', () => {
    it('updates a content field', () => {
      useTimelineStore.getState().updateSceneContent('scene_1', 'text', 'Updated text');
      const tracks = useTimelineStore.getState().tracks;
      const v1 = tracks.find((t) => t.track_id === 'v1')!;
      expect(v1.content.text).toBe('Updated text');
    });

    it('preserves other content fields', () => {
      useTimelineStore.getState().updateSceneContent('scene_1', 'text', 'New');
      const tracks = useTimelineStore.getState().tracks;
      const v1 = tracks.find((t) => t.track_id === 'v1')!;
      expect(v1.content.scene_type).toBe('hook');
    });
  });

  describe('undo/redo', () => {
    it('undo restores previous state', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      const before = useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame;
      expect(before).toBe(10);

      useTimelineStore.getState().undo();
      const after = useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame;
      expect(after).toBe(0);
    });

    it('redo re-applies undone change', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      useTimelineStore.getState().undo();
      useTimelineStore.getState().redo();
      const v1 = useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!;
      expect(v1.start_frame).toBe(10);
    });

    it('undo with empty stack does nothing', () => {
      const before = useTimelineStore.getState().tracks;
      useTimelineStore.getState().undo();
      expect(useTimelineStore.getState().tracks).toEqual(before);
    });

    it('redo with empty stack does nothing', () => {
      const before = useTimelineStore.getState().tracks;
      useTimelineStore.getState().redo();
      expect(useTimelineStore.getState().tracks).toEqual(before);
    });

    it('new action clears redo stack', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      useTimelineStore.getState().undo();
      expect(useTimelineStore.getState().redoStack.length).toBe(1);

      useTimelineStore.getState().moveScene('scene_1', 20);
      expect(useTimelineStore.getState().redoStack.length).toBe(0);
    });

    it('undo stack caps at 50', () => {
      for (let i = 0; i < 60; i++) {
        useTimelineStore.getState().moveScene('scene_1', 1);
      }
      expect(useTimelineStore.getState().undoStack.length).toBeLessThanOrEqual(50);
    });
  });

  describe('derived: scenes()', () => {
    it('returns unique video scenes sorted by start_frame', () => {
      const scenes = useTimelineStore.getState().scenes();
      expect(scenes).toHaveLength(2);
      expect(scenes[0].scene_id).toBe('scene_1');
      expect(scenes[1].scene_id).toBe('scene_2');
    });

    it('includes scene_type and text from content', () => {
      const scenes = useTimelineStore.getState().scenes();
      expect(scenes[0].scene_type).toBe('hook');
      expect(scenes[0].text).toBe('Hello');
    });
  });

  describe('derived: track filters', () => {
    it('videoTracks returns only video', () => {
      expect(useTimelineStore.getState().videoTracks()).toHaveLength(2);
    });

    it('subtitleTracks returns only subtitle', () => {
      expect(useTimelineStore.getState().subtitleTracks()).toHaveLength(1);
    });

    it('audioTracks returns only audio', () => {
      expect(useTimelineStore.getState().audioTracks()).toHaveLength(1);
    });
  });

  describe('derived: currentWordTimings()', () => {
    it('returns word timings for current frame in subtitle track', () => {
      useTimelineStore.setState({ currentFrame: 10 });
      const timings = useTimelineStore.getState().currentWordTimings();
      expect(timings).toHaveLength(1);
      expect(timings[0].word).toBe('Hello');
    });

    it('returns empty when no subtitle at current frame', () => {
      useTimelineStore.setState({ currentFrame: 500 });
      expect(useTimelineStore.getState().currentWordTimings()).toHaveLength(0);
    });
  });

  describe('derived: selectedScene()', () => {
    it('returns null when nothing selected', () => {
      expect(useTimelineStore.getState().selectedScene()).toBeNull();
    });

    it('returns scene data when selected', () => {
      useTimelineStore.getState().selectScene('scene_1');
      const scene = useTimelineStore.getState().selectedScene();
      expect(scene).not.toBeNull();
      expect(scene!.scene_id).toBe('scene_1');
      expect(scene!.scene_type).toBe('hook');
    });
  });

  describe('derived: totalWidthPx()', () => {
    it('computes total width', () => {
      useTimelineStore.setState({ durationFrames: 300, framePerPixel: 2 });
      expect(useTimelineStore.getState().totalWidthPx()).toBe(150);
    });
  });

  describe('derived: currentSeconds()', () => {
    it('computes seconds from currentFrame and fps', () => {
      useTimelineStore.setState({ currentFrame: 60, fps: 30 });
      expect(useTimelineStore.getState().currentSeconds()).toBe(2);
    });
  });
});
