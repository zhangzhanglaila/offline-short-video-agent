"""
场景元素编排 - 将场景数据派生为多个错开时间出现的元素图层。

实现"元素逐个入场"的编排感（D3核心）：
内容场景 = 序号徽章 → 关键词标签 → 字幕，三者先后滑入。

设计：从现有场景数据(文字/关键词/序号)规则派生元素，
无需修改内容模型或依赖LLM，离线可用。
"""

from pathlib import Path
from typing import List, Tuple

from core.compose.motion.animation_spec import (
    OverlayLayer, AnimationSpec,
    ANIM_SLIDE_LEFT, ANIM_SLIDE_UP, ANIM_FADE_IN,
)


# 元素出现的错开间隔(秒)
_STAGGER = 0.25
# 首个元素起始延迟(秒，稍晚于画面出现)
_BASE_START = 0.25


def build_content_overlays(
    scene,
    content_index: int,
    renderer,
    work_dir,
    with_badge: bool = True,
) -> List[OverlayLayer]:
    """为内容场景构建多元素覆盖层(错开时间出现)。

    元素顺序(逐个入场)：
      1. 序号徽章(从左滑入)
      2. 关键词标签(从左滑入，稍晚)
      3. 字幕(从下滑入，最后)

    Args:
        scene: 内容场景(需有 scene_id/text/keywords)
        content_index: 内容场景的序号(从1开始，用于徽章数字)
        renderer: SceneImageRenderer实例
        work_dir: 工作目录
        with_badge: 是否显示序号徽章和关键词标签

    Returns:
        OverlayLayer列表(按出现顺序)
    """
    work_dir = Path(work_dir)
    sid = scene.scene_id
    layers: List[OverlayLayer] = []
    order = 0

    if with_badge:
        # 1. 序号徽章
        badge_path = str(work_dir / f"scene_{sid:03d}_badge.png")
        if renderer.render_badge_overlay(content_index, badge_path):
            layers.append(OverlayLayer(
                badge_path,
                AnimationSpec(anim_type=ANIM_SLIDE_LEFT,
                              start=_BASE_START + _STAGGER * order, duration=0.45),
            ))
            order += 1

        # 2. 关键词标签(取首个关键词)
        keyword = _first_keyword(scene)
        if keyword:
            chip_path = str(work_dir / f"scene_{sid:03d}_chip.png")
            if renderer.render_keyword_chip_overlay(keyword, chip_path):
                layers.append(OverlayLayer(
                    chip_path,
                    AnimationSpec(anim_type=ANIM_SLIDE_LEFT,
                                  start=_BASE_START + _STAGGER * order, duration=0.45),
                ))
                order += 1

    # 3. 字幕(最后出现，从下滑入)
    sub_path = str(work_dir / f"scene_{sid:03d}_sub.png")
    if renderer.render_subtitle_overlay(scene.text, sub_path):
        layers.append(OverlayLayer(
            sub_path,
            AnimationSpec(anim_type=ANIM_SLIDE_UP,
                          start=_BASE_START + _STAGGER * order, duration=0.5),
        ))

    return layers


def _first_keyword(scene) -> str:
    """取场景的首个有效关键词。

    Args:
        scene: 场景

    Returns:
        关键词，无则空串
    """
    for kw in (scene.keywords or []):
        if kw and kw.strip():
            return kw.strip()
    return ""
