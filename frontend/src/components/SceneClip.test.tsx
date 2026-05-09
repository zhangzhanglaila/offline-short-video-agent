import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SceneClip } from './SceneClip';
import { useTimelineStore } from '../store/timelineStore';
import type { SceneClipData } from '../store/timelineStore';

const clip: SceneClipData = {
  scene_id: 'scene_1',
  scene_type: 'hook',
  text: 'Redis is fast',
  start_frame: 0,
  end_frame: 90,
  layer: 0,
};

describe('SceneClip', () => {
  beforeEach(() => {
    useTimelineStore.setState({
      tracks: [],
      durationFrames: 900,
      fps: 30,
      framePerPixel: 2,
      selectedSceneId: null,
      undoStack: [],
      redoStack: [],
    });
  });

  it('renders scene type and text', () => {
    render(<SceneClip clip={clip} />);
    expect(screen.getByText('hook')).toBeInTheDocument();
    expect(screen.getByText('Redis is fast')).toBeInTheDocument();
  });

  it('applies correct CSS class for scene type', () => {
    const { container } = render(<SceneClip clip={clip} />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain('scene-clip--hook');
  });

  it('applies selected class when selected', () => {
    useTimelineStore.setState({ selectedSceneId: 'scene_1' });
    const { container } = render(<SceneClip clip={clip} />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain('scene-clip--selected');
  });

  it('selects scene on click', () => {
    const { container } = render(<SceneClip clip={clip} />);
    fireEvent.mouseDown(container.firstChild as HTMLElement);
    expect(useTimelineStore.getState().selectedSceneId).toBe('scene_1');
  });

  it('positions clip using framePerPixel', () => {
    useTimelineStore.setState({ framePerPixel: 3 });
    const { container } = render(<SceneClip clip={clip} />);
    const el = container.firstChild as HTMLElement;
    expect(el.style.left).toBe('0px'); // 0 / 3
    expect(el.style.width).toBe(`${90 / 3}px`); // 90 / 3 = 30px
  });

  it('shows title attribute with details', () => {
    const { container } = render(<SceneClip clip={clip} />);
    const el = container.firstChild as HTMLElement;
    expect(el.title).toContain('hook');
    expect(el.title).toContain('Redis is fast');
    expect(el.title).toContain('0 → 90');
  });
});
