import { useEffect } from 'react';
import { useTimelineStore } from '../store/timelineStore';

/** Global keyboard shortcuts for timeline editing. */
export function useKeyboard() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const store = useTimelineStore.getState();
      const target = e.target as HTMLElement;
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable;

      // Don't capture when typing in inputs
      if (isInput) return;

      switch (e.key) {
        case ' ':
          e.preventDefault();
          store.togglePlay();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          store.nudgeFrame(e.shiftKey ? -10 : -1);
          break;
        case 'ArrowRight':
          e.preventDefault();
          store.nudgeFrame(e.shiftKey ? 10 : 1);
          break;
        case 'Home':
          e.preventDefault();
          store.seekToFrame(0);
          break;
        case 'End':
          e.preventDefault();
          store.seekToFrame(store.durationFrames);
          break;
        case 'z':
        case 'Z':
          if (!e.ctrlKey && !e.metaKey) {
            store.zoomIn();
          } else {
            // Ctrl+Z = undo
            e.preventDefault();
            store.undo();
          }
          break;
        case 'x':
        case 'X':
          if (!e.ctrlKey && !e.metaKey) {
            store.zoomOut();
          }
          break;
        case 'y':
        case 'Y':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            store.redo();
          }
          break;
        case 'l':
        case 'L':
          if (!e.ctrlKey && !e.metaKey) {
            store.toggleLoop();
          }
          break;
        case 'Escape':
          store.selectScene(null);
          break;
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);
}
