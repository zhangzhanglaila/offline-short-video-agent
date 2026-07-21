# -*- coding: utf-8 -*-
"""
动效配置系统
定义不同风格的默认动效效果
"""
from typing import Dict, List, Any


# 动效配置格式
ANIMATION_CONFIGS = {
    "minimal": {
        "title": {
            "type": "fade",
            "duration": 0.6,
            "delay": 0.0,
            "easing": "ease_out"
        },
        "subtitle": {
            "type": "fade",
            "duration": 0.5,
            "delay": 0.3,
            "easing": "ease_out"
        },
        "bullets": {
            "type": "slide",
            "duration": 0.4,
            "delay": 0.5,
            "direction": "left",
            "stagger": 0.15  # 每个要点之间的延迟
        },
        "footer": {
            "type": "fade",
            "duration": 0.3,
            "delay": 0.0,
            "easing": "linear"
        }
    },

    "vibrant": {
        "title": {
            "type": "zoom",
            "duration": 0.5,
            "delay": 0.0,
            "easing": "ease_out"
        },
        "subtitle": {
            "type": "slide",
            "duration": 0.4,
            "delay": 0.2,
            "direction": "right",
            "easing": "ease_out"
        },
        "bullets": {
            "type": "fade",
            "duration": 0.3,
            "delay": 0.4,
            "stagger": 0.1
        },
        "footer": {
            "type": "fade",
            "duration": 0.3,
            "delay": 0.0
        }
    },

    "cinematic": {
        "title": {
            "type": "fade",
            "duration": 1.0,
            "delay": 0.0,
            "easing": "ease_in_out"
        },
        "subtitle": {
            "type": "fade",
            "duration": 0.8,
            "delay": 0.5,
            "easing": "ease_in_out"
        },
        "bullets": {
            "type": "fade",
            "duration": 0.6,
            "delay": 1.0,
            "stagger": 0.2
        },
        "footer": {
            "type": "fade",
            "duration": 0.5,
            "delay": 0.0,
            "easing": "linear"
        }
    },

    "tech": {
        "title": {
            "type": "typewriter",
            "duration": 0.8,
            "delay": 0.0
        },
        "subtitle": {
            "type": "slide",
            "duration": 0.4,
            "delay": 0.6,
            "direction": "left"
        },
        "bullets": {
            "type": "blink",
            "duration": 0.3,
            "delay": 0.8,
            "stagger": 0.15,
            "repeat": 2
        },
        "footer": {
            "type": "fade",
            "duration": 0.2,
            "delay": 0.0
        }
    },

    "manga": {
        "title": {
            "type": "zoom",
            "duration": 0.4,
            "delay": 0.0,
            "easing": "ease_out"
        },
        "subtitle": {
            "type": "slide",
            "duration": 0.3,
            "delay": 0.2,
            "direction": "bottom"
        },
        "bullets": {
            "type": "slide",
            "duration": 0.3,
            "delay": 0.3,
            "direction": "right",
            "stagger": 0.1
        },
        "footer": {
            "type": "fade",
            "duration": 0.2,
            "delay": 0.0
        }
    }
}


def get_animation_config(style_id: str, element: str = None) -> Dict:
    """
    获取动效配置

    Args:
        style_id: 风格ID
        element: 元素类型 (title/subtitle/bullets/footer)

    Returns:
        动效配置字典
    """
    style_configs = ANIMATION_CONFIGS.get(style_id, {})

    if element:
        return style_configs.get(element, {})

    return style_configs


def list_animation_styles() -> List[str]:
    """列出所有支持动效的风格"""
    return list(ANIMATION_CONFIGS.keys())


def has_animations(style_id: str) -> bool:
    """检查风格是否配置了动效"""
    return style_id in ANIMATION_CONFIGS


# ═══════════════════════════════════════════════════════════════
# 动效元素类型
# ═══════════════════════════════════════════════════════════════

class AnimationElement:
    """动效元素类型"""

    TITLE = "title"
    SUBTITLE = "subtitle"
    BULLETS = "bullets"
    FOOTER = "footer"
    HIGHLIGHT = "highlight"  # 高亮强调
