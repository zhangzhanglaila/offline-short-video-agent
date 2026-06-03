# -*- coding: utf-8 -*-
"""
Scene Planner v3 — LLM 驱动的场景规划

全流程 LLM：
1. LLM 分析文案，提取视觉元素
2. LLM 决定场景布局（对象+位置+关系）
3. LLM 决定环境元素
4. 渲染器根据 LLM 输出生成视频

不再使用硬编码模板。
"""

from __future__ import annotations

import json
import re
from typing import List, Optional, Callable

from core.svg_lineart_library import (
    Illustration, SceneObject, SceneLayout, Stroke, Weight,
    get_illustration, KEYWORD_MAP,
)


# ═══════════════════════════════════════════════════════════════
# LLM Prompt
# ═══════════════════════════════════════════════════════════════

SCENE_PLANNER_PROMPT = """You are a visual scene designer for whiteboard animation videos.

Given a narration sentence, design a scene layout. Output ONLY valid JSON.

Available objects (use these exact keywords):
robot, person_standing, person_sitting, person_pointing, laptop, monitor,
database, book_open, brain, lightbulb, gear, city_skyline, cloud,
chat_bubble, magnifying_glass, check_mark, arrow_right, arrow_down

Rules:
1. Choose 1-3 objects that best represent the narration
2. Place them with x,y coordinates (canvas is 1920x1080, center is 960,540)
3. The MAIN object should be largest (scale 3.0-5.0) and centered
4. Supporting objects should be smaller (scale 1.5-2.5) and offset
5. Choose an environment type: flow_vertical, flow_horizontal, dots, desk, thought_bubbles
6. Describe the visual metaphor (what story this scene tells)

Output JSON:
{
  "objects": [
    {"keyword": "brain", "x": 700, "y": 200, "scale": 4.0},
    {"keyword": "database", "x": 300, "y": 350, "scale": 2.2},
    {"keyword": "monitor", "x": 1200, "y": 300, "scale": 2.5}
  ],
  "environment": "flow_vertical",
  "metaphor": "data flows into brain, results appear on screen"
}

Environment types:
- flow_vertical: vertical flow lines (top to bottom)
- flow_horizontal: horizontal flow lines (left to right)
- dots: scattered decorative dots
- desk: desk line at bottom
- thought_bubbles: thought bubble dots
- search_rays: radial rays from center
- none: no environment
"""


# ═══════════════════════════════════════════════════════════════
# 环境元素生成
# ═══════════════════════════════════════════════════════════════

def _make_flow_vertical(w: int, h: int) -> List[Stroke]:
    cx = w / 2
    strokes = [
        Stroke(points=[(cx, 100), (cx, 300)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(cx - 15, 280), (cx, 300), (cx + 15, 280)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(cx, 500), (cx, 700)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(cx - 15, 680), (cx, 700), (cx + 15, 680)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(cx - 200, 80), (cx - 200, 800)], weight=Weight.ENVIRONMENT, color_key="muted"),
        Stroke(points=[(cx + 200, 80), (cx + 200, 800)], weight=Weight.ENVIRONMENT, color_key="muted"),
    ]
    for i in range(6):
        y = 150 + i * 100
        strokes.append(Stroke(points=[(cx - 4, y), (cx + 4, y)], weight=Weight.ACCENT, color_key="accent"))
    return strokes


def _make_flow_horizontal(w: int, h: int) -> List[Stroke]:
    cy = h / 2 + 40
    return [
        Stroke(points=[(200, cy), (600, cy)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(580, cy - 12), (600, cy), (580, cy + 12)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(800, cy), (1200, cy)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(1180, cy - 12), (1200, cy), (1180, cy + 12)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(80, 60), (w - 80, 60)], weight=Weight.ENVIRONMENT, color_key="muted"),
        Stroke(points=[(80, h - 60), (w - 80, h - 60)], weight=Weight.ENVIRONMENT, color_key="muted"),
    ]


def _make_dots(w: int, h: int) -> List[Stroke]:
    import random
    strokes = []
    for _ in range(12):
        x = random.randint(40, w - 40)
        y = random.randint(40, h - 120)
        strokes.append(Stroke(points=[(x, y), (x + 2, y)], weight=Weight.ENVIRONMENT, color_key="muted"))
    return strokes


def _make_desk(w: int, h: int) -> List[Stroke]:
    desk_y = h * 0.72
    return [
        Stroke(points=[(w * 0.05, desk_y), (w * 0.95, desk_y)], weight=Weight.ENVIRONMENT, color_key="line"),
        Stroke(points=[(w * 0.08, desk_y + 8), (w * 0.92, desk_y + 8)], weight=Weight.ENVIRONMENT, color_key="muted"),
    ]


def _make_thought_bubbles(w: int, h: int) -> List[Stroke]:
    cx = w * 0.75
    return [
        Stroke(points=[(cx, h * 0.55), (cx + 3, h * 0.55)], weight=Weight.DETAIL, color_key="line"),
        Stroke(points=[(cx + 20, h * 0.48), (cx + 25, h * 0.48)], weight=Weight.DETAIL, color_key="line"),
        Stroke(points=[(cx + 40, h * 0.40), (cx + 48, h * 0.40)], weight=Weight.DETAIL, color_key="line"),
    ]


def _make_search_rays(w: int, h: int) -> List[Stroke]:
    import math
    cx, cy = w / 2, h / 2 - 40
    strokes = []
    for angle_deg in range(0, 360, 45):
        angle = math.radians(angle_deg)
        r1, r2 = 200, 260
        x1 = cx + r1 * math.cos(angle)
        y1 = cy + r1 * math.sin(angle)
        x2 = cx + r2 * math.cos(angle)
        y2 = cy + r2 * math.sin(angle)
        strokes.append(Stroke(points=[(x1, y1), (x2, y2)], weight=Weight.ENVIRONMENT, color_key="muted"))
    return strokes


_ENV_MAKERS = {
    "flow_vertical": _make_flow_vertical,
    "flow_horizontal": _make_flow_horizontal,
    "dots": _make_dots,
    "desk": _make_desk,
    "thought_bubbles": _make_thought_bubbles,
    "search_rays": _make_search_rays,
    "none": lambda w, h: [],
}


# ═══════════════════════════════════════════════════════════════
# LLM 响应解析
# ═══════════════════════════════════════════════════════════════

def _parse_llm_response(text: str) -> Optional[dict]:
    """解析 LLM JSON 响应"""
    # 提取 JSON
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group())
        except json.JSONDecodeError:
            pass

    return None


def _validate_and_convert(data: dict, canvas_w: int, canvas_h: int) -> SceneLayout:
    """验证 LLM 输出并转换为 SceneLayout"""
    objects = []
    for obj in data.get("objects", []):
        kw = obj.get("keyword", "person")
        # 验证关键词是否在库中
        if kw not in KEYWORD_MAP:
            kw = "person"

        objects.append(SceneObject(
            keyword=kw,
            x=float(obj.get("x", canvas_w / 2)),
            y=float(obj.get("y", canvas_h / 2)),
            scale=float(obj.get("scale", 3.0)),
            delay=len(objects) * 0.15,
        ))

    if not objects:
        objects.append(SceneObject("person", canvas_w / 2 - 100, canvas_h / 2 - 100, 3.0, 0))

    env_type = data.get("environment", "dots")
    env_maker = _ENV_MAKERS.get(env_type, _make_dots)
    environment = env_maker(canvas_w, canvas_h)

    return SceneLayout(title="", objects=objects, environment=environment)


# ═══════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════

def plan_scene_with_llm(
    text: str,
    llm_fn: Callable[[str], str],
    canvas_w: int = 1920,
    canvas_h: int = 1080,
) -> SceneLayout:
    """
    用 LLM 规划单个场景。

    Args:
        text: 一句旁白
        llm_fn: LLM 调用函数 (prompt) -> response
        canvas_w, canvas_h: 画布尺寸

    Returns:
        SceneLayout
    """
    prompt = f"{SCENE_PLANNER_PROMPT}\n\nNarration: {text}"

    try:
        response = llm_fn(prompt)
        data = _parse_llm_response(response)
        if data and data.get("objects"):
            scene = _validate_and_convert(data, canvas_w, canvas_h)
            scene.title = text[:30]
            return scene
    except Exception as e:
        print(f"  LLM 场景规划失败: {e}")

    # 回退：单对象居中
    return SceneLayout(
        title=text[:30],
        objects=[SceneObject("person", canvas_w / 2 - 100, canvas_h / 2 - 100, 3.5, 0)],
        environment=_make_dots(canvas_w, canvas_h),
    )


def texts_to_scenes_with_llm(
    texts: List[str],
    llm_fn: Callable[[str], str],
    canvas_w: int = 1920,
    canvas_h: int = 1080,
) -> List[SceneLayout]:
    """用 LLM 将多句文案分解为多个场景"""
    scenes = []
    for i, text in enumerate(texts):
        print(f"  LLM 规划场景 {i+1}/{len(texts)}: {text[:30]}...")
        scene = plan_scene_with_llm(text, llm_fn, canvas_w, canvas_h)
        scenes.append(scene)
    return scenes


# ═══════════════════════════════════════════════════════════════
# 回退方案（无 LLM 时使用）
# ═══════════════════════════════════════════════════════════════

def plan_scene_fallback(text: str, canvas_w: int = 1920, canvas_h: int = 1080) -> SceneLayout:
    """回退方案：关键词匹配"""
    from core.svg_lineart_library import KEYWORD_MAP

    text_lower = text.lower()
    cx, cy = canvas_w / 2, canvas_h / 2

    # 简单关键词匹配
    found = []
    for kw in ["robot", "laptop", "book", "brain", "database", "city",
                "monitor", "gear", "lightbulb", "person", "magnifying_glass",
                "chat_bubble", "check_mark"]:
        if kw in text_lower:
            found.append(kw)

    if not found:
        found = ["person"]

    # 构建对象
    objects = []
    for i, kw in enumerate(found[:3]):
        x = cx - 150 + i * 200
        y = cy - 100
        objects.append(SceneObject(kw, x, y, 3.0, i * 0.15))

    return SceneLayout(
        title=text[:30],
        objects=objects,
        environment=_make_dots(canvas_w, canvas_h),
    )


def texts_to_scenes_fallback(texts: List[str], canvas_w: int = 1920, canvas_h: int = 1080) -> List[SceneLayout]:
    """回退方案"""
    return [plan_scene_fallback(t, canvas_w, canvas_h) for t in texts]
