import React, { useEffect, useRef } from 'react';
import { useTimelineStore } from '../store/timelineStore';
import { secondsToTimecode } from '../utils/frameConversion';

/** Playback controls: play/pause, seek, loop, auto-scroll. */
export const PlaybackControls: React.FC = () => {
  const {
    currentFrame, fps, durationFrames, isPlaying, loop, autoScroll,
    setCurrentFrame, togglePlay, setPlaying, toggleLoop, toggleAutoScroll,
  } = useTimelineStore();
  const timerRef = useRef<number | null>(null);

  // Playback loop
  useEffect(() => {
    if (isPlaying) {
      const interval = 1000 / fps;
      timerRef.current = window.setInterval(() => {
        const { currentFrame, durationFrames, loop } = useTimelineStore.getState();
        if (currentFrame >= durationFrames) {
          if (loop) {
            setCurrentFrame(0);
          } else {
            setPlaying(false);
          }
          return;
        }
        setCurrentFrame(currentFrame + 1);
      }, interval);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, fps, setCurrentFrame, setPlaying]);

  const currentSec = currentFrame / fps;
  const durationSec = durationFrames / fps;

  return (
    <div className="playback-controls">
      <button className="playback-btn" onClick={togglePlay} title="Space">
        {isPlaying ? '⏸' : '▶'}
      </button>
      <button className="playback-btn" onClick={() => setCurrentFrame(0)} title="Home">
        ⏮
      </button>

      <input
        type="range"
        className="playback-scrubber"
        min={0}
        max={durationFrames}
        value={currentFrame}
        onChange={(e) => setCurrentFrame(Number(e.target.value))}
      />

      <span className="playback-time">
        {secondsToTimecode(currentSec)} / {secondsToTimecode(durationSec)}
      </span>

      <span className="playback-frame">
        F{currentFrame}
      </span>

      <button
        className={`playback-btn playback-btn--toggle ${loop ? 'playback-btn--active' : ''}`}
        onClick={toggleLoop}
        title="Loop (L)"
      >
        🔁
      </button>

      <button
        className={`playback-btn playback-btn--toggle ${autoScroll ? 'playback-btn--active' : ''}`}
        onClick={toggleAutoScroll}
        title="Auto-scroll"
      >
        📌
      </button>
    </div>
  );
};
