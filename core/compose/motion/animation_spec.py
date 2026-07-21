"""
动画规格 - 描述元素图层的入场动画。

配合 text_animations.py 生成FFmpeg滤镜，实现文字/元素的
淡入、上滑、缩放等入场效果，支持多元素错开时间出现。
"""

from dataclasses import dataclass, field
from typing import Dict, Any


# 支持的入场动画类型
ANIM_NONE = "none"              # 无动画(静态)
ANIM_FADE_IN = "fade_in"        # 淡入
ANIM_SLIDE_UP = "slide_up"      # 从下方滑入(带淡入)
ANIM_SLIDE_DOWN = "slide_down"  # 从上方滑入(带淡入)
ANIM_ZOOM_IN = "zoom_in"        # 放大淡入


@dataclass
class AnimationSpec:
    """元素入场动画规格。

    Attributes:
        anim_type: 动画类型 (none/fade_in/slide_up/slide_down/zoom_in)
        start: 相对场景的开始时间(秒)
        duration: 动画时长(秒)
        params: 额外参数(如滑动距离slide_px)
    """

    anim_type: str = ANIM_FADE_IN
    start: float = 0.0
    duration: float = 0.5
    params: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_static(self) -> bool:
        """是否为无动画的静态层。"""
        return self.anim_type == ANIM_NONE


@dataclass
class OverlayLayer:
    """一个覆盖图层(透明PNG) + 其入场动画。

    Attributes:
        image_path: 透明PNG路径
        animation: 入场动画规格
    """

    image_path: str
    animation: AnimationSpec = field(default_factory=AnimationSpec)
