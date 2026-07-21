"""
场景片段规格 - 描述如何将一个场景渲染为(运动)视频片段。

用于视频合成Agent与FFmpeg合成器之间传递分层信息：
背景层(可运镜) + 可选的静态覆盖层(字幕/元素)。
"""

from dataclasses import dataclass, field
from typing import Optional, List

from core.compose.motion.ken_burns import KenBurnsSpec
from core.compose.motion.animation_spec import OverlayLayer


@dataclass
class SceneClipSpec:
    """单个场景的片段合成规格。

    Attributes:
        background_path: 背景路径(素材图/文字卡，或视频素材)
        duration: 片段时长(秒)
        ken_burns: 运镜规格。None表示背景静止。
        overlay_path: (向后兼容)单个静态透明覆盖层PNG
        overlays: 带入场动画的覆盖层列表(D2)，优先于overlay_path
        background_is_video: 背景是否为视频素材(D5)。True时loop+cover-fit，
                             不应用Ken Burns(视频本身在动)
    """

    background_path: str
    duration: float
    ken_burns: Optional[KenBurnsSpec] = None
    overlay_path: Optional[str] = None
    overlays: List[OverlayLayer] = field(default_factory=list)
    background_is_video: bool = False

    @property
    def has_motion(self) -> bool:
        """是否有运镜。"""
        return self.ken_burns is not None

    @property
    def has_overlay(self) -> bool:
        """是否有覆盖层(静态单层或动画多层)。"""
        return bool(self.overlay_path) or bool(self.overlays)
