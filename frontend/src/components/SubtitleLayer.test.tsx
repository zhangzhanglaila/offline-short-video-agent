import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SubtitleLayer } from './SubtitleLayer';
import { useTimelineStore } from '../store/timelineStore';
import type { TrackData } from '../store/timelineStore';

const trackWithWords: TrackData = {
  track_id: 's1',
  track_type: 'subtitle',
  layer: 1,
  start_frame: 0,
  end_frame: 90,
  scene_id: 'hook',
  content: {
    text: 'Hello World',
    word_timings: [
      { word: 'Hello', start: 0.0, end: 0.5, start_frame: 0, end_frame: 15 },
      { word: 'World', start: 0.5, end: 1.0, start_frame: 15, end_frame: 30 },
    ],
  },
};

const trackWithoutWords: TrackData = {
  track_id: 's2',
  track_type: 'subtitle',
  layer: 1,
  start_frame: 0,
  end_frame: 90,
  scene_id: 'hook',
  content: { text: 'Plain text' },
};

describe('SubtitleLayer', () => {
  beforeEach(() => {
    useTimelineStore.setState({
      fps: 30,
      framePerPixel: 2,
      currentFrame: 0,
    });
  });

  it('renders word spans when word_timings exist', () => {
    render(<SubtitleLayer track={trackWithWords} />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('World')).toBeInTheDocument();
  });

  it('renders plain text when no word_timings', () => {
    render(<SubtitleLayer track={trackWithoutWords} />);
    expect(screen.getByText('Plain text')).toBeInTheDocument();
  });

  it('highlights active word based on currentFrame', () => {
    // currentFrame = 20, fps = 30 → now = 0.667s → "World" is active (0.5-1.0)
    useTimelineStore.setState({ currentFrame: 20 });
    const { container } = render(<SubtitleLayer track={trackWithWords} />);
    const words = container.querySelectorAll('.subtitle-word');
    expect(words[0].className).not.toContain('active');
    expect(words[1].className).toContain('active');
  });

  it('clicking a word seeks to its start_frame', () => {
    render(<SubtitleLayer track={trackWithWords} />);
    fireEvent.click(screen.getByText('World'));
    const state = useTimelineStore.getState();
    expect(state.currentFrame).toBe(15);
  });

  it('clicking a word stops playback', () => {
    useTimelineStore.setState({ isPlaying: true });
    render(<SubtitleLayer track={trackWithWords} />);
    fireEvent.click(screen.getByText('Hello'));
    expect(useTimelineStore.getState().isPlaying).toBe(false);
  });

  it('positions based on framePerPixel', () => {
    useTimelineStore.setState({ framePerPixel: 3 });
    const { container } = render(<SubtitleLayer track={trackWithWords} />);
    const el = container.querySelector('.subtitle-track') as HTMLElement;
    // left = 0/3 = 0, width = (90-0)/3 = 30
    expect(el.style.left).toBe('0px');
    expect(el.style.width).toBe('30px');
  });

  it('shows timing title on word hover', () => {
    render(<SubtitleLayer track={trackWithWords} />);
    const hello = screen.getByText('Hello');
    expect(hello.title).toContain('0.00s');
    expect(hello.title).toContain('0.50s');
  });
});
