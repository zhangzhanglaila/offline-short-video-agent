import { describe, it, expect, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { TimeRuler } from './TimeRuler';
import { useTimelineStore } from '../store/timelineStore';

describe('TimeRuler', () => {
  beforeEach(() => {
    useTimelineStore.setState({
      durationFrames: 300,
      fps: 30,
      framePerPixel: 2,
    });
  });

  it('renders a time-ruler container', () => {
    const { container } = render(<TimeRuler />);
    const ruler = container.querySelector('.time-ruler');
    expect(ruler).toBeTruthy();
  });

  it('renders tick marks for each second', () => {
    const { container } = render(<TimeRuler />);
    const ticks = container.querySelectorAll('.time-tick');
    // 300 frames / 30 fps = 10 seconds → 11 ticks (0s through 10s)
    expect(ticks.length).toBe(11);
  });

  it('displays second labels', () => {
    const { container } = render(<TimeRuler />);
    const labels = container.querySelectorAll('.tick-label');
    expect(labels[0].textContent).toBe('0s');
    expect(labels[1].textContent).toBe('1s');
    expect(labels[10].textContent).toBe('10s');
  });

  it('positions ticks based on framePerPixel', () => {
    useTimelineStore.setState({ framePerPixel: 3 });
    const { container } = render(<TimeRuler />);
    const ticks = container.querySelectorAll('.time-tick');
    // First tick at frame 0 → left = 0/3 = 0
    expect((ticks[0] as HTMLElement).style.left).toBe('0px');
    // Second tick at frame 30 → left = 30/3 = 10
    expect((ticks[1] as HTMLElement).style.left).toBe('10px');
  });

  it('renders sub-ticks when zoomed in enough', () => {
    // framePerPixel = 2, fps = 30, pxPerTick = 30/2 = 15 (< 40, no sub-ticks)
    const { container: c1 } = render(<TimeRuler />);
    expect(c1.querySelectorAll('.time-subtick').length).toBe(0);

    // Zoom in more: framePerPixel = 0.5, pxPerTick = 30/0.5 = 60 (> 40, sub-ticks)
    useTimelineStore.setState({ framePerPixel: 0.5 });
    const { container: c2 } = render(<TimeRuler />);
    expect(c2.querySelectorAll('.time-subtick').length).toBeGreaterThan(0);
  });

  it('sets ruler width based on duration and zoom', () => {
    const { container } = render(<TimeRuler />);
    const ruler = container.querySelector('.time-ruler') as HTMLElement;
    // totalPx = ceil(300 / 2) = 150
    expect(ruler.style.width).toBe('150px');
  });
});
