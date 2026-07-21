# -*- coding: utf-8 -*-
"""
电影风格配置
适用场景: 故事叙述、纪录片、情感内容
设计特征: 暗调背景、胶片颗粒、电影调色、窄边框
"""

style = {
    # ========== 基本信息 ==========
    "id": "cinematic",
    "name": "电影风格",
    "name_cn": "电影质感",
    "category": "storytelling",
    "description": "电影感十足的叙事风格，适合情感故事",

    # ========== 色彩配置 ==========
    "colors": {
        "background": "#0A0A0A",
        "primary": "#E5E5E5",      # 主文字色(灰白)
        "secondary": "#8A8A8A",    # 次要文字
        "accent": "#FF9500",       # 强调色(橙色)
        "card_bg": "#1A1A1A",
        "card_border": "#333333",
    },

    # ========== 字体配置 ==========
    "typography": {
        "title_font": "Georgia-Bold",
        "title_size": 48,
        "body_font": "Georgia",
        "body_size": 24,
        "line_height": 1.6,
        "letter_spacing": 0.2,
    },

    # ========== 布局配置 ==========
    "layout": {
        "padding": 60,
        "card_bg": "#1A1A1A",
        "card_border": "#333333",
        "card_border_width": 2,
        "card_radius": 4,
        "card_shadow": None,
    },

    # ========== 效果配置 ==========
    "effects": {
        "transition": "fadegrays",
        "transition_duration": 0.6,
        "emphasis": "slow_zoom",
        "emphasis_scale": 1.06,
        "animation_speed": "slow",
    },

    # ========== 装饰元素 ==========
    "decorations": {
        "enable_halftone": False,
        "enable_speed_lines": False,
        "enable_crosshatch": True,     # 微妙纹理
        "enable_bg_speckles": False,
        "enable_inner_border": True,
        "enable_decorative_lines": True,
        "enable_progress_dots": True,
        "enable_numbered_circles": False,
        "enable_bottom_tags": False,
    },

    # ========== 底部标签 ==========
    "tags_bottom": [],

    # ========== 默认文案 ==========
    "placeholder_text": "画面参考",
    "default_subtitle": "故事继续",
    "tag_text": "",
    "tag_secondary": "",

    # ========== 特效配置 ==========
    "film_grain": True,
    "vignette": True,
    "color_grading": {
        "teal_orange": True,    # 青橙色调
        "contrast": 1.15,
        "saturation": 0.95,
        "warmth": 0.1,
    },
}

# ========== 兼容现有渲染器的映射 ==========
legacy_config = {
    "paper_color": "#0A0A0A",
    "panel_bg": "#151515",
    "bubble_bg": "#1A1A1A",
    "text_c": "#E5E5E5",
    "accent_red": "#FF9500",
    "accent_blue": "#4A90D9",
    "border_color": "#333333",
    "border_width": 2,
    "deco_color": "#666666",
    "panel_gap": 14,
    "card_radius": 4,
    "card_border_color": (51, 51, 51, 200),
    "card_border_width": 2,
    "text_secondary": (138, 138, 138, 255),
    "text_muted": (100, 100, 100, 255),
    "progress_inactive": (50, 50, 50, 255),
    "media_panel_bg": (26, 26, 26, 255),
    "title_color_override": "#FF9500",
    "body_color_override": None,
    "bg_grid": False,
    "crosshatch_spacing": 30,
    "crosshatch_opacity": 5,
    "crosshatch_angle": 45,
}

style.update(legacy_config)
