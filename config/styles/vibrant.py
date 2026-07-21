# -*- coding: utf-8 -*-
"""
活力风格配置
适用场景: 生活方式、美妆、美食、旅行
设计特征: 高饱和度、渐变背景、圆润形状、动态阴影
"""

style = {
    # ========== 基本信息 ==========
    "id": "vibrant",
    "name": "活力风格",
    "name_cn": "活力时尚",
    "category": "lifestyle",
    "description": "色彩鲜明的时尚生活风格，充满活力",

    # ========== 色彩配置 ==========
    "colors": {
        "background": {
            "type": "gradient",
            "value": ["#FF9A9E", "#FECFEF", "#FECFEF"],  # 粉色渐变
            "angle": 135,
        },
        "primary": "#FFFFFF",       # 主文字色(白)
        "secondary": "#FFF0F0",     # 次要文字
        "accent": "#FF6B6B",         # 强调色(珊瑚红)
        "card_bg": "#FFFFFF",
        "card_border": "transparent",
    },

    # ========== 字体配置 ==========
    "typography": {
        "title_font": "Arial-Bold",
        "title_size": 52,
        "body_font": "Arial",
        "body_size": 26,
        "line_height": 1.5,
        "letter_spacing": 0.5,
    },

    # ========== 布局配置 ==========
    "layout": {
        "padding": 40,
        "card_bg": "#FFFFFF",
        "card_border": "transparent",
        "card_border_width": 0,
        "card_radius": 20,
        "card_shadow": "0 8 24 rgba(255, 107, 107, 0.15)",
    },

    # ========== 效果配置 ==========
    "effects": {
        "transition": "zoom",
        "transition_duration": 0.5,
        "emphasis": "bounce",
        "emphasis_scale": 1.12,
        "animation_speed": "fast",
    },

    # ========== 装饰元素 ==========
    "decorations": {
        "enable_halftone": False,
        "enable_speed_lines": False,
        "enable_crosshatch": False,
        "enable_bg_speckles": True,      # 微妙斑点
        "enable_inner_border": False,
        "enable_decorative_lines": True, # 保留装饰线
        "enable_progress_dots": True,
        "enable_numbered_circles": True,
        "enable_bottom_tags": True,
    },

    # ========== 底部标签 ==========
    "tags_bottom": ["收藏", "点赞", "分享"],

    # ========== 默认文案 ==========
    "placeholder_text": "素材参考",
    "default_subtitle": "精彩内容",
    "tag_text": "VIBRANT",
    "tag_secondary": "STYLE",

    # ========== 渐变配置 ==========
    "gradient": {
        "type": "linear",
        "colors": ["#FF9A9E", "#FECFEF"],
        "angle": 135,
    },
}

# ========== 兼容现有渲染器的映射 ==========
legacy_config = {
    "paper_color": "#FFF5F5",
    "panel_bg": "#FFFFFF",
    "bubble_bg": "#FFFAFA",
    "text_c": "#2D2D2D",
    "accent_red": "#FF6B6B",
    "accent_blue": "#4ECDC4",
    "border_color": "#FFB4B4",
    "border_width": 3,
    "deco_color": "#FF6B6B",
    "panel_gap": 14,
    "card_radius": 20,
    "card_border_color": (255, 180, 180, 100),
    "card_border_width": 2,
    "text_secondary": (102, 102, 102, 255),
    "text_muted": (170, 170, 170, 255),
    "progress_inactive": (255, 220, 220, 255),
    "media_panel_bg": (255, 250, 250, 255),
    "title_color_override": "#FF6B6B",
    "body_color_override": None,
    "bg_grid": False,
    "speckle_count": 50,
}

style.update(legacy_config)
