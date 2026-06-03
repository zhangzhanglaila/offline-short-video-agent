# -*- coding: utf-8 -*-
"""
Scene Planner — 文案 → 场景分解

不要单独画一个"机器人"，而是画"机器人在操作电脑，屏幕显示任务完成"。

输入：一句旁白
输出：SceneLayout（objects + environment + title）
"""

from __future__ import annotations

import re
from typing import List, Optional

from core.svg_lineart_library import (
    Illustration, SceneObject, SceneLayout, Stroke, Weight,
    get_illustration, PERSON_SITTING, LAPTOP, CHECK_MARK,
)


# ═══════════════════════════════════════════════════════════════
# 场景模板
# ═══════════════════════════════════════════════════════════════

# 每个模板定义：objects 的相对位置 + 环境元素
# 坐标是相对于画布中心的偏移（像素）

SCENE_TEMPLATES = {
    # 人物 + 电脑 + 任务完成
    "robot_working": {
        "objects": [
            {"keyword": "robot", "x": -350, "y": 100, "scale": 2.8},
            {"keyword": "laptop", "x": 80, "y": 180, "scale": 2.2},
            {"keyword": "check_mark", "x": 320, "y": 80, "scale": 1.2},
        ],
        "env": "desk",
    },
    # 人物思考
    "person_thinking": {
        "objects": [
            {"keyword": "person_sitting", "x": -200, "y": 80, "scale": 2.8},
            {"keyword": "brain", "x": 180, "y": 40, "scale": 2.0},
            {"keyword": "lightbulb", "x": 350, "y": -40, "scale": 1.0},
        ],
        "env": "thought_bubbles",
    },
    # 搜索发现
    "search_found": {
        "objects": [
            {"keyword": "person_standing", "x": -300, "y": 60, "scale": 2.6},
            {"keyword": "magnifying_glass", "x": 20, "y": 100, "scale": 2.2},
            {"keyword": "check_mark", "x": 300, "y": 60, "scale": 1.4},
        ],
        "env": "dots",
    },
    # 数据处理
    "data_processing": {
        "objects": [
            {"keyword": "database", "x": -300, "y": 80, "scale": 2.4},
            {"keyword": "gear", "x": 0, "y": 60, "scale": 1.8},
            {"keyword": "monitor", "x": 280, "y": 60, "scale": 2.2},
        ],
        "env": "flow_lines",
    },
    # 对话交流
    "conversation": {
        "objects": [
            {"keyword": "person_standing", "x": -300, "y": 80, "scale": 2.6},
            {"keyword": "chat_bubble", "x": 40, "y": 20, "scale": 2.0},
            {"keyword": "person_standing", "x": 300, "y": 80, "scale": 2.6},
        ],
        "env": "dots",
    },
    # 书本学习
    "learning": {
        "objects": [
            {"keyword": "person_sitting", "x": -200, "y": 80, "scale": 2.6},
            {"keyword": "book_open", "x": 120, "y": 120, "scale": 2.4},
            {"keyword": "brain", "x": 350, "y": 20, "scale": 1.6},
        ],
        "env": "desk",
    },
    # 城市/系统
    "system_overview": {
        "objects": [
            {"keyword": "city_skyline", "x": 0, "y": 120, "scale": 3.5},
        ],
        "env": "dots",
    },
    # 机器人 + 大脑
    "ai_agent": {
        "objects": [
            {"keyword": "robot", "x": -250, "y": 80, "scale": 2.8},
            {"keyword": "brain", "x": 100, "y": 40, "scale": 2.2},
            {"keyword": "gear", "x": 340, "y": 80, "scale": 1.6},
        ],
        "env": "flow_lines",
    },
    # 单对象特写
    "single": {
        "objects": [],  # 动态填充
        "env": "dots",
    },
}


# ═══════════════════════════════════════════════════════════════
# 环境元素生成
# ═══════════════════════════════════════════════════════════════

def _make_desk(canvas_w: int, canvas_h: int) -> List[Stroke]:
    """桌面环境"""
    desk_y = canvas_h * 0.72
    return [
        # 桌面线
        Stroke(
            points=[(canvas_w * 0.05, desk_y), (canvas_w * 0.95, desk_y)],
            weight=Weight.ENVIRONMENT, color_key="line",
        ),
        # 桌面阴影
        Stroke(
            points=[(canvas_w * 0.08, desk_y + 8), (canvas_w * 0.92, desk_y + 8)],
            weight=Weight.ENVIRONMENT, color_key="muted",
        ),
    ]


def _make_dots(canvas_w: int, canvas_h: int) -> List[Stroke]:
    """散点装饰"""
    import random
    dots = []
    for _ in range(12):
        x = random.randint(40, canvas_w - 40)
        y = random.randint(40, canvas_h - 120)
        dots.append(Stroke(
            points=[(x, y), (x + 2, y)],
            weight=Weight.ENVIRONMENT, color_key="muted",
        ))
    return dots


def _make_flow_lines(canvas_w: int, canvas_h: int) -> List[Stroke]:
    """流动的装饰线"""
    return [
        Stroke(
            points=[(canvas_w * 0.1, canvas_h * 0.15), (canvas_w * 0.9, canvas_h * 0.15)],
            weight=Weight.ENVIRONMENT, color_key="muted",
        ),
        Stroke(
            points=[(canvas_w * 0.1, canvas_h * 0.85), (canvas_w * 0.9, canvas_h * 0.85)],
            weight=Weight.ENVIRONMENT, color_key="muted",
        ),
    ]


def _make_thought_bubbles(canvas_w: int, canvas_h: int) -> List[Stroke]:
    """思考泡泡装饰"""
    return [
        # 小圆点
        Stroke(points=[(canvas_w * 0.75, canvas_h * 0.55), (canvas_w * 0.75 + 3, canvas_h * 0.55)],
               weight=Weight.DETAIL, color_key="line"),
        Stroke(points=[(canvas_w * 0.78, canvas_h * 0.50), (canvas_w * 0.78 + 5, canvas_h * 0.50)],
               weight=Weight.DETAIL, color_key="line"),
        Stroke(points=[(canvas_w * 0.82, canvas_h * 0.44), (canvas_w * 0.82 + 8, canvas_h * 0.44)],
               weight=Weight.DETAIL, color_key="line"),
    ]


_ENV_MAKERS = {
    "desk": _make_desk,
    "dots": _make_dots,
    "flow_lines": _make_flow_lines,
    "thought_bubbles": _make_thought_bubbles,
}


# ═══════════════════════════════════════════════════════════════
# 关键词提取
# ═══════════════════════════════════════════════════════════════

_CN_EN = {
    "机器人": "robot", "电脑": "laptop", "计算机": "computer", "屏幕": "monitor",
    "书": "book", "脑": "brain", "大脑": "brain", "服务器": "server",
    "数据库": "database", "城市": "city", "建筑": "city", "云": "cloud",
    "齿轮": "gear", "灯": "lightbulb", "灯泡": "lightbulb",
    "人": "person", "搜索": "magnifying_glass", "放大镜": "magnifying_glass",
    "消息": "chat_bubble", "聊天": "chat_bubble", "对话": "chat_bubble",
    "缓存": "database", "redis": "database", "数据": "database",
    "agent": "robot", "智能": "brain", "思考": "brain", "想法": "lightbulb",
    "成功": "check_mark", "完成": "check_mark", "任务": "check_mark",
    "工具": "gear", "系统": "gear", "配置": "gear",
    "学习": "book", "知识": "book", "读书": "book",
}

_KEYWORD_PRIORITY = [
    "robot", "laptop", "computer", "book", "brain", "server",
    "database", "city", "monitor", "cloud", "gear", "lightbulb",
    "person", "person_sitting", "magnifying_glass", "chat_bubble",
    "check_mark", "arrow",
]


def _extract_keywords(text: str) -> List[str]:
    """从文案中提取视觉关键词"""
    text_lower = text.lower()
    found = []

    # 英文关键词
    for kw in _KEYWORD_PRIORITY:
        if kw in text_lower and kw not in found:
            found.append(kw)

    # 中文关键词
    for cn, en in _CN_EN.items():
        if cn in text and en not in found:
            found.append(en)

    return found


def _pick_template(keywords: List[str], text: str) -> str:
    """根据关键词选择场景模板"""
    kw_set = set(keywords)

    # 包含 robot + laptop → robot_working
    if "robot" in kw_set and ("laptop" in kw_set or "computer" in kw_set or "monitor" in kw_set):
        return "robot_working"

    # 包含 person + brain/lightbulb → person_thinking
    if ("person" in kw_set or "person_sitting" in kw_set) and ("brain" in kw_set or "lightbulb" in kw_set):
        return "person_thinking"

    # 包含 search/find → search_found
    if "magnifying_glass" in kw_set:
        return "search_found"

    # 包含 database + gear → data_processing
    if "database" in kw_set and "gear" in kw_set:
        return "data_processing"

    # 包含 chat → conversation
    if "chat_bubble" in kw_set:
        return "conversation"

    # 包含 book → learning
    if "book" in kw_set:
        return "learning"

    # 包含 city → system_overview
    if "city" in kw_set:
        return "system_overview"

    # 包含 robot + brain → ai_agent
    if "robot" in kw_set and "brain" in kw_set:
        return "ai_agent"

    # 中文匹配
    if any(w in text for w in ["执行", "工作", "操作", "运行"]):
        return "robot_working"
    if any(w in text for w in ["思考", "想", "分析", "理解"]):
        return "person_thinking"
    if any(w in text for w in ["搜索", "查找", "发现"]):
        return "search_found"
    if any(w in text for w in ["数据", "处理", "存储", "缓存"]):
        return "data_processing"
    if any(w in text for w in ["说", "讲", "告诉", "对话"]):
        return "conversation"
    if any(w in text for w in ["学习", "知识", "读"]):
        return "learning"

    return "single"


# ═══════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════

def plan_scene(
    text: str,
    canvas_w: int = 1920,
    canvas_h: int = 1080,
) -> SceneLayout:
    """
    将一句旁白分解为场景布局。

    1. 提取关键词
    2. 选择场景模板
    3. 放置对象
    4. 生成环境

    Returns:
        SceneLayout(title, objects, environment)
    """
    keywords = _extract_keywords(text)
    template_name = _pick_template(keywords, text)
    template = SCENE_TEMPLATES[template_name]

    # 画布中心
    cx, cy = canvas_w / 2, canvas_h / 2 - 40

    # 构建对象列表
    objects = []
    if template_name == "single":
        # 单对象居中
        kw = keywords[0] if keywords else "person"
        objects.append(SceneObject(keyword=kw, x=cx - 100, y=cy - 80, scale=3.5, delay=0))
    else:
        for i, obj_def in enumerate(template["objects"]):
            objects.append(SceneObject(
                keyword=obj_def["keyword"],
                x=cx + obj_def["x"],
                y=cy + obj_def["y"],
                scale=obj_def["scale"],
                delay=i * 0.2,
            ))

    # 生成环境
    env_type = template.get("env", "dots")
    env_maker = _ENV_MAKERS.get(env_type, _make_dots)
    environment = env_maker(canvas_w, canvas_h)

    return SceneLayout(
        title=text[:30],
        objects=objects,
        environment=environment,
    )


def texts_to_scenes(
    texts: List[str],
    canvas_w: int = 1920,
    canvas_h: int = 1080,
) -> List[SceneLayout]:
    """将多句文案分解为多个场景"""
    return [plan_scene(t, canvas_w, canvas_h) for t in texts]
