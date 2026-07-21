"""
转场选择 - 为场景边界智能选择FFmpeg xfade转场类型。

FFmpeg xfade原生支持40+种转场，比PIL合成质量更高。
根据相邻场景类型选择：
- 涉及标题卡/结尾卡的边界用柔和转场(fade类)
- 内容场景之间用动感转场(slide/wipe/zoom)，并轮换避免雷同
"""

from typing import List


# 柔和转场(用于标题卡/结尾卡边界)
_GENTLE = ["fade", "dissolve", "smoothup", "circleopen", "smoothleft"]

# 动感转场(用于内容场景之间)
_DYNAMIC = ["slideleft", "wipeleft", "slideright", "smoothright",
            "zoomin", "slideup", "wiperight"]

# 文字卡类型(柔和边界判断)
_CARD_TYPES = {"title_card", "conclusion"}


def select_transition(from_type: str, to_type: str, index: int) -> str:
    """为一个场景边界选择转场类型。

    Args:
        from_type: 前一场景类型
        to_type: 后一场景类型
        index: 边界索引(用于轮换避免雷同)

    Returns:
        xfade转场名称
    """
    # 涉及文字卡的边界 → 柔和
    if from_type in _CARD_TYPES or to_type in _CARD_TYPES:
        return _GENTLE[index % len(_GENTLE)]
    # 内容之间 → 动感轮换
    return _DYNAMIC[index % len(_DYNAMIC)]


def build_transitions(scene_types: List[str]) -> List[str]:
    """为整个场景序列生成各边界的转场列表。

    Args:
        scene_types: 场景类型列表(按顺序)

    Returns:
        转场名称列表，长度为 len(scene_types)-1
    """
    transitions: List[str] = []
    for i in range(len(scene_types) - 1):
        transitions.append(
            select_transition(scene_types[i], scene_types[i + 1], i)
        )
    return transitions
