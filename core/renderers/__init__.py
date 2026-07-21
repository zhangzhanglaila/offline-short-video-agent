# -*- coding: utf-8 -*-
"""
风格渲染器包
"""
from core.renderers.manga_renderer import MangaStyleRenderer
from core.renderers.minimal_renderer import MinimalStyleRenderer
from core.renderers.vibrant_renderer import VibrantStyleRenderer
from core.renderers.cinematic_renderer import CinematicStyleRenderer
from core.renderers.tech_renderer import TechStyleRenderer

__all__ = [
    "MangaStyleRenderer",
    "MinimalStyleRenderer",
    "VibrantStyleRenderer",
    "CinematicStyleRenderer",
    "TechStyleRenderer",
]
