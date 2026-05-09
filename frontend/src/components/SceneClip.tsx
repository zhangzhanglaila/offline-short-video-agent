import React, { useCallback, useRef, useState } from 'react';
import { useTimelineStore } from '../store/timelineStore';
import type { SceneClipData } from '../store/timelineStore';

/** A single scene clip in the video track. Supports horizontal drag. */
export const SceneClip: React.FC<{ clip: SceneClipData }> = ({ clip }) => {
  const { framePerPixel, selectedSceneId, selectScene, moveScene } = useTimelineStore();
  const isSelected = selectedSceneId === clip.scene_id;
  const dragRef = useRef<{ startX: number; startFrame: number } | null>(null);
  const [dragging, setDragging] = useState(false);

  const left = clip.start_frame / framePerPixel;
  const width = (clip.end_frame - clip.start_frame) / framePerPixel;

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    selectScene(clip.scene_id);
    dragRef.current = { startX: e.clientX, startFrame: clip.start_frame };
    setDragging(true);

    const handleMouseMove = (ev: MouseEvent) => {
      if (!dragRef.current) return;
      const dx = ev.clientX - dragRef.current.startX;
      const deltaFrames = Math.round(dx * framePerPixel);
      if (deltaFrames !== 0) {
        moveScene(clip.scene_id, deltaFrames);
        dragRef.current.startX = ev.clientX;
        dragRef.current.startFrame += deltaFrames;
      }
    };

    const handleMouseUp = () => {
      dragRef.current = null;
      setDragging(false);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  }, [clip, framePerPixel, selectScene, moveScene]);

  return (
    <div
      className={`scene-clip scene-clip--${clip.scene_type} ${isSelected ? 'scene-clip--selected' : ''} ${dragging ? 'scene-clip--dragging' : ''}`}
      style={{ left, width }}
      onMouseDown={handleMouseDown}
      title={`${clip.scene_type}: ${clip.text}\n${clip.start_frame} → ${clip.end_frame}`}
    >
      <div className="scene-clip__label">
        <span className="scene-clip__type">{clip.scene_type}</span>
        <span className="scene-clip__text">{clip.text.slice(0, 20)}</span>
      </div>
    </div>
  );
};
