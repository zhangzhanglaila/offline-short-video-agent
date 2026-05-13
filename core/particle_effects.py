# -*- coding: utf-8 -*-
"""
粒子特效 + 漏光转场引擎 — 纯 Pillow 生成叠加层 PNG
零新依赖。为视频增光添彩：火花粒子、浮动尘埃、电影漏光、脉冲光环。
"""
import math
import random as _random
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFilter

_ORNG = _random.Random()


def _hex_to_rgba(hex_str: str, alpha: int = 255) -> tuple:
    h = hex_str.lstrip('#')
    if len(h) == 8:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16))
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)
    return (0, 0, 0, alpha)


# ═══════════════════════════════════════════════════════════════
# 火花粒子叠加层
# ═══════════════════════════════════════════════════════════════

def generate_sparkle_overlay(output_path: str, width: int = 1080, height: int = 1920,
                              particle_count: int = 60, accent_hex: str = "#FFD700",
                              seed: int = None) -> str:
    """生成金色/彩色火花粒子 PNG 叠加层 — 用于大数字/强调场景。

    粒子特征：不同大小(2-8px)、随机位置、辉光晕染、部分十字星芒。
    """
    rng = _random.Random(seed or 42)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    accent = _hex_to_rgba(accent_hex)

    for _ in range(particle_count):
        x = rng.randint(40, width - 40)
        y = rng.randint(40, height - 40)
        size = rng.randint(2, 8)
        alpha = rng.randint(120, 255)
        color = (accent[0], accent[1], accent[2], alpha)

        # 辉光晕
        glow_r = size * 2.5
        glow_alpha = alpha // 4
        for gr in range(int(glow_r), int(glow_r * 0.3), -1):
            ga = glow_alpha * (gr / glow_r)
            draw.ellipse([x - gr, y - gr, x + gr, y + gr],
                         fill=(color[0], color[1], color[2], int(ga)))

        # 核心点
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

        # 十字星芒（大粒子专用）
        if size >= 5 and rng.random() < 0.4:
            beam_len = size * 4
            for angle in [0, math.pi / 2, math.pi / 4, -math.pi / 4]:
                ex = x + int(beam_len * math.cos(angle))
                ey = y + int(beam_len * math.sin(angle))
                beam_alpha = alpha // 3
                draw.line([(x, y), (ex, ey)],
                          fill=(color[0], color[1], color[2], beam_alpha), width=max(1, size // 3))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 浮动尘埃
# ═══════════════════════════════════════════════════════════════

def generate_dust_overlay(output_path: str, width: int = 1080, height: int = 1920,
                           particle_count: int = 120, seed: int = None) -> str:
    """生成极细微浮动尘埃 — 增强电影质感。"""
    rng = _random.Random(seed or 7)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    for _ in range(particle_count):
        x = rng.randint(0, width)
        y = rng.randint(0, height)
        size = rng.randint(1, 3)
        alpha = rng.randint(15, 60)
        draw.ellipse([x, y, x + size, y + size],
                     fill=(255, 255, 240, alpha))

    # 微模糊
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 电影漏光转场
# ═══════════════════════════════════════════════════════════════

def generate_light_leak(output_path: str, width: int = 1080, height: int = 1920,
                         style: str = "warm", seed: int = None) -> str:
    """生成电影级漏光叠加层 PNG — 有机光斑/光晕，用于转场。

    style: warm(暖橙)/cool(冷蓝)/mixed(混合)
    """
    rng = _random.Random(seed or 99)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    styles = {
        "warm": [(255, 180, 80), (255, 140, 40), (255, 220, 140)],
        "cool": [(80, 160, 255), (40, 100, 220), (140, 200, 255)],
        "mixed": [(255, 160, 60), (80, 140, 255), (255, 200, 120)],
    }
    palette = styles.get(style, styles["warm"])

    # 2-4 个大型有机光斑
    spot_count = rng.randint(2, 4)
    for _ in range(spot_count):
        cx = rng.randint(0, width)
        cy = rng.randint(0, height // 3)  # 集中在画面上部
        max_r = rng.randint(height // 4, height // 2)
        color = rng.choice(palette)

        # 多层渐隐光晕
        for layer in range(6):
            r = int(max_r * (1 - layer * 0.15))
            alpha = int(40 * (1 - layer * 0.15))
            if r > 0 and alpha > 0:
                draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                             fill=(color[0], color[1], color[2], alpha))

    # 高斯模糊让光斑更有机
    img = img.filter(ImageFilter.GaussianBlur(radius=width / 80))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def generate_light_leak_set(output_dir: str, width: int = 1080, height: int = 1920,
                             count: int = 8) -> List[str]:
    """生成一组漏光转场 PNG，供随机选用。"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    styles = ["warm", "cool", "mixed"]
    for i in range(count):
        fp = str(out / f"light_leak_{i:02d}.png")
        generate_light_leak(fp, width, height, style=styles[i % len(styles)], seed=i * 13)
        paths.append(fp)
    return paths


# ═══════════════════════════════════════════════════════════════
# 脉冲光环 (用于 big_number 场景)
# ═══════════════════════════════════════════════════════════════

def generate_pulse_ring(output_path: str, width: int = 1080, height: int = 1920,
                         ring_radius: int = 200, accent_hex: str = "#E04040",
                         ring_count: int = 3) -> str:
    """生成脉冲光环 PNG — 同心圆环围绕中心点，用于 big_number 强调。"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    accent = _hex_to_rgba(accent_hex)
    cx, cy = width // 2, height // 2

    for ri in range(ring_count):
        r = ring_radius + ri * 40
        alpha = max(30, 180 - ri * 50)
        width_px = max(1, 4 - ri)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=(accent[0], accent[1], accent[2], alpha), width=width_px)

    # 外圈辉光
    glow_r = ring_radius + ring_count * 40 + 30
    glow_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img, "RGBA")
    glow_draw.ellipse([cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r],
                      outline=(accent[0], accent[1], accent[2], 25), width=18)
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=15))
    img = Image.alpha_composite(img, glow_img)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


# ═══════════════════════════════════════════════════════════════
# 场景叠加层综合生成
# ═══════════════════════════════════════════════════════════════

def generate_overlays_for_scenes(scenes: List[dict], output_dir: str,
                                  width: int = 1080, height: int = 1920) -> dict:
    """根据场景列表生成对应叠加层。

    返回: {scene_index: {"sparkle": path, "pulse_ring": path, ...}}
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    overlays = {}

    for i, scene in enumerate(scenes):
        emphasis = scene.get("emphasis", "")
        ve = scene.get("visual_element", "")

        scene_overlays = {}

        if emphasis == "big_number" or ve == "big_number":
            fp = str(out / f"sparkle_{i:03d}.png")
            generate_sparkle_overlay(fp, width, height, particle_count=80, seed=i * 31)
            scene_overlays["sparkle"] = fp

            fp2 = str(out / f"pulse_{i:03d}.png")
            generate_pulse_ring(fp2, width, height, ring_radius=min(width, height) // 5, seed=i * 17)
            scene_overlays["pulse_ring"] = fp2

        elif emphasis in ("chart_done",):
            fp = str(out / f"sparkle_{i:03d}.png")
            generate_sparkle_overlay(fp, width, height, particle_count=35,
                                      accent_hex="#FFD700", seed=i * 31)
            scene_overlays["sparkle"] = fp

        if scene_overlays:
            overlays[str(i)] = scene_overlays

    return overlays
