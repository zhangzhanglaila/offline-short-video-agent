import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Inspector } from './Inspector';
import { useTimelineStore } from '../store/timelineStore';
import type { TrackData } from '../store/timelineStore';

const tracks: TrackData[] = [
  {
    track_id: 'v1',
    track_type: 'video',
    layer: 0,
    start_frame: 0,
    end_frame: 90,
    scene_id: 'scene_1',
    content: { text: 'Hello World', scene_type: 'hook' },
  },
];

describe('Inspector', () => {
  beforeEach(() => {
    useTimelineStore.setState({
      tracks,
      durationFrames: 900,
      fps: 30,
      selectedSceneId: null,
      undoStack: [],
      redoStack: [],
    });
  });

  it('shows placeholder when no scene selected', () => {
    render(<Inspector />);
    expect(screen.getByText(/Select a scene/)).toBeInTheDocument();
  });

  it('shows keyboard shortcuts when no scene selected', () => {
    render(<Inspector />);
    expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
    expect(screen.getByText(/Play.*Pause/)).toBeInTheDocument();
  });

  it('shows scene details when selected', () => {
    useTimelineStore.setState({ selectedSceneId: 'scene_1' });
    render(<Inspector />);
    expect(screen.getByText('Scene: scene_1')).toBeInTheDocument();
    expect(screen.getByText('hook')).toBeInTheDocument();
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('shows frame range', () => {
    useTimelineStore.setState({ selectedSceneId: 'scene_1' });
    render(<Inspector />);
    expect(screen.getByText(/0 → 90/)).toBeInTheDocument();
  });

  it('shows duration', () => {
    useTimelineStore.setState({ selectedSceneId: 'scene_1' });
    render(<Inspector />);
    expect(screen.getByText('3.0s')).toBeInTheDocument(); // 90 frames / 30fps
  });

  it('shows layer', () => {
    useTimelineStore.setState({ selectedSceneId: 'scene_1' });
    render(<Inspector />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('enters edit mode on type click', () => {
    useTimelineStore.setState({ selectedSceneId: 'scene_1' });
    render(<Inspector />);
    fireEvent.click(screen.getByText('hook'));
    // Should show a select dropdown
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('enters edit mode on text click', () => {
    useTimelineStore.setState({ selectedSceneId: 'scene_1' });
    render(<Inspector />);
    fireEvent.click(screen.getByText('Hello World'));
    // Should show a textarea
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('undo button disabled when stack empty', () => {
    useTimelineStore.setState({ selectedSceneId: 'scene_1', undoStack: [] });
    render(<Inspector />);
    const undoBtn = screen.getByTitle('Undo (Ctrl+Z)');
    expect(undoBtn).toBeDisabled();
  });

  it('redo button disabled when stack empty', () => {
    useTimelineStore.setState({ selectedSceneId: 'scene_1', redoStack: [] });
    render(<Inspector />);
    const redoBtn = screen.getByTitle('Redo (Ctrl+Y)');
    expect(redoBtn).toBeDisabled();
  });

  it('resize slider has correct bounds', () => {
    useTimelineStore.setState({ selectedSceneId: 'scene_1' });
    render(<Inspector />);
    const slider = screen.getByRole('slider');
    expect(slider).toHaveAttribute('min', '10');   // start_frame + 10
    expect(slider).toHaveAttribute('max', '600');  // start_frame + 600
  });
});
