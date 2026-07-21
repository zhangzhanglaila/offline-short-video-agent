# -*- coding: utf-8 -*-
"""
文字动效引擎
提供文字进场、强调、退场动画效果
"""
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import math


class AnimationType(Enum):
    """动效类型"""
    FADE = "fade"           # 淡入淡出
    SLIDE = "slide"         # 滑动
    ZOOM = "zoom"           # 缩放
    TYPEWRITER = "typewriter"  # 打字机
    BLINK = "blink"         # 闪烁


class EasingType(Enum):
    """缓动函数类型"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"


@dataclass
class AnimationConfig:
    """动效配置"""
    type: AnimationType
    duration: float = 0.5      # 持续时间(秒)
    delay: float = 0.0         # 延迟(秒)
    direction: str = "left"   # 方向 (for slide: left/right/top/bottom)
    easing: EasingType = EasingType.EASE_OUT
    repeat: int = 1            # 重复次数 (for blink)


class TextAnimator:
    """文字动效器"""

    def __init__(self, width: int = 1080, height: int = 1920, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps

    def animate(
        self,
        text: str,
        config: AnimationConfig,
        draw_callback: Callable,
        frame_range: Tuple[int, int] = (0, -1)
    ) -> List[Tuple[int, any]]:
        """
        应用动效生成多帧

        Args:
            text: 要动画的文字
            config: 动效配置
            draw_callback: 绘制回调函数 (draw, text, x, y, alpha, **kwargs) -> None
            frame_range: 帧范围 (start, end), -1表示自动计算

        Returns:
            [(frame_index, image), ...] 帧序列
        """
        total_frames = int(config.duration * self.fps)
        delay_frames = int(config.delay * self.fps)
        start, end = frame_range

        if end == -1:
            end = total_frames + delay_frames

        frames = []

        for frame_idx in range(start, end):
            # 计算进度 0.0 - 1.0
            if frame_idx < delay_frames:
                progress = 0.0
            elif frame_idx < delay_frames + total_frames:
                progress = (frame_idx - delay_frames) / total_frames
            else:
                progress = 1.0

            # 应用缓动
            eased = self._apply_easing(progress, config.easing)

            # 应用动效
            params = self._apply_animation(config, eased, frame_idx)
            frames.append((frame_idx, params))

        return frames

    def _apply_easing(self, t: float, easing: EasingType) -> float:
        """应用缓动函数"""
        t = max(0.0, min(1.0, t))

        if easing == EasingType.LINEAR:
            return t
        elif easing == EasingType.EASE_IN:
            return t * t
        elif easing == EasingType.EASE_OUT:
            return 1.0 - (1.0 - t) * (1.0 - t)
        elif easing == EasingType.EASE_IN_OUT:
            return t * t * (3.0 - 2.0 * t)
        else:
            return t

    def _apply_animation(self, config: AnimationConfig, progress: float,
                        frame_idx: int) -> Dict:
        """应用具体动效"""
        params = {"progress": progress, "frame": frame_idx}

        if config.type == AnimationType.FADE:
            params["alpha"] = int(255 * progress)
            params["visible"] = progress > 0

        elif config.type == AnimationType.SLIDE:
            offset = int(self.width * (1.0 - progress))
            if config.direction == "left":
                params["offset_x"] = -offset
                params["offset_y"] = 0
            elif config.direction == "right":
                params["offset_x"] = offset
                params["offset_y"] = 0
            elif config.direction == "top":
                params["offset_x"] = 0
                params["offset_y"] = -offset
            elif config.direction == "bottom":
                params["offset_x"] = 0
                params["offset_y"] = offset
            else:
                params["offset_x"] = -offset
                params["offset_y"] = 0

        elif config.type == AnimationType.ZOOM:
            scale = 0.5 + 0.5 * progress
            params["scale"] = scale
            params["alpha"] = int(255 * progress)

        elif config.type == AnimationType.TYPEWRITER:
            chars_visible = int(progress * len(params.get("text", "")))
            params["chars_visible"] = chars_visible
            params["alpha"] = 255

        elif config.type == AnimationType.BLINK:
            # 闪烁效果
            cycle = (progress * config.repeat * 2) % 2
            params["alpha"] = 255 if cycle < 1 else 50
            params["visible"] = True

        else:
            params["alpha"] = 255
            params["visible"] = True

        return params


class AnimationComposer:
    """动效组合器 - 组合多个动效"""

    def __init__(self, fps: int = 30):
        self.fps = fps
        self.animations: List[Dict] = []

    def add(self, text: str, config: AnimationConfig,
            draw_callback: Callable, start_frame: int = 0):
        """添加动效"""
        self.animations.append({
            "text": text,
            "config": config,
            "callback": draw_callback,
            "start": start_frame
        })

    def render(self, width: int, height: int) -> List[Tuple[int, any]]:
        """渲染所有动效帧序列"""
        if not self.animations:
            return []

        total_frames = 0
        for anim in self.animations:
            duration = int(anim["config"].duration * self.fps)
            delay = int(anim["config"].delay * self.fps)
            end = anim["start"] + delay + duration
            total_frames = max(total_frames, end)

        frames = []
        for frame_idx in range(total_frames):
            frame_params = []
            for anim in self.animations:
                animator = TextAnimator(width, height, self.fps)
                anim_frames = animator.animate(
                    anim["text"],
                    anim["config"],
                    anim["callback"],
                    (anim["start"], -1)
                )
                for idx, params in anim_frames:
                    if idx == frame_idx:
                        frame_params.append({
                            "text": anim["text"],
                            "callback": anim["callback"],
                            "params": params
                        })
                        break

            if frame_params:
                frames.append((frame_idx, frame_params))

        return frames


# ═══════════════════════════════════════════════════════════════
# 预设动效配置
# ═══════════════════════════════════════════════════════════════

class PresetAnimations:
    """预设动效配置"""

    @staticmethod
    def fade_in(duration: float = 0.5) -> AnimationConfig:
        """淡入"""
        return AnimationConfig(type=AnimationType.FADE, duration=duration)

    @staticmethod
    def fade_out(duration: float = 0.5) -> AnimationConfig:
        """淡出"""
        return AnimationConfig(type=AnimationType.FADE, duration=duration)

    @staticmethod
    def slide_from_left(duration: float = 0.6) -> AnimationConfig:
        """从左滑入"""
        return AnimationConfig(
            type=AnimationType.SLIDE,
            duration=duration,
            direction="left"
        )

    @staticmethod
    def slide_from_right(duration: float = 0.6) -> AnimationConfig:
        """从右滑入"""
        return AnimationConfig(
            type=AnimationType.SLIDE,
            duration=duration,
            direction="right"
        )

    @staticmethod
    def zoom_in(duration: float = 0.5) -> AnimationConfig:
        """缩放进入"""
        return AnimationConfig(
            type=AnimationType.ZOOM,
            duration=duration
        )

    @staticmethod
    def typewriter(duration: float = 1.0) -> AnimationConfig:
        """打字机效果"""
        return AnimationConfig(
            type=AnimationType.TYPEWRITER,
            duration=duration
        )

    @staticmethod
    def blink(duration: float = 0.5, repeat: int = 3) -> AnimationConfig:
        """闪烁强调"""
        return AnimationConfig(
            type=AnimationType.BLINK,
            duration=duration,
            repeat=repeat
        )


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

def create_animator(width: int = 1080, height: int = 1920,
                    fps: int = 30) -> TextAnimator:
    """创建动效器"""
    return TextAnimator(width, height, fps)


def compose_animations(fps: int = 30) -> AnimationComposer:
    """创建动效组合器"""
    return AnimationComposer(fps)
