import React from 'react';
import { useTimelineStore } from '../store/timelineStore';
import type { TrackData } from '../store/timelineStore';
import { SceneClip } from './SceneClip';
import { SubtitleLayer } from './SubtitleLayer';

/** A single track row in the timeline. */
export const Track: React.FC<{ track: TrackData }> = ({ track }) => {
  const { totalWidthPx } = useTimelineStore();
  const totalPx = totalWidthPx();

  const typeLabel = {
    video: 'V',
    subtitle: 'S',
    audio: 'A',
  }[track.track_type] || '?';

  return (
    <div className="track" style={{ width: totalPx }}>
      <div className="track__label">
        <span className={`track__type track__type--${track.track_type}`}>
          {typeLabel}
        </span>
        <span className="track__id">{track.scene_id}</span>
      </div>
      <div className="track__content">
        {track.track_type === 'video' && (
          <SceneClip
            clip={{
              scene_id: track.scene_id,
              scene_type: (track.content.scene_type as string) || '',
              text: (track.content.text as string) || '',
              start_frame: track.start_frame,
              end_frame: track.end_frame,
              layer: track.layer,
            }}
          />
        )}
        {track.track_type === 'subtitle' && <SubtitleLayer track={track} />}
        {track.track_type === 'audio' && (
          <div
            className="audio-clip"
            style={{
              left: track.start_frame / useTimelineStore.getState().framePerPixel,
              width: (track.end_frame - track.start_frame) / useTimelineStore.getState().framePerPixel,
            }}
          />
        )}
      </div>
    </div>
  );
};
