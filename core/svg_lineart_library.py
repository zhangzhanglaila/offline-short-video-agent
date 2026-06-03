# -*- coding: utf-8 -*-
"""
Continuous Line Art Library — 贝塞尔连续曲线插画

核心原则：
1. 连续曲线，不是矩形拼接
2. 线宽分层：outline(4px) / detail(2px) / accent(5px) / env(1px)
3. 每个对象是一条或几条流畅的 path
4. 手绘感，不是 CAD 图

每条 path 是贝塞尔控制点序列，渲染时用 Catmull-Rom 或直接连线平滑。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
import math


# ═══════════════════════════════════════════════════════════════
# 线宽层级
# ═══════════════════════════════════════════════════════════════

class Weight:
    """线宽层级"""
    OUTLINE = 4       # 主体轮廓
    DETAIL = 2        # 内部细节
    ACCENT = 5        # 强调元素
    ENVIRONMENT = 1   # 环境/装饰


# ═══════════════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════════════

@dataclass
class Stroke:
    """一条连续笔触"""
    points: List[Tuple[float, float]]  # 控制点 (归一化 0-100)
    weight: int = Weight.OUTLINE        # 线宽层级
    closed: bool = False
    color_key: str = "line"             # line / accent / muted

    def length(self) -> float:
        total = 0.0
        for i in range(1, len(self.points)):
            dx = self.points[i][0] - self.points[i-1][0]
            dy = self.points[i][1] - self.points[i-1][1]
            total += math.sqrt(dx * dx + dy * dy)
        return total


@dataclass
class Illustration:
    """一幅完整插画"""
    name: str
    strokes: List[Stroke]
    width: float = 100
    height: float = 100


@dataclass
class SceneObject:
    """场景中的一个对象"""
    keyword: str              # 插画关键词
    x: float = 0             # 画布上的 x 位置
    y: float = 0             # 画布上的 y 位置
    scale: float = 1.0       # 缩放
    delay: float = 0         # 动画延迟 (0-1)


@dataclass
class SceneLayout:
    """一个场景的完整布局"""
    title: str
    objects: List[SceneObject]
    environment: List[Stroke] = field(default_factory=list)  # 环境元素


# ═══════════════════════════════════════════════════════════════
# 贝塞尔工具
# ═══════════════════════════════════════════════════════════════

def _smooth_points(raw: List[Tuple[float, float]], segments: int = 8) -> List[Tuple[float, float]]:
    """将控制点序列插值为平滑曲线（Catmull-Rom 样条）"""
    if len(raw) < 2:
        return raw

    result = []
    for i in range(len(raw) - 1):
        p0 = raw[max(0, i - 1)]
        p1 = raw[i]
        p2 = raw[min(len(raw) - 1, i + 1)]
        p3 = raw[min(len(raw) - 1, i + 2)]

        for t_i in range(segments):
            t = t_i / segments
            t2 = t * t
            t3 = t2 * t

            x = 0.5 * (
                (2 * p1[0]) +
                (-p0[0] + p2[0]) * t +
                (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            y = 0.5 * (
                (2 * p1[1]) +
                (-p0[1] + p2[1]) * t +
                (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            result.append((x, y))

    result.append(raw[-1])
    return result


def _to_canvas(points: List[Tuple[float, float]], ox: float, oy: float, scale: float) -> List[Tuple[float, float]]:
    """归一化坐标 → 画布坐标"""
    return [(ox + x * scale, oy + y * scale) for x, y in points]


# ═══════════════════════════════════════════════════════════════
# 插画定义 — 用连续曲线手绘
# ═══════════════════════════════════════════════════════════════

# ── 人物：连续曲线画出坐姿 ────────────────────────────────

PERSON_SITTING = Illustration(
    name="person_sitting",
    strokes=[
        # 头（圆润的椭圆，一条线完成）
        Stroke(points=[
            (44, 12), (38, 14), (34, 18), (32, 24),
            (34, 30), (38, 34), (44, 36), (50, 36),
            (56, 34), (60, 30), (62, 24), (60, 18),
            (56, 14), (50, 12), (44, 12),
        ], weight=Weight.OUTLINE, closed=True),
        # 头发（几笔飘逸的线条）
        Stroke(points=[(36, 16), (32, 12), (38, 8), (46, 6), (54, 8), (60, 12), (58, 16)], weight=Weight.DETAIL),
        # 左眼
        Stroke(points=[(40, 22), (42, 20), (44, 22), (42, 24), (40, 22)], weight=Weight.DETAIL, closed=True),
        # 右眼
        Stroke(points=[(50, 22), (52, 20), (54, 22), (52, 24), (50, 22)], weight=Weight.DETAIL, closed=True),
        # 微笑
        Stroke(points=[(44, 28), (47, 30), (50, 28)], weight=Weight.DETAIL),
        # 身体躯干（一条流畅的线）
        Stroke(points=[(46, 36), (44, 42), (42, 50), (42, 58), (44, 64)], weight=Weight.OUTLINE),
        Stroke(points=[(54, 36), (56, 42), (58, 50), (58, 58), (56, 64)], weight=Weight.OUTLINE),
        # 左臂（自然弯曲）
        Stroke(points=[(44, 42), (36, 48), (30, 56), (28, 62)], weight=Weight.OUTLINE),
        # 右臂（拿着东西的姿势）
        Stroke(points=[(56, 42), (64, 46), (70, 52), (72, 58)], weight=Weight.OUTLINE),
        # 左腿
        Stroke(points=[(44, 64), (40, 72), (38, 80), (36, 86)], weight=Weight.OUTLINE),
        # 右腿
        Stroke(points=[(56, 64), (60, 72), (62, 80), (64, 86)], weight=Weight.OUTLINE),
        # 鞋子
        Stroke(points=[(32, 86), (36, 86), (40, 88)], weight=Weight.DETAIL),
        Stroke(points=[(60, 86), (64, 86), (68, 88)], weight=Weight.DETAIL),
    ],
)

PERSON_STANDING = Illustration(
    name="person_standing",
    strokes=[
        # 头
        Stroke(points=[
            (44, 8), (38, 10), (34, 14), (32, 20),
            (34, 26), (38, 30), (44, 32), (50, 32),
            (56, 30), (60, 26), (62, 20), (60, 14),
            (56, 10), (50, 8), (44, 8),
        ], weight=Weight.OUTLINE, closed=True),
        # 头发
        Stroke(points=[(36, 12), (34, 8), (40, 4), (50, 2), (60, 4), (64, 10), (60, 12)], weight=Weight.DETAIL),
        # 眼睛
        Stroke(points=[(40, 18), (42, 16), (44, 18)], weight=Weight.DETAIL),
        Stroke(points=[(52, 18), (54, 16), (56, 18)], weight=Weight.DETAIL),
        # 嘴
        Stroke(points=[(46, 24), (50, 26), (54, 24)], weight=Weight.DETAIL),
        # 脖子
        Stroke(points=[(47, 32), (47, 36)], weight=Weight.DETAIL),
        Stroke(points=[(53, 32), (53, 36)], weight=Weight.DETAIL),
        # 身体（衬衫轮廓）
        Stroke(points=[
            (47, 36), (40, 40), (36, 48), (34, 56), (36, 62), (40, 66),
        ], weight=Weight.OUTLINE),
        Stroke(points=[
            (53, 36), (60, 40), (64, 48), (66, 56), (64, 62), (60, 66),
        ], weight=Weight.OUTLINE),
        # 左臂
        Stroke(points=[(40, 40), (32, 50), (28, 60), (26, 68)], weight=Weight.OUTLINE),
        # 右臂
        Stroke(points=[(60, 40), (68, 50), (72, 60), (74, 68)], weight=Weight.OUTLINE),
        # 手
        Stroke(points=[(24, 68), (26, 70), (28, 68)], weight=Weight.DETAIL),
        Stroke(points=[(72, 68), (74, 70), (76, 68)], weight=Weight.DETAIL),
        # 裤子
        Stroke(points=[(40, 66), (38, 76), (36, 86), (34, 94)], weight=Weight.OUTLINE),
        Stroke(points=[(60, 66), (62, 76), (64, 86), (66, 94)], weight=Weight.OUTLINE),
        # 腰带
        Stroke(points=[(40, 66), (50, 68), (60, 66)], weight=Weight.DETAIL),
        # 鞋
        Stroke(points=[(30, 94), (34, 94), (38, 96)], weight=Weight.DETAIL),
        Stroke(points=[(62, 94), (66, 94), (70, 96)], weight=Weight.DETAIL),
    ],
)

PERSON_POINTING = Illustration(
    name="person_pointing",
    strokes=[
        # 头
        Stroke(points=[
            (38, 10), (32, 12), (28, 18), (28, 24),
            (30, 30), (36, 34), (42, 34), (48, 32),
            (52, 26), (52, 20), (50, 14), (44, 10), (38, 10),
        ], weight=Weight.OUTLINE, closed=True),
        # 眼睛（看向右边）
        Stroke(points=[(36, 20), (38, 18), (40, 20)], weight=Weight.DETAIL),
        Stroke(points=[(44, 20), (46, 18), (48, 20)], weight=Weight.DETAIL),
        # 嘴
        Stroke(points=[(38, 26), (42, 28)], weight=Weight.DETAIL),
        # 身体
        Stroke(points=[(38, 34), (36, 42), (34, 52), (36, 60)], weight=Weight.OUTLINE),
        Stroke(points=[(48, 34), (50, 42), (52, 52), (50, 60)], weight=Weight.OUTLINE),
        # 左臂（指向右边，一条流畅的线）
        Stroke(points=[(36, 40), (42, 38), (52, 34), (64, 30), (76, 28), (84, 26)], weight=Weight.OUTLINE),
        # 手指
        Stroke(points=[(84, 26), (90, 24)], weight=Weight.ACCENT),
        Stroke(points=[(84, 26), (88, 28)], weight=Weight.DETAIL),
        # 右臂
        Stroke(points=[(50, 40), (54, 48), (52, 56)], weight=Weight.OUTLINE),
        # 腿
        Stroke(points=[(36, 60), (34, 72), (32, 84)], weight=Weight.OUTLINE),
        Stroke(points=[(50, 60), (54, 72), (56, 84)], weight=Weight.OUTLINE),
    ],
)

# ── 电脑/笔记本 ──────────────────────────────────────────

LAPTOP = Illustration(
    name="laptop",
    strokes=[
        # 屏幕（一条线画出梯形）
        Stroke(points=[
            (18, 12), (14, 14), (12, 18), (12, 52),
            (14, 56), (86, 56), (88, 52), (88, 18),
            (86, 14), (82, 12), (18, 12),
        ], weight=Weight.OUTLINE, closed=True),
        # 屏幕内边框
        Stroke(points=[
            (16, 16), (16, 50), (84, 50), (84, 16), (16, 16),
        ], weight=Weight.DETAIL, closed=True),
        # 屏幕内容：代码行（流畅的波浪线表示文字）
        Stroke(points=[(22, 24), (38, 24), (42, 22), (48, 24), (56, 24)], weight=Weight.DETAIL),
        Stroke(points=[(26, 30), (44, 30), (50, 30), (60, 30)], weight=Weight.DETAIL),
        Stroke(points=[(22, 36), (32, 36), (38, 36), (52, 36)], weight=Weight.DETAIL),
        Stroke(points=[(26, 42), (50, 42), (56, 42)], weight=Weight.DETAIL),
        Stroke(points=[(22, 48), (40, 48)], weight=Weight.DETAIL),
        # 光标（闪烁）
        Stroke(points=[(42, 48), (42, 50)], weight=Weight.ACCENT, color_key="accent"),
        # 键盘底座
        Stroke(points=[
            (8, 56), (92, 56), (88, 68), (86, 72),
            (14, 72), (12, 68), (8, 56),
        ], weight=Weight.OUTLINE, closed=True),
        # 键盘行
        Stroke(points=[(18, 60), (82, 60)], weight=Weight.DETAIL),
        Stroke(points=[(20, 64), (80, 64)], weight=Weight.DETAIL),
        Stroke(points=[(22, 68), (78, 68)], weight=Weight.DETAIL),
        # 触控板
        Stroke(points=[
            (40, 72), (60, 72), (60, 78), (40, 78), (40, 72),
        ], weight=Weight.DETAIL, closed=True),
    ],
)

# ── 书本（打开的） ──────────────────────────────────────

BOOK_OPEN = Illustration(
    name="book_open",
    strokes=[
        # 左页（一条流畅的曲线）
        Stroke(points=[
            (50, 18), (46, 16), (38, 14), (28, 12), (18, 12),
            (12, 14), (10, 18), (10, 78), (12, 82), (18, 84),
            (28, 84), (38, 84), (46, 82), (50, 80),
        ], weight=Weight.OUTLINE),
        # 右页
        Stroke(points=[
            (50, 18), (54, 16), (62, 14), (72, 12), (82, 12),
            (88, 14), (90, 18), (90, 78), (88, 82), (82, 84),
            (72, 84), (62, 84), (54, 82), (50, 80),
        ], weight=Weight.OUTLINE),
        # 书脊
        Stroke(points=[(50, 18), (50, 80)], weight=Weight.ACCENT),
        # 左页文字行
        Stroke(points=[(18, 26), (42, 26)], weight=Weight.DETAIL),
        Stroke(points=[(18, 34), (44, 34)], weight=Weight.DETAIL),
        Stroke(points=[(18, 42), (40, 42)], weight=Weight.DETAIL),
        Stroke(points=[(18, 50), (44, 50)], weight=Weight.DETAIL),
        Stroke(points=[(18, 58), (36, 58)], weight=Weight.DETAIL),
        # 右页文字行
        Stroke(points=[(56, 26), (82, 26)], weight=Weight.DETAIL),
        Stroke(points=[(56, 34), (80, 34)], weight=Weight.DETAIL),
        Stroke(points=[(56, 42), (84, 42)], weight=Weight.DETAIL),
        Stroke(points=[(56, 50), (78, 50)], weight=Weight.DETAIL),
        # 右页小图
        Stroke(points=[
            (60, 58), (78, 58), (78, 72), (60, 72), (60, 58),
        ], weight=Weight.DETAIL, closed=True),
    ],
)

# ── 电脑屏幕（显示器） ──────────────────────────────────

MONITOR = Illustration(
    name="monitor",
    strokes=[
        # 屏幕外框（圆角矩形，一条线）
        Stroke(points=[
            (15, 8), (12, 10), (10, 14), (10, 56),
            (12, 60), (88, 60), (90, 56), (90, 14),
            (88, 10), (85, 8), (15, 8),
        ], weight=Weight.OUTLINE, closed=True),
        # 屏幕
        Stroke(points=[
            (14, 12), (14, 54), (86, 54), (86, 12), (14, 12),
        ], weight=Weight.DETAIL, closed=True),
        # 屏幕内容：图表
        Stroke(points=[(20, 48), (20, 24), (24, 20)], weight=Weight.DETAIL),
        Stroke(points=[(24, 48), (24, 30), (28, 26)], weight=Weight.DETAIL),
        Stroke(points=[(28, 48), (28, 22), (32, 18)], weight=Weight.DETAIL),
        Stroke(points=[(32, 48), (32, 34), (36, 30)], weight=Weight.DETAIL),
        # 上升箭头
        Stroke(points=[(40, 44), (52, 32), (60, 28), (72, 20)], weight=Weight.ACCENT, color_key="accent"),
        # 箭头头
        Stroke(points=[(68, 18), (74, 20), (70, 24)], weight=Weight.ACCENT, color_key="accent"),
        # 支架
        Stroke(points=[(42, 60), (42, 72), (36, 76)], weight=Weight.OUTLINE),
        Stroke(points=[(58, 60), (58, 72), (64, 76)], weight=Weight.OUTLINE),
        # 底座
        Stroke(points=[(30, 76), (70, 76)], weight=Weight.OUTLINE),
        Stroke(points=[(32, 76), (28, 80), (72, 80), (68, 76)], weight=Weight.DETAIL),
    ],
)

# ── 机器人（可爱的，不是方块） ──────────────────────────

ROBOT = Illustration(
    name="robot",
    strokes=[
        # 天线
        Stroke(points=[(50, 4), (50, 14)], weight=Weight.DETAIL),
        # 天线头
        Stroke(points=[
            (46, 4), (50, 0), (54, 4), (50, 8), (46, 4),
        ], weight=Weight.ACCENT, closed=True, color_key="accent"),
        # 头（圆润）
        Stroke(points=[
            (32, 14), (28, 18), (26, 24), (26, 32),
            (28, 38), (32, 42), (38, 44), (50, 44),
            (62, 44), (68, 42), (72, 38), (74, 32),
            (74, 24), (72, 18), (68, 14), (62, 12),
            (50, 12), (38, 12), (32, 14),
        ], weight=Weight.OUTLINE, closed=True),
        # 眼睛（大而圆）
        Stroke(points=[
            (36, 22), (32, 24), (30, 28), (32, 32),
            (36, 34), (40, 32), (42, 28), (40, 24), (36, 22),
        ], weight=Weight.OUTLINE, closed=True),
        Stroke(points=[
            (58, 22), (54, 24), (52, 28), (54, 32),
            (58, 34), (62, 32), (64, 28), (62, 24), (58, 22),
        ], weight=Weight.OUTLINE, closed=True),
        # 瞳孔
        Stroke(points=[(36, 28), (38, 26)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(58, 28), (60, 26)], weight=Weight.ACCENT, color_key="accent"),
        # 嘴巴（微笑的弧线）
        Stroke(points=[(40, 38), (44, 40), (50, 42), (56, 40), (60, 38)], weight=Weight.DETAIL),
        # 身体
        Stroke(points=[
            (30, 46), (26, 50), (24, 58), (24, 70),
            (26, 76), (30, 80), (70, 80), (74, 76),
            (76, 70), (76, 58), (74, 50), (70, 46), (30, 46),
        ], weight=Weight.OUTLINE, closed=True),
        # 胸部面板
        Stroke(points=[
            (38, 52), (62, 52), (62, 68), (38, 68), (38, 52),
        ], weight=Weight.DETAIL, closed=True),
        # 心脏指示灯
        Stroke(points=[
            (46, 56), (50, 52), (54, 56), (50, 62), (46, 56),
        ], weight=Weight.ACCENT, closed=True, color_key="accent"),
        # 按钮
        Stroke(points=[(42, 64), (46, 64)], weight=Weight.DETAIL),
        Stroke(points=[(50, 64), (58, 64)], weight=Weight.DETAIL),
        # 左臂
        Stroke(points=[(24, 52), (16, 58), (12, 66), (10, 74)], weight=Weight.OUTLINE),
        # 右臂
        Stroke(points=[(76, 52), (84, 58), (88, 66), (90, 74)], weight=Weight.OUTLINE),
        # 手
        Stroke(points=[(8, 74), (10, 76), (12, 74)], weight=Weight.DETAIL),
        Stroke(points=[(88, 74), (90, 76), (92, 74)], weight=Weight.DETAIL),
        # 左腿
        Stroke(points=[(36, 80), (34, 88), (32, 94)], weight=Weight.OUTLINE),
        # 右腿
        Stroke(points=[(64, 80), (66, 88), (68, 94)], weight=Weight.OUTLINE),
        # 脚
        Stroke(points=[(28, 94), (32, 94), (36, 96)], weight=Weight.DETAIL),
        Stroke(points=[(64, 94), (68, 94), (72, 96)], weight=Weight.DETAIL),
    ],
)

# ── 大脑 ──────────────────────────────────────────────

BRAIN = Illustration(
    name="brain",
    strokes=[
        # 外轮廓（一条连续的波浪线）
        Stroke(points=[
            (48, 12), (40, 10), (32, 14), (24, 20),
            (18, 28), (14, 38), (14, 50), (16, 60),
            (22, 70), (30, 76), (40, 80), (48, 82),
            (56, 80), (66, 76), (74, 70), (80, 60),
            (82, 50), (82, 38), (78, 28), (72, 20),
            (64, 14), (56, 10), (48, 12),
        ], weight=Weight.OUTLINE, closed=True),
        # 中间沟回
        Stroke(points=[(48, 12), (46, 24), (48, 38), (44, 52), (48, 66), (48, 82)], weight=Weight.ACCENT),
        # 左脑褶皱
        Stroke(points=[(28, 28), (34, 36), (28, 46)], weight=Weight.DETAIL),
        Stroke(points=[(22, 48), (30, 56), (24, 64)], weight=Weight.DETAIL),
        # 右脑褶皱
        Stroke(points=[(68, 28), (62, 36), (68, 46)], weight=Weight.DETAIL),
        Stroke(points=[(74, 48), (66, 56), (72, 64)], weight=Weight.DETAIL),
        # 底部脑干
        Stroke(points=[(42, 82), (48, 90), (54, 82)], weight=Weight.DETAIL),
        # 神经突触（小点）
        Stroke(points=[(34, 32), (36, 34)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(62, 32), (64, 34)], weight=Weight.ACCENT, color_key="accent"),
    ],
)

# ── 数据库 ──────────────────────────────────────────────

DATABASE = Illustration(
    name="database",
    strokes=[
        # 顶部椭圆
        Stroke(points=[
            (20, 18), (26, 12), (36, 8), (50, 6),
            (64, 8), (74, 12), (80, 18), (74, 24),
            (64, 28), (50, 30), (36, 28), (26, 24), (20, 18),
        ], weight=Weight.OUTLINE, closed=True),
        # 侧面线
        Stroke(points=[(20, 18), (20, 72)], weight=Weight.OUTLINE),
        Stroke(points=[(80, 18), (80, 72)], weight=Weight.OUTLINE),
        # 底部椭圆
        Stroke(points=[
            (20, 72), (26, 78), (36, 82), (50, 84),
            (64, 82), (74, 78), (80, 72), (74, 66),
            (64, 62), (50, 60), (36, 62), (26, 66), (20, 72),
        ], weight=Weight.OUTLINE, closed=True),
        # 中间分隔线
        Stroke(points=[
            (20, 40), (26, 46), (36, 50), (50, 52),
            (64, 50), (74, 46), (80, 40),
        ], weight=Weight.DETAIL),
        # 数据条目
        Stroke(points=[(30, 34), (60, 34)], weight=Weight.DETAIL),
        Stroke(points=[(34, 38), (56, 38)], weight=Weight.DETAIL),
        Stroke(points=[(30, 48), (62, 48)], weight=Weight.DETAIL),
        # 锁图标（安全）
        Stroke(points=[
            (44, 56), (44, 64), (56, 64), (56, 56),
            (52, 54), (48, 54), (44, 56),
        ], weight=Weight.ACCENT, closed=True, color_key="accent"),
    ],
)

# ── 灯泡 ──────────────────────────────────────────────

LIGHTBULB = Illustration(
    name="lightbulb",
    strokes=[
        # 灯泡外形（一条流畅的曲线）
        Stroke(points=[
            (50, 8), (42, 10), (34, 16), (28, 24),
            (24, 34), (22, 44), (24, 54), (28, 62),
            (34, 68), (36, 74), (36, 80), (64, 80),
            (64, 74), (66, 68), (72, 62), (76, 54),
            (78, 44), (76, 34), (72, 24), (66, 16),
            (58, 10), (50, 8),
        ], weight=Weight.OUTLINE, closed=True),
        # 灯丝
        Stroke(points=[(40, 52), (44, 42), (48, 52), (52, 42), (56, 52)], weight=Weight.ACCENT, color_key="accent"),
        # 底座螺纹
        Stroke(points=[(36, 80), (64, 80)], weight=Weight.DETAIL),
        Stroke(points=[(38, 84), (62, 84)], weight=Weight.DETAIL),
        Stroke(points=[(40, 88), (60, 88)], weight=Weight.DETAIL),
        Stroke(points=[(44, 92), (56, 92)], weight=Weight.DETAIL),
        # 光线（放射状短线条）
        Stroke(points=[(50, 2), (50, 6)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(20, 18), (24, 22)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(76, 18), (80, 22)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(14, 44), (18, 44)], weight=Weight.ACCENT, color_key="accent"),
        Stroke(points=[(82, 44), (86, 44)], weight=Weight.ACCENT, color_key="accent"),
    ],
)

# ── 齿轮 ──────────────────────────────────────────────

GEAR = Illustration(
    name="gear",
    strokes=[
        # 外齿（一条连续的波浪线）
        Stroke(points=[
            (50, 6), (54, 8), (56, 4), (60, 8), (62, 12),
            (66, 10), (70, 14), (68, 18), (72, 22), (76, 24),
            (78, 28), (76, 32), (80, 36), (82, 42), (78, 46),
            (80, 50), (82, 56), (78, 60), (76, 64), (78, 68),
            (74, 72), (70, 70), (68, 74), (64, 72), (60, 76),
            (56, 74), (54, 78), (50, 76), (46, 78), (44, 74),
            (40, 76), (36, 72), (32, 74), (28, 70), (26, 74),
            (22, 70), (20, 64), (18, 60), (20, 56), (18, 50),
            (20, 46), (18, 42), (20, 36), (22, 32), (20, 28),
            (22, 24), (26, 22), (28, 18), (26, 14), (30, 10),
            (34, 12), (36, 8), (40, 4), (44, 8), (46, 6), (50, 6),
        ], weight=Weight.OUTLINE, closed=True),
        # 内圆
        Stroke(points=[
            (42, 36), (38, 40), (36, 46), (38, 52),
            (42, 56), (50, 58), (58, 56), (62, 52),
            (64, 46), (62, 40), (58, 36), (50, 34), (42, 36),
        ], weight=Weight.DETAIL, closed=True),
        # 中心孔
        Stroke(points=[
            (46, 44), (50, 42), (54, 44), (54, 48),
            (50, 50), (46, 48), (46, 44),
        ], weight=Weight.ACCENT, closed=True),
    ],
)

# ── 对话气泡 ──────────────────────────────────────────

CHAT_BUBBLE = Illustration(
    name="chat_bubble",
    strokes=[
        # 气泡外形
        Stroke(points=[
            (10, 12), (8, 14), (6, 18), (6, 48),
            (8, 52), (12, 54), (50, 54), (54, 56),
            (48, 64), (44, 68), (48, 62), (54, 58),
            (56, 54), (88, 54), (92, 52), (94, 48),
            (94, 18), (92, 14), (88, 12), (10, 12),
        ], weight=Weight.OUTLINE, closed=True),
        # 文字行
        Stroke(points=[(18, 24), (50, 24)], weight=Weight.DETAIL),
        Stroke(points=[(18, 32), (62, 32)], weight=Weight.DETAIL),
        Stroke(points=[(18, 40), (44, 40)], weight=Weight.DETAIL),
    ],
)

# ── 放大镜 ──────────────────────────────────────────

MAGNIFYING_GLASS = Illustration(
    name="magnifying_glass",
    strokes=[
        # 镜片圆
        Stroke(points=[
            (38, 16), (30, 18), (24, 24), (20, 32),
            (18, 42), (20, 52), (24, 60), (30, 66),
            (38, 68), (48, 68), (56, 66), (62, 60),
            (66, 52), (68, 42), (66, 32), (62, 24),
            (56, 18), (48, 16), (38, 16),
        ], weight=Weight.OUTLINE, closed=True),
        # 镜片反光
        Stroke(points=[(32, 26), (36, 22), (42, 20)], weight=Weight.DETAIL),
        # 手柄
        Stroke(points=[(64, 64), (70, 70), (76, 76), (80, 82)], weight=Weight.OUTLINE),
        # 手柄握把
        Stroke(points=[(76, 78), (82, 84), (86, 80), (80, 74)], weight=Weight.DETAIL),
    ],
)

# ── 城市天际线 ──────────────────────────────────────────

CITY_SKYLINE = Illustration(
    name="city_skyline",
    strokes=[
        # 建筑群（一条连续的天际线）
        Stroke(points=[
            (2, 92), (2, 60), (8, 58), (8, 45), (12, 44),
            (12, 35), (16, 34), (16, 55), (22, 54),
            (22, 28), (26, 26), (26, 20), (30, 18),
            (34, 20), (34, 45), (38, 44), (38, 55),
            (44, 54), (44, 38), (48, 36), (48, 28),
            (50, 24), (52, 22), (54, 24), (56, 28),
            (56, 36), (60, 38), (60, 50), (64, 48),
            (64, 32), (68, 30), (68, 22), (70, 18),
            (72, 16), (74, 18), (74, 40), (78, 42),
            (78, 55), (82, 54), (82, 42), (86, 40),
            (86, 50), (90, 52), (90, 65), (94, 64),
            (94, 55), (98, 54), (98, 92),
        ], weight=Weight.OUTLINE),
        # 地面线
        Stroke(points=[(0, 92), (100, 92)], weight=Weight.ACCENT),
        # 窗户（小点）
        Stroke(points=[(10, 48), (12, 48)], weight=Weight.ENVIRONMENT),
        Stroke(points=[(10, 52), (12, 52)], weight=Weight.ENVIRONMENT),
        Stroke(points=[(24, 32), (26, 32)], weight=Weight.ENVIRONMENT),
        Stroke(points=[(24, 36), (26, 36)], weight=Weight.ENVIRONMENT),
        Stroke(points=[(46, 42), (48, 42)], weight=Weight.ENVIRONMENT),
        Stroke(points=[(46, 46), (48, 46)], weight=Weight.ENVIRONMENT),
        Stroke(points=[(66, 34), (68, 34)], weight=Weight.ENVIRONMENT),
        Stroke(points=[(66, 38), (68, 38)], weight=Weight.ENVIRONMENT),
        # 月亮
        Stroke(points=[
            (84, 8), (88, 6), (92, 8), (94, 12),
            (94, 16), (92, 20), (88, 22), (84, 20),
            (82, 16), (82, 12), (84, 8),
        ], weight=Weight.DETAIL, closed=True),
    ],
)

# ── 云 ──────────────────────────────────────────────

CLOUD = Illustration(
    name="cloud",
    strokes=[
        Stroke(points=[
            (22, 58), (16, 54), (14, 46), (18, 38),
            (24, 32), (28, 24), (36, 20), (46, 18),
            (56, 20), (64, 24), (70, 32), (76, 36),
            (82, 38), (86, 46), (84, 54), (78, 58),
            (22, 58),
        ], weight=Weight.OUTLINE, closed=True),
    ],
)

# ── 勾选 ──────────────────────────────────────────────

CHECK_MARK = Illustration(
    name="check_mark",
    strokes=[
        Stroke(points=[(12, 48), (36, 72), (88, 20)], weight=Weight.ACCENT, color_key="accent"),
    ],
)

# ── 箭头 ──────────────────────────────────────────────

ARROW_RIGHT = Illustration(
    name="arrow_right",
    strokes=[
        Stroke(points=[(8, 50), (78, 50)], weight=Weight.ACCENT),
        Stroke(points=[(68, 36), (88, 50), (68, 64)], weight=Weight.ACCENT),
    ],
)

ARROW_DOWN = Illustration(
    name="arrow_down",
    strokes=[
        Stroke(points=[(50, 8), (50, 72)], weight=Weight.ACCENT),
        Stroke(points=[(36, 62), (50, 82), (64, 62)], weight=Weight.ACCENT),
    ],
)


# ═══════════════════════════════════════════════════════════════
# 关键词索引
# ═══════════════════════════════════════════════════════════════

KEYWORD_MAP = {
    # 人物
    "person": PERSON_STANDING, "people": PERSON_STANDING, "user": PERSON_STANDING,
    "person_sitting": PERSON_SITTING, "sitting": PERSON_SITTING,
    "person_standing": PERSON_STANDING,
    "pointing": PERSON_POINTING, "person_pointing": PERSON_POINTING,
    "thinking": PERSON_SITTING, "agent": PERSON_SITTING,

    # 科技
    "laptop": LAPTOP, "computer": LAPTOP, "code": LAPTOP, "programming": LAPTOP,
    "monitor": MONITOR, "screen": MONITOR, "display": MONITOR,
    "server": DATABASE, "database": DATABASE, "redis": DATABASE, "cache": DATABASE, "data": DATABASE,
    "cloud": CLOUD, "network": CLOUD,

    # 书本
    "book": BOOK_OPEN, "reading": BOOK_OPEN, "study": BOOK_OPEN,
    "learning": BOOK_OPEN, "knowledge": BOOK_OPEN,

    # 城市
    "city": CITY_SKYLINE, "building": CITY_SKYLINE, "skyline": CITY_SKYLINE,

    # AI/机器人
    "robot": ROBOT, "ai": ROBOT, "machine": ROBOT, "bot": ROBOT,
    "brain": BRAIN, "mind": BRAIN, "think": BRAIN, "thought": BRAIN,
    "idea": LIGHTBULB, "lightbulb": LIGHTBULB, "creative": LIGHTBULB, "insight": LIGHTBULB,
    "gear": GEAR, "tool": GEAR, "system": GEAR, "config": GEAR, "settings": GEAR,

    # 符号
    "arrow": ARROW_RIGHT, "arrow_right": ARROW_RIGHT, "arrow_down": ARROW_DOWN,
    "check": CHECK_MARK, "success": CHECK_MARK, "done": CHECK_MARK, "complete": CHECK_MARK,
    "chat": CHAT_BUBBLE, "message": CHAT_BUBBLE, "talk": CHAT_BUBBLE,
    "search": MAGNIFYING_GLASS, "find": MAGNIFYING_GLASS, "look": MAGNIFYING_GLASS,
}


def get_illustration(keyword: str) -> Illustration:
    kw = keyword.lower().strip().replace(" ", "_")
    return KEYWORD_MAP.get(kw, PERSON_STANDING)
