import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Track } from './Track';
import { useTimelineStore } from '../store/timelineStore';
import type { TrackData } from '../store/timelineStore';

const videoTrack: TrackData = {
  track_id: 'v1',
  track_type: 'video',
  layer: 0,
  start_frame: 0,
  end_frame: 90,
  scene_id: 'hook',
  content: { scene_type: 'hook', text: 'Hello' },
};

const subtitleTrack: TrackData = {
  track_id: 's1',
  track_type: 'subtitle',
  layer: 1,
  start_frame: 0,
  end_frame: 90,
  scene_id: 'hook',
  content: { text: 'Hello', word_timings: [{ word: 'Hello', start: 0, end: 0.5, start_frame: 0, end_frame: 15 }] },
};

const audioTrack: TrackData = {
  track_id: 'a1',
  track_type: 'audio',
  layer: 2,
  start_frame: 0,
  end_frame: 90,
  scene_id: 'hook',
  content: { audio_path: 'test.mp3' },
};

describe('Track', () => {
  beforeEach(() => {
    useTimelineStore.setState({
      tracks: [videoTrack, subtitleTrack, audioTrack],
      durationFrames: 300,
      fps: 30,
      framePerPixel: 2,
      currentFrame: 0,
      selectedSceneId: null,
      undoStack: [],
      redoStack: [],
    });
  });

  it('renders track label with type badge', () => {
    render(<Track track={videoTrack} />);
    expect(screen.getByText('V')).toBeInTheDocument();
    expect(screen.getAllByText('hook').length).toBeGreaterThanOrEqual(1);
  });

  it('shows S badge for subtitle track', () => {
    render(<Track track={subtitleTrack} />);
    expect(screen.getByText('S')).toBeInTheDocument();
  });

  it('shows A badge for audio track', () => {
    render(<Track track={audioTrack} />);
    expect(screen.getByText('A')).toBeInTheDocument();
  });

  it('renders SceneClip for video track', () => {
    const { container } = render(<Track track={videoTrack} />);
    expect(container.querySelector('.scene-clip')).toBeTruthy();
  });

  it('renders SubtitleLayer for subtitle track', () => {
    const { container } = render(<Track track={subtitleTrack} />);
    expect(container.querySelector('.subtitle-track')).toBeTruthy();
  });

  it('renders audio-clip for audio track', () => {
    const { container } = render(<Track track={audioTrack} />);
    expect(container.querySelector('.audio-clip')).toBeTruthy();
  });

  it('applies track type CSS class', () => {
    const { container } = render(<Track track={videoTrack} />);
    const badge = container.querySelector('.track__type');
    expect(badge?.className).toContain('track__type--video');
  });
});
