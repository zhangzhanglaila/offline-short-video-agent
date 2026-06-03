# -*- coding: utf-8 -*-
"""
Scene Planner v4 — 箭头跟随对象位置

核心改动：
- 环境元素根据对象实际位置动态生成
- 箭头从一个对象指向另一个对象
- 流动线表达真实的语义关系
"""

from __future__ import annotations

import json
import math
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
5. Define FLOW connections between objects (which flows into which)
6. Describe the visual metaphor

Output JSON:
{
  "objects": [
    {"keyword": "database", "x": 400, "y": 300, "scale": 3.0},
    {"keyword": "brain", "x": 900, "y": 200, "scale": 4.0},
    {"keyword": "monitor", "x": 1400, "y": 300, "scale": 3.0}
  ],
  "flows": [
    {"from": 0, "to": 1, "label": "data"},
    {"from": 1, "to": 2, "label": "result"}
  ],
  "metaphor": "data flows into brain, results appear on screen"
}

IMPORTANT:
- "flows" defines the arrows between objects (from object index to object index)
- Flows should follow the logical order of the narration
- Do NOT add random decorative arrows
"""


# ═══════════════════════════════════════════════════════════════
# 根据对象位置生成连接线
# ═══════════════════════════════════════════════════════════════

def _make_flow_between_objects(
    obj1: SceneObject,
    obj2: SceneObject,
    art1_width: float = 100,
    art1_height: float = 100,
    art2_width: float = 100,
    art2_height: float = 100,
) -> List[Stroke]:
    """
    在两个对象之间生成连接箭头。
    箭头从 obj1 的右边缘指向 obj2 的左边缘。
    """
    # 计算 obj1 的右边缘中心
    x1 = obj1.x + art1_width * obj1.scale
    y1 = obj1.y + (art1_height * obj1.scale) / 2

    # 计算 obj2 的左边缘中心
    x2 = obj2.x
    y2 = obj2.y + (art2_height * obj2.scale) / 2

    # 中间点（用于曲线）
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2

    strokes = []

    # 连接线（带一点弧度）
    strokes.append(Stroke(
        points=[(x1, y1), (mid_x, mid_y - 20), (x2, y2)],
        weight=Weight.ACCENT,
        color_key="accent",
    ))

    # 箭头头部
    angle = math.atan2(y2 - (mid_y - 20), x2 - mid_x)
    head_size = 15
    hx1 = x2 - head_size * math.cos(angle - 0.4)
    hy1 = y2 - head_size * math.sin(angle - 0.4)
    hx2 = x2 - head_size * math.cos(angle + 0.4)
    hy2 = y2 - head_size * math.sin(angle + 0.4)

    strokes.append(Stroke(
        points=[(hx1, hy1), (x2, y2), (hx2, hy2)],
        weight=Weight.ACCENT,
        color_key="accent",
    ))

    return strokes


def _make_environment_for_objects(
    objects: List[SceneObject],
    flows: List[dict],
    canvas_w: int,
    canvas_h: int,
) -> List[Stroke]:
    """根据对象位置和流动关系生成环境元素"""
    strokes = []

    # 根据 flows 生成连接线
    for flow in flows:
        from_idx = flow.get("from", 0)
        to_idx = flow.get("to", 1)

        if 0 <= from_idx < len(objects) and 0 <= to_idx < len(objects):
            obj1 = objects[from_idx]
            obj2 = objects[to_idx]

            # 获取插画尺寸
            art1 = get_illustration(obj1.keyword)
            art2 = get_illustration(obj2.keyword)

            flow_strokes = _make_flow_between_objects(
                obj1, obj2,
                art1.width, art1.height,
                art2.width, art2.height,
            )
            strokes.extend(flow_strokes)

    # 添加底部装饰线（轻量级）
    strokes.append(Stroke(
        points=[(80, canvas_h - 50), (canvas_w - 80, canvas_h - 50)],
        weight=Weight.ENVIRONMENT,
        color_key="muted",
    ))

    return strokes


# ═══════════════════════════════════════════════════════════════
# LLM 响应解析
# ═══════════════════════════════════════════════════════════════

def _parse_llm_response(text: str) -> Optional[dict]:
    """解析 LLM JSON 响应"""
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

    # 获取流动关系
    flows = data.get("flows", [])

    # 如果没有定义 flows，自动生成（按顺序连接）
    if not flows and len(objects) > 1:
        for i in range(len(objects) - 1):
            flows.append({"from": i, "to": i + 1})

    # 根据对象位置和流动关系生成环境元素
    environment = _make_environment_for_objects(objects, flows, canvas_w, canvas_h)

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
    """用 LLM 规划单个场景"""
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

    # 回退
    return _fallback_scene(text, canvas_w, canvas_h)


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
# 回退方案
# ═══════════════════════════════════════════════════════════════

def _fallback_scene(text: str, canvas_w: int, canvas_h: int) -> SceneLayout:
    """回退方案：关键词匹配 + 自动连线"""
    text_lower = text.lower()
    cx, cy = canvas_w / 2, canvas_h / 2

    found = []
    for kw in ["robot", "laptop", "book", "brain", "database", "city",
                "monitor", "gear", "lightbulb", "person", "magnifying_glass",
                "chat_bubble", "check_mark"]:
        if kw in text_lower:
            found.append(kw)

    if not found:
        found = ["person"]

    # 构建对象（水平排列）
    objects = []
    n = len(found)
    total_w = n * 300
    start_x = cx - total_w / 2

    for i, kw in enumerate(found):
        x = start_x + i * 300
        y = cy - 100
        objects.append(SceneObject(kw, x, y, 3.0, i * 0.15))

    # 自动生成连接线
    flows = [{"from": i, "to": i + 1} for i in range(n - 1)]
    environment = _make_environment_for_objects(objects, flows, canvas_w, canvas_h)

    return SceneLayout(title=text[:30], objects=objects, environment=environment)


def texts_to_scenes_fallback(texts: List[str], canvas_w: int = 1920, canvas_h: int = 1080) -> List[SceneLayout]:
    """回退方案"""
    return [_fallback_scene(t, canvas_w, canvas_h) for t in texts]
