# -*- coding: utf-8 -*-
"""
科技风格配置
适用场景: 科技评测、编程教程、极客内容
设计特征: 深色背景、霓虹点缀、网格装饰、等宽字体
"""

style = {
    # ========== 基本信息 ==========
    "id": "tech",
    "name": "科技风格",
    "name_cn": "科技霓虹",
    "category": "technology",
    "description": "赛博朋克科技风格，适合技术内容",

    # ========== 色彩配置 ==========
    "colors": {
        "background": "#0D1117",      # GitHub深色主题
        "primary": "#C9D1D9",         # 主文字色
        "secondary": "#8B949E",       # 次要文字
        "accent": "#58A6FF",          # 强调色(青色)
        "accent_secondary": "#FF7B72",  # 次强调色(粉红)
        "card_bg": "#161B22",
        "card_border": "#30363D",
    },

    # ========== 字体配置 ==========
    "typography": {
        "title_font": "Arial-Bold",
        "title_size": 44,
        "body_font": "Consolas",
        "body_size": 22,
        "code_font": "Consolas",
        "code_size": 18,
        "line_height": 1.5,
        "letter_spacing": 0,
    },

    # ========== 布局配置 ==========
    "layout": {
        "padding": 50,
        "card_bg": "#161B22",
        "card_border": "#30363D",
        "card_border_width": 1,
        "card_radius": 6,
        "card_shadow": None,
    },

    # ========== 效果配置 ==========
    "effects": {
        "transition": "wipe",
        "transition_duration": 0.35,
        "emphasis": "glow",
        "emphasis_scale": 1.05,
        "animation_speed": "normal",
    },

    # ========== 装饰元素 ==========
    "decorations": {
        "enable_halftone": False,
        "enable_speed_lines": False,
        "enable_crosshatch": False,
        "enable_bg_speckles": False,
        "enable_inner_border": True,
        "enable_decorative_lines": True,
        "enable_progress_dots": True,
        "enable_numbered_circles": True,
        "enable_bottom_tags": False,
    },

    # ========== 底部标签 ==========
    "tags_bottom": [],

    # ========== 默认文案 ==========
    "placeholder_text": "CODE REF",
    "default_subtitle": "详细解析",
    "tag_text": "TECH",
    "tag_secondary": "DEV",

    # ========== 网格背景 ==========
    "bg_grid": True,
    "bg_grid_color": (0, 255, 255, 8),
    "bg_grid_spacing": 40,

    # ========== 霓虹效果 ==========
    "glow": {
        "enabled": True,
        "intensity": 0.6,
        "color": "#58A6FF",
    },

    # ========== 代码高亮 ==========
    "code_highlight": {
        "keyword": "#FF7B72",
        "string": "#A5D6FF",
        "comment": "#8B949E",
        "function": "#D2A8FF",
        "number": "#79C0FF",
    },
}

# ========== 兼容现有渲染器的映射 ==========
legacy_config = {
    "paper_color": "#0D1117",
    "panel_bg": "#161B22",
    "bubble_bg": "#21262D",
    "text_c": "#C9D1D9",
    "accent_red": "#FF7B72",
    "accent_blue": "#58A6FF",
    "border_color": "#30363D",
    "border_width": 2,
    "deco_color": "#58A6FF",
    "panel_gap": 14,
    "card_radius": 6,
    "card_border_color": (48, 54, 61, 150),
    "card_border_width": 1,
    "text_secondary": (139, 148, 158, 255),
    "text_muted": (100, 110, 120, 255),
    "progress_inactive": (35, 40, 50, 255),
    "media_panel_bg": (22, 27, 34, 255),
    "title_color_override": "#58A6FF",
    "body_color_override": None,
    "bg_grid": True,
    "bg_grid_color": (0, 255, 255, 8),
    "bg_grid_spacing": 40,
    "bg_grid_opacity": 8,
}

style.update(legacy_config)
