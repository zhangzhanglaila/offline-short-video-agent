# -*- coding: utf-8 -*-
"""
Line Art Renderer v3 — 视觉导演驱动的场景渲染

核心改进：
1. Visual Director 决定构图（不是图标排列）
2. 主次分明（hero 70% + support 30%）
3. 流动连接线（不是孤立图标）
4. 画布利用率 60-80%
5. 视觉隐喻（工厂/旅程/生长/转变/生态）
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.visual_director import (
    SceneComposition, SceneElement, FlowConnection,
    VisualMetaphor, direct_scene, direct_scenes,
)
from core.svg_lineart_library import get_illustration, Weight

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# 样式
# ═══════════════════════════════════════════════════════════════

COLORS = {
    "bg": (248, 248, 248),
    "line": (31, 31, 31),
    "accent": (255, 107, 90),
    "muted": (200, 200, 200),
    "connector": (180, 180, 180),
}

WEIGHT_SCALE = {
    Weight.OUTLINE: 4,
    Weight.DETAIL: 2,
    Weight.ACCENT: 5,
    Weight.ENVIRONMENT: 1,
}

_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_font_cache = {}


def _get_font(size: int):
    if size in _font_cache:
        return _font_cache[size]
    for path in _FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(path, size)
            _font_cache[size] = font
            return font
        except (IOError, OSError):
            continue
    font = ImageFont.load_default()
    _font_cache[size] = font
    return font


def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ═══════════════════════════════════════════════════════════════
# 平滑 + 路径
# ═══════════════════════════════════════════════════════════════

def _smooth(raw: List[Tuple[float, float]], segments: int = 6) -> List[Tuple[float, float]]:
    if len(raw) < 3:
        return raw
    result = []
    for i in range(len(raw) - 1):
        p0 = raw[max(0, i - 1)]
        p1 = raw[i]
        p2 = raw[min(len(raw) - 1, i + 1)]
        p3 = raw[min(len(raw) - 1, i + 2)]
        for s in range(segments):
            t = s / segments
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2*p1[0]) + (-p0[0]+p2[0])*t + (2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2 + (-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            y = 0.5 * ((2*p1[1]) + (-p0[1]+p2[1])*t + (2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2 + (-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            result.append((x, y))
    result.append(raw[-1])
    return result


def _path_length(points: List[Tuple[float, float]]) -> float:
    total = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        total += math.sqrt(dx * dx + dy * dy)
    return total


def _cut_path(points: List[Tuple[float, float]], target_len: float) -> List[Tuple[float, float]]:
    if not points:
        return []
    result = [points[0]]
    acc = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        seg = math.sqrt(dx * dx + dy * dy)
        if acc + seg <= target_len:
            result.append(points[i])
            acc += seg
        else:
            remain = target_len - acc
            if seg > 0:
                t = remain / seg
                result.append((points[i-1][0] + dx * t, points[i-1][1] + dy * t))
            return result
    return result


# ═══════════════════════════════════════════════════════════════
# 元素绘制
# ═══════════════════════════════════════════════════════════════

def _draw_rect(
    draw: ImageDraw.ImageDraw,
    x: float, y: float, w: float, h: float,
    label: str,
    weight: int,
    color: Tuple[int, int, int],
    progress: float,
    radius: int = 8,
):
    """绘制圆角矩形 + 标签，带绘制动画"""
    if progress <= 0:
        return

    # 矩形绘制动画（从左到右）
    rect_p = _ease_out_cubic(_clamp(progress / 0.5))
    visible_w = w * rect_p

    # 填充
    draw.rounded_rectangle(
        [x, y, x + visible_w, y + h],
        radius=min(radius, visible_w / 2),
        fill=(255, 255, 255),
        outline=color,
        width=weight,
    )

    # 标签（逐字出现）
    if label and progress > 0.4:
        text_p = _ease_out_cubic(_clamp((progress - 0.4) / 0.5))
        font = _get_font(max(16, int(weight * 6)))
        visible_chars = max(1, int(len(label) * text_p))
        visible_text = label[:visible_chars]

        bbox = draw.textbbox((0, 0), visible_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = x + (w - tw) / 2
        ty = y + (h - th) / 2 - 2

        draw.text((tx, ty), visible_text, fill=color, font=font)


def _draw_circle(
    draw: ImageDraw.ImageDraw,
    x: float, y: float, w: float, h: float,
    label: str,
    weight: int,
    color: Tuple[int, int, int],
    progress: float,
):
    """绘制圆形 + 标签"""
    if progress <= 0:
        return

    scale = _ease_out_cubic(_clamp(progress / 0.5))
    cx, cy = x + w / 2, y + h / 2
    rx, ry = w / 2 * scale, h / 2 * scale

    draw.ellipse(
        [cx - rx, cy - ry, cx + rx, cy + ry],
        fill=(255, 255, 255),
        outline=color,
        width=weight,
    )

    if label and progress > 0.4:
        text_p = _ease_out_cubic(_clamp((progress - 0.4) / 0.5))
        font = _get_font(max(14, int(weight * 5)))
        visible_chars = max(1, int(len(label) * text_p))
        visible_text = label[:visible_chars]
        bbox = draw.textbbox((0, 0), visible_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((cx - tw / 2, cy - th / 2), visible_text, fill=color, font=font)


def _draw_element(
    draw: ImageDraw.ImageDraw,
    elem: SceneElement,
    canvas_w: int, canvas_h: int,
    progress: float,
):
    """绘制单个场景元素"""
    x = elem.x * canvas_w
    y = elem.y * canvas_h
    w = elem.w * canvas_w
    h = elem.h * canvas_h

    color = COLORS.get(elem.color_key, COLORS["line"])

    if elem.shape == "rect":
        _draw_rect(draw, x, y, w, h, elem.label, elem.weight, color, progress)
    elif elem.shape == "circle":
        _draw_circle(draw, x, y, w, h, elem.label, elem.weight, color, progress)
    elif elem.shape == "text":
        if progress > 0.2:
            text_p = _ease_out_cubic(_clamp((progress - 0.2) / 0.6))
            font = _get_font(max(18, elem.weight * 6))
            visible_chars = max(1, int(len(elem.label) * text_p))
            draw.text((x, y), elem.label[:visible_chars], fill=color, font=font)


def _draw_connection(
    draw: ImageDraw.ImageDraw,
    conn: FlowConnection,
    elements: List[SceneElement],
    canvas_w: int, canvas_h: int,
    progress: float,
):
    """绘制两个元素之间的流动连接线"""
    if progress <= 0:
        return

    # 找到起止元素
    from_elem = next((e for e in elements if e.name == conn.from_name), None)
    to_elem = next((e for e in elements if e.name == conn.to_name), None)

    if not from_elem or not to_elem:
        return

    # 起点：from 元素的右边缘中心
    fx = (from_elem.x + from_elem.w) * canvas_w
    fy = (from_elem.y + from_elem.h / 2) * canvas_h

    # 终点：to 元素的左边缘中心
    tx = to_elem.x * canvas_w
    ty = (to_elem.y + to_elem.h / 2) * canvas_h

    # 绘制箭头线
    line_progress = _ease_out_cubic(_clamp(progress / 0.7))

    # 贝塞尔控制点
    mid_x = (fx + tx) / 2
    if conn.style == "curved":
        mid_y = (fy + ty) / 2 - 40
    else:
        mid_y = (fy + ty) / 2

    # 绘制曲线（用折线近似）
    points = []
    steps = 20
    for s in range(steps + 1):
        t = s / steps
        t2 = t * t
        # 二次贝塞尔
        px = (1-t)**2 * fx + 2*(1-t)*t * mid_x + t2 * tx
        py = (1-t)**2 * fy + 2*(1-t)*t * mid_y + t2 * ty
        points.append((px, py))

    # 截取到目标长度
    total_len = _path_length(points)
    target_len = total_len * line_progress
    visible = _cut_path(points, target_len)

    if len(visible) >= 2:
        color = COLORS["connector"]
        draw.line(visible, fill=color, width=2)

        # 箭头头
        if progress > 0.7:
            head_progress = _clamp((progress - 0.7) / 0.3)
            end_x, end_y = visible[-1]
            prev_x, prev_y = visible[-2]
            angle = math.atan2(end_y - prev_y, end_x - prev_x)

            head_size = 10 * head_progress
            hx1 = end_x - head_size * math.cos(angle - 0.4)
            hy1 = end_y - head_size * math.sin(angle - 0.4)
            hx2 = end_x - head_size * math.cos(angle + 0.4)
            hy2 = end_y - head_size * math.sin(angle + 0.4)

            draw.line([(end_x, end_y), (hx1, hy1)], fill=color, width=2)
            draw.line([(end_x, end_y), (hx2, hy2)], fill=color, width=2)


def _draw_background(
    draw: ImageDraw.ImageDraw,
    strokes: List[Tuple[float, float, float, float]],
    canvas_w: int, canvas_h: int,
    progress: float,
):
    """绘制背景装饰线"""
    if progress <= 0:
        return

    env_progress = _ease_out_cubic(_clamp(progress / 0.3))
    color = COLORS["muted"]

    for x1, y1, x2, y2 in strokes:
        px1, py1 = x1 * canvas_w, y1 * canvas_h
        px2, py2 = x2 * canvas_w, y2 * canvas_h

        cur_x2 = px1 + (px2 - px1) * env_progress
        cur_y2 = py1 + (py2 - py1) * env_progress

        draw.line([(px1, py1), (cur_x2, cur_y2)], fill=color, width=1)


# ═══════════════════════════════════════════════════════════════
# 场景帧渲染
# ═══════════════════════════════════════════════════════════════

def render_scene_frame(
    scene: SceneComposition,
    canvas_w: int = 1920,
    canvas_h: int = 1080,
    progress: float = 1.0,
) -> Image.Image:
    """渲染一个场景的一帧"""
    img = Image.new("RGB", (canvas_w, canvas_h), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # 1. 背景装饰（0-30%）
    _draw_background(draw, scene.background_strokes, canvas_w, canvas_h, progress)

    # 2. 连接线（20-70%）— 先画，在元素下面
    for conn in scene.connections:
        conn_progress = _clamp((progress - 0.2) / 0.5)
        _draw_connection(draw, conn, scene.elements, canvas_w, canvas_h, conn_progress)

    # 3. 元素（10-80%）— 按 draw_order 排序
    sorted_elements = sorted(scene.elements, key=lambda e: e.draw_order)
    for i, elem in enumerate(sorted_elements):
        elem_start = 0.1 + i * 0.05
        elem_progress = _clamp((progress - elem_start) / max(0.3, 0.7 - i * 0.05))
        _draw_element(draw, elem, canvas_w, canvas_h, elem_progress)

    # 4. 标题（60-100%）
    if scene.title and progress > 0.6:
        title_progress = _clamp((progress - 0.6) / 0.3)
        font = _get_font(32)
        visible_chars = max(1, int(len(scene.title) * title_progress))
        visible_title = scene.title[:visible_chars]
        bbox = draw.textbbox((0, 0), visible_title, font=font)
        tw = bbox[2] - bbox[0]
        tx = (canvas_w - tw) / 2
        ty = canvas_h - 60
        draw.text((tx, ty), visible_title, fill=COLORS["line"], font=font)

    return img


# ═══════════════════════════════════════════════════════════════
# 视频生成
# ═══════════════════════════════════════════════════════════════

def render_lineart_video(
    scenes: List[SceneComposition],
    output_path: str,
    canvas_w: int = 1920,
    canvas_h: int = 1080,
    fps: int = 30,
    draw_duration: float = 4.0,
    hold_duration: float = 2.0,
) -> str:
    """生成线条插画手绘视频"""
    output_path = Path(output_path)
    temp_dir = output_path.parent / f"_lineart_frames_{output_path.stem}"

    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    frame_idx = 0
    total_scenes = len(scenes)

    print(f"\n{'='*50}")
    print(f"  Line Art Animation v3")
    print(f"  Scenes: {total_scenes}")
    print(f"  Canvas: {canvas_w}x{canvas_h}")
    print(f"{'='*50}")

    for si, scene in enumerate(scenes):
        draw_frames = int(draw_duration * fps)
        for f in range(draw_frames):
            progress = f / draw_frames
            img = render_scene_frame(scene, canvas_w, canvas_h, progress)
            img.save(str(temp_dir / f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

        hold_frames = int(hold_duration * fps)
        last_img = render_scene_frame(scene, canvas_w, canvas_h, 1.0)
        for f in range(hold_frames):
            last_img.save(str(temp_dir / f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

        hero = next((e for e in scene.elements if e.role == "hero"), None)
        hero_name = hero.label if hero else "?"
        print(f"  Scene {si+1}/{total_scenes}: [{scene.metaphor}] hero={hero_name}")

    print(f"\n  Encoding ({frame_idx} frames)...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(temp_dir / "frame_%05d.png"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, timeout=300)

    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    print(f"  Output: {output_path}")
    return str(output_path)


# ═══════════════════════════════════════════════════════════════
# 完整管线
# ═══════════════════════════════════════════════════════════════

def generate_lineart_video(
    script_lines: List[str],
    output_path: str = "output/lineart_video.mp4",
    draw_duration: float = 4.0,
    hold_duration: float = 2.0,
) -> str:
    """
    从文案生成线条插画手绘视频。

    Pipeline:
      Script → Visual Director → Scene Composition → Frame Rendering → Video
    """
    print(f"\n  Script lines: {len(script_lines)}")
    for i, line in enumerate(script_lines):
        print(f"    [{i+1}] {line}")

    scenes = direct_scenes(script_lines)

    return render_lineart_video(
        scenes, output_path,
        draw_duration=draw_duration,
        hold_duration=hold_duration,
    )


# ═══════════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Line Art Renderer v3 — Visual Director")
    print("=" * 50)

    script = [
        "AI Agent 是一种智能系统",
        "Agent 使用 Tool 获取信息",
        "数据存储在 Database 中",
        "Brain 处理并生成决策",
        "Robot 执行最终任务",
    ]

    output = generate_lineart_video(
        script,
        output_path="output/test_lineart_v3.mp4",
        draw_duration=3.5,
        hold_duration=2.0,
    )

    print(f"\nDone! Output: {output}")
