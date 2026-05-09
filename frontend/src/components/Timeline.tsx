import React, { useRef, useCallback, useEffect } from 'react';
import { useTimelineStore } from '../store/timelineStore';
import { Track } from './Track';
import { PlaybackControls } from './PlaybackControls';
import { Inspector } from './Inspector';

/** Main timeline editor component. */
export const Timeline: React.FC = () => {
  const {
    tracks, fps, framePerPixel, currentFrame, autoScroll,
    scenes, setZoom, setCurrentFrame,
  } = useTimelineStore();

  const containerRef = useRef<HTMLDivElement>(null);

  // Click on ruler to seek
  const handleRulerClick = useCallback((e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left + (containerRef.current?.scrollLeft || 0);
    const frame = Math.round(x * framePerPixel);
    setCurrentFrame(frame);
  }, [framePerPixel, setCurrentFrame]);

  // Mouse wheel zoom (Ctrl+wheel)
  const handleWheel = useCallback((e: React.WheelEvent) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      const store = useTimelineStore.getState();
      if (e.deltaY < 0) {
        store.zoomIn();
      } else {
        store.zoomOut();
      }
    }
  }, []);

  // Auto-scroll to keep playhead visible
  useEffect(() => {
    if (!autoScroll) return;
    const container = containerRef.current;
    if (!container) return;

    const playheadX = currentFrame / framePerPixel;
    const viewLeft = container.scrollLeft;
    const viewRight = viewLeft + container.clientWidth;
    const margin = container.clientWidth * 0.1;

    if (playheadX < viewLeft + margin) {
      container.scrollLeft = Math.max(0, playheadX - margin);
    } else if (playheadX > viewRight - margin) {
      container.scrollLeft = playheadX - container.clientWidth + margin;
    }
  }, [currentFrame, framePerPixel, autoScroll]);

  // Current time indicator position
  const playheadX = currentFrame / framePerPixel;
  const totalPx = Math.ceil(useTimelineStore.getState().durationFrames / framePerPixel);

  // Group tracks by type
  const videoTracks = tracks.filter((t) => t.track_type === 'video');
  const subtitleTracks = tracks.filter((t) => t.track_type === 'subtitle');
  const audioTracks = tracks.filter((t) => t.track_type === 'audio');

  return (
    <div className="timeline-editor">
      {/* Header */}
      <div className="timeline-header">
        <h2 className="timeline-title">Timeline</h2>
        <div className="timeline-info">
          <span>{scenes().length} scenes</span>
          <span>{tracks.length} tracks</span>
          <span>{fps}fps</span>
        </div>
        <div className="zoom-controls">
          <button onClick={() => setZoom(framePerPixel * 1.5)} title="Zoom out (X)">−</button>
          <span className="zoom-label">{framePerPixel.toFixed(1)} f/px</span>
          <button onClick={() => setZoom(framePerPixel / 1.5)} title="Zoom in (Z)">+</button>
        </div>
      </div>

      {/* Playback controls */}
      <PlaybackControls />

      {/* Timeline body + Inspector side panel */}
      <div className="timeline-main">
        <div className="timeline-body" ref={containerRef} onWheel={handleWheel}>
          {/* Time ruler */}
          <div className="timeline-ruler-container" onClick={handleRulerClick}>
            <div className="track-label-spacer" />
            <div className="time-ruler" style={{ width: totalPx }}>
              {Array.from({ length: Math.ceil(useTimelineStore.getState().durationFrames / fps) + 1 }, (_, i) => {
                const frame = i * fps;
                const x = frame / framePerPixel;
                return (
                  <div key={i} className="time-tick" style={{ left: x }}>
                    <div className="tick-line" />
                    <span className="tick-label">{i}s</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Video tracks */}
          {videoTracks.length > 0 && (
            <div className="track-group">
              <div className="track-group-label">Video</div>
              {videoTracks.map((t) => <Track key={t.track_id} track={t} />)}
            </div>
          )}

          {/* Subtitle tracks */}
          {subtitleTracks.length > 0 && (
            <div className="track-group">
              <div className="track-group-label">Subs</div>
              {subtitleTracks.map((t) => <Track key={t.track_id} track={t} />)}
            </div>
          )}

          {/* Audio tracks */}
          {audioTracks.length > 0 && (
            <div className="track-group">
              <div className="track-group-label">Audio</div>
              {audioTracks.map((t) => <Track key={t.track_id} track={t} />)}
            </div>
          )}

          {/* Playhead */}
          <div className="playhead" style={{ left: playheadX }} />
        </div>

        {/* Inspector side panel */}
        <Inspector />
      </div>
    </div>
  );
};
