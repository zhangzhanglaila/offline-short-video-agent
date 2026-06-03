# -*- coding: utf-8 -*-
"""
Line Art Renderer v2 — 场景级线条插画手绘动画

核心改进：
1. 多对象场景（不是单个图标）
2. 贝塞尔平滑曲线
3. 三种线宽层级
4. 环境元素
5. 交错动画

渲染流程：
  SceneLayout → 逐帧绘制所有对象+环境 → FFmpeg编码 → 视频
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.svg_lineart_library import (
    Illustration, Stroke, Weight, get_illustration,
)
from core.scene_planner import (
    SceneLayout, SceneObject,
    plan_scene_with_llm, texts_to_scenes_with_llm,
    plan_scene_fallback, texts_to_scenes_fallback,
)

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
# Catmull-Rom 样条平滑
# ═══════════════════════════════════════════════════════════════

def _smooth(raw: List[Tuple[float, float]], segments: int = 6) -> List[Tuple[float, float]]:
    """Catmull-Rom 样条插值，让折线变成平滑曲线"""
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


# ═══════════════════════════════════════════════════════════════
# 路径长度 + 插值
# ═══════════════════════════════════════════════════════════════

def _path_length(points: List[Tuple[float, float]]) -> float:
    total = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        total += math.sqrt(dx * dx + dy * dy)
    return total


def _cut_path(points: List[Tuple[float, float]], target_len: float) -> List[Tuple[float, float]]:
    """沿路径截取 target_len 长度"""
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
                result.append((
                    points[i-1][0] + dx * t,
                    points[i-1][1] + dy * t,
                ))
            return result

    return result


# ═══════════════════════════════════════════════════════════════
# 单条笔触绘制
# ═══════════════════════════════════════════════════════════════

def _draw_stroke(
    draw: ImageDraw.ImageDraw,
    stroke: Stroke,
    ox: float, oy: float, scale: float,
    progress: float,
):
    """绘制一条笔触，根据 progress 决定绘制多少"""
    if progress <= 0 or len(stroke.points) < 2:
        return

    # 转换到画布坐标
    canvas_pts = [(ox + x * scale, oy + y * scale) for x, y in stroke.points]

    # 平滑
    smooth_pts = _smooth(canvas_pts, segments=6)

    # 计算总长度和目标长度
    total = _path_length(smooth_pts)
    draw_len = total * _ease_out_cubic(_clamp(progress))

    # 截取
    visible = _cut_path(smooth_pts, draw_len)
    if len(visible) < 2:
        return

    # 颜色
    color = COLORS.get(stroke.color_key, COLORS["line"])

    # 线宽
    lw = WEIGHT_SCALE.get(stroke.weight, 3)

    # 绘制
    draw.line(visible, fill=color, width=lw, joint="curve")

    # 闭合
    if stroke.closed and progress >= 0.95:
        draw.line([visible[-1], visible[0]], fill=color, width=lw, joint="curve")


# ═══════════════════════════════════════════════════════════════
# 单幅插画绘制
# ═══════════════════════════════════════════════════════════════

def _draw_illustration(
    draw: ImageDraw.ImageDraw,
    art: Illustration,
    x: float, y: float, scale: float,
    progress: float,
):
    """绘制一幅插画的所有笔触"""
    n = len(art.strokes)
    for i, stroke in enumerate(art.strokes):
        # 交错：每条笔触延迟
        offset = i * 0.06
        stroke_progress = _clamp((progress - offset) / max(0.15, 1.0 - offset * (n - 1) / n))

        _draw_stroke(draw, stroke, x, y, scale, stroke_progress)


# ═══════════════════════════════════════════════════════════════
# 场景帧渲染
# ═══════════════════════════════════════════════════════════════

def render_scene_frame(
    scene: SceneLayout,
    canvas_w: int = 1920,
    canvas_h: int = 1080,
    progress: float = 1.0,
) -> Image.Image:
    """
    渲染一个场景的一帧。

    1. 绘制环境元素（最先出现）
    2. 绘制所有对象（交错出现）
    3. 绘制标题
    """
    img = Image.new("RGB", (canvas_w, canvas_h), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # ── 环境元素（0-30% 进度）────────────────
    env_progress = _clamp(progress / 0.3)
    for stroke in scene.environment:
        _draw_stroke(draw, stroke, 0, 0, 1.0, env_progress)

    # ── 对象（10%-90% 进度）────────────────
    n_obj = len(scene.objects)
    for i, obj in enumerate(scene.objects):
        # 每个对象交错出现
        obj_start = 0.1 + obj.delay
        obj_duration = max(0.3, 0.8 - obj.delay)
        obj_progress = _clamp((progress - obj_start) / obj_duration)

        art = get_illustration(obj.keyword)
        _draw_illustration(draw, art, obj.x, obj.y, obj.scale, obj_progress)

    # ── 标题（60%-100% 进度）────────────────
    if scene.title and progress > 0.6:
        title_progress = _clamp((progress - 0.6) / 0.3)
        font = _get_font(32)
        visible_chars = max(1, int(len(scene.title) * title_progress))
        visible_title = scene.title[:visible_chars]

        bbox = draw.textbbox((0, 0), visible_title, font=font)
        tw = bbox[2] - bbox[0]
        tx = (canvas_w - tw) / 2
        ty = canvas_h - 80

        draw.text((tx, ty), visible_title, fill=COLORS["line"], font=font)

    return img


# ═══════════════════════════════════════════════════════════════
# 视频生成
# ═══════════════════════════════════════════════════════════════

def render_lineart_video(
    scenes: List[SceneLayout],
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
    print(f"  Line Art Animation v2")
    print(f"  Scenes: {total_scenes}")
    print(f"  Canvas: {canvas_w}x{canvas_h}")
    print(f"{'='*50}")

    for si, scene in enumerate(scenes):
        # 绘制阶段
        draw_frames = int(draw_duration * fps)
        for f in range(draw_frames):
            progress = f / draw_frames
            img = render_scene_frame(scene, canvas_w, canvas_h, progress)
            img.save(str(temp_dir / f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

        # 停留阶段
        hold_frames = int(hold_duration * fps)
        last_img = render_scene_frame(scene, canvas_w, canvas_h, 1.0)
        for f in range(hold_frames):
            last_img.save(str(temp_dir / f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

        obj_names = [o.keyword for o in scene.objects]
        print(f"  Scene {si+1}/{total_scenes}: {', '.join(obj_names)}")

    # FFmpeg 编码
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
    llm_fn=None,
) -> str:
    """
    从文案生成线条插画手绘视频。

    Pipeline:
      Script → LLM Scene Planner → Scene Layouts → Frame Rendering → Video

    Args:
        script_lines: 文案列表
        output_path: 输出路径
        draw_duration: 绘制时长
        hold_duration: 停留时长
        llm_fn: LLM 调用函数 (prompt) -> response。如果为 None 则用回退方案。
    """
    print(f"\n  Script lines: {len(script_lines)}")
    for i, line in enumerate(script_lines):
        print(f"    [{i+1}] {line}")

    # 使用 LLM 或回退方案
    if llm_fn:
        print(f"\n  使用 LLM 规划场景...")
        scenes = texts_to_scenes_with_llm(script_lines, llm_fn)
    else:
        print(f"\n  使用回退方案（关键词匹配）...")
        scenes = texts_to_scenes_fallback(script_lines)

    return render_lineart_video(
        scenes, output_path,
        draw_duration=draw_duration,
        hold_duration=hold_duration,
    )


# ═══════════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Line Art Renderer v2 — Test")
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
        output_path="output/test_lineart_v2.mp4",
        draw_duration=3.5,
        hold_duration=2.0,
    )

    print(f"\nDone! Output: {output}")
