import { describe, it, expect } from 'vitest';
import { frameToSeconds, secondsToFrame, frameToTimecode, secondsToTimecode } from './frameConversion';

describe('frameToSeconds', () => {
  it('converts 0 frames to 0 seconds', () => {
    expect(frameToSeconds(0, 30)).toBe(0);
  });

  it('converts 30 frames to 1 second at 30fps', () => {
    expect(frameToSeconds(30, 30)).toBe(1);
  });

  it('converts 900 frames to 30 seconds at 30fps', () => {
    expect(frameToSeconds(900, 30)).toBe(30);
  });

  it('handles 24fps', () => {
    expect(frameToSeconds(48, 24)).toBe(2);
  });

  it('handles fractional results', () => {
    expect(frameToSeconds(1, 30)).toBeCloseTo(1 / 30);
  });
});

describe('secondsToFrame', () => {
  it('converts 0 seconds to 0 frames', () => {
    expect(secondsToFrame(0, 30)).toBe(0);
  });

  it('converts 1 second to 30 frames at 30fps', () => {
    expect(secondsToFrame(1, 30)).toBe(30);
  });

  it('rounds to nearest frame', () => {
    expect(secondsToFrame(0.5, 30)).toBe(15);
    expect(secondsToFrame(0.033, 30)).toBe(1); // ~1 frame
  });

  it('handles 24fps', () => {
    expect(secondsToFrame(2, 24)).toBe(48);
  });
});

describe('frameToTimecode', () => {
  it('formats frame 0 at 30fps', () => {
    expect(frameToTimecode(0, 30)).toBe('00:00:00.00');
  });

  it('formats 30 frames (1 second) at 30fps', () => {
    expect(frameToTimecode(30, 30)).toBe('00:00:01.00');
  });

  it('formats 900 frames (30 seconds) at 30fps', () => {
    expect(frameToTimecode(900, 30)).toBe('00:00:30.00');
  });

  it('formats 1830 frames (1 minute 1 second) at 30fps', () => {
    expect(frameToTimecode(1830, 30)).toBe('00:01:01.00');
  });

  it('formats partial seconds', () => {
    expect(frameToTimecode(45, 30)).toBe('00:00:01.15'); // 1.5 seconds = 1s + 15 frames
  });
});

describe('secondsToTimecode', () => {
  it('formats 0 seconds', () => {
    expect(secondsToTimecode(0)).toBe('00:00:00.000');
  });

  it('formats 1.5 seconds', () => {
    expect(secondsToTimecode(1.5)).toBe('00:00:01.500');
  });

  it('formats 61.25 seconds', () => {
    expect(secondsToTimecode(61.25)).toBe('00:01:01.250');
  });

  it('formats 3661 seconds (1h 1m 1s)', () => {
    expect(secondsToTimecode(3661)).toBe('01:01:01.000');
  });
});
