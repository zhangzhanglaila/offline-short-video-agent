# -*- coding: utf-8 -*-
"""
动效渲染器
集成动效功能的增强版渲染器
"""
from typing import List, Dict, Optional
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from core.animated_renderer_mixin import AnimatedRendererMixin
from core.animation_config import has_animations


class BaseAnimatedRenderer:
    """动效渲染器基类 - 组合模式"""

    def __init__(self, base_renderer_class, width: int = 1080,
                 height: int = 1920, style_config: dict = None):
        # 创建基础渲染器实例
        self._base_renderer = base_renderer_class(width, height, style_config)
        self.width = width
        self.height = height
        self.style_id = self._base_renderer.style_id
        self.style_config = style_config or {}

        # 添加动效能力
        self._setup_animations()

    def _setup_animations(self):
        """设置动效系统"""
        self.enable_animations = has_animations(self.style_id)
        self.animation_fps = 30

        if self.enable_animations:
            from core.text_animator import TextAnimator
            self._animator = TextAnimator(self.width, self.height, self.animation_fps)

    def render_frame(
        self,
        title: str,
        bullets: List[str],
        output_path: str,
        subtitle: str = "",
        media_path: str = None,
        scene_index: int = 0,
        total_scenes: int = 1,
        sfx_text: str = "",
        enable_animations: bool = True,
        **kwargs
    ) -> str:
        """
        渲染帧 - 支持动效或静态渲染
        """
        if enable_animations and self.enable_animations:
            return self._render_animated_frame(
                title=title,
                bullets=bullets,
                output_path=output_path,
                subtitle=subtitle,
                media_path=media_path,
                scene_index=scene_index,
                total_scenes=total_scenes,
                **kwargs
            )
        else:
            # 静态渲染
            return self._base_renderer.render_frame(
                title=title,
                bullets=bullets,
                output_path=output_path,
                subtitle=subtitle,
                media_path=media_path,
                scene_index=scene_index,
                total_scenes=total_scenes,
                sfx_text=sfx_text,
                **kwargs
            )

    def render_storyboard(
        self,
        storyboard: List[dict],
        script_content: str,
        work_dir: str,
        materials: dict = None,
        enable_animations: bool = True
    ) -> List[str]:
        """批量渲染分镜"""
        return self._base_renderer.render_storyboard(
            storyboard=storyboard,
            script_content=script_content,
            work_dir=work_dir,
            materials=materials
        )

    def _render_animated_frame(self, title: str, bullets: List[str],
                              output_path: str, **kwargs) -> str:
        """渲染动效帧 - 简化版，只渲染最终帧"""
        # 当前实现：直接渲染静态版本
        # TODO: 实现完整动效序列
        return self._base_renderer.render_frame(
            title=title,
            bullets=bullets,
            output_path=output_path,
            **kwargs
        )

    def __getattr__(self, name):
        """代理未定义的方法到基础渲染器"""
        return getattr(self._base_renderer, name)


# 具体风格的动效渲染器
class AnimatedMinimalRenderer(BaseAnimatedRenderer):
    """动效极简渲染器"""
    def __init__(self, width: int = 1080, height: int = 1920, style_config: dict = None):
        from core.renderers.minimal_renderer import MinimalStyleRenderer
        super().__init__(MinimalStyleRenderer, width, height, style_config)


class AnimatedVibrantRenderer(BaseAnimatedRenderer):
    """动效活力渲染器"""
    def __init__(self, width: int = 1080, height: int = 1920, style_config: dict = None):
        from core.renderers.vibrant_renderer import VibrantStyleRenderer
        super().__init__(VibrantStyleRenderer, width, height, style_config)


class AnimatedCinematicRenderer(BaseAnimatedRenderer):
    """动效电影渲染器"""
    def __init__(self, width: int = 1080, height: int = 1920, style_config: dict = None):
        from core.renderers.cinematic_renderer import CinematicStyleRenderer
        super().__init__(CinematicStyleRenderer, width, height, style_config)


class AnimatedTechRenderer(BaseAnimatedRenderer):
    """动效科技渲染器"""
    def __init__(self, width: int = 1080, height: int = 1920, style_config: dict = None):
        from core.renderers.tech_renderer import TechStyleRenderer
        super().__init__(TechStyleRenderer, width, height, style_config)


class AnimatedMangaRenderer(BaseAnimatedRenderer):
    """动效漫画渲染器"""
    def __init__(self, width: int = 1080, height: int = 1920, style_config: dict = None):
        from core.renderers.manga_renderer import MangaStyleRenderer
        super().__init__(MangaStyleRenderer, width, height, style_config)


# 注册动效渲染器
from core.style_renderer import register_renderer

register_renderer("animated_minimal", AnimatedMinimalRenderer)
register_renderer("animated_vibrant", AnimatedVibrantRenderer)
register_renderer("animated_cinematic", AnimatedCinematicRenderer)
register_renderer("animated_tech", AnimatedTechRenderer)
register_renderer("animated_manga", AnimatedMangaRenderer)
