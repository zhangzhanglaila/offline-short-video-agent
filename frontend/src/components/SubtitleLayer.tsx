import React, { useMemo, useCallback } from 'react';
import { useTimelineStore } from '../store/timelineStore';
import type { TrackData, WordTiming } from '../store/timelineStore';

/** Subtitle layer with per-word TTS highlight. Click a word to seek. */
export const SubtitleLayer: React.FC<{ track: TrackData }> = ({ track }) => {
  const { framePerPixel, currentFrame, fps, setCurrentFrame, setPlaying } = useTimelineStore();

  const left = track.start_frame / framePerPixel;
  const width = (track.end_frame - track.start_frame) / framePerPixel;
  const text = (track.content.text as string) || '';
  const wordTimings = (track.content.word_timings as WordTiming[]) || [];

  // Find which word is currently active
  const activeWordIdx = useMemo(() => {
    if (!wordTimings.length) return -1;
    const now = currentFrame / fps;
    for (let i = 0; i < wordTimings.length; i++) {
      if (now >= wordTimings[i].start && now <= wordTimings[i].end) {
        return i;
      }
    }
    return -1;
  }, [wordTimings, currentFrame, fps]);

  // Click word to seek
  const handleWordClick = useCallback((wt: WordTiming) => {
    setPlaying(false);
    setCurrentFrame(wt.start_frame);
  }, [setCurrentFrame, setPlaying]);

  return (
    <div className="subtitle-track" style={{ left, width }}>
      <div className="subtitle-track__text">
        {wordTimings.length > 0 ? (
          wordTimings.map((wt, i) => (
            <span
              key={i}
              className={`subtitle-word ${i === activeWordIdx ? 'subtitle-word--active' : ''}`}
              onClick={() => handleWordClick(wt)}
              title={`${wt.start.toFixed(2)}s → ${wt.end.toFixed(2)}s`}
            >
              {wt.word}
            </span>
          ))
        ) : (
          <span>{text}</span>
        )}
      </div>
    </div>
  );
};
