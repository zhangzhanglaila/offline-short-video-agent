# -*- coding: utf-8 -*-
"""
Visual Director — 视觉导演层

不是"画什么图标"，而是"用什么画面讲故事"。

核心职责：
1. 选择视觉隐喻（工厂/旅程/生长/对比）
2. 确定主次关系（主角70% + 辅助30%）
3. 定义对象关系（流动/包含/序列）
4. 填充画布（60-80%利用率）
5. 添加动态连接（流动线/粒子）

输入：一句旁白
输出：完整的场景描述（不是图标列表）
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional


# ═══════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════

class VisualMetaphor:
    """视觉隐喻类型"""
    FACTORY = "factory"          # 工厂流水线
    JOURNEY = "journey"          # 旅程/路径
    GROWTH = "growth"            # 生长/发芽
    CONTAINER = "container"      # 容器/框架
    TRANSFORMATION = "transform" # A变成B
    ECOSYSTEM = "ecosystem"      # 生态系统


@dataclass
class SceneElement:
    """场景中的一个视觉元素"""
    name: str                     # 元素标识
    role: str                     # hero / support / background / connector
    shape: str                    # rect / circle / path / text / flow_line
    x: float                      # 归一化位置 (0-1)
    y: float                      # 归一化位置 (0-1)
    w: float = 0                  # 归一化宽度
    h: float = 0                  # 归一化高度
    label: str = ""               # 文字标签
    weight: int = 3               # 线宽
    color_key: str = "line"       # line / accent / muted
    draw_order: int = 0           # 绘制顺序
    animation: str = "draw"       # draw / flow / pulse / grow
    children: List['SceneElement'] = field(default_factory=list)


@dataclass
class FlowConnection:
    """两个元素之间的流动连接"""
    from_name: str
    to_name: str
    style: str = "straight"       # straight / curved / zigzag
    animated: bool = True         # 是否有流动动画
    points: List[Tuple[float, float]] = field(default_factory=list)  # 控制点


@dataclass
class SceneComposition:
    """完整的场景构图"""
    title: str
    metaphor: str
    elements: List[SceneElement]
    connections: List[FlowConnection]
    background_strokes: List[Tuple[float, float, float, float]] = field(default_factory=list)  # (x1,y1,x2,y2) 装饰线
    canvas_utilization: float = 0.7  # 目标画布利用率


# ═══════════════════════════════════════════════════════════════
# 视觉隐喻库
# ═══════════════════════════════════════════════════════════════

def _factory_scene(
    hero_name: str,
    hero_label: str,
    inputs: List[Tuple[str, str]],
    outputs: List[Tuple[str, str]],
    canvas_w: float = 1920,
    canvas_h: float = 1080,
) -> SceneComposition:
    """
    工厂隐喻：数据流入 → 处理 → 结果流出

    布局：
    ┌────────────────────────────────────────┐
    │                                        │
    │   [Input1]  ──→  ┌────────┐  ──→ [Output1] │
    │   [Input2]  ──→  │  HERO  │  ──→ [Output2] │
    │   [Input3]  ──→  └────────┘  ──→ [Output3] │
    │                    ↑ 处理中               │
    │              ⚙️ ⚙️ ⚙️                    │
    │                                        │
    └────────────────────────────────────────┘
    """
    elements = []
    connections = []

    # Hero 元素（居中，占大比例）
    hero_x, hero_y = 0.4, 0.35
    hero_w, hero_h = 0.22, 0.3
    elements.append(SceneElement(
        name=hero_name, role="hero", shape="rect",
        x=hero_x, y=hero_y, w=hero_w, h=hero_h,
        label=hero_label, weight=4, color_key="line",
        draw_order=5,
    ))

    # 输入元素（左侧）
    input_x = 0.08
    for i, (iname, ilabel) in enumerate(inputs):
        iy = 0.2 + i * 0.25
        elements.append(SceneElement(
            name=iname, role="support", shape="rect",
            x=input_x, y=iy, w=0.14, h=0.12,
            label=ilabel, weight=3, color_key="line",
            draw_order=2,
        ))
        connections.append(FlowConnection(
            from_name=iname, to_name=hero_name,
            style="straight", animated=True,
        ))

    # 输出元素（右侧）
    output_x = 0.78
    for i, (oname, olabel) in enumerate(outputs):
        oy = 0.2 + i * 0.25
        elements.append(SceneElement(
            name=oname, role="support", shape="rect",
            x=output_x, y=oy, w=0.14, h=0.12,
            label=olabel, weight=3, color_key="line",
            draw_order=2,
        ))
        connections.append(FlowConnection(
            from_name=hero_name, to_name=oname,
            style="straight", animated=True,
        ))

    # 处理齿轮（hero下方）
    for i in range(3):
        elements.append(SceneElement(
            name=f"gear_{i}", role="background", shape="circle",
            x=0.35 + i * 0.1, y=0.72, w=0.06, h=0.06,
            weight=2, color_key="accent",
            draw_order=1, animation="spin",
        ))

    # 装饰线
    bg_strokes = [
        (0.05, 0.85, 0.95, 0.85),  # 底部水平线
        (0.05, 0.1, 0.95, 0.1),    # 顶部水平线
    ]

    return SceneComposition(
        title="", metaphor=VisualMetaphor.FACTORY,
        elements=elements, connections=connections,
        background_strokes=bg_strokes,
    )


def _flow_scene(
    hero_name: str,
    hero_label: str,
    steps: List[Tuple[str, str]],
    canvas_w: float = 1920,
    canvas_h: float = 1080,
) -> SceneComposition:
    """
    流程隐喻：A → B → C 的视觉旅程

    布局：
    ┌────────────────────────────────────────┐
    │                                        │
    │   ┌────┐    ┌────┐    ┌────┐    ┌────┐ │
    │   │ A  │ →  │ B  │ →  │ C  │ →  │ D  │ │
    │   └────┘    └────┘    └────┘    └────┘ │
    │                                        │
    │         流动的连接线贯穿全图            │
    │                                        │
    └────────────────────────────────────────┘
    """
    elements = []
    connections = []

    n = len(steps) + 1  # +1 for hero
    step_w = 0.8 / (n + 1)
    start_x = 0.1

    # Hero 在中间位置
    hero_idx = len(steps) // 2
    for i, (sname, slabel) in enumerate(steps):
        sx = start_x + i * step_w
        is_hero = (i == hero_idx)
        elements.append(SceneElement(
            name=sname, role="hero" if is_hero else "support",
            shape="rect",
            x=sx, y=0.35, w=step_w * 0.8, h=0.2,
            label=slabel,
            weight=4 if is_hero else 3,
            color_key="line",
            draw_order=5 if is_hero else 2,
        ))
        if i > 0:
            connections.append(FlowConnection(
                from_name=steps[i-1][0], to_name=sname,
                style="straight", animated=True,
            ))

    # 背景流动线
    bg_strokes = [
        (0.05, 0.65, 0.95, 0.65),
    ]

    return SceneComposition(
        title="", metaphor=VisualMetaphor.JOURNEY,
        elements=elements, connections=connections,
        background_strokes=bg_strokes,
    )


def _growth_scene(
    hero_name: str,
    hero_label: str,
    stages: List[Tuple[str, str]],
    canvas_w: float = 1920,
    canvas_h: float = 1080,
) -> SceneComposition:
    """
    生长隐喻：从种子到大树

    布局：
    ┌────────────────────────────────────────┐
    │              ┌────┐                    │
    │              │结果│ ← 成熟              │
    │              └────┘                    │
    │                ↑                       │
    │           ┌────┐                       │
    │           │成长│ ← 发展                │
    │           └────┘                       │
    │                ↑                       │
    │           ┌────┐                       │
    │           │种子│ ← 起点                │
    │           └────┘                       │
    └────────────────────────────────────────┘
    """
    elements = []
    connections = []

    n = len(stages) + 1
    step_h = 0.7 / (n + 1)
    center_x = 0.35

    for i, (sname, slabel) in enumerate(stages):
        sy = 0.15 + i * step_h
        is_hero = (i == len(stages) // 2)
        elements.append(SceneElement(
            name=sname, role="hero" if is_hero else "support",
            shape="rect",
            x=center_x, y=sy, w=0.2, h=0.1,
            label=slabel,
            weight=4 if is_hero else 3,
            color_key="line",
            draw_order=5 if is_hero else 2,
        ))
        if i > 0:
            connections.append(FlowConnection(
                from_name=stages[i-1][0], to_name=sname,
                style="curved", animated=True,
            ))

    # 右侧装饰：成长曲线
    elements.append(SceneElement(
        name="growth_curve", role="background", shape="path",
        x=0.7, y=0.2, w=0.2, h=0.6,
        weight=2, color_key="accent",
        draw_order=1, animation="draw",
    ))

    return SceneComposition(
        title="", metaphor=VisualMetaphor.GROWTH,
        elements=elements, connections=connections,
    )


def _transformation_scene(
    before_name: str,
    before_label: str,
    after_name: str,
    after_label: str,
    canvas_w: float = 1920,
    canvas_h: float = 1080,
) -> SceneComposition:
    """
    转变隐喻：A 变成 B

    布局：
    ┌────────────────────────────────────────┐
    │                                        │
    │   ┌──────┐    ═══════>    ┌──────┐    │
    │   │ 之前 │    转变过程    │ 之后 │    │
    │   └──────┘               └──────┘    │
    │                                        │
    │        中间：粒子/光线/变形动画        │
    │                                        │
    └────────────────────────────────────────┘
    """
    elements = []
    connections = []

    # 之前
    elements.append(SceneElement(
        name=before_name, role="support", shape="rect",
        x=0.1, y=0.3, w=0.2, h=0.25,
        label=before_label, weight=3, color_key="line",
        draw_order=2,
    ))

    # 之后（hero）
    elements.append(SceneElement(
        name=after_name, role="hero", shape="rect",
        x=0.7, y=0.3, w=0.2, h=0.25,
        label=after_label, weight=4, color_key="accent",
        draw_order=5,
    ))

    # 转变连接
    connections.append(FlowConnection(
        from_name=before_name, to_name=after_name,
        style="curved", animated=True,
    ))

    # 转变过程装饰
    for i in range(5):
        elements.append(SceneElement(
            name=f"particle_{i}", role="background", shape="circle",
            x=0.35 + i * 0.06, y=0.42, w=0.03, h=0.03,
            weight=2, color_key="accent",
            draw_order=1, animation="pulse",
        ))

    return SceneComposition(
        title="", metaphor=VisualMetaphor.TRANSFORMATION,
        elements=elements, connections=connections,
    )


def _ecosystem_scene(
    center_name: str,
    center_label: str,
    surrounding: List[Tuple[str, str]],
    canvas_w: float = 1920,
    canvas_h: float = 1080,
) -> SceneComposition:
    """
    生态隐喻：中心节点 + 周围连接

    布局：
    ┌────────────────────────────────────────┐
    │         [A]        [B]                 │
    │            ↘      ↙                    │
    │              [中心]                     │
    │            ↗      ↘                    │
    │         [C]        [D]                 │
    │                                        │
    └────────────────────────────────────────┘
    """
    elements = []
    connections = []

    # 中心
    elements.append(SceneElement(
        name=center_name, role="hero", shape="circle",
        x=0.4, y=0.35, w=0.2, h=0.2,
        label=center_label, weight=4, color_key="line",
        draw_order=5,
    ))

    # 周围节点
    n = len(surrounding)
    radius = 0.25
    cx, cy = 0.5, 0.45
    for i, (sname, slabel) in enumerate(surrounding):
        angle = (2 * math.pi * i) / n - math.pi / 2
        sx = cx + radius * math.cos(angle)
        sy = cy + radius * math.sin(angle)
        elements.append(SceneElement(
            name=sname, role="support", shape="rect",
            x=sx - 0.07, y=sy - 0.05, w=0.14, h=0.1,
            label=slabel, weight=3, color_key="line",
            draw_order=2,
        ))
        connections.append(FlowConnection(
            from_name=center_name, to_name=sname,
            style="curved", animated=True,
        ))

    return SceneComposition(
        title="", metaphor=VisualMetaphor.ECOSYSTEM,
        elements=elements, connections=connections,
    )


# ═══════════════════════════════════════════════════════════════
# 文案分析 → 隐喻选择
# ═══════════════════════════════════════════════════════════════

def _analyze_text(text: str) -> Dict:
    """分析文案，提取语义结构"""
    text_lower = text.lower()

    result = {
        "metaphor": VisualMetaphor.FACTORY,
        "hero_keyword": "brain",
        "hero_label": "处理",
        "inputs": [],
        "outputs": [],
        "steps": [],
        "action": "process",
    }

    # 检测动作类型
    if any(w in text for w in ["→", "->", "然后", "接着", "首先", "最后", "流程", "步骤"]):
        result["metaphor"] = VisualMetaphor.JOURNEY
        result["action"] = "sequence"
    elif any(w in text for w in ["变成", "转换", "转化", "成为", "从...到", "升级"]):
        result["metaphor"] = VisualMetaphor.TRANSFORMATION
        result["action"] = "transform"
    elif any(w in text for w in ["生长", "发展", "成长", "进化", "萌芽", "开花"]):
        result["metaphor"] = VisualMetaphor.GROWTH
        result["action"] = "grow"
    elif any(w in text for w in ["连接", "网络", "关系", "生态", "系统", "包括", "组成"]):
        result["metaphor"] = VisualMetaphor.ECOSYSTEM
        result["action"] = "connect"
    elif any(w in text for w in ["处理", "分析", "计算", "执行", "运行", "调用", "使用"]):
        result["metaphor"] = VisualMetaphor.FACTORY
        result["action"] = "process"

    # 提取关键词
    keyword_map = {
        "agent": ("robot", "Agent"),
        "robot": ("robot", "机器人"),
        "brain": ("brain", "大脑"),
        "数据库": ("database", "数据库"),
        "database": ("database", "Database"),
        "redis": ("database", "Redis"),
        "缓存": ("database", "缓存"),
        "data": ("database", "数据"),
        "电脑": ("laptop", "电脑"),
        "laptop": ("laptop", "电脑"),
        "computer": ("laptop", "电脑"),
        "monitor": ("monitor", "屏幕"),
        "屏幕": ("monitor", "屏幕"),
        "book": ("book", "书本"),
        "书": ("book", "书本"),
        "知识": ("book", "知识"),
        "city": ("city", "城市"),
        "城市": ("city", "城市"),
        "tool": ("gear", "工具"),
        "工具": ("gear", "工具"),
        "gear": ("gear", "齿轮"),
        "齿轮": ("gear", "齿轮"),
        "idea": ("lightbulb", "想法"),
        "想法": ("lightbulb", "想法"),
        "搜索": ("magnifying_glass", "搜索"),
        "search": ("magnifying_glass", "搜索"),
        "消息": ("chat_bubble", "消息"),
        "chat": ("chat_bubble", "消息"),
        "成功": ("check_mark", "成功"),
        "完成": ("check_mark", "完成"),
        "result": ("check_mark", "结果"),
        "结果": ("check_mark", "结果"),
    }

    found_keywords = []
    for kw, (shape, label) in keyword_map.items():
        if kw in text_lower:
            found_keywords.append((shape, label))

    if found_keywords:
        result["hero_keyword"] = found_keywords[0][0]
        result["hero_label"] = found_keywords[0][1]

    # 构建输入/输出/步骤
    if result["metaphor"] == VisualMetaphor.FACTORY:
        # 输入：前半部分关键词
        # 输出：后半部分关键词
        if len(found_keywords) >= 3:
            result["inputs"] = [(found_keywords[0][0], found_keywords[0][1])]
            result["hero_keyword"] = found_keywords[1][0]
            result["hero_label"] = found_keywords[1][1]
            result["outputs"] = [(found_keywords[2][0], found_keywords[2][1])]
        elif len(found_keywords) == 2:
            result["inputs"] = [(found_keywords[0][0], found_keywords[0][1])]
            result["outputs"] = [(found_keywords[1][0], found_keywords[1][1])]

    elif result["metaphor"] == VisualMetaphor.JOURNEY:
        result["steps"] = [(kw, label) for kw, label in found_keywords]

    elif result["metaphor"] == VisualMetaphor.ECOSYSTEM:
        if found_keywords:
            result["hero_keyword"] = found_keywords[0][0]
            result["hero_label"] = found_keywords[0][1]
            result["surrounding"] = [(kw, label) for kw, label in found_keywords[1:]]

    return result


# ═══════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════

def direct_scene(
    text: str,
    canvas_w: float = 1920,
    canvas_h: float = 1080,
) -> SceneComposition:
    """
    视觉导演：将一句旁白转化为完整的场景构图。

    不是"画什么图标"，而是"用什么画面讲故事"。
    """
    analysis = _analyze_text(text)

    metaphor = analysis["metaphor"]
    hero_kw = analysis["hero_keyword"]
    hero_label = analysis["hero_label"]

    if metaphor == VisualMetaphor.FACTORY:
        scene = _factory_scene(
            hero_kw, hero_label,
            analysis.get("inputs", [("database", "数据")]),
            analysis.get("outputs", [("check_mark", "结果")]),
            canvas_w, canvas_h,
        )
    elif metaphor == VisualMetaphor.JOURNEY:
        steps = analysis.get("steps", [("database", "数据"), ("gear", "处理"), ("check_mark", "结果")])
        scene = _flow_scene(hero_kw, hero_label, steps, canvas_w, canvas_h)
    elif metaphor == VisualMetaphor.GROWTH:
        stages = analysis.get("steps", [("database", "种子"), ("gear", "成长"), ("check_mark", "结果")])
        scene = _growth_scene(hero_kw, hero_label, stages, canvas_w, canvas_h)
    elif metaphor == VisualMetaphor.TRANSFORMATION:
        scene = _transformation_scene(
            "database", "数据输入",
            hero_kw, hero_label,
            canvas_w, canvas_h,
        )
    elif metaphor == VisualMetaphor.ECOSYSTEM:
        surrounding = analysis.get("surrounding", [("laptop", "电脑"), ("database", "数据"), ("gear", "工具")])
        scene = _ecosystem_scene(hero_kw, hero_label, surrounding, canvas_w, canvas_h)
    else:
        scene = _factory_scene(hero_kw, hero_label, [("database", "数据")], [("check_mark", "结果")], canvas_w, canvas_h)

    scene.title = text[:30]
    return scene


def direct_scenes(
    texts: List[str],
    canvas_w: float = 1920,
    canvas_h: float = 1080,
) -> List[SceneComposition]:
    """将多句旁白转化为多个场景"""
    return [direct_scene(t, canvas_w, canvas_h) for t in texts]
