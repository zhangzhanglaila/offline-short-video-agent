# -*- coding: utf-8 -*-
"""
config package - 统一配置导出
"""
from pathlib import Path

# 确保 styles 目录存在
STYLES_DIR = Path(__file__).parent / "styles"
if not STYLES_DIR.exists():
    STYLES_DIR.mkdir(parents=True, exist_ok=True)

# 导出风格相关函数
try:
    from config.styles import (
        get_style,
        get_style_legacy,
        list_styles,
        get_style_by_category,
        get_available_style_ids,
        style_exists,
        get_visual_styles_config,
    )
    __all__ = [
        "get_style",
        "get_style_legacy",
        "list_styles",
        "get_style_by_category",
        "get_available_style_ids",
        "style_exists",
        "get_visual_styles_config",
    ]
except ImportError:
    # 风格模块加载失败时的降级
    __all__ = []
