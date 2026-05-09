import React from 'react';
import { useTimelineStore } from '../store/timelineStore';

/** Time ruler showing frame/second markers above the timeline. */
export const TimeRuler: React.FC = () => {
  const { durationFrames, fps, framePerPixel } = useTimelineStore();
  const totalPx = Math.ceil(durationFrames / framePerPixel);

  // Generate tick marks every second
  const ticks: React.ReactNode[] = [];
  const framesPerTick = fps; // one tick per second
  const pxPerTick = framesPerTick / framePerPixel;

  for (let frame = 0; frame <= durationFrames; frame += framesPerTick) {
    const x = frame / framePerPixel;
    const sec = Math.floor(frame / fps);
    ticks.push(
      <div
        key={frame}
        className="time-tick"
        style={{ left: x }}
      >
        <div className="tick-line" />
        <span className="tick-label">{sec}s</span>
      </div>
    );

    // Sub-ticks (every 10 frames)
    if (pxPerTick > 40) {
      for (let sub = framesPerTick / 2; sub < framesPerTick; sub += Math.max(1, Math.floor(fps / 4))) {
        const subFrame = frame + sub;
        if (subFrame > durationFrames) break;
        const sx = subFrame / framePerPixel;
        ticks.push(
          <div key={`sub-${subFrame}`} className="time-subtick" style={{ left: sx }}>
            <div className="subtick-line" />
          </div>
        );
      }
    }
  }

  return (
    <div className="time-ruler" style={{ width: totalPx }}>
      {ticks}
    </div>
  );
};
