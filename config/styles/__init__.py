# -*- coding: utf-8 -*-
"""
风格模板加载器
统一管理所有视觉风格配置，提供加载、查询、兼容性映射功能
"""
from pathlib import Path
from typing import Dict, List, Optional
import importlib.util

# 风格配置目录
STYLES_DIR = Path(__file__).parent

# 已加载的风格缓存
_loaded_styles: Dict[str, dict] = None


def load_all_styles() -> Dict[str, dict]:
    """加载所有风格配置文件。

    Returns:
        {style_id: style_config} 字典
    """
    global _loaded_styles
    if _loaded_styles is not None:
        return _loaded_styles

    styles = {}
    style_files = [
        "minimal.py",
        "vibrant.py",
        "cinematic.py",
        "tech.py",
        "manga.py",
    ]

    for filename in style_files:
        style_path = STYLES_DIR / filename
        if not style_path.exists():
            continue

        try:
            # 动态导入风格模块
            spec = importlib.util.spec_from_file_location(filename[:-3], style_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 获取 style 变量
                style_config = getattr(module, 'style', None)
                if style_config and isinstance(style_config, dict):
                    style_id = style_config.get('id', filename[:-3])
                    styles[style_id] = style_config
        except Exception as e:
            print(f"[StyleLoader] Failed to load {filename}: {e}")

    _loaded_styles = styles
    return styles


def get_style(style_id: str) -> Optional[dict]:
    """获取指定风格配置。

    Args:
        style_id: 风格ID (minimal/vibrant/cinematic/tech/manga)

    Returns:
        风格配置字典，不存在返回 None
    """
    styles = load_all_styles()
    return styles.get(style_id)


def get_style_legacy(style_id: str) -> dict:
    """获取风格的 legacy 配置格式，兼容现有渲染器。

    返回的配置直接兼容 VISUAL_STYLES 格式，包含所有渲染器需要的字段。
    """
    style = get_style(style_id)
    if not style:
        # 降级到空配置
        return {}

    # 过滤出 legacy 渲染器需要的字段
    legacy_fields = {
        "paper_color", "panel_bg", "bubble_bg", "text_c",
        "accent_red", "accent_blue", "border_color", "border_width",
        "deco_color", "panel_gap", "card_radius", "card_border_color",
        "card_border_width", "text_secondary", "text_muted",
        "progress_inactive", "media_panel_bg", "title_color_override",
        "body_color_override", "bg_grid", "bg_grid_color",
        "bg_grid_spacing", "bg_grid_opacity", "halftone_dot_size",
        "halftone_spacing", "halftone_angle", "halftone_opacity",
        "speckle_count", "speedline_count", "crosshatch_spacing",
        "crosshatch_angle", "crosshatch_opacity", "enable_halftone",
        "enable_speed_lines", "enable_crosshatch", "enable_bg_speckles",
        "enable_inner_border", "enable_decorative_lines",
        "enable_progress_dots", "enable_numbered_circles", "enable_bottom_tags",
    }

    legacy = {}
    for field in legacy_fields:
        if field in style:
            legacy[field] = style[field]

    return legacy


def list_styles() -> List[dict]:
    """列出所有可用的风格信息。

    Returns:
        [{id, name, name_cn, category, description}] 列表
    """
    styles = load_all_styles()
    result = []
    for style_id, config in styles.items():
        result.append({
            "id": config.get("id", style_id),
            "name": config.get("name", ""),
            "name_cn": config.get("name_cn", ""),
            "category": config.get("category", ""),
            "description": config.get("description", ""),
        })
    return result


def get_style_by_category(category: str) -> List[dict]:
    """根据分类获取风格列表。

    Args:
        category: 分类名 (education/lifestyle/storytelling/technology/acg)

    Returns:
        匹配的风格列表
    """
    styles = load_all_styles()
    return [s for s in styles.values() if s.get("category") == category]


# ========== 便捷函数 ==========

def get_default_style() -> str:
    """获取默认风格ID."""
    return "minimal"


def get_available_style_ids() -> List[str]:
    """获取所有可用的风格ID列表。"""
    return list(load_all_styles().keys())


def style_exists(style_id: str) -> bool:
    """检查风格是否存在。"""
    return style_id in load_all_styles()


# ========== 兼容层：与现有 config.py 集成 ==========

def get_visual_styles_config() -> Dict[str, dict]:
    """返回 VISUAL_STYLES 格式的配置字典，用于向后兼容。

    这个函数生成的格式可以完全替代 config.py 中的 VISUAL_STYLES。
    """
    styles = load_all_styles()
    result = {}
    for style_id, config in styles.items():
        result[style_id] = get_style_legacy(style_id)
    return result


if __name__ == "__main__":
    # 测试代码
    print("Available styles:")
    for style_info in list_styles():
        print(f"  - {style_info['id']}: {style_info['name_cn']} ({style_info['category']})")

    print("\nMinimal style config:")
    import pprint
    pprint.pprint(get_style("minimal"))
