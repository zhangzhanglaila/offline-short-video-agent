# -*- coding: utf-8 -*-
"""
漫画风格配置 (优化版)
适用场景: 二次元、ACG、轻科普
设计特征: 网点纸、速度线、气泡框、粗描边
本文件优化现有漫画风格，使其更符合现代审美
"""

style = {
    # ========== 基本信息 ==========
    "id": "manga",
    "name": "漫画风格",
    "name_cn": "日式漫画",
    "category": "acg",
    "description": "经典日式漫画风格，适合ACG和轻科普",

    # ========== 色彩配置 ==========
    "colors": {
        "background": "#FFF8F0",      # 米白漫画纸
        "primary": "#1A1A2E",         # 主文字色
        "secondary": "#4A4A5E",      # 次要文字
        "accent": "#E04040",          # 强调色(红)
        "accent_secondary": "#3060C0",  # 次强调色(蓝)
        "card_bg": "#FFFBF5",
        "card_border": "#1A1A2E",
    },

    # ========== 字体配置 ==========
    "typography": {
        "title_font": "Arial-Bold",
        "title_size": 52,
        "body_font": "Arial",
        "body_size": 28,
        "line_height": 1.4,
        "letter_spacing": 0,
    },

    # ========== 布局配置 ==========
    "layout": {
        "padding": 60,
        "card_bg": "#FFFBF5",
        "card_border": "#1A1A2E",
        "card_border_width": 2,
        "card_radius": 10,
        "card_shadow": None,
    },

    # ========== 效果配置 ==========
    "effects": {
        "transition": "pixelize",
        "transition_duration": 0.3,
        "emphasis": "shake",
        "emphasis_scale": 1.08,
        "animation_speed": "normal",
    },

    # ========== 装饰元素 ==========
    "decorations": {
        "enable_halftone": True,          # 网点纸
        "enable_speed_lines": True,       # 速度线
        "enable_crosshatch": True,        # 交叉排线
        "enable_bg_speckles": True,       # 纸张纹理
        "enable_inner_border": True,
        "enable_decorative_lines": True,
        "enable_progress_dots": True,
        "enable_numbered_circles": True,
        "enable_bottom_tags": True,
    },

    # ========== 底部标签 ==========
    "tags_bottom": ["收藏", "点赞", "转发"],

    # ========== 默认文案 ==========
    "placeholder_text": "素材参考",
    "default_subtitle": "详细讲解 · 建议收藏反复观看",
    "tag_text": "MANGA EXPLAIN",
    "tag_secondary": "MANGA",

    # ========== 网点纸配置 ==========
    "halftone": {
        "dot_size": 2,
        "spacing": 8,
        "angle": 45,
        "opacity": 0.04,
    },

    # ========== 速度线配置 ==========
    "speed_lines": {
        "count": 28,
        "opacity": 60,
    },

    # ========== 交叉排线配置 ==========
    "crosshatch": {
        "spacing": 22,
        "angle": 30,
        "opacity": 7,
    },
}

# ========== 兼容现有渲染器的映射 ==========
# 这些是现有的 MANGA_STYLE_CONFIG 值，保持兼容
legacy_config = {
    "paper_color": "#FFF8F0",
    "panel_bg": "#FFFBF5",
    "bubble_bg": "#FFFFFF",
    "text_c": "#1A1A2E",
    "accent_red": "#E04040",
    "accent_blue": "#3060C0",
    "border_color": "#1A1A2E",
    "border_width": 5,
    "deco_color": "#1A1A2E",
    "panel_gap": 14,
    "card_radius": 10,
    "card_border_color": (180, 180, 190, 100),
    "card_border_width": 1,
    "text_secondary": (80, 80, 90, 255),
    "text_muted": (150, 150, 160, 255),
    "progress_inactive": (200, 200, 210, 255),
    "media_panel_bg": (248, 246, 242, 255),
    "title_color_override": None,
    "body_color_override": None,
    "bg_grid": False,
    "halftone_dot_size": 2,
    "halftone_spacing": 8,
    "halftone_angle": 45,
    "halftone_opacity": 0.04,
    "speckle_count": 80,
    "speedline_count": 28,
    "crosshatch_spacing": 22,
    "crosshatch_angle": 30,
    "crosshatch_opacity": 7,
}

style.update(legacy_config)
