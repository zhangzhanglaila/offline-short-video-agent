# -*- coding: utf-8 -*-
"""
动效渲染器混入类
为风格渲染器添加动效支持
"""
from typing import List, Dict, Optional, Tuple, Callable
from pathlib import Path
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from core.text_animator import (
    TextAnimator, AnimationComposer,
    AnimationConfig, AnimationType, EasingType,
    PresetAnimations
)
from core.animation_config import get_animation_config, has_animations


class AnimatedRendererMixin:
    """动效渲染器混入类 - 为渲染器添加动效能力"""

    def __init__(self):
        # 动效配置
        self.enable_animations = True
        self.animation_fps = 30
        self._animator = None
        self._animation_frames = []

    def setup_animations(self, style_id: str = None):
        """初始化动效系统"""
        self.style_id = style_id or getattr(self, 'style_id', 'minimal')

        if not has_animations(self.style_id):
            self.enable_animations = False
            return

        self._animator = TextAnimator(
            self.width, self.height, self.animation_fps
        )
        self.enable_animations = True

    def render_animated_frame(
        self,
        title: str,
        bullets: List[str],
        output_path: str,
        subtitle: str = "",
        scene_index: int = 0,
        total_scenes: int = 1,
        save_frames: bool = False,
        **kwargs
    ) -> str:
        """
        渲染带动效的帧序列

        Args:
            title: 标题
            bullets: 要点列表
            output_path: 输出路径
            subtitle: 副标题
            scene_index: 场景索引
            total_scenes: 总场景数
            save_frames: 是否保存中间帧

        Returns:
            最终帧路径 或 帧序列目录
        """
        if not HAS_PIL:
            raise RuntimeError("PIL is required for animated rendering")

        if not self.enable_animations or not self._animator:
            # 降级为普通渲染
            return self.render_frame(
                title=title,
                bullets=bullets,
                output_path=output_path,
                subtitle=subtitle,
                scene_index=scene_index,
                total_scenes=total_scenes,
                **kwargs
            )

        # 创建动效组合器
        composer = AnimationComposer(self.animation_fps)

        # 添加标题动效
        title_config = self._get_animation_config("title")
        if title_config:
            config = self._parse_animation_config(title_config)
            composer.add(
                title,
                config,
                lambda d, t, x, y, a, **kw: self._draw_animated_title(
                    d, t, x, y, a, **kw
                ),
                start_frame=0
            )

        # 添加副标题动效
        subtitle_config = self._get_animation_config("subtitle")
        if subtitle_config and subtitle:
            config = self._parse_animation_config(subtitle_config)
            composer.add(
                subtitle,
                config,
                lambda d, t, x, y, a, **kw: self._draw_animated_subtitle(
                    d, t, x, y, a, **kw
                ),
                start_frame=0
            )

        # 添加要点动效
        bullets_config = self._get_animation_config("bullets")
        if bullets_config and bullets:
            stagger = bullets_config.get("stagger", 0.15)
            for i, bullet in enumerate(bullets):
                config = self._parse_animation_config(bullets_config)
                config.delay += i * stagger  # 错开时间
                composer.add(
                    bullet,
                    config,
                    lambda d, t, x, y, a, **kw: self._draw_animated_bullet(
                        d, t, x, y, a, **kw
                    ),
                    start_frame=0
                )

        # 渲染所有帧
        frames = composer.render(self.width, self.height)

        if not frames:
            # 降级
            return self.render_frame(
                title=title,
                bullets=bullets,
                output_path=output_path,
                subtitle=subtitle,
                scene_index=scene_index,
                total_scenes=total_scenes,
                **kwargs
            )

        # 保存帧
        output_dir = Path(output_path).parent
        if save_frames:
            frames_dir = output_dir / f"frames_{Path(output_path).stem}"
            frames_dir.mkdir(parents=True, exist_ok=True)

        last_frame = None
        for frame_idx, frame_params in frames:
            img = self._render_animated_frame(
                frame_params, title, bullets, subtitle,
                scene_index, total_scenes
            )

            if save_frames:
                frame_path = frames_dir / f"frame_{frame_idx:04d}.png"
                img.save(frame_path, quality=95)

            last_frame = img

        # 保存最终帧
        if last_frame:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            last_frame.save(output_path, quality=95)
            return output_path

        return output_path

    def _get_animation_config(self, element: str) -> Dict:
        """获取元素动效配置"""
        return get_animation_config(self.style_id, element)

    def _parse_animation_config(self, config: Dict) -> AnimationConfig:
        """解析动效配置"""
        anim_type = AnimationType[config.get("type", "fade").upper()]
        duration = config.get("duration", 0.5)
        delay = config.get("delay", 0.0)
        easing = EasingType[config.get("easing", "ease_out").upper()]
        direction = config.get("direction", "left")
        repeat = config.get("repeat", 1)

        return AnimationConfig(
            type=anim_type,
            duration=duration,
            delay=delay,
            direction=direction,
            easing=easing,
            repeat=repeat
        )

    def _render_animated_frame(
        self,
        frame_params: List[Dict],
        title: str,
        bullets: List[str],
        subtitle: str,
        scene_index: int,
        total_scenes: int
    ) -> Image.Image:
        """渲染单个动效帧"""
        # 创建画布
        bg_color = getattr(self, 'bg_color', '#FFFFFF')
        img = Image.new("RGB", (self.width, self.height), bg_color)
        draw = ImageDraw.Draw(img)

        # 按层级渲染
        y = self.padding

        # 标题
        for param in frame_params:
            if param["text"] == title:
                params = param["params"]
                alpha = params.get("alpha", 255)
                offset_x = params.get("offset_x", 0)
                offset_y = params.get("offset_y", 0)
                scale = params.get("scale", 1.0)

                self._draw_animated_title(
                    draw, title, self.padding + offset_x,
                    y + offset_y, alpha, scale=scale
                )

        # 副标题
        if subtitle:
            for param in frame_params:
                if param["text"] == subtitle:
                    params = param["params"]
                    self._draw_animated_subtitle(
                        draw, subtitle, self.padding,
                        y + 60, params.get("alpha", 255)
                    )

        # 底部
        self._draw_footer(draw, scene_index, total_scenes,
                         self.height - self.padding)

        return img

    def _draw_animated_title(self, draw, text: str, x: int, y: int,
                            alpha: int, scale: float = 1.0):
        """绘制动效标题"""
        if alpha <= 0:
            return

        title_font = self._get_font("title", self.title_size)

        # 缩放
        if scale != 1.0:
            size = int(self.title_size * scale)
            title_font = self._get_font("title", size)

        # 应用透明度
        color = self._apply_alpha(self.primary_color, alpha)
        draw.text((x, y), text, fill=color, font=title_font)

    def _draw_animated_subtitle(self, draw, text: str, x: int, y: int,
                               alpha: int):
        """绘制动效副标题"""
        if alpha <= 0:
            return

        body_font = self._get_font("body", int(self.body_size * 0.9))
        color = self._apply_alpha(self.colors.get("secondary", "#666"), alpha)
        draw.text((x, y), text, fill=color, font=body_font)

    def _draw_animated_bullet(self, draw, text: str, x: int, y: int,
                             alpha: int):
        """绘制动效要点"""
        if alpha <= 0:
            return

        body_font = self._get_font("body", self.body_size)
        color = self._apply_alpha(self.primary_color, alpha)
        draw.text((x, y), text, fill=color, font=body_font)

    def _apply_alpha(self, color: str, alpha: int) -> Tuple:
        """应用透明度到颜色"""
        if isinstance(color, str):
            # Hex color
            h = color.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            return (*rgb, alpha)
        return color
