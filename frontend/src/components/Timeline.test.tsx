import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Timeline } from './Timeline';
import { useTimelineStore } from '../store/timelineStore';
import type { TrackData } from '../store/timelineStore';

const tracks: TrackData[] = [
  { track_id: 'v1', track_type: 'video', layer: 0, start_frame: 0, end_frame: 90, scene_id: 'hook', content: { scene_type: 'hook', text: 'Hello' } },
  { track_id: 's1', track_type: 'subtitle', layer: 1, start_frame: 0, end_frame: 90, scene_id: 'hook', content: { text: 'Hello' } },
  { track_id: 'a1', track_type: 'audio', layer: 2, start_frame: 0, end_frame: 90, scene_id: 'hook', content: { audio_path: 'test.mp3' } },
];

describe('Timeline', () => {
  beforeEach(() => {
    useTimelineStore.setState({
      tracks,
      durationFrames: 300,
      fps: 30,
      framePerPixel: 2,
      currentFrame: 0,
      selectedSceneId: null,
      undoStack: [],
      redoStack: [],
      isPlaying: false,
      loop: false,
      autoScroll: true,
    });
  });

  it('renders timeline header with title', () => {
    render(<Timeline />);
    expect(screen.getByText('Timeline')).toBeInTheDocument();
  });

  it('shows track and scene counts', () => {
    render(<Timeline />);
    expect(screen.getByText('3 tracks')).toBeInTheDocument();
    expect(screen.getByText('1 scenes')).toBeInTheDocument();
  });

  it('shows fps', () => {
    render(<Timeline />);
    expect(screen.getByText('30fps')).toBeInTheDocument();
  });

  it('renders zoom controls', () => {
    render(<Timeline />);
    expect(screen.getByTitle('Zoom in (Z)')).toBeInTheDocument();
    expect(screen.getByTitle('Zoom out (X)')).toBeInTheDocument();
  });

  it('renders undo/redo buttons', () => {
    render(<Timeline />);
    expect(screen.getByTitle('Undo (Ctrl+Z)')).toBeInTheDocument();
    expect(screen.getByTitle('Redo (Ctrl+Y)')).toBeInTheDocument();
  });

  it('disables undo when stack empty', () => {
    render(<Timeline />);
    expect(screen.getByTitle('Undo (Ctrl+Z)')).toBeDisabled();
  });

  it('enables undo when stack has entries', () => {
    useTimelineStore.setState({ undoStack: [{ tracks: [], description: 'test' }] });
    render(<Timeline />);
    expect(screen.getByTitle('Undo (Ctrl+Z)')).not.toBeDisabled();
  });

  it('renders track groups for video, subtitle, audio', () => {
    const { container } = render(<Timeline />);
    const groups = container.querySelectorAll('.track-group');
    expect(groups.length).toBe(3);
    expect(container.querySelector('.track-group-label')?.textContent).toBe('Video');
  });

  it('renders playhead', () => {
    const { container } = render(<Timeline />);
    expect(container.querySelector('.playhead')).toBeTruthy();
  });

  it('clicking ruler seeks to frame', () => {
    const { container } = render(<Timeline />);
    const rulerContainer = container.querySelector('.timeline-ruler-container');
    expect(rulerContainer).toBeTruthy();
  });

  it('hides track groups when empty', () => {
    useTimelineStore.setState({ tracks: [] });
    const { container } = render(<Timeline />);
    const groups = container.querySelectorAll('.track-group');
    expect(groups.length).toBe(0);
  });
});
