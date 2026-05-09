import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PlaybackControls } from './PlaybackControls';
import { useTimelineStore } from '../store/timelineStore';

describe('PlaybackControls', () => {
  beforeEach(() => {
    useTimelineStore.setState({
      currentFrame: 0,
      fps: 30,
      durationFrames: 900,
      isPlaying: false,
      loop: false,
      autoScroll: true,
    });
  });

  it('renders play button when not playing', () => {
    render(<PlaybackControls />);
    expect(screen.getByText('▶')).toBeInTheDocument();
  });

  it('renders pause button when playing', () => {
    useTimelineStore.setState({ isPlaying: true });
    render(<PlaybackControls />);
    expect(screen.getByText('⏸')).toBeInTheDocument();
  });

  it('toggles play on click', () => {
    render(<PlaybackControls />);
    fireEvent.click(screen.getByText('▶'));
    expect(useTimelineStore.getState().isPlaying).toBe(true);
  });

  it('resets to frame 0 on Home click', () => {
    useTimelineStore.setState({ currentFrame: 100 });
    render(<PlaybackControls />);
    fireEvent.click(screen.getByTitle('Home'));
    expect(useTimelineStore.getState().currentFrame).toBe(0);
  });

  it('displays current frame number', () => {
    useTimelineStore.setState({ currentFrame: 42 });
    render(<PlaybackControls />);
    expect(screen.getByText('F42')).toBeInTheDocument();
  });

  it('displays timecode', () => {
    useTimelineStore.setState({ currentFrame: 30, fps: 30 });
    render(<PlaybackControls />);
    expect(screen.getByText(/00:00:01\.00/)).toBeInTheDocument();
  });

  it('loop button reflects state', () => {
    const { unmount } = render(<PlaybackControls />);
    const loopBtn = screen.getByTitle('Loop (L)');
    expect(loopBtn.className).not.toContain('playback-btn--active');
    unmount();

    useTimelineStore.setState({ loop: true });
    render(<PlaybackControls />);
    const loopBtnActive = screen.getByTitle('Loop (L)');
    expect(loopBtnActive.className).toContain('playback-btn--active');
  });

  it('auto-scroll button reflects state', () => {
    useTimelineStore.setState({ autoScroll: false });
    render(<PlaybackControls />);
    const btn = screen.getByTitle('Auto-scroll');
    expect(btn.className).not.toContain('playback-btn--active');
  });

  it('scrubber has correct range', () => {
    render(<PlaybackControls />);
    const scrubber = screen.getByRole('slider');
    expect(scrubber).toHaveAttribute('min', '0');
    expect(scrubber).toHaveAttribute('max', '900');
  });

  it('scrubber changes frame on input', () => {
    render(<PlaybackControls />);
    const scrubber = screen.getByRole('slider');
    fireEvent.change(scrubber, { target: { value: '450' } });
    expect(useTimelineStore.getState().currentFrame).toBe(450);
  });
});
