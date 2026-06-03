# -*- coding: utf-8 -*-
"""
SVG Line Art Library — 预定义线条插画素材

每个元素是一组 SVG path，用 strokeDashoffset 动画实现手绘效果。
所有坐标归一化到 0-100 的画布，渲染时按需缩放。

核心动画原理：
  strokeDasharray = pathLength
  strokeDashoffset = pathLength → 0
  效果 = 线条逐步绘制
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import math


@dataclass
class PathData:
    """一条 SVG path 的数据"""
    points: List[Tuple[float, float]]  # 归一化坐标 (0-100)
    closed: bool = False               # 是否闭合
    label: str = ""                    # 用途标签

    def to_pil_points(self, ox: float, oy: float, scale: float) -> List[Tuple[float, float]]:
        """转换为 PIL 绘制坐标"""
        return [(ox + x * scale, oy + y * scale) for x, y in self.points]


@dataclass
class LineArt:
    """一幅线条插画，由多条 path 组成"""
    name: str
    paths: List[PathData]
    width: float = 100    # 归一化宽度
    height: float = 100   # 归一化高度


# ═══════════════════════════════════════════════════════════════
# 人物
# ═══════════════════════════════════════════════════════════════

PERSON_STANDING = LineArt(
    name="person_standing",
    paths=[
        # 头（圆）
        PathData(points=[
            (42, 8), (38, 10), (36, 14), (36, 18), (38, 22),
            (42, 24), (48, 24), (52, 22), (54, 18), (54, 14),
            (52, 10), (48, 8), (42, 8),
        ], closed=True, label="head"),
        # 身体
        PathData(points=[(45, 24), (45, 52)], label="body"),
        # 左臂
        PathData(points=[(45, 30), (30, 44)], label="left_arm"),
        # 右臂
        PathData(points=[(45, 30), (60, 44)], label="right_arm"),
        # 左腿
        PathData(points=[(45, 52), (32, 80)], label="left_leg"),
        # 右腿
        PathData(points=[(45, 52), (58, 80)], label="right_leg"),
        # 左脚
        PathData(points=[(32, 80), (26, 82)], label="left_foot"),
        # 右脚
        PathData(points=[(58, 80), (64, 82)], label="right_foot"),
    ],
)

PERSON_THINKING = LineArt(
    name="person_thinking",
    paths=[
        # 头
        PathData(points=[
            (42, 8), (38, 10), (36, 14), (36, 18), (38, 22),
            (42, 24), (48, 24), (52, 22), (54, 18), (54, 14),
            (52, 10), (48, 8), (42, 8),
        ], closed=True, label="head"),
        # 身体
        PathData(points=[(45, 24), (45, 52)], label="body"),
        # 左臂（自然下垂）
        PathData(points=[(45, 30), (32, 46)], label="left_arm"),
        # 右臂（托腮）
        PathData(points=[(45, 30), (58, 32), (56, 18)], label="right_arm"),
        # 左腿
        PathData(points=[(45, 52), (34, 78)], label="left_leg"),
        # 右腿
        PathData(points=[(45, 52), (56, 78)], label="right_leg"),
        # 思考泡泡
        PathData(points=[
            (62, 6), (66, 4), (70, 4), (74, 6), (76, 10),
            (76, 14), (74, 18), (70, 20), (66, 20), (62, 18),
            (60, 14), (60, 10), (62, 6),
        ], closed=True, label="thought_bubble"),
        # 小圆点1
        PathData(points=[(58, 22), (59, 23)], label="dot1"),
        # 小圆点2
        PathData(points=[(56, 26), (57, 27)], label="dot2"),
    ],
)

PERSON_POINTING = LineArt(
    name="person_pointing",
    paths=[
        # 头
        PathData(points=[
            (42, 8), (38, 10), (36, 14), (36, 18), (38, 22),
            (42, 24), (48, 24), (52, 22), (54, 18), (54, 14),
            (52, 10), (48, 8), (42, 8),
        ], closed=True, label="head"),
        # 身体
        PathData(points=[(45, 24), (45, 52)], label="body"),
        # 左臂（指向右边）
        PathData(points=[(45, 30), (70, 26), (80, 24)], label="left_arm"),
        # 右臂
        PathData(points=[(45, 30), (32, 46)], label="right_arm"),
        # 左腿
        PathData(points=[(45, 52), (34, 78)], label="left_leg"),
        # 右腿
        PathData(points=[(45, 52), (56, 78)], label="right_leg"),
    ],
)


# ═══════════════════════════════════════════════════════════════
# 电脑/科技
# ═══════════════════════════════════════════════════════════════

LAPTOP = LineArt(
    name="laptop",
    paths=[
        # 屏幕
        PathData(points=[
            (20, 10), (80, 10), (80, 55), (20, 55), (20, 10),
        ], closed=True, label="screen"),
        # 屏幕内框
        PathData(points=[
            (24, 14), (76, 14), (76, 51), (24, 51), (24, 14),
        ], closed=True, label="screen_inner"),
        # 键盘底座
        PathData(points=[
            (10, 55), (90, 55), (85, 70), (15, 70), (10, 55),
        ], closed=True, label="keyboard"),
        # 键盘线条
        PathData(points=[(20, 60), (80, 60)], label="key_line1"),
        PathData(points=[(22, 64), (78, 64)], label="key_line2"),
        # 屏幕内容（代码行）
        PathData(points=[(28, 22), (50, 22)], label="code1"),
        PathData(points=[(28, 28), (60, 28)], label="code2"),
        PathData(points=[(32, 34), (55, 34)], label="code3"),
        PathData(points=[(28, 40), (45, 40)], label="code4"),
        PathData(points=[(32, 46), (65, 46)], label="code5"),
    ],
)

MONITOR = LineArt(
    name="monitor",
    paths=[
        # 屏幕外框
        PathData(points=[
            (15, 5), (85, 5), (85, 60), (15, 60), (15, 5),
        ], closed=True, label="frame"),
        # 屏幕
        PathData(points=[
            (19, 9), (81, 9), (81, 56), (19, 56), (19, 9),
        ], closed=True, label="screen"),
        # 支架
        PathData(points=[(45, 60), (45, 75)], label="stand"),
        # 底座
        PathData(points=[(30, 75), (70, 75)], label="base"),
    ],
)

SERVER = LineArt(
    name="server",
    paths=[
        # 机箱1
        PathData(points=[
            (20, 5), (55, 5), (55, 30), (20, 30), (20, 5),
        ], closed=True, label="case1"),
        # 机箱2
        PathData(points=[
            (20, 35), (55, 35), (55, 60), (20, 60), (20, 35),
        ], closed=True, label="case2"),
        # 机箱3
        PathData(points=[
            (20, 65), (55, 65), (55, 90), (20, 90), (20, 65),
        ], closed=True, label="case3"),
        # 指示灯
        PathData(points=[(25, 15), (27, 15)], label="led1"),
        PathData(points=[(25, 45), (27, 45)], label="led2"),
        PathData(points=[(25, 75), (27, 75)], label="led3"),
        # 连接线
        PathData(points=[(55, 20), (70, 20), (70, 50), (55, 50)], label="cable1"),
        PathData(points=[(55, 50), (70, 50), (70, 80), (55, 80)], label="cable2"),
    ],
)


# ═══════════════════════════════════════════════════════════════
# 书本/学习
# ═══════════════════════════════════════════════════════════════

BOOK_OPEN = LineArt(
    name="book_open",
    paths=[
        # 左页
        PathData(points=[
            (50, 15), (50, 80), (10, 80), (10, 20),
            (15, 18), (20, 16), (30, 14), (40, 14), (50, 15),
        ], closed=False, label="left_page"),
        # 右页
        PathData(points=[
            (50, 15), (50, 80), (90, 80), (90, 20),
            (85, 18), (80, 16), (70, 14), (60, 14), (50, 15),
        ], closed=False, label="right_page"),
        # 书脊
        PathData(points=[(50, 15), (50, 80)], label="spine"),
        # 文字行（左页）
        PathData(points=[(18, 30), (44, 30)], label="text_l1"),
        PathData(points=[(18, 38), (42, 38)], label="text_l2"),
        PathData(points=[(18, 46), (46, 46)], label="text_l3"),
        PathData(points=[(18, 54), (40, 54)], label="text_l4"),
        # 文字行（右页）
        PathData(points=[(56, 30), (82, 30)], label="text_r1"),
        PathData(points=[(56, 38), (84, 38)], label="text_r2"),
        PathData(points=[(56, 46), (80, 46)], label="text_r3"),
    ],
)

BOOK_CLOSED = LineArt(
    name="book_closed",
    paths=[
        # 书封面
        PathData(points=[
            (20, 10), (80, 10), (80, 85), (20, 85), (20, 10),
        ], closed=True, label="cover"),
        # 书脊
        PathData(points=[(20, 10), (16, 12), (16, 83), (20, 85)], label="spine"),
        # 书页边缘
        PathData(points=[(22, 12), (78, 12)], label="page_edge"),
        # 标题线
        PathData(points=[(30, 35), (70, 35)], label="title1"),
        PathData(points=[(35, 42), (65, 42)], label="title2"),
        # 装饰线
        PathData(points=[(30, 60), (70, 60)], label="deco"),
    ],
)


# ═══════════════════════════════════════════════════════════════
# 城市/建筑
# ═══════════════════════════════════════════════════════════════

CITY_SKYLINE = LineArt(
    name="city_skyline",
    paths=[
        # 建筑1（矮）
        PathData(points=[(5, 90), (5, 55), (20, 55), (20, 90)], closed=True, label="b1"),
        # 建筑2（高）
        PathData(points=[(20, 90), (20, 30), (35, 30), (35, 90)], closed=True, label="b2"),
        # 建筑3（中）
        PathData(points=[(35, 90), (35, 45), (50, 45), (50, 90)], closed=True, label="b3"),
        # 建筑4（最高）
        PathData(points=[(50, 90), (50, 20), (62, 15), (74, 20), (74, 90)], closed=True, label="b4"),
        # 建筑5
        PathData(points=[(74, 90), (74, 40), (90, 40), (90, 90)], closed=True, label="b5"),
        # 建筑6
        PathData(points=[(90, 90), (90, 50), (98, 50), (98, 90)], closed=True, label="b6"),
        # 窗户（建筑2）
        PathData(points=[(24, 38), (28, 38), (28, 44), (24, 44), (24, 38)], closed=True, label="w1"),
        PathData(points=[(24, 50), (28, 50), (28, 56), (24, 56), (24, 50)], closed=True, label="w2"),
        PathData(points=[(30, 38), (34, 38), (34, 44), (30, 44), (30, 38)], closed=True, label="w3"),
        # 窗户（建筑4）
        PathData(points=[(54, 28), (58, 28), (58, 34), (54, 34), (54, 28)], closed=True, label="w4"),
        PathData(points=[(60, 28), (64, 28), (64, 34), (60, 34), (60, 28)], closed=True, label="w5"),
        PathData(points=[(54, 40), (58, 40), (58, 46), (54, 46), (54, 40)], closed=True, label="w6"),
        # 地面线
        PathData(points=[(0, 90), (100, 90)], label="ground"),
        # 月亮
        PathData(points=[
            (82, 8), (86, 6), (90, 8), (92, 12), (92, 16),
            (90, 20), (86, 22), (82, 20), (80, 16), (80, 12), (82, 8),
        ], closed=True, label="moon"),
    ],
)

BUILDING_OFFICE = LineArt(
    name="building_office",
    paths=[
        # 建筑主体
        PathData(points=[
            (10, 90), (10, 15), (90, 15), (90, 90),
        ], closed=True, label="building"),
        # 层线
        PathData(points=[(10, 30), (90, 30)], label="floor1"),
        PathData(points=[(10, 45), (90, 45)], label="floor2"),
        PathData(points=[(10, 60), (90, 60)], label="floor3"),
        PathData(points=[(10, 75), (90, 75)], label="floor4"),
        # 窗户行1
        PathData(points=[(18, 18), (28, 18), (28, 26), (18, 26), (18, 18)], closed=True, label="w1"),
        PathData(points=[(36, 18), (46, 18), (46, 26), (36, 26), (36, 18)], closed=True, label="w2"),
        PathData(points=[(54, 18), (64, 18), (64, 26), (54, 26), (54, 18)], closed=True, label="w3"),
        PathData(points=[(72, 18), (82, 18), (82, 26), (72, 26), (72, 18)], closed=True, label="w4"),
        # 门
        PathData(points=[
            (40, 90), (40, 76), (60, 76), (60, 90),
        ], closed=True, label="door"),
    ],
)


# ═══════════════════════════════════════════════════════════════
# 机器人/AI
# ═══════════════════════════════════════════════════════════════

ROBOT = LineArt(
    name="robot",
    paths=[
        # 天线
        PathData(points=[(50, 5), (50, 15)], label="antenna"),
        PathData(points=[
            (46, 5), (50, 2), (54, 5), (50, 8), (46, 5),
        ], closed=True, label="antenna_tip"),
        # 头
        PathData(points=[
            (30, 15), (70, 15), (70, 40), (30, 40), (30, 15),
        ], closed=True, label="head"),
        # 眼睛
        PathData(points=[
            (38, 22), (44, 22), (44, 28), (38, 28), (38, 22),
        ], closed=True, label="eye_l"),
        PathData(points=[
            (56, 22), (62, 22), (62, 28), (56, 28), (56, 22),
        ], closed=True, label="eye_r"),
        # 嘴
        PathData(points=[(40, 34), (60, 34)], label="mouth"),
        # 身体
        PathData(points=[
            (25, 42), (75, 42), (75, 70), (25, 70), (25, 42),
        ], closed=True, label="body"),
        # 身体装饰
        PathData(points=[(35, 50), (65, 50)], label="body_line1"),
        PathData(points=[(35, 58), (65, 58)], label="body_line2"),
        # 心脏指示灯
        PathData(points=[
            (46, 48), (50, 44), (54, 48), (50, 52), (46, 48),
        ], closed=True, label="heart"),
        # 左臂
        PathData(points=[(25, 46), (12, 55), (10, 65)], label="left_arm"),
        # 右臂
        PathData(points=[(75, 46), (88, 55), (90, 65)], label="right_arm"),
        # 左腿
        PathData(points=[(35, 70), (35, 85), (30, 90)], label="left_leg"),
        # 右腿
        PathData(points=[(65, 70), (65, 85), (70, 90)], label="right_leg"),
    ],
)


# ═══════════════════════════════════════════════════════════════
# 概念/抽象
# ═══════════════════════════════════════════════════════════════

LIGHTBULB = LineArt(
    name="lightbulb",
    paths=[
        # 灯泡外形
        PathData(points=[
            (50, 10), (38, 16), (30, 28), (28, 42), (32, 54),
            (38, 62), (38, 72), (62, 72), (62, 62), (68, 54),
            (72, 42), (70, 28), (62, 16), (50, 10),
        ], closed=True, label="bulb"),
        # 灯丝
        PathData(points=[(42, 50), (46, 42), (50, 50), (54, 42), (58, 50)], label="filament"),
        # 底座
        PathData(points=[(38, 72), (62, 72)], label="base_top"),
        PathData(points=[(40, 76), (60, 76)], label="base_mid"),
        PathData(points=[(42, 80), (58, 80)], label="base_bottom"),
        # 光线
        PathData(points=[(50, 2), (50, 6)], label="ray_top"),
        PathData(points=[(22, 20), (26, 24)], label="ray_left"),
        PathData(points=[(74, 20), (78, 24)], label="ray_right"),
        PathData(points=[(16, 42), (20, 42)], label="ray_far_left"),
        PathData(points=[(80, 42), (84, 42)], label="ray_far_right"),
    ],
)

BRAIN = LineArt(
    name="brain",
    paths=[
        # 左脑
        PathData(points=[
            (48, 20), (38, 18), (28, 22), (20, 32), (18, 45),
            (20, 58), (26, 68), (36, 74), (48, 76),
        ], label="left_brain"),
        # 右脑
        PathData(points=[
            (48, 20), (58, 18), (68, 22), (76, 32), (78, 45),
            (76, 58), (70, 68), (60, 74), (48, 76),
        ], label="right_brain"),
        # 中间纹路
        PathData(points=[(48, 20), (46, 32), (48, 45), (46, 58), (48, 76)], label="center"),
        # 左纹路
        PathData(points=[(30, 30), (36, 38), (30, 48)], label="left_fold1"),
        PathData(points=[(26, 50), (34, 56), (28, 64)], label="left_fold2"),
        # 右纹路
        PathData(points=[(66, 30), (60, 38), (66, 48)], label="right_fold1"),
        PathData(points=[(70, 50), (62, 56), (68, 64)], label="right_fold2"),
        # 底部
        PathData(points=[(40, 78), (48, 82), (56, 78)], label="stem"),
    ],
)

GEAR = LineArt(
    name="gear",
    paths=[
        # 齿轮外形（简化）
        PathData(points=[
            (50, 10), (55, 12), (58, 8), (62, 12), (65, 16),
            (70, 14), (74, 18), (72, 24), (76, 28), (80, 32),
            (78, 38), (82, 42), (84, 48), (80, 52), (82, 58),
            (78, 62), (76, 68), (70, 68), (68, 74), (62, 72),
            (58, 76), (54, 72), (50, 76), (46, 72), (42, 76),
            (38, 72), (34, 74), (30, 68), (24, 68), (22, 62),
            (18, 58), (20, 52), (16, 48), (18, 42), (22, 38),
            (20, 32), (24, 28), (28, 24), (26, 18), (30, 14),
            (35, 16), (38, 12), (42, 8), (45, 12), (50, 10),
        ], closed=True, label="outer"),
        # 内圆
        PathData(points=[
            (42, 38), (38, 42), (38, 50), (42, 54), (50, 56),
            (58, 54), (62, 50), (62, 42), (58, 38), (50, 36),
            (42, 38),
        ], closed=True, label="inner"),
    ],
)

CLOUD = LineArt(
    name="cloud",
    paths=[
        PathData(points=[
            (25, 60), (18, 56), (16, 48), (20, 40), (28, 36),
            (32, 28), (40, 24), (50, 22), (60, 24), (68, 28),
            (72, 34), (80, 36), (84, 44), (82, 52), (76, 58),
            (70, 60), (25, 60),
        ], closed=True, label="body"),
    ],
)

DATABASE = LineArt(
    name="database",
    paths=[
        # 顶部椭圆
        PathData(points=[
            (20, 15), (30, 10), (50, 8), (70, 10), (80, 15),
            (70, 20), (50, 22), (30, 20), (20, 15),
        ], closed=True, label="top"),
        # 侧面线
        PathData(points=[(20, 15), (20, 75)], label="left_side"),
        PathData(points=[(80, 15), (80, 75)], label="right_side"),
        # 底部椭圆
        PathData(points=[
            (20, 75), (30, 80), (50, 82), (70, 80), (80, 75),
            (70, 70), (50, 68), (30, 70), (20, 75),
        ], closed=True, label="bottom"),
        # 中间分隔
        PathData(points=[
            (20, 38), (30, 42), (50, 44), (70, 42), (80, 38),
        ], label="mid1"),
        PathData(points=[
            (20, 55), (30, 59), (50, 61), (70, 59), (80, 55),
        ], label="mid2"),
    ],
)

ARROW_RIGHT = LineArt(
    name="arrow_right",
    paths=[
        PathData(points=[(10, 50), (80, 50)], label="shaft"),
        PathData(points=[(70, 35), (90, 50), (70, 65)], label="head"),
    ],
)

ARROW_DOWN = LineArt(
    name="arrow_down",
    paths=[
        PathData(points=[(50, 10), (50, 75)], label="shaft"),
        PathData(points=[(35, 65), (50, 85), (65, 65)], label="head"),
    ],
)

CHECK_MARK = LineArt(
    name="check_mark",
    paths=[
        PathData(points=[(15, 50), (40, 75), (85, 25)], label="check"),
    ],
)

CHAT_BUBBLE = LineArt(
    name="chat_bubble",
    paths=[
        PathData(points=[
            (10, 10), (90, 10), (90, 60), (55, 60),
            (40, 80), (45, 60), (10, 60), (10, 10),
        ], closed=True, label="bubble"),
        PathData(points=[(25, 30), (75, 30)], label="line1"),
        PathData(points=[(25, 42), (60, 42)], label="line2"),
    ],
)

MAGNIFYING_GLASS = LineArt(
    name="magnifying_glass",
    paths=[
        # 镜片圆
        PathData(points=[
            (36, 20), (28, 24), (24, 34), (24, 44), (28, 54),
            (36, 58), (46, 58), (54, 54), (58, 44), (58, 34),
            (54, 24), (46, 20), (36, 20),
        ], closed=True, label="lens"),
        # 手柄
        PathData(points=[(56, 56), (72, 72)], label="handle"),
        PathData(points=[(68, 68), (76, 76), (80, 72), (72, 64)], label="grip"),
    ],
)

NETWORK = LineArt(
    name="network",
    paths=[
        # 节点
        PathData(points=[
            (46, 16), (50, 12), (54, 16), (50, 20), (46, 16),
        ], closed=True, label="node_top"),
        PathData(points=[
            (16, 66), (20, 62), (24, 66), (20, 70), (16, 66),
        ], closed=True, label="node_left"),
        PathData(points=[
            (76, 66), (80, 62), (84, 66), (80, 70), (76, 66),
        ], closed=True, label="node_right"),
        PathData(points=[
            (16, 36), (20, 32), (24, 36), (20, 40), (16, 36),
        ], closed=True, label="node_mid_left"),
        PathData(points=[
            (76, 36), (80, 32), (84, 36), (80, 40), (76, 36),
        ], closed=True, label="node_mid_right"),
        # 连接线
        PathData(points=[(50, 20), (20, 36)], label="edge1"),
        PathData(points=[(50, 20), (80, 36)], label="edge2"),
        PathData(points=[(20, 40), (20, 62)], label="edge3"),
        PathData(points=[(80, 40), (80, 62)], label="edge4"),
        PathData(points=[(24, 66), (76, 66)], label="edge5"),
        PathData(points=[(20, 40), (80, 40)], label="edge6"),
    ],
)


# ═══════════════════════════════════════════════════════════════
# 索引表：关键词 → 插画
# ═══════════════════════════════════════════════════════════════

KEYWORD_MAP = {
    # 人物
    "person": PERSON_STANDING,
    "people": PERSON_STANDING,
    "user": PERSON_STANDING,
    "thinking": PERSON_THINKING,
    "pointing": PERSON_POINTING,
    "agent": PERSON_THINKING,

    # 科技
    "laptop": LAPTOP,
    "computer": LAPTOP,
    "code": LAPTOP,
    "programming": LAPTOP,
    "monitor": MONITOR,
    "screen": MONITOR,
    "server": SERVER,
    "database": DATABASE,
    "redis": DATABASE,
    "cache": DATABASE,
    "cloud": CLOUD,
    "network": NETWORK,

    # 书本
    "book": BOOK_OPEN,
    "reading": BOOK_OPEN,
    "study": BOOK_OPEN,
    "learning": BOOK_OPEN,
    "knowledge": BOOK_CLOSED,

    # 城市
    "city": CITY_SKYLINE,
    "building": BUILDING_OFFICE,
    "office": BUILDING_OFFICE,
    "work": BUILDING_OFFICE,

    # AI/机器人
    "robot": ROBOT,
    "ai": ROBOT,
    "machine": ROBOT,
    "brain": BRAIN,
    "idea": LIGHTBULB,
    "lightbulb": LIGHTBULB,
    "creative": LIGHTBULB,
    "gear": GEAR,
    "tool": GEAR,
    "system": GEAR,

    # 符号
    "arrow": ARROW_RIGHT,
    "check": CHECK_MARK,
    "success": CHECK_MARK,
    "chat": CHAT_BUBBLE,
    "message": CHAT_BUBBLE,
    "search": MAGNIFYING_GLASS,
    "find": MAGNIFYING_GLASS,
}


def get_lineart(keyword: str) -> LineArt:
    """根据关键词获取插画，找不到返回默认人物"""
    kw = keyword.lower().strip()
    return KEYWORD_MAP.get(kw, PERSON_STANDING)


def list_available() -> List[str]:
    """列出所有可用的插画名"""
    return list(set(a.name for a in KEYWORD_MAP.values())) + [
        "arrow_right", "arrow_down", "check_mark",
    ]
