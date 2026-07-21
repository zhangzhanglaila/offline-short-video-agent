# -*- coding: utf-8 -*-
"""
Manga 风格渲染器
将现有的 MangaFrameRenderer 包装为 StyleRenderer 接口
"""
from typing import List, Dict, Optional
from pathlib import Path

from core.style_renderer import StyleRenderer, register_renderer


class MangaStyleRenderer(StyleRenderer):
    """日式漫画风格渲染器"""

    def __init__(self, width: int = 1080, height: int = 1920,
                 style_config: dict = None):
        super().__init__(width, height, style_config)
        # 延迟导入实际的渲染器
        from core.manga_frame_renderer import MangaFrameRenderer
        self.renderer = MangaFrameRenderer(
            width=width,
            height=height,
            visual_style="manga"
        )

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
        accent_color: str = None,
        visual_element: str = "",
        visual_data: dict = None,
        visible_bullets: int = 0,
        **kwargs
    ) -> str:
        """渲染单帧漫画讲解图"""
        return self.renderer.render_frame(
            title=title,
            bullets=bullets,
            output_path=output_path,
            subtitle=subtitle,
            media_path=media_path,
            scene_index=scene_index,
            total_scenes=total_scenes,
            sfx_text=sfx_text,
            accent_color=accent_color or self.get_color("accent"),
            visual_element=visual_element,
            visual_data=visual_data,
            visible_bullets=visible_bullets,
        )

    def render_storyboard(
        self,
        storyboard: List[dict],
        script_content: str,
        work_dir: str,
        materials: dict = None
    ) -> List[str]:
        """批量渲染分镜"""
        return self.renderer.render_storyboard(
            storyboard=storyboard,
            script_content=script_content,
            work_dir=work_dir,
            materials=materials or {}
        )


# 注册渲染器
register_renderer("manga", MangaStyleRenderer)
