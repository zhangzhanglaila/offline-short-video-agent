# -*- coding: utf-8 -*-
"""
Scene Planner v2 — 统一场景区，不是图标排列

核心原则：
1. 整个画面讲同一个故事
2. 元素之间有流动关系
3. 画面利用率 60-80%
4. 有视觉隐喻（工厂、传送带、河流）
5. 有主次之分（主元素70%，辅助30%）
"""

from __future__ import annotations

from typing import List
from core.svg_lineart_library import (
    Illustration, SceneObject, SceneLayout, Stroke, Weight,
    get_illustration,
)


# ═══════════════════════════════════════════════════════════════
# 场景模板 v2 — 统一构图，不是图标排列
# ═══════════════════════════════════════════════════════════════

def _scene_data_to_result(canvas_w: int, canvas_h: int) -> SceneLayout:
    """数据→处理→结果：垂直流动构图"""
    cx = canvas_w / 2
    return SceneLayout(
        title="",
        objects=[
            # 顶部：数据输入
            SceneObject("database", x=cx - 120, y=60, scale=2.4, delay=0),
            # 中部：处理引擎（主角，更大）
            SceneObject("gear", x=cx - 80, y=340, scale=2.8, delay=0.15),
            # 底部：结果输出
            SceneObject("monitor", x=cx - 140, y=600, scale=2.4, delay=0.3),
        ],
        environment=_make_flow_vertical(canvas_w, canvas_h, cx),
    )


def _scene_thinking(canvas_w: int, canvas_h: int) -> SceneLayout:
    """思考场景：人物+大脑+灯泡，垂直流动"""
    cx = canvas_w / 2
    return SceneLayout(
        title="",
        objects=[
            # 人物在左侧偏下
            SceneObject("person_sitting", x=cx - 420, y=200, scale=3.2, delay=0),
            # 大脑在中间（主角，最大）
            SceneObject("brain", x=cx - 120, y=120, scale=3.5, delay=0.1),
            # 灯泡在右上角
            SceneObject("lightbulb", x=cx + 280, y=60, scale=1.8, delay=0.25),
        ],
        environment=_make_thought_flow(canvas_w, canvas_h, cx),
    )


def _scene_agent_working(canvas_w: int, canvas_h: int) -> SceneLayout:
    """Agent工作场景：机器人+电脑+勾选，水平构图"""
    cx = canvas_w / 2
    cy = canvas_h / 2
    return SceneLayout(
        title="",
        objects=[
            # 机器人在左侧（主角）
            SceneObject("robot", x=cx - 420, y=120, scale=3.5, delay=0),
            # 电脑在中间
            SceneObject("laptop", x=cx - 100, y=220, scale=2.8, delay=0.15),
            # 勾选在右侧
            SceneObject("check_mark", x=cx + 300, y=180, scale=1.8, delay=0.3),
        ],
        environment=_make_horizontal_flow(canvas_w, canvas_h, cx, cy),
    )


def _scene_search(canvas_w: int, canvas_h: int) -> SceneLayout:
    """搜索场景：人物+放大镜+发现"""
    cx = canvas_w / 2
    return SceneLayout(
        title="",
        objects=[
            # 人物在左
            SceneObject("person_standing", x=cx - 380, y=120, scale=3.0, delay=0),
            # 放大镜在中间（主角）
            SceneObject("magnifying_glass", x=cx - 100, y=160, scale=3.2, delay=0.1),
            # 勾选在右
            SceneObject("check_mark", x=cx + 280, y=140, scale=1.6, delay=0.25),
        ],
        environment=_make_search_rays(canvas_w, canvas_h, cx),
    )


def _scene_conversation(canvas_w: int, canvas_h: int) -> SceneLayout:
    """对话场景：两人+气泡"""
    cx = canvas_w / 2
    return SceneLayout(
        title="",
        objects=[
            # 左边人物
            SceneObject("person_standing", x=cx - 400, y=140, scale=3.0, delay=0),
            # 对话气泡（主角）
            SceneObject("chat_bubble", x=cx - 100, y=80, scale=3.2, delay=0.1),
            # 右边人物
            SceneObject("person_standing", x=cx + 260, y=140, scale=3.0, delay=0.2),
        ],
        environment=_make_conversation_dots(canvas_w, canvas_h, cx),
    )


def _scene_learning(canvas_w: int, canvas_h: int) -> SceneLayout:
    """学习场景：人物+书本+大脑"""
    cx = canvas_w / 2
    return SceneLayout(
        title="",
        objects=[
            # 人物在左下
            SceneObject("person_sitting", x=cx - 380, y=220, scale=3.0, delay=0),
            # 书本在中间（主角）
            SceneObject("book_open", x=cx - 120, y=160, scale=3.2, delay=0.1),
            # 大脑在右上
            SceneObject("brain", x=cx + 260, y=80, scale=2.4, delay=0.2),
        ],
        environment=_make_knowledge_flow(canvas_w, canvas_h, cx),
    )


def _scene_system(canvas_w: int, canvas_h: int) -> SceneLayout:
    """系统场景：城市天际线"""
    cx = canvas_w / 2
    return SceneLayout(
        title="",
        objects=[
            # 城市占满底部
            SceneObject("city_skyline", x=cx - 400, y=200, scale=5.0, delay=0),
        ],
        environment=_make_city_sky(canvas_w, canvas_h),
    )


def _scene_ai_agent(canvas_w: int, canvas_h: int) -> SceneLayout:
    """AI Agent场景：机器人+大脑+齿轮，垂直流动"""
    cx = canvas_w / 2
    return SceneLayout(
        title="",
        objects=[
            # 机器人在左下
            SceneObject("robot", x=cx - 380, y=200, scale=3.2, delay=0),
            # 大脑在中间（主角）
            SceneObject("brain", x=cx - 100, y=100, scale=3.5, delay=0.12),
            # 齿轮在右侧
            SceneObject("gear", x=cx + 260, y=260, scale=2.0, delay=0.24),
        ],
        environment=_make_ai_flow(canvas_w, canvas_h, cx),
    )


def _scene_single(canvas_w: int, canvas_h: int, keyword: str) -> SceneLayout:
    """单对象大特写"""
    cx = canvas_w / 2
    cy = canvas_h / 2
    return SceneLayout(
        title="",
        objects=[
            SceneObject(keyword, x=cx - 200, y=cy - 200, scale=5.0, delay=0),
        ],
        environment=_make_focus_dots(canvas_w, canvas_h, cx, cy),
    )


# ═══════════════════════════════════════════════════════════════
# 环境元素 — 流动线、数据粒子、连接线
# ═══════════════════════════════════════════════════════════════

def _make_flow_vertical(w: int, h: int, cx: float) -> List[Stroke]:
    """垂直流动线：从上到下的数据流"""
    strokes = []
    # 主流动线
    strokes.append(Stroke(
        points=[(cx, 180), (cx, 300)],
        weight=Weight.ACCENT, color_key="accent",
    ))
    strokes.append(Stroke(
        points=[(cx, 480), (cx, 580)],
        weight=Weight.ACCENT, color_key="accent",
    ))
    # 箭头
    strokes.append(Stroke(
        points=[(cx - 15, 280), (cx, 300), (cx + 15, 280)],
        weight=Weight.ACCENT, color_key="accent",
    ))
    strokes.append(Stroke(
        points=[(cx - 15, 560), (cx, 580), (cx + 15, 560)],
        weight=Weight.ACCENT, color_key="accent",
    ))
    # 侧边装饰线
    strokes.append(Stroke(
        points=[(cx - 200, 100), (cx - 200, 700)],
        weight=Weight.ENVIRONMENT, color_key="muted",
    ))
    strokes.append(Stroke(
        points=[(cx + 200, 100), (cx + 200, 700)],
        weight=Weight.ENVIRONMENT, color_key="muted",
    ))
    # 数据粒子点
    for i in range(6):
        y = 200 + i * 80
        strokes.append(Stroke(
            points=[(cx - 4, y), (cx + 4, y)],
            weight=Weight.ACCENT, color_key="accent",
        ))
    return strokes


def _make_thought_flow(w: int, h: int, cx: float) -> List[Stroke]:
    """思考流动线：从人物→大脑→灯泡"""
    strokes = []
    # 人物到大脑的连接线
    strokes.append(Stroke(
        points=[(cx - 200, 350), (cx - 120, 280), (cx - 80, 200)],
        weight=Weight.DETAIL, color_key="line",
    ))
    # 大脑到灯泡的连接线
    strokes.append(Stroke(
        points=[(cx + 80, 200), (cx + 180, 140), (cx + 260, 100)],
        weight=Weight.DETAIL, color_key="line",
    ))
    # 思考泡泡
    for i, (bx, by) in enumerate([(cx + 40, 300), (cx + 80, 260), (cx + 120, 220)]):
        strokes.append(Stroke(
            points=[(bx, by), (bx + 6, by)],
            weight=Weight.DETAIL, color_key="line",
        ))
    # 底部装饰线
    strokes.append(Stroke(
        points=[(100, h - 60), (w - 100, h - 60)],
        weight=Weight.ENVIRONMENT, color_key="muted",
    ))
    return strokes


def _make_horizontal_flow(w: int, h: int, cx: float, cy: float) -> List[Stroke]:
    """水平流动线：从左到右"""
    strokes = []
    flow_y = cy + 40
    # 主流动线
    strokes.append(Stroke(
        points=[(cx - 250, flow_y), (cx - 50, flow_y)],
        weight=Weight.ACCENT, color_key="accent",
    ))
    strokes.append(Stroke(
        points=[(cx + 100, flow_y), (cx + 250, flow_y)],
        weight=Weight.ACCENT, color_key="accent",
    ))
    # 箭头
    strokes.append(Stroke(
        points=[(cx - 70, flow_y - 12), (cx - 50, flow_y), (cx - 70, flow_y + 12)],
        weight=Weight.ACCENT, color_key="accent",
    ))
    strokes.append(Stroke(
        points=[(cx + 230, flow_y - 12), (cx + 250, flow_y), (cx + 230, flow_y + 12)],
        weight=Weight.ACCENT, color_key="accent",
    ))
    # 背景水平线
    strokes.append(Stroke(
        points=[(80, 60), (w - 80, 60)],
        weight=Weight.ENVIRONMENT, color_key="muted",
    ))
    strokes.append(Stroke(
        points=[(80, h - 60), (w - 80, h - 60)],
        weight=Weight.ENVIRONMENT, color_key="muted",
    ))
    return strokes


def _make_search_rays(w: int, h: int, cx: float) -> List[Stroke]:
    """搜索光线：从放大镜向外放射"""
    strokes = []
    gcx, gcy = cx, 300
    for angle_deg in range(0, 360, 45):
        import math
        angle = math.radians(angle_deg)
        r1, r2 = 180, 240
        x1 = gcx + r1 * math.cos(angle)
        y1 = gcy + r1 * math.sin(angle)
        x2 = gcx + r2 * math.cos(angle)
        y2 = gcy + r2 * math.sin(angle)
        strokes.append(Stroke(
            points=[(x1, y1), (x2, y2)],
            weight=Weight.ENVIRONMENT, color_key="muted",
        ))
    return strokes


def _make_conversation_dots(w: int, h: int, cx: float) -> List[Stroke]:
    """对话装饰点"""
    strokes = []
    for i in range(8):
        x = 100 + i * (w - 200) / 7
        strokes.append(Stroke(
            points=[(x, 40), (x + 3, 40)],
            weight=Weight.ENVIRONMENT, color_key="muted",
        ))
    return strokes


def _make_knowledge_flow(w: int, h: int, cx: float) -> List[Stroke]:
    """知识流动线：书本→大脑"""
    strokes = []
    strokes.append(Stroke(
        points=[(cx + 120, 280), (cx + 180, 200), (cx + 240, 140)],
        weight=Weight.DETAIL, color_key="line",
    ))
    # 底部装饰
    strokes.append(Stroke(
        points=[(100, h - 50), (w - 100, h - 50)],
        weight=Weight.ENVIRONMENT, color_key="muted",
    ))
    return strokes


def _make_city_sky(w: int, h: int) -> List[Stroke]:
    """城市天空装饰"""
    strokes = []
    # 地平线
    strokes.append(Stroke(
        points=[(0, h * 0.85), (w, h * 0.85)],
        weight=Weight.ENVIRONMENT, color_key="muted",
    ))
    return strokes


def _make_ai_flow(w: int, h: int, cx: float) -> List[Stroke]:
    """AI流动线"""
    strokes = []
    # 机器人到大脑
    strokes.append(Stroke(
        points=[(cx - 180, 350), (cx - 100, 250)],
        weight=Weight.DETAIL, color_key="line",
    ))
    # 大脑到齿轮
    strokes.append(Stroke(
        points=[(cx + 80, 250), (cx + 240, 320)],
        weight=Weight.DETAIL, color_key="line",
    ))
    return strokes


def _make_focus_dots(w: int, h: int, cx: float, cy: float) -> List[Stroke]:
    """聚焦装饰点"""
    strokes = []
    import math
    for angle_deg in range(0, 360, 30):
        angle = math.radians(angle_deg)
        r = 350
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        strokes.append(Stroke(
            points=[(x, y), (x + 3, y)],
            weight=Weight.ENVIRONMENT, color_key="muted",
        ))
    return strokes


# ═══════════════════════════════════════════════════════════════
# 模板索引
# ═══════════════════════════════════════════════════════════════

_TEMPLATES = {
    "data_to_result": _scene_data_to_result,
    "thinking": _scene_thinking,
    "agent_working": _scene_agent_working,
    "search": _scene_search,
    "conversation": _scene_conversation,
    "learning": _scene_learning,
    "system": _scene_system,
    "ai_agent": _scene_ai_agent,
    "single": None,  # 动态
}

_CN_EN = {
    "机器人": "robot", "电脑": "laptop", "屏幕": "monitor",
    "书": "book", "脑": "brain", "大脑": "brain",
    "数据库": "database", "城市": "city",
    "齿轮": "gear", "灯": "lightbulb", "灯泡": "lightbulb",
    "人": "person", "搜索": "magnifying_glass",
    "消息": "chat_bubble", "聊天": "chat_bubble",
    "缓存": "database", "数据": "database",
    "agent": "robot", "智能": "brain", "思考": "brain",
    "成功": "check_mark", "完成": "check_mark",
    "工具": "gear", "tool": "gear", "系统": "gear",
    "学习": "book", "知识": "book",
    "信息": "brain", "处理": "gear", "决策": "brain",
}


def _extract_keywords(text: str) -> List[str]:
    text_lower = text.lower()
    found = []

    # 英文关键词（精确匹配单词边界）
    import re
    for kw in ["robot", "laptop", "book", "brain", "database", "city",
                "monitor", "gear", "lightbulb", "person", "magnifying_glass",
                "chat_bubble", "check_mark"]:
        if re.search(r'\b' + kw + r'\b', text_lower) or kw in text_lower:
            if kw not in found:
                found.append(kw)

    # 特殊处理：Agent → robot（不是person）
    if re.search(r'\bagent\b', text_lower) and "robot" not in found:
        found.append("robot")

    # 中文关键词
    for cn, en in _CN_EN.items():
        if cn in text and en not in found:
            found.append(en)

    return found


def _pick_template(keywords: List[str], text: str) -> str:
    kw = set(keywords)

    # 优先匹配：robot + brain → ai_agent（不是 agent_working）
    if "robot" in kw and "brain" in kw:
        return "ai_agent"

    # robot + gear → ai_agent（工具使用）
    if "robot" in kw and "gear" in kw:
        return "ai_agent"

    # robot + laptop/monitor → agent_working
    if "robot" in kw and ("laptop" in kw or "computer" in kw or "monitor" in kw):
        return "agent_working"

    # brain 单独出现 → thinking
    if "brain" in kw:
        return "thinking"

    # person + brain/lightbulb → thinking
    if ("person" in kw) and ("brain" in kw or "lightbulb" in kw):
        return "thinking"

    if "magnifying_glass" in kw:
        return "search"
    if "chat_bubble" in kw:
        return "conversation"
    if "book" in kw:
        return "learning"
    if "city" in kw:
        return "system"

    # database/gear → data_to_result
    if "database" in kw or "gear" in kw:
        return "data_to_result"

    # 中文语义匹配
    if any(w in text for w in ["执行", "工作", "操作", "运行"]):
        return "agent_working"
    if any(w in text for w in ["思考", "想", "分析", "理解", "处理", "决策"]):
        return "thinking"
    if any(w in text for w in ["搜索", "查找", "发现"]):
        return "search"
    if any(w in text for w in ["数据", "存储", "缓存"]):
        return "data_to_result"
    if any(w in text for w in ["学习", "知识", "读"]):
        return "learning"

    return "single"


# ═══════════════════════════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════════════════════════

def plan_scene(text: str, canvas_w: int = 1920, canvas_h: int = 1080) -> SceneLayout:
    """将一句旁白分解为场景布局"""
    keywords = _extract_keywords(text)
    template_name = _pick_template(keywords, text)

    if template_name == "single":
        kw = keywords[0] if keywords else "person"
        scene = _scene_single(canvas_w, canvas_h, kw)
    else:
        scene = _TEMPLATES[template_name](canvas_w, canvas_h)

    scene.title = text[:30]
    return scene


def texts_to_scenes(texts: List[str], canvas_w: int = 1920, canvas_h: int = 1080) -> List[SceneLayout]:
    """将多句文案分解为多个场景"""
    return [plan_scene(t, canvas_w, canvas_h) for t in texts]
