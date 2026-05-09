import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { Timeline } from './Timeline';
import { useTimelineStore } from '../store/timelineStore';
import { useKeyboard } from '../hooks/useKeyboard';
import type { TrackData } from '../store/timelineStore';

const tracks: TrackData[] = [
  { track_id: 'v1', track_type: 'video', layer: 0, start_frame: 0, end_frame: 90, scene_id: 'scene_1', content: { scene_type: 'hook', text: 'Hello' } },
  { track_id: 'v2', track_type: 'video', layer: 0, start_frame: 90, end_frame: 200, scene_id: 'scene_2', content: { scene_type: 'graph', text: 'World' } },
  { track_id: 's1', track_type: 'subtitle', layer: 1, start_frame: 0, end_frame: 90, scene_id: 'scene_1', content: { text: 'Hello' } },
  { track_id: 'a1', track_type: 'audio', layer: 2, start_frame: 0, end_frame: 90, scene_id: 'scene_1', content: {} },
];

function resetStore() {
  useTimelineStore.setState({
    tracks,
    durationFrames: 200,
    fps: 30,
    framePerPixel: 2,
    currentFrame: 0,
    isPlaying: false,
    loop: false,
    autoScroll: true,
    selectedSceneId: null,
    undoStack: [],
    redoStack: [],
    scrollX: 0,
    activeWordIndex: -1,
  });
}

/** Wrapper that registers the keyboard hook (like App.tsx does). */
function WithKeyboard({ children }: { children: React.ReactNode }) {
  useKeyboard();
  return <>{children}</>;
}

describe('Undo/Redo Integration', () => {
  beforeEach(() => {
    resetStore();
  });

  describe('Toolbar buttons', () => {
    it('undo button is disabled when undoStack is empty', () => {
      render(<Timeline />);
      const undoBtn = screen.getByTitle('Undo (Ctrl+Z)');
      expect(undoBtn).toBeDisabled();
    });

    it('redo button is disabled when redoStack is empty', () => {
      render(<Timeline />);
      const redoBtn = screen.getByTitle('Redo (Ctrl+Y)');
      expect(redoBtn).toBeDisabled();
    });

    it('undo button enables after a move operation', () => {
      const { unmount } = render(<Timeline />);
      useTimelineStore.getState().moveScene('scene_1', 10);
      unmount();

      render(<Timeline />);
      const undoBtn = screen.getByTitle('Undo (Ctrl+Z)');
      expect(undoBtn).not.toBeDisabled();
    });

    it('clicking undo reverts the last change', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      expect(useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame).toBe(10);

      render(<Timeline />);
      act(() => {
        fireEvent.click(screen.getByTitle('Undo (Ctrl+Z)'));
      });

      expect(useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame).toBe(0);
    });

    it('clicking redo re-applies the undone change', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      useTimelineStore.getState().undo();

      render(<Timeline />);
      act(() => {
        fireEvent.click(screen.getByTitle('Redo (Ctrl+Y)'));
      });

      expect(useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame).toBe(10);
    });

    it('undo count displays number of undo entries', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      useTimelineStore.getState().moveScene('scene_1', 20);

      render(<Timeline />);
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('undo count is empty when stack is empty', () => {
      render(<Timeline />);
      const countEl = screen.getByTitle('Undo (Ctrl+Z)').closest('.undo-redo-controls')?.querySelector('.undo-count');
      expect(countEl?.textContent).toBe('');
    });
  });

  describe('Keyboard shortcuts (via useKeyboard hook)', () => {
    it('Ctrl+Z triggers undo', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);

      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'z', ctrlKey: true, bubbles: true }));
      });

      expect(useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame).toBe(0);
    });

    it('Ctrl+Y triggers redo', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      useTimelineStore.getState().undo();

      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'y', ctrlKey: true, bubbles: true }));
      });

      expect(useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame).toBe(10);
    });

    it('Meta+Z triggers undo (macOS)', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);

      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'z', metaKey: true, bubbles: true }));
      });

      expect(useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame).toBe(0);
    });

    it('Space toggles play', () => {
      render(<WithKeyboard><Timeline /></WithKeyboard>);
      expect(useTimelineStore.getState().isPlaying).toBe(false);

      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }));
      });
      expect(useTimelineStore.getState().isPlaying).toBe(true);

      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }));
      });
      expect(useTimelineStore.getState().isPlaying).toBe(false);
    });

    it('Arrow keys nudge frame', () => {
      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
      });
      expect(useTimelineStore.getState().currentFrame).toBe(1);

      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }));
      });
      expect(useTimelineStore.getState().currentFrame).toBe(0);
    });

    it('Shift+Arrow nudges by 10', () => {
      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', shiftKey: true, bubbles: true }));
      });
      expect(useTimelineStore.getState().currentFrame).toBe(10);
    });

    it('L toggles loop', () => {
      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'l', bubbles: true }));
      });
      expect(useTimelineStore.getState().loop).toBe(true);
    });

    it('Escape deselects scene', () => {
      useTimelineStore.setState({ selectedSceneId: 'scene_1' });
      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
      });
      expect(useTimelineStore.getState().selectedSceneId).toBeNull();
    });

    it('Home seeks to start', () => {
      useTimelineStore.setState({ currentFrame: 50 });
      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Home', bubbles: true }));
      });
      expect(useTimelineStore.getState().currentFrame).toBe(0);
    });

    it('End seeks to end', () => {
      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'End', bubbles: true }));
      });
      expect(useTimelineStore.getState().currentFrame).toBe(200);
    });

    it('Z without Ctrl zooms in', () => {
      useTimelineStore.setState({ framePerPixel: 4 });
      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'z', bubbles: true }));
      });
      expect(useTimelineStore.getState().framePerPixel).toBeCloseTo(4 / 1.5);
    });

    it('X without Ctrl zooms out', () => {
      useTimelineStore.setState({ framePerPixel: 4 });
      render(<WithKeyboard><Timeline /></WithKeyboard>);
      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'x', bubbles: true }));
      });
      expect(useTimelineStore.getState().framePerPixel).toBeCloseTo(4 * 1.5);
    });
  });

  describe('Multi-step undo/redo', () => {
    it('undoes multiple changes in reverse order', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      useTimelineStore.getState().moveScene('scene_1', 20);

      render(<Timeline />);

      act(() => { fireEvent.click(screen.getByTitle('Undo (Ctrl+Z)')); });
      expect(useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame).toBe(10);

      act(() => { fireEvent.click(screen.getByTitle('Undo (Ctrl+Z)')); });
      expect(useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame).toBe(0);
    });

    it('redo button enables after undo', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);
      useTimelineStore.getState().undo();

      render(<Timeline />);
      const redoBtn = screen.getByTitle('Redo (Ctrl+Y)');
      expect(redoBtn).not.toBeDisabled();
    });

    it('keyboard undo/redo round-trip', () => {
      useTimelineStore.getState().moveScene('scene_1', 10);

      render(<WithKeyboard><Timeline /></WithKeyboard>);

      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'z', ctrlKey: true, bubbles: true }));
      });
      expect(useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame).toBe(0);

      act(() => {
        window.dispatchEvent(new KeyboardEvent('keydown', { key: 'y', ctrlKey: true, bubbles: true }));
      });
      expect(useTimelineStore.getState().tracks.find((t) => t.track_id === 'v1')!.start_frame).toBe(10);
    });
  });
});
