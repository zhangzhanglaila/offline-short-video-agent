# -*- coding: utf-8 -*-
"""
极简风格配置
适用场景: 知识科普、教育、商务
设计特征: 大量留白、纯色背景、大字号、极简装饰
"""

style = {
    # ========== 基本信息 ==========
    "id": "minimal",
    "name": "极简风格",
    "name_cn": "极简清新",
    "category": "education",
    "description": "简洁大方的教育科普风格，强调内容本身",

    # ========== 色彩配置 ==========
    "colors": {
        "background": "#FFFFFF",
        "primary": "#1A1A1A",      # 主文字色
        "secondary": "#666666",    # 次要文字
        "accent": "#3B82F6",       # 强调色(蓝色)
        "card_bg": "#FAFAFA",      # 卡片背景
        "card_border": "#E5E5E5",  # 卡片边框
    },

    # ========== 字体配置 ==========
    "typography": {
        "title_font": "Arial-Bold",
        "title_size": 56,
        "body_font": "Arial",
        "body_size": 28,
        "line_height": 1.4,
        "letter_spacing": 0,
    },

    # ========== 布局配置 ==========
    "layout": {
        "padding": 80,
        "card_bg": "transparent",
        "card_border": "#E5E5E5",
        "card_border_width": 1,
        "card_radius": 8,
        "card_shadow": None,
    },

    # ========== 效果配置 ==========
    "effects": {
        "transition": "fade",
        "transition_duration": 0.4,
        "emphasis": "scale",
        "emphasis_scale": 1.08,
        "animation_speed": "normal",
    },

    # ========== 装饰元素 ==========
    "decorations": {
        "enable_halftone": False,
        "enable_speed_lines": False,
        "enable_crosshatch": False,
        "enable_bg_speckles": False,
        "enable_inner_border": False,
        "enable_decorative_lines": False,
        "enable_progress_dots": True,     # 保留进度条
        "enable_numbered_circles": True,  # 保留序号
        "enable_bottom_tags": False,
    },

    # ========== 底部标签 ==========
    "tags_bottom": [],

    # ========== 默认文案 ==========
    "placeholder_text": "图片参考",
    "default_subtitle": "详细讲解",
    "tag_text": "",
    "tag_secondary": "",

    # ========== 渐变配置(可选) ==========
    "gradient": None,
}

# ========== 兼容现有渲染器的映射 ==========
# 这些字段直接映射到现有的 VISUAL_STYLES 格式
legacy_config = {
    "paper_color": "#FFFFFF",
    "panel_bg": "#FAFAFA",
    "bubble_bg": "#FFFFFF",
    "text_c": "#1A1A1A",
    "accent_red": "#3B82F6",
    "accent_blue": "#3B82F6",
    "border_color": "#E5E5E5",
    "border_width": 2,
    "deco_color": "#E5E5E5",
    "panel_gap": 14,
    "card_radius": 8,
    "card_border_color": (229, 229, 229, 80),
    "card_border_width": 1,
    "text_secondary": (102, 102, 102, 255),
    "text_muted": (160, 160, 160, 255),
    "progress_inactive": (220, 220, 225, 255),
    "media_panel_bg": (250, 250, 250, 255),
    "title_color_override": None,
    "body_color_override": None,
    "bg_grid": False,
}

# 合并配置
style.update(legacy_config)
