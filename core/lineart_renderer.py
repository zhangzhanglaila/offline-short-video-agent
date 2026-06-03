# -*- coding: utf-8 -*-
"""
Line Art Renderer — 逐帧渲染线条插画手绘动画

核心原理：
  每条 path 的总长度 = pathLength
  strokeDasharray = pathLength
  strokeDashoffset 从 pathLength → 0
  效果 = 线条从起点逐步绘制到终点

在 PIL 中实现：
  1. 计算每条 path 的总长度
  2. 根据当前进度，只绘制前 N 个点
  3. 最后一个点用插值平滑过渡
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.svg_lineart_library import (
    LineArt, PathData, get_lineart,
    PERSON_STANDING, LAPTOP, BOOK_OPEN, CITY_SKYLINE, ROBOT, BRAIN,
)

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# 样式配置
# ═══════════════════════════════════════════════════════════════

LINEART_STYLE = {
    "bg": "#F8F8F8",
    "line": "#1F1F1F",
    "accent": "#FF6B5A",
    "line_width": 3,
    "font_size": 28,
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


def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ═══════════════════════════════════════════════════════════════
# 路径长度计算
# ═══════════════════════════════════════════════════════════════

def _path_length(points: List[Tuple[float, float]]) -> float:
    """计算折线总长度"""
    total = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        total += math.sqrt(dx * dx + dy * dy)
    return total


def _interpolate_on_path(
    points: List[Tuple[float, float]],
    target_length: float,
) -> Tuple[List[Tuple[float, float]], Tuple[float, float]]:
    """
    沿路径走 target_length 距离，返回已走过的点 + 最终插值点。
    """
    if not points:
        return [], (0, 0)

    result = [points[0]]
    accumulated = 0.0

    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        seg_len = math.sqrt(dx * dx + dy * dy)

        if accumulated + seg_len <= target_length:
            result.append(points[i])
            accumulated += seg_len
        else:
            # 在这条线段上插值
            remaining = target_length - accumulated
            if seg_len > 0:
                t = remaining / seg_len
                ix = points[i-1][0] + dx * t
                iy = points[i-1][1] + dy * t
                result.append((ix, iy))
            return result, result[-1]

    return result, result[-1]


# ═══════════════════════════════════════════════════════════════
# 单条 Path 绘制
# ═══════════════════════════════════════════════════════════════

def _draw_path_animated(
    draw: ImageDraw.ImageDraw,
    path: PathData,
    ox: float,
    oy: float,
    scale: float,
    progress: float,
    color: Tuple[int, int, int],
    line_width: int,
):
    """
    绘制一条 path，根据 progress (0-1) 决定绘制多少。

    实现 strokeDashoffset 效果：
      progress=0 → 不绘制
      progress=0.5 → 绘制前 50% 的路径
      progress=1 → 完整绘制
    """
    if progress <= 0:
        return

    # 转换坐标
    pil_points = path.to_pil_points(ox, oy, scale)
    if len(pil_points) < 2:
        return

    # 计算总长度
    total_len = _path_length(pil_points)
    if total_len <= 0:
        return

    # 目标长度
    draw_len = total_len * _ease_out_cubic(_clamp(progress))

    # 获取要绘制的点
    drawn_points, end_point = _interpolate_on_path(pil_points, draw_len)

    if len(drawn_points) < 2:
        return

    # 绘制线条
    draw.line(drawn_points, fill=color, width=line_width, joint="curve")

    # 如果是闭合路径且进度=1，连接首尾
    if path.closed and progress >= 0.99:
        draw.line([drawn_points[-1], drawn_points[0]], fill=color, width=line_width, joint="curve")


# ═══════════════════════════════════════════════════════════════
# 整幅插画绘制
# ═══════════════════════════════════════════════════════════════

def render_lineart_frame(
    art: LineArt,
    canvas_w: int,
    canvas_h: int,
    progress: float,
    art_x: float = 0,
    art_y: float = 0,
    art_scale: float = 1.0,
    line_width: int = 3,
    color: Tuple[int, int, int] = (31, 31, 31),
    bg_color: Tuple[int, int, int] = (248, 248, 248),
) -> Image.Image:
    """
    渲染一幅线条插画的某一帧。

    Args:
        art: 线条插画数据
        canvas_w, canvas_h: 画布尺寸
        progress: 总体进度 0-1（所有 path 同步推进）
        art_x, art_y: 插画在画布上的位置
        art_scale: 缩放（1.0 = 100px 宽）
        line_width: 线条宽度
        color: 线条颜色
        bg_color: 背景颜色

    Returns:
        PIL Image
    """
    img = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    draw = ImageDraw.Draw(img)

    # 计算每条 path 的进度（交错动画：每条 path 稍微延迟）
    n_paths = len(art.paths)
    for i, path in enumerate(art.paths):
        # 交错：每条 path 延迟 offset
        offset = i * 0.08  # 每条延迟 8%
        path_progress = _clamp((progress - offset) / (1.0 - offset * (n_paths - 1) / n_paths))

        # 选择颜色：标签为特殊用途的用强调色
        path_color = color
        if path.label in ("heart", "antenna_tip", "led1", "led2", "led3"):
            path_color = (255, 107, 90)  # accent

        _draw_path_animated(
            draw, path,
            ox=art_x, oy=art_y, scale=art_scale,
            progress=path_progress,
            color=path_color,
            line_width=line_width,
        )

    return img


def render_scene_frame(
    illustrations: List[Tuple[LineArt, float, float, float]],
    canvas_w: int = 1920,
    canvas_h: int = 1080,
    progress: float = 1.0,
    bg_color: Tuple[int, int, int] = (248, 248, 248),
    line_color: Tuple[int, int, int] = (31, 31, 31),
    title: str = "",
    line_width: int = 3,
) -> Image.Image:
    """
    渲染一个包含多个插画的场景。
    直接在画布上绘制所有插画，不做合成。
    """
    img = Image.new("RGB", (canvas_w, canvas_h), bg_color)
    draw = ImageDraw.Draw(img)

    n = len(illustrations)
    for i, (art, x, y, scale) in enumerate(illustrations):
        # 每个插画交错出现
        offset = i * 0.15
        art_progress = _clamp((progress - offset) / max(0.3, 1.0 - offset))

        # 直接在画布上绘制每条 path
        n_paths = len(art.paths)
        for j, path in enumerate(art.paths):
            path_offset = j * 0.08
            path_progress = _clamp((art_progress - path_offset) / max(0.1, 1.0 - path_offset * (n_paths - 1) / n_paths))

            path_color = line_color
            if path.label in ("heart", "antenna_tip", "led1", "led2", "led3"):
                path_color = (255, 107, 90)

            _draw_path_animated(
                draw, path,
                ox=x, oy=y, scale=scale,
                progress=path_progress,
                color=path_color,
                line_width=line_width,
            )

    # 绘制标题
    if title and progress > 0.5:
        title_progress = _clamp((progress - 0.5) / 0.3)
        font = _get_font(36)
        visible_chars = max(1, int(len(title) * title_progress))
        visible_title = title[:visible_chars]

        bbox = draw.textbbox((0, 0), visible_title, font=font)
        tw = bbox[2] - bbox[0]
        tx = (canvas_w - tw) / 2
        ty = canvas_h - 100

        draw.text((tx, ty), visible_title, fill=line_color, font=font)

    return img


# ═══════════════════════════════════════════════════════════════
# 视频生成
# ═══════════════════════════════════════════════════════════════

def render_lineart_video(
    scenes: List[dict],
    output_path: str,
    canvas_w: int = 1920,
    canvas_h: int = 1080,
    fps: int = 30,
    draw_duration: float = 3.0,
    hold_duration: float = 2.0,
):
    """
    生成线条插画手绘视频。

    Args:
        scenes: 场景列表 [{"illustrations": [(keyword, x, y, scale), ...], "title": "..."}]
        output_path: 输出路径
        canvas_w, canvas_h: 画布尺寸
        fps: 帧率
        draw_duration: 每幅插画的绘制时长（秒）
        hold_duration: 绘制完成后的停留时长（秒）
    """
    output_path = Path(output_path)
    temp_dir = output_path.parent / f"_lineart_frames_{output_path.stem}"

    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    frame_idx = 0
    bg = _hex_to_rgb(LINEART_STYLE["bg"])
    line = _hex_to_rgb(LINEART_STYLE["line"])

    total_scenes = len(scenes)
    print(f"\n{'='*50}")
    print(f"  Line Art Animation")
    print(f"  Scenes: {total_scenes}")
    print(f"  Canvas: {canvas_w}x{canvas_h}")
    print(f"{'='*50}")

    for scene_idx, scene in enumerate(scenes):
        title = scene.get("title", "")
        raw_illusts = scene.get("illustrations", [])

        # 转换为 (LineArt, x, y, scale)
        illustrations = []
        for item in raw_illusts:
            if isinstance(item, str):
                keyword = item
                x, y, scale = 100, 100, 1.0
            elif isinstance(item, dict):
                keyword = item.get("keyword", "person")
                x = item.get("x", 100)
                y = item.get("y", 100)
                scale = item.get("scale", 1.0)
            elif isinstance(item, tuple) and len(item) == 4:
                keyword, x, y, scale = item
            else:
                continue

            art = get_lineart(keyword)
            illustrations.append((art, x, y, scale))

        if not illustrations:
            continue

        # 绘制阶段：progress 0→1
        draw_frames = int(draw_duration * fps)
        for f in range(draw_frames):
            progress = f / draw_frames
            img = render_scene_frame(
                illustrations, canvas_w, canvas_h, progress,
                bg_color=bg, line_color=line, title=title,
            )
            img.save(str(temp_dir / f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

        # 停留阶段：保持最后一帧
        hold_frames = int(hold_duration * fps)
        last_img = render_scene_frame(
            illustrations, canvas_w, canvas_h, 1.0,
            bg_color=bg, line_color=line, title=title,
        )
        for f in range(hold_frames):
            last_img.save(str(temp_dir / f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

        print(f"  Scene {scene_idx+1}/{total_scenes}: "
              f"{len(illustrations)} illustrations, "
              f"{draw_duration + hold_duration:.1f}s")

    # FFmpeg 编码
    print(f"\n  Encoding video ({frame_idx} frames)...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(temp_dir / "frame_%05d.png"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, timeout=300)

    # 清理
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    print(f"  Output: {output_path}")
    return str(output_path)


# ═══════════════════════════════════════════════════════════════
# 场景理解：文案 → 插画组合
# ═══════════════════════════════════════════════════════════════

def _extract_visual_keyword(text: str) -> str:
    """从文案中提取视觉关键词"""
    text_lower = text.lower()

    # 优先匹配具体对象
    priority = [
        "robot", "laptop", "computer", "book", "brain", "server",
        "database", "city", "building", "cloud", "gear", "lightbulb",
        "person", "monitor", "network", "chat",
    ]
    for kw in priority:
        if kw in text_lower:
            return kw

    # 中文匹配
    cn_map = {
        "机器人": "robot", "电脑": "laptop", "计算机": "computer",
        "书": "book", "脑": "brain", "服务器": "server",
        "数据库": "database", "城市": "city", "建筑": "building",
        "云": "cloud", "齿轮": "gear", "灯": "lightbulb",
        "人": "person", "屏幕": "monitor", "网络": "network",
        "消息": "chat", "聊天": "chat", "搜索": "search",
        "缓存": "database", "redis": "database",
        "agent": "robot", "智能": "brain", "思考": "brain",
    }
    for cn, en in cn_map.items():
        if cn in text:
            return en

    return "person"


def text_to_scene(text: str, canvas_w: int = 1920, canvas_h: int = 1080) -> dict:
    """
    将一句文案转换为一个场景描述。

    Returns:
        {"illustrations": [(keyword, x, y, scale), ...], "title": "..."}
    """
    # 提取关键词
    keyword = _extract_visual_keyword(text)

    # 计算布局（居中）
    art = get_lineart(keyword)
    scale = min(canvas_w, canvas_h) / 150  # 插画占画布约 60%
    x = (canvas_w - art.width * scale) / 2
    y = (canvas_h - art.height * scale) / 2 - 40  # 稍微偏上，留空间给标题

    return {
        "illustrations": [(keyword, x, y, scale)],
        "title": text[:30],  # 标题取前30字
    }


def texts_to_scenes(texts: List[str]) -> List[dict]:
    """将多句文案转换为多个场景"""
    return [text_to_scene(t) for t in texts]


# ═══════════════════════════════════════════════════════════════
# 完整管线入口
# ═══════════════════════════════════════════════════════════════

def generate_lineart_video(
    script_lines: List[str],
    output_path: str = "output/lineart_video.mp4",
    draw_duration: float = 3.0,
    hold_duration: float = 2.0,
) -> str:
    """
    从文案生成线条插画手绘视频。

    Args:
        script_lines: 文案列表（每行一个场景）
        output_path: 输出路径
        draw_duration: 绘制时长
        hold_duration: 停留时长

    Returns:
        输出路径
    """
    scenes = texts_to_scenes(script_lines)
    return render_lineart_video(
        scenes, output_path,
        draw_duration=draw_duration,
        hold_duration=hold_duration,
    )


# ═══════════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Line Art Renderer — Test")
    print("=" * 50)

    # 测试所有可用插画
    from core.svg_lineart_library import list_available, KEYWORD_MAP

    print(f"\n可用插画: {len(KEYWORD_MAP)} 个关键词映射")
    print(f"插画类型: {', '.join(sorted(set(a.name for a in KEYWORD_MAP.values())))}")

    # 生成测试视频
    script = [
        "AI Agent 是一种智能系统",
        "Agent 使用 Tool 获取信息",
        "数据存储在 Database 中",
        "Brain 处理并生成决策",
        "Robot 执行最终任务",
    ]

    output = generate_lineart_video(
        script,
        output_path="output/test_lineart.mp4",
        draw_duration=2.5,
        hold_duration=1.5,
    )

    print(f"\nDone! Output: {output}")
