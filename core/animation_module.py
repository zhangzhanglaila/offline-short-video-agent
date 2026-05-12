# -*- coding: utf-8 -*-
"""
动画生成模块 - 基于FFmpeg动态效果
支持：Ken Burns缩放、文字逐字出现、转场动画、关键帧动画、技术讲座风格多图层合成
"""
import subprocess
import random
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from config import OUTPUT_WIDTH, OUTPUT_HEIGHT, OUTPUT_FPS, OUTPUT_CRF
from core.utils.ffmpeg_runner import run_ffmpeg_safe


class AnimationModule:
    """动画生成模块 - FFmpeg动态效果"""

    # 转场效果列表
    TRANSITIONS = ["fade", "dissolve", "wipe", "blur", "none"]

    def __init__(self):
        """初始化动画模块"""
        self.output_width = OUTPUT_WIDTH
        self.output_height = OUTPUT_HEIGHT
        self.output_fps = OUTPUT_FPS
        self.output_crf = OUTPUT_CRF

    def create_ken_burns_clip(self, image_path: str, output_path: str,
                               duration: float = 3.0,
                               zoom_in: bool = True,
                               zoom_range: Tuple[float, float] = (1.0, 1.15),
                               pan_x: float = 0.0,
                               pan_y: float = 0.0) -> bool:
        """
        创建Ken Burns效果（缩放+平移）— 全帧contain模式，模糊背景补全。

        参数:
            image_path: 输入图片路径
            output_path: 输出视频路径
            duration: 持续时间（秒）
            zoom_in: True=放大，False=缩小
            zoom_range: 缩放范围 (起始, 结束)
            pan_x: 水平平移量（-1到1）
            pan_y: 垂直平移量（-1到1）

        返回:
            是否成功
        """
        if not Path(image_path).exists():
            print(f"[错误] 图片不存在: {image_path}")
            return False

        zoom_start, zoom_end = zoom_range
        if not zoom_in:
            zoom_start, zoom_end = zoom_end, zoom_start

        W, H = self.output_width, self.output_height
        total_frames = int(duration * self.output_fps)
        zoom_delta = (zoom_end - zoom_start) / total_frames

        # 全帧contain: 模糊背景 + 居中缩放
        filter_complex = (
            f"[0:v]split=2[fg][bg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},boxblur=15:8[bgblur];"
            f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"zoompan=z='min(zoom+{zoom_delta:.6f},{zoom_end})':"
            f"x='iw/2-(iw/zoom/2)+{int(pan_x*40)}':"
            f"y='ih/2-(ih/zoom/2)+{int(pan_y*40)}':"
            f"d={total_frames}:s={W}x{H}:fps={self.output_fps}[fgzoom];"
            f"[bgblur][fgzoom]overlay=(W-w)/2:(H-h)/2"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-framerate", str(self.output_fps),
            "-i", image_path,
            "-filter_complex", filter_complex,
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(self.output_crf),
            "-t", str(duration),
            output_path
        ]

        return self._run_ffmpeg(cmd)

    def create_pan_zoom_clip(self, image_path: str, output_path: str,
                              duration: float = 3.0,
                              effect: str = "zoom_in",
                              placement: str = "right") -> bool:
        """
        创建推拉缩放效果 — 全帧contain模式，模糊背景补全。

        参数:
            image_path: 输入图片路径
            output_path: 输出视频路径
            duration: 持续时间（秒）
            effect: 效果类型 (zoom_in/zoom_out/static)

        返回:
            是否成功
        """
        if not Path(image_path).exists():
            return False

        W, H = self.output_width, self.output_height
        total_frames = int(duration * self.output_fps)

        zoom_effects = {
            "zoom_in": ("1.0", "1.3"),
            "zoom_out": ("1.3", "1.0"),
            "static": ("1.0", "1.0"),
        }
        zoom_start, zoom_end = zoom_effects.get(effect, ("1.0", "1.0"))
        zoom_delta = (float(zoom_end) - float(zoom_start)) / total_frames

        # 全帧contain: 模糊背景 + 居中缩放前景
        filter_complex = (
            f"[0:v]split=2[fg][bg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},boxblur=15:8[bgblur];"
            f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"zoompan=z='min(zoom+{zoom_delta:.6f},{zoom_end})':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={W}x{H}:fps={self.output_fps}[fgzoom];"
            f"[bgblur][fgzoom]overlay=(W-w)/2:(H-h)/2"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-framerate", str(self.output_fps),
            "-i", image_path,
            "-filter_complex", filter_complex,
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(self.output_crf),
            output_path
        ]

        return self._run_ffmpeg(cmd)

    def _create_contain_clip(self, image_path: str, output_path: str, duration: float) -> bool:
        """完整显示素材 + 模糊背景补全（稳定版）。"""
        if not Path(image_path).exists():
            return False
        filter_complex = (
            f"[0:v]split=2[fgsrc][bgsrc];"
            f"[bgsrc]scale={self.output_width}:{self.output_height}:force_original_aspect_ratio=increase,"
            f"crop={self.output_width}:{self.output_height},boxblur=20:10[bg];"
            f"[fgsrc]scale={self.output_width}:{self.output_height}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-framerate", str(self.output_fps),
            "-i", image_path,
            "-t", str(duration),
            "-filter_complex", filter_complex,
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(self.output_crf),
            output_path,
        ]
        return self._run_ffmpeg(cmd)

    def create_manga_frame_clip(self, image_path: str, output_path: str,
                                 duration: float = 3.0) -> bool:
        """漫画帧直转视频 — 帧已是1080×1920全尺寸，无需裁剪/缩放。"""
        if not Path(image_path).exists():
            return False
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-framerate", str(self.output_fps),
            "-i", image_path,
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(self.output_crf),
            "-pix_fmt", "yuv420p",
            output_path
        ]
        return self._run_ffmpeg(cmd)
    def _run_ffmpeg(self, cmd: List[str]) -> bool:
        return run_ffmpeg_safe(cmd)


# ==================== 便捷函数 ====================
_anim_instance = None


def get_animation_module() -> AnimationModule:
    global _anim_instance
    if _anim_instance is None:
        _anim_instance = AnimationModule()
    return _anim_instance
