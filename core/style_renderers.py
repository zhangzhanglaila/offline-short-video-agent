# -*- coding: utf-8 -*-
"""
风格渲染器系统 - 统一入口
提供便捷的渲染器获取和使用接口
"""
from pathlib import Path
from typing import List, Dict, Optional

from core.style_renderer import StyleRenderer, get_renderer, register_renderer
from core.renderers.manga_renderer import MangaStyleRenderer
from core.renderers.minimal_renderer import MinimalStyleRenderer
from core.renderers.vibrant_renderer import VibrantStyleRenderer
from core.renderers.cinematic_renderer import CinematicStyleRenderer
from core.renderers.tech_renderer import TechStyleRenderer


# 确保所有渲染器已注册
_ALL_RENDERERS = {
    "minimal": MinimalStyleRenderer,
    "vibrant": VibrantStyleRenderer,
    "cinematic": CinematicStyleRenderer,
    "tech": TechStyleRenderer,
    "manga": MangaStyleRenderer,
}


def get_available_styles() -> List[str]:
    """获取所有可用的风格ID列表"""
    return list(_ALL_RENDERERS.keys())


def create_renderer(style_id: str, width: int = 1080, height: int = 1920) -> Optional[StyleRenderer]:
    """创建风格渲染器

    Args:
        style_id: 风格ID (minimal/vibrant/cinematic/tech/manga)
        width: 输出宽度
        height: 输出高度

    Returns:
        渲染器实例，失败返回 None
    """
    return get_renderer(style_id, width=width, height=height)


def render_frame(
    style_id: str,
    title: str,
    bullets: List[str],
    output_path: str,
    width: int = 1080,
    height: int = 1920,
    **kwargs
) -> Optional[str]:
    """便捷函数：渲染单帧

    Args:
        style_id: 风格ID
        title: 标题
        bullets: 要点列表
        output_path: 输出路径
        width: 宽度
        height: 高度
        **kwargs: 其他参数传递给 render_frame

    Returns:
        输出文件路径，失败返回 None
    """
    renderer = create_renderer(style_id, width, height)
    if not renderer:
        return None

    try:
        return renderer.render_frame(
            title=title,
            bullets=bullets,
            output_path=output_path,
            **kwargs
        )
    except Exception as e:
        print(f"[render_frame] Failed: {e}")
        return None


def render_storyboard(
    style_id: str,
    storyboard: List[dict],
    script_content: str,
    work_dir: str,
    width: int = 1080,
    height: int = 1920,
    materials: dict = None
) -> List[str]:
    """便捷函数：批量渲染分镜

    Args:
        style_id: 风格ID
        storyboard: 分镜列表
        script_content: 脚本内容
        work_dir: 输出目录
        width: 宽度
        height: 高度
        materials: 素材映射

    Returns:
        生成的文件路径列表
    """
    renderer = create_renderer(style_id, width, height)
    if not renderer:
        return []

    try:
        return renderer.render_storyboard(
            storyboard=storyboard,
            script_content=script_content,
            work_dir=work_dir,
            materials=materials or {}
        )
    except Exception as e:
        print(f"[render_storyboard] Failed: {e}")
        return []


# 兼容层：与现有 manga_frame_renderer 模块兼容
class MangaFrameRenderer:
    """兼容层：将调用转发到新的风格渲染器"""

    def __init__(self, width: int = 1080, height: int = 1920,
                 visual_style: str = "manga"):
        self.width = width
        self.height = height
        self.visual_style = visual_style
        # 创建实际渲染器
        self._renderer = create_renderer(visual_style, width, height)

    def render_frame(self, *args, **kwargs):
        """转发到实际渲染器"""
        if not self._renderer:
            raise RuntimeError(f"Failed to create renderer for style: {self.visual_style}")
        return self._renderer.render_frame(*args, **kwargs)

    def render_storyboard(self, *args, **kwargs):
        """转发到实际渲染器"""
        if not self._renderer:
            raise RuntimeError(f"Failed to create renderer for style: {self.visual_style}")
        return self._renderer.render_storyboard(*args, **kwargs)


__all__ = [
    "get_available_styles",
    "create_renderer",
    "render_frame",
    "render_storyboard",
    "MangaFrameRenderer",  # 兼容导出
]
