# -*- coding: utf-8 -*-
"""
风格渲染器基类
定义所有风格渲染器的统一接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pathlib import Path


class StyleRenderer(ABC):
    """风格渲染器基类 - 定义统一接口"""

    def __init__(self, width: int = 1080, height: int = 1920,
                 style_config: dict = None):
        """
        初始化渲染器

        Args:
            width: 输出宽度
            height: 输出高度
            style_config: 风格配置字典
        """
        self.width = width
        self.height = height
        self.orientation = "landscape" if width > height else "portrait"
        self.style_config = style_config or {}
        self.style_id = self.style_config.get("id", "unknown")

    # ═══════════════════════════════════════════════════════════════
    # 必须实现的抽象方法
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
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
        **kwargs
    ) -> str:
        """
        渲染单帧画面

        Args:
            title: 场景标题
            bullets: 要点列表
            output_path: 输出路径
            subtitle: 副标题/场景描述
            media_path: 素材图片路径
            scene_index: 当前场景索引
            total_scenes: 总场景数
            sfx_text: 特效文字
            **kwargs: 其他风格特定参数

        Returns:
            输出文件路径
        """
        pass

    @abstractmethod
    def render_storyboard(
        self,
        storyboard: List[dict],
        script_content: str,
        work_dir: str,
        materials: dict = None
    ) -> List[str]:
        """
        批量渲染分镜

        Args:
            storyboard: 分镜列表
            script_content: 完整脚本文本
            work_dir: 工作目录
            materials: {scene_index: file_path} 素材映射

        Returns:
            生成的图片路径列表
        """
        pass

    # ═══════════════════════════════════════════════════════════════
    # 可选的钩子方法（子类可重写）
    # ═══════════════════════════════════════════════════════════════

    def pre_render(self) -> None:
        """渲染前钩子 - 初始化资源"""
        pass

    def post_render(self) -> None:
        """渲染后钩子 - 清理资源"""
        pass

    def validate_config(self) -> bool:
        """验证风格配置是否有效"""
        return bool(self.style_config)

    # ═══════════════════════════════════════════════════════════════
    # 工具方法
    # ═══════════════════════════════════════════════════════════════

    def get_style_config(self, key: str, default: Any = None) -> Any:
        """获取风格配置项"""
        return self.style_config.get(key, default)

    def get_color(self, color_key: str) -> str:
        """获取颜色配置"""
        colors = self.style_config.get("colors", {})
        return colors.get(color_key, "#000000")

    def get_layout(self, key: str, default: Any = None) -> Any:
        """获取布局配置"""
        layout = self.style_config.get("layout", {})
        return layout.get(key, default)


class StyleRendererFactory:
    """风格渲染器工厂 - 根据风格ID创建对应渲染器"""

    _renderers: Dict[str, type] = {}

    @classmethod
    def register(cls, style_id: str, renderer_class: type) -> None:
        """注册渲染器"""
        cls._renderers[style_id] = renderer_class

    @classmethod
    def create(cls, style_id: str, style_config: dict = None,
               width: int = 1080, height: int = 1920) -> Optional[StyleRenderer]:
        """
        创建渲染器实例

        Args:
            style_id: 风格ID
            style_config: 风格配置（可选，未提供则加载）
            width: 输出宽度
            height: 输出高度

        Returns:
            渲染器实例，失败返回 None
        """
        # 加载风格配置
        if style_config is None:
            try:
                from styles import get_style_legacy
                style_config = get_style_legacy(style_id)
                if not style_config:
                    # 尝试新格式
                    from styles import get_style
                    full_config = get_style(style_id)
                    if full_config:
                        # 合并新旧配置
                        style_config = {**full_config, **get_style_legacy(style_id)}
            except Exception as e:
                print(f"[StyleRendererFactory] Failed to load config for {style_id}: {e}")

        if not style_config:
            print(f"[StyleRendererFactory] No config found for style: {style_id}")
            return None

        # 获取渲染器类
        renderer_class = cls._renderers.get(style_id)
        if not renderer_class:
            print(f"[StyleRendererFactory] No renderer registered for: {style_id}")
            return None

        # 创建实例
        try:
            return renderer_class(
                width=width,
                height=height,
                style_config=style_config
            )
        except Exception as e:
            print(f"[StyleRendererFactory] Failed to create renderer: {e}")
            return None

    @classmethod
    def list_available(cls) -> List[str]:
        """列出所有已注册的风格ID"""
        return list(cls._renderers.keys())


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

def get_renderer(style_id: str = "minimal", width: int = 1080,
                height: int = 1920) -> Optional[StyleRenderer]:
    """获取风格渲染器的便捷函数"""
    return StyleRendererFactory.create(style_id, width=width, height=height)


def register_renderer(style_id: str, renderer_class: type) -> None:
    """注册渲染器的便捷函数"""
    StyleRendererFactory.register(style_id, renderer_class)
