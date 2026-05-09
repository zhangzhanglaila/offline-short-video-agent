"""FFmpeg Executor — Thin subprocess wrapper for ffmpeg/ffprobe.

Domain-agnostic command execution with timeout and error handling.
All ffmpeg calls go through this single point for:
  - Consistent error reporting
  - Timeout enforcement
  - Future: dry-run mode, command logging, parallel limiting
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FFmpegResult:
    """Result of an ffmpeg command execution."""
    success: bool
    returncode: int
    stdout: str
    stderr: str
    command: list[str]

    @property
    def error(self) -> Optional[str]:
        return self.stderr if not self.success else None


def run_ffmpeg(
    args: list[str],
    timeout: int = 300,
    check: bool = False,
) -> FFmpegResult:
    """Execute an ffmpeg command.

    Args:
        args: Arguments after 'ffmpeg' (e.g. ['-i', 'in.mp4', ...]).
        timeout: Max seconds to wait. Default 5 minutes.
        check: If True, raise on non-zero exit.

    Returns:
        FFmpegResult with stdout/stderr/returncode.
    """
    cmd = ["ffmpeg", "-y", *args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return FFmpegResult(
            success=result.returncode == 0,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            command=cmd,
        )
    except subprocess.TimeoutExpired:
        return FFmpegResult(
            success=False,
            returncode=-1,
            stdout="",
            stderr=f"ffmpeg timed out after {timeout}s",
            command=cmd,
        )
    except FileNotFoundError:
        return FFmpegResult(
            success=False,
            returncode=-1,
            stdout="",
            stderr="ffmpeg not found in PATH",
            command=cmd,
        )


def run_ffprobe(args: list[str], timeout: int = 30) -> FFmpegResult:
    """Execute an ffprobe command."""
    cmd = ["ffprobe", *args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return FFmpegResult(
            success=result.returncode == 0,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            command=cmd,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return FFmpegResult(
            success=False,
            returncode=-1,
            stdout="",
            stderr=str(e),
            command=cmd,
        )


def get_video_duration(path: Path, timeout: int = 10) -> float:
    """Get video duration in seconds via ffprobe."""
    result = run_ffprobe([
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ], timeout=timeout)
    if result.success:
        try:
            return float(result.stdout.strip())
        except ValueError:
            pass
    return 0.0
