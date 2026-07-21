"""
场景片段规格 - 描述如何将一个场景渲染为(运动)视频片段。

用于视频合成Agent与FFmpeg合成器之间传递分层信息：
背景层(可运镜) + 可选的静态覆盖层(字幕/元素)。
"""

from dataclasses import dataclass
from typing import Optional

from core.compose.motion.ken_burns import KenBurnsSpec


@dataclass
class SceneClipSpec:
    """单个场景的片段合成规格。

    Attributes:
        background_path: 背景图路径(素材原图或已渲染的文字卡)
        duration: 片段时长(秒)
        ken_burns: 运镜规格。None表示背景静止。
        overlay_path: 可选的透明覆盖层PNG(字幕/元素)，静态叠加在背景上
    """

    background_path: str
    duration: float
    ken_burns: Optional[KenBurnsSpec] = None
    overlay_path: Optional[str] = None

    @property
    def has_motion(self) -> bool:
        """是否有运镜。"""
        return self.ken_burns is not None

    @property
    def has_overlay(self) -> bool:
        """是否有覆盖层。"""
        return self.overlay_path is not None
