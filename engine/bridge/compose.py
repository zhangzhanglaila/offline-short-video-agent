"""Compose — ffmpeg-based scene concatenation with crossfade transitions.

Takes individually rendered scene mp4 files and concatenates them into
a final video, applying xfade transitions at scene boundaries.

Usage:
    from engine.bridge.compose import compose_scenes
    final = compose_scenes(
        scene_videos=[Path("scene_0.mp4"), Path("scene_1.mp4"), Path("scene_2.mp4")],
        overlaps=[8, 8],  # xfade frames between scene 0↔1 and 1↔2
        output_path=Path("final.mp4"),
        fps=30,
    )
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional


def _get_video_duration(path: Path, fps: int = 30) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True, text=True, check=True,
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        # Fallback: estimate from file (assume 1 frame per 1/fps)
        return 0.0


def _compute_xfade_offsets(
    scene_durations: list[float],
    overlaps: list[int],
    fps: int,
) -> list[float]:
    """Compute the offset (in seconds) for each xfade transition.

    The offset is the timestamp in the accumulated output where
    the transition begins. Each successive offset must account for
    the duration consumed by previous xfade overlaps.

    Args:
        scene_durations: Duration in seconds of each scene video.
        overlaps: overlap[i] = xfade frame count between scene[i] and scene[i+1].
        fps: Frames per second.

    Returns:
        List of offsets in seconds, one per xfade transition.
    """
    offsets = []
    accumulated = 0.0

    for i in range(len(overlaps)):
        # The transition starts at: accumulated + scene_duration - overlap_duration
        overlap_sec = overlaps[i] / fps
        offset = accumulated + scene_durations[i] - overlap_sec
        offsets.append(max(0, offset))
        # After this xfade, the accumulated time advances by scene duration minus overlap
        accumulated += scene_durations[i] - overlap_sec

    return offsets


def compose_scenes(
    scene_videos: list[Path],
    overlaps: list[int],
    output_path: Path,
    fps: int = 30,
    transition: str = "fade",
) -> Path:
    """Concatenate scene videos with xfade transitions.

    Uses ffmpeg's xfade filter for video and acrossfade for audio.
    Each scene video must have both video and audio streams.

    Args:
        scene_videos: Ordered list of scene mp4 paths.
        overlaps: overlap[i] = xfade frames between scene[i] and scene[i+1].
            len(overlaps) must be len(scene_videos) - 1.
        output_path: Path for the final output mp4.
        fps: Frames per second (for computing xfade durations).
        transition: xfade transition type ("fade", "wipeleft", etc.).

    Returns:
        Path to the output mp4.
    """
    if not scene_videos:
        raise ValueError("No scene videos provided")

    # Single scene: just copy
    if len(scene_videos) == 1:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(scene_videos[0], output_path)
        return output_path

    # Validate overlaps
    if len(overlaps) != len(scene_videos) - 1:
        raise ValueError(
            f"Expected {len(scene_videos) - 1} overlaps, got {len(overlaps)}"
        )

    # Get scene durations
    scene_durations = [_get_video_duration(v, fps) for v in scene_videos]
    if any(d <= 0 for d in scene_durations):
        # Fallback: use ffprobe with more verbose output
        raise RuntimeError("Could not determine duration of one or more scene videos")

    # Compute xfade offsets
    offsets = _compute_xfade_offsets(scene_durations, overlaps, fps)

    # Build ffmpeg filter graph
    inputs = []
    for v in scene_videos:
        inputs.extend(["-i", str(v)])

    filter_parts = []
    audio_parts = []
    prev_video_label = "[0:v]"
    prev_audio_label = "[0:a]"

    for i in range(1, len(scene_videos)):
        overlap_sec = overlaps[i - 1] / fps
        offset = offsets[i - 1]

        is_last = i == len(scene_videos) - 1
        video_label = "[vout]" if is_last else f"[v{i}]"
        audio_label = "[aout]" if is_last else f"[a{i}]"

        # Video xfade
        filter_parts.append(
            f"{prev_video_label}[{i}:v]xfade=transition={transition}:"
            f"duration={overlap_sec:.3f}:offset={offset:.3f}{video_label}"
        )

        # Audio crossfade
        audio_parts.append(
            f"{prev_audio_label}[{i}:a]acrossfade=d={overlap_sec:.3f}{audio_label}"
        )

        prev_video_label = video_label
        prev_audio_label = audio_label

    filter_graph = ";".join(filter_parts + audio_parts)

    # Build ffmpeg command
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_graph,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg compose failed:\n{result.stderr[-500:]}"
        )

    return output_path


def compose_scenes_simple(
    scene_videos: list[Path],
    output_path: Path,
) -> Path:
    """Concatenate scene videos without transitions (simple concat).

    Uses ffmpeg's concat demuxer for lossless concatenation.
    Faster than xfade but no transitions between scenes.

    Args:
        scene_videos: Ordered list of scene mp4 paths.
        output_path: Path for the final output mp4.

    Returns:
        Path to the output mp4.
    """
    if not scene_videos:
        raise ValueError("No scene videos provided")

    if len(scene_videos) == 1:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(scene_videos[0], output_path)
        return output_path

    # Write concat file
    concat_file = output_path.parent / "concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in scene_videos:
            f.write(f"file '{v.resolve()}'\n")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg concat failed:\n{result.stderr[-500:]}"
        )

    # Clean up concat file
    concat_file.unlink(missing_ok=True)

    return output_path
