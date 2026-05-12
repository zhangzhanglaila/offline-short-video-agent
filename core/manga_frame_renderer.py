# -*- coding: utf-8 -*-
"""
漫画帧渲染引擎 — 真正的日式漫画风格竖屏帧生成器
用 Pillow + numpy 生成网点纸、气泡框、速度线、分镜格等漫画元素。
输出 1080×1920 竖屏 PNG，文字讲解为主，图片为辅。
"""
import math
import random
from pathlib import Path
from typing import List, Optional, Tuple
from io import BytesIO

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import config


# ── 漫画风格默认值 ──────────────────────────────────────────
MANGA = getattr(config, "MANGA_STYLE_CONFIG", {
    "paper_color": "#FFF8F0",
    "panel_gap": 14,
    "border_width": 5,
    "halftone_dot_size": 3,
    "halftone_spacing": 6,
    "speedline_count": 28,
    "text_color_primary": "#1A1A2E",
    "accent_red": "#E04040",
    "accent_blue": "#3060C0",
})

W = 1080   # 竖屏宽度
H = 1920   # 竖屏高度
PANEL_GAP = MANGA["panel_gap"]
BORDER_W = MANGA["border_width"]
PAPER = MANGA["paper_color"]
TEXT_C = MANGA["text_color_primary"]
RED = MANGA["accent_red"]
BLUE = MANGA["accent_blue"]


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def _load_fonts():
    """加载漫画用字体：标题粗体、正文、SFX大字。"""
    fonts = {}
    font_roots = [
        "C:/Windows/Fonts",
        "/System/Library/Fonts",
        "/usr/share/fonts",
        "/usr/local/share/fonts",
    ]
    candidates = {
        "title": ["msyhbd.ttc", "simhei.ttf", "NotoSansCJK-Bold.ttc", "Arial Bold.ttf"],
        "body":  ["msyh.ttc", "simsun.ttc", "NotoSansCJK-Regular.ttc", "Arial.ttf"],
        "sfx":   ["simhei.ttf", "msyhbd.ttc", "Impact.ttf", "Arial.ttf"],
    }

    for key, names in candidates.items():
        for name in names:
            for root in font_roots:
                fp = Path(root) / name
                if fp.exists():
                    try:
                        fonts[key] = str(fp)
                        break
                    except Exception:
                        continue
            if key in fonts:
                break
        if key not in fonts:
            fonts[key] = None  # 回退到 default
    return fonts


_FONTS = None

def _get_font(size: int, style: str = "body") -> ImageFont.FreeTypeFont:
    global _FONTS
    if _FONTS is None:
        _FONTS = _load_fonts()
    fp = _FONTS.get(style)
    if fp:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            pass
    try:
        return ImageFont.truetype(_FONTS.get("body") or "", size)
    except Exception:
        return ImageFont.load_default()


# ═══════════════════════════════════════════════════════════════
# 网点纸 / 砂目 (Halftone / Screentone)
# ═══════════════════════════════════════════════════════════════

def _halftone_pattern(width: int, height: int,
                      dot_size: int = 3, spacing: int = 6,
                      angle_deg: float = 45) -> Image.Image:
    """生成圆点网点纸图案 (灰度图，用于叠加/遮罩)。"""
    if not HAS_NUMPY:
        return None
    period = dot_size + spacing
    if period < 2:
        period = 2
    angle = math.radians(angle_deg)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    xs = np.arange(width, dtype=np.float64)
    ys = np.arange(height, dtype=np.float64)
    xv, yv = np.meshgrid(xs, ys)
    # 旋转坐标系
    xx = xv * cos_a - yv * sin_a
    yy = xv * sin_a + yv * cos_a
    # 到最近网点中心的距离
    cx = np.round(xx / period) * period
    cy = np.round(yy / period) * period
    dx = xx - cx
    dy = yy - cy
    dist = np.sqrt(dx * dx + dy * dy)

    mask = (dist <= dot_size / 2.0).astype(np.uint8) * 255
    return Image.fromarray(mask, mode="L")


def apply_halftone(canvas: Image.Image, region: Tuple[int,int,int,int],
                   dot_size: int = None, spacing: int = None,
                   angle: float = 45, opacity: float = 0.35):
    """在 canvas 的指定区域上叠加网点纸效果。"""
    if not HAS_NUMPY:
        # 降级：用纯色覆盖表示网点
        overlay = Image.new("RGBA", (region[2]-region[0], region[3]-region[1]),
                            (0, 0, 0, int(opacity * 255)))
        canvas.paste(overlay, (region[0], region[1]), overlay)
        return

    ds = dot_size if dot_size is not None else MANGA["halftone_dot_size"]
    sp = spacing if spacing is not None else MANGA["halftone_spacing"]
    rw = region[2] - region[0]
    rh = region[3] - region[1]
    if rw <= 0 or rh <= 0:
        return

    pattern = _halftone_pattern(rw, rh, ds, sp, angle)
    if pattern is None:
        return

    # 转为 RGBA 叠加
    alpha = pattern.point(lambda p: int(p * opacity) if p > 0 else 0)
    overlay = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    overlay.putalpha(alpha)
    canvas.paste(overlay, (region[0], region[1]), overlay)


# ═══════════════════════════════════════════════════════════════
# 速度线 / 集中线 (Speed Lines)
# ═══════════════════════════════════════════════════════════════

def draw_speed_lines(draw: ImageDraw.Draw,
                     cx: int, cy: int,
                     inner_r: int, outer_r: int,
                     count: int = 28, opacity: int = 60):
    """以 (cx,cy) 为中心绘制辐射状速度线（集中线）。"""
    color = (0, 0, 0, opacity) if isinstance(draw, object) else (0, 0, 0)
    for i in range(count):
        angle = (2 * math.pi * i / count) + random.uniform(-0.08, 0.08)
        # 线条长度微变化
        r1 = inner_r + random.randint(0, 15)
        r2 = outer_r - random.randint(0, 30)
        x1 = cx + int(r1 * math.cos(angle))
        y1 = cy + int(r1 * math.sin(angle))
        x2 = cx + int(r2 * math.cos(angle))
        y2 = cy + int(r2 * math.sin(angle))
        w = random.randint(1, 3)
        draw.line([(x1, y1), (x2, y2)], fill=(0, 0, 0, opacity), width=w)


def draw_parallel_speed_lines(draw: ImageDraw.Draw,
                              x0: int, y0: int, x1: int, y1: int,
                              count: int = 16, opacity: int = 50):
    """绘制平行速度线（水平或垂直方向的动态线）。"""
    for i in range(count):
        if abs(x1 - x0) > abs(y1 - y0):
            # 水平方向
            frac = i / max(count - 1, 1)
            y = y0 + int((y1 - y0) * frac)
            lx = x0 + random.randint(-20, 20)
            rx = x1 + random.randint(-20, 20)
            segs = [(lx, y)]
            cx_pos = lx
            while cx_pos < rx:
                seg_len = random.randint(30, 120)
                cx_pos += seg_len
                cy_jitter = y + random.randint(-4, 4)
                segs.append((min(cx_pos, rx), cy_jitter))
            for s in range(len(segs) - 1):
                w = random.randint(1, 3)
                draw.line([segs[s], segs[s+1]], fill=(0, 0, 0, opacity), width=w)
        else:
            frac = i / max(count - 1, 1)
            x = x0 + int((x1 - x0) * frac)
            ty = y0 + random.randint(-20, 20)
            by = y1 + random.randint(-20, 20)
            segs = [(x, ty)]
            cy_pos = ty
            while cy_pos < by:
                seg_len = random.randint(30, 120)
                cy_pos += seg_len
                cx_jitter = x + random.randint(-4, 4)
                segs.append((cx_jitter, min(cy_pos, by)))
            for s in range(len(segs) - 1):
                w = random.randint(1, 3)
                draw.line([segs[s], segs[s+1]], fill=(0, 0, 0, opacity), width=w)


# ═══════════════════════════════════════════════════════════════
# 对话框 / 气泡 (Speech Bubble)
# ═══════════════════════════════════════════════════════════════

def draw_speech_bubble(draw: ImageDraw.Draw,
                       bounds: Tuple[int,int,int,int],
                       tail_tip: Tuple[int,int],
                       tail_base_width: int = 30,
                       fill_color: str = "#FFFFFF",
                       outline_color: str = "#1A1A2E",
                       outline_width: int = 4):
    """绘制椭圆对话框 + 三角尾巴。

    bounds: (x0, y0, x1, y1) — 椭圆包围盒
    tail_tip: (tx, ty) — 尾巴尖端点
    """
    x0, y0, x1, y1 = bounds
    # 圆角矩形主体
    r = 24
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r,
                           fill=fill_color, outline=outline_color,
                           width=outline_width)

    # 三角尾巴 — 决定尾巴方向
    tx, ty = tail_tip
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2

    # 找最近边的连接点
    if tx < x0:  # 左侧
        bx, by = x0 + 10, max(y0 + 40, min(y1 - 40, ty))
    elif tx > x1:  # 右侧
        bx, by = x1 - 10, max(y0 + 40, min(y1 - 40, ty))
    elif ty < y0:  # 上方
        bx, by = max(x0 + 40, min(x1 - 40, tx)), y0 + 10
    else:  # 下方
        bx, by = max(x0 + 40, min(x1 - 40, tx)), y1 - 10

    # 尾巴三角形
    hw = tail_base_width // 2
    if abs(tx - bx) > abs(ty - by):
        dy = hw
        dx = abs(tx - bx) // 3
        mid_x = (tx + bx) // 2
        pts = [(tx, ty), (bx - dx, by - dy), (bx + dx, by + dy)]
    else:
        dx = hw
        dy = abs(ty - by) // 3
        mid_y = (ty + by) // 2
        pts = [(tx, ty), (bx - dx, by - dy), (bx + dx, by + dy)]

    # 先用填充色画三角形盖住边框线
    draw.polygon(pts, fill=fill_color)
    # 再画三角形轮廓
    draw.line([pts[0], pts[1]], fill=outline_color, width=outline_width)
    draw.line([pts[0], pts[2]], fill=outline_color, width=outline_width)
    # 重画气泡主体边框（盖住连接处）
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r,
                           fill=None, outline=outline_color, width=outline_width)


def draw_thought_bubble(draw: ImageDraw.Draw,
                        bounds: Tuple[int,int,int,int],
                        tail_origin: Tuple[int,int],
                        fill_color: str = "#FFFFFF",
                        outline_color: str = "#A0A8B0"):
    """绘制云朵状思考气泡（小圆点组成的尾巴）。"""
    x0, y0, x1, y1 = bounds
    # 主气泡：更圆润
    draw.rounded_rectangle([x0, y0, x1, y1], radius=30,
                           fill=fill_color, outline=outline_color, width=3)

    # 云朵尾巴：一串递减的小圆
    tx, ty = tail_origin
    # 找气泡最近点
    if tx < x0:
        sx, sy = x0, max(y0 + 30, min(y1 - 30, ty))
    elif tx > x1:
        sx, sy = x1, max(y0 + 30, min(y1 - 30, ty))
    elif ty < y0:
        sx, sy = max(x0 + 30, min(x1 - 30, tx)), y0
    else:
        sx, sy = max(x0 + 30, min(x1 - 30, tx)), y1

    sizes = [14, 10, 7, 5]
    for i, r in enumerate(sizes):
        frac = (i + 1) / len(sizes)
        px = int(sx + (tx - sx) * frac)
        py = int(sy + (ty - sy) * frac)
        draw.ellipse([px - r, py - r, px + r, py + r],
                     fill=fill_color, outline=outline_color, width=2)


# ═══════════════════════════════════════════════════════════════
# 分镜格面板 (Panel)
# ═══════════════════════════════════════════════════════════════

def draw_manga_panel(draw: ImageDraw.Draw,
                     bounds: Tuple[int,int,int,int],
                     border_color: str = "#1A1A2E",
                     border_width: int = None,
                     inner_highlight: bool = True):
    """绘制漫画分镜格边框（外粗内细双线）。"""
    bw = border_width if border_width is not None else BORDER_W
    x0, y0, x1, y1 = bounds
    # 外边框（粗）
    draw.rectangle([x0, y0, x1, y1], outline=border_color, width=bw)
    # 内边框（细，留间隙）
    if inner_highlight and bw >= 4:
        inset = bw + 2
        draw.rectangle([x0 + inset, y0 + inset, x1 - inset, y1 - inset],
                       outline=border_color, width=max(1, bw // 3))


# ═══════════════════════════════════════════════════════════════
# 漫画帧渲染器主类
# ═══════════════════════════════════════════════════════════════

class MangaFrameRenderer:
    """漫画帧渲染器 — 生成真正的漫画风格讲解帧。"""

    def __init__(self, width: int = None, height: int = None,
                 dark_mode: bool = False):
        self.w = width or W
        self.h = height or H
        self.dark = dark_mode
        if dark_mode:
            self.paper = "#1E1E2E"
            self.panel_bg = "#2A2A3C"
            self.bubble_bg = "#323248"
            self.text_c = "#E8E8F0"
        else:
            self.paper = PAPER
            self.panel_bg = "#FFFBF5"
            self.bubble_bg = "#FFFFFF"
            self.text_c = TEXT_C

    # ── 单帧渲染 ──────────────────────────────────────────

    def render_frame(self,
                     title: str,
                     bullets: List[str],
                     output_path: str,
                     subtitle: str = "",
                     media_path: str = None,
                     scene_index: int = 0,
                     total_scenes: int = 1,
                     sfx_text: str = "",
                     accent_color: str = None) -> str:
        """渲染单帧漫画讲解图。

        布局 (1080×1920)：
        ┌──────────────────────────┐
        │  标题面板 + 网点背景       │  240px
        │  ▸ SFX 拟声词（可选）     │
        ├──────────────┬───────────┤
        │  要点气泡1    │           │
        │  要点气泡2    │  素材图片  │  主内容区 ~1400px
        │  要点气泡3    │  (可选)   │
        │  要点气泡4    │           │
        ├──────────────┴───────────┤
        │  副标题/补充说明           │  200px
        │  场景编号                 │
        └──────────────────────────┘
        """
        accent = accent_color or (RED if not self.dark else "#FF6B6B")

        # 创建画布
        img = Image.new("RGB", (self.w, self.h), self.paper)
        draw = ImageDraw.Draw(img, "RGBA")

        # ── 1. 顶部标题区 ──
        title_y1 = self._draw_title_header(draw, title, sfx_text, accent)

        # ── 2. 底部信息区 ──
        bottom_y0 = self._draw_bottom_bar(draw, subtitle, scene_index, total_scenes, accent)

        # ── 3. 中间主内容区 ──
        main_y0 = title_y1 + PANEL_GAP
        main_y1 = bottom_y0 - PANEL_GAP

        has_media = media_path and Path(media_path).exists()
        if has_media:
            self._draw_content_with_media(draw, img, bullets, media_path,
                                          main_y0, main_y1, accent)
        else:
            self._draw_content_text_only(draw, img, bullets,
                                         main_y0, main_y1, accent)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, quality=92)
        return output_path

    # ── 标题头 ──────────────────────────────────────────

    def _draw_title_header(self, draw, title: str, sfx: str, accent: str) -> int:
        """绘制顶部标题面板，返回标题区底部 y 坐标。"""
        header_h = 260
        y0, y1 = PANEL_GAP, PANEL_GAP + header_h

        # 标题面板背景
        draw.rounded_rectangle([PANEL_GAP, y0, self.w - PANEL_GAP, y1],
                               radius=16, fill=self.panel_bg,
                               outline="#1A1A2E", width=BORDER_W)

        # 内边框装饰
        draw.rounded_rectangle([PANEL_GAP + BORDER_W + 3, y0 + BORDER_W + 3,
                                self.w - PANEL_GAP - BORDER_W - 3, y1 - BORDER_W - 3],
                               radius=12, outline="#1A1A2E", width=2)

        # SFX 拟声词（大号字，描边）
        sfx_font = _get_font(72, "sfx")
        if sfx:
            sfx_w = draw.textlength(sfx, font=sfx_font)
            sfx_x = self.w - PANEL_GAP - 50 - int(sfx_w)
            sfx_y = y0 + 20
            for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                draw.text((sfx_x + ox, sfx_y + oy), sfx, fill="#1A1A2E", font=sfx_font)
            draw.text((sfx_x, sfx_y), sfx, fill=accent, font=sfx_font)

        # 标题文字（描边）
        title_font = _get_font(52, "title")
        tx = PANEL_GAP + 30
        ty = y0 + 50
        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((tx + ox, ty + oy), title[:20], fill="#1A1A2E", font=title_font)
        draw.text((tx, ty), title[:20], fill=accent, font=title_font)

        # 标题下方装饰线
        deco_y = ty + 80
        draw.line([(tx, deco_y), (tx + 200, deco_y)], fill="#1A1A2E", width=3)
        draw.line([(tx, deco_y + 8), (tx + 120, deco_y + 8)], fill=accent, width=2)

        return y1

    # ── 底栏 ────────────────────────────────────────────

    def _draw_bottom_bar(self, draw, subtitle: str, idx: int, total: int, accent: str) -> int:
        """绘制底部信息栏，返回栏顶部 y 坐标。"""
        bar_h = 180
        y1 = self.h - PANEL_GAP
        y0 = y1 - bar_h

        draw.rounded_rectangle([PANEL_GAP, y0, self.w - PANEL_GAP, y1],
                               radius=14, fill=self.panel_bg,
                               outline="#1A1A2E", width=BORDER_W)

        # 场景编号
        num_font = _get_font(28, "body")
        num_text = f"第 {idx+1}/{total} 话"
        draw.text((PANEL_GAP + 24, y0 + 16), num_text, fill="#8A8A9A", font=num_font)

        # 副标题
        if subtitle:
            sub_font = _get_font(32, "body")
            sub = subtitle[:40]
            sub_w = draw.textlength(sub, font=sub_font)
            sub_x = (self.w - int(sub_w)) // 2
            draw.text((sub_x, y0 + 60), sub, fill=self.text_c, font=sub_font)

            # 底部装饰速度线
            line_y = y0 + 110
            draw_parallel_speed_lines(draw, PANEL_GAP + 40, line_y,
                                      self.w - PANEL_GAP - 40, line_y,
                                      count=8, opacity=25)

        # 右侧 "▶ NEXT" 标识
        next_font = _get_font(24, "body")
        draw.text((self.w - PANEL_GAP - 120, y0 + 16), "▶ NEXT",
                  fill=accent, font=next_font)

        return y0

    # ── 纯文字内容区 ────────────────────────────────────

    def _draw_content_text_only(self, draw, img, bullets: List[str],
                                y0: int, y1: int, accent: str):
        """纯文字要点布局：多格不规则排版。"""
        n = len(bullets)
        if n == 0:
            return

        content_h = y1 - y0
        margin = PANEL_GAP + 10

        if n == 1:
            # 单要点：大字居中 + 速度线背景
            self._draw_single_bullet_hero(draw, bullets[0], y0, y1, accent)
        elif n == 2:
            # 双要点：上下平分
            h0 = content_h // 2 - 8
            self._draw_bullet_panel(draw, bullets[0], margin, y0,
                                    self.w - margin, y0 + h0, accent, 0)
            self._draw_bullet_panel(draw, bullets[1], margin, y0 + h0 + 16,
                                    self.w - margin, y1, accent, 1)
        elif n == 3:
            # 三要点：上大下二
            h_top = content_h * 3 // 5
            h_bot = content_h - h_top - 12
            w_half = (self.w - margin * 2 - 12) // 2
            self._draw_bullet_panel(draw, bullets[0], margin, y0,
                                    self.w - margin, y0 + h_top, accent, 0)
            self._draw_bullet_panel(draw, bullets[1], margin, y0 + h_top + 12,
                                    margin + w_half, y1, accent, 1)
            self._draw_bullet_panel(draw, bullets[2], margin + w_half + 12, y0 + h_top + 12,
                                    self.w - margin, y1, accent, 2)
        else:
            # 4+ 要点：2×2 网格
            h_half = (content_h - 12) // 2
            w_half = (self.w - margin * 2 - 12) // 2
            positions = [
                (margin, y0, margin + w_half, y0 + h_half),
                (margin + w_half + 12, y0, self.w - margin, y0 + h_half),
                (margin, y0 + h_half + 12, margin + w_half, y1),
                (margin + w_half + 12, y0 + h_half + 12, self.w - margin, y1),
            ]
            for i, (bx0, by0, bx1, by1) in enumerate(positions[:4]):
                if i < n:
                    self._draw_bullet_panel(draw, bullets[i], bx0, by0, bx1, by1, accent, i)

    def _draw_single_bullet_hero(self, draw, text: str, y0: int, y1: int, accent: str):
        """单要点 Hero 布局：大号文字 + 集中线背景。"""
        cx, cy = self.w // 2, (y0 + y1) // 2
        draw_speed_lines(draw, cx, cy, 120, 580, count=28, opacity=30)

        font = _get_font(56, "title")
        lines = self._wrap_text(text, font, self.w - 200)
        line_h = 78
        total_h = len(lines) * line_h
        start_y = (y0 + y1 - total_h) // 2 + 20

        for ln in lines:
            tw = draw.textlength(ln, font=font)
            x = (self.w - int(tw)) // 2
            for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
                draw.text((x + ox, start_y + oy), ln, fill="#1A1A2E", font=font)
            draw.text((x, start_y), ln, fill=accent, font=font)
            start_y += line_h

    def _draw_bullet_panel(self, draw, text: str,
                           x0: int, y0: int, x1: int, y1: int,
                           accent: str, index: int):
        """绘制单个要点面板：漫画格 + 强调符号 + 文字。"""
        panel_w = x1 - x0
        panel_h = y1 - y0
        if panel_w < 60 or panel_h < 60:
            return

        # 面板背景填充 + 边框
        draw.rounded_rectangle([x0, y0, x1, y1], radius=10,
                               fill=(255, 252, 248, 255) if not self.dark else (40, 40, 55, 255),
                               outline="#1A1A2E", width=BORDER_W)

        # 序号圆圈
        circ_r = 20
        circ_x = x0 + 24
        circ_y = y0 + 20
        draw.ellipse([circ_x, circ_y, circ_x + circ_r * 2, circ_y + circ_r * 2],
                     fill=accent, outline="#1A1A2E", width=3)
        num_font = _get_font(18, "title")
        num_str = str(index + 1)
        nw = draw.textlength(num_str, font=num_font)
        draw.text((circ_x + circ_r - int(nw) // 2, circ_y + 8),
                  num_str, fill="#FFFFFF", font=num_font)

        # 要点文字
        body_font = _get_font(34, "body")
        max_text_w = panel_w - 90
        text_y = y0 + 18
        text_x = circ_x + circ_r * 2 + 18

        # 小面板时缩小字号
        if panel_h < 180:
            body_font = _get_font(26, "body")
        if panel_h < 120:
            body_font = _get_font(20, "body")

        line_h = body_font.size + 12
        lines = self._wrap_text(text, body_font, max_text_w)
        for ln in lines[:3]:
            draw.text((text_x, text_y), ln, fill=self.text_c, font=body_font)
            text_y += line_h

        # 面板角落装饰
        deco_size = 7
        for dx, dy in [(x1 - 14, y0 + 6), (x0 + 6, y1 - 14)]:
            draw.rectangle([dx, dy, dx + deco_size, dy + deco_size], fill=accent)

    # ── 带素材的内容区 ──────────────────────────────────

    def _draw_content_with_media(self, draw, img, bullets: List[str],
                                 media_path: str, y0: int, y1: int, accent: str):
        """文字+素材混合布局：左文字面板 + 右素材图。"""
        content_h = y1 - y0
        media_w = 360
        gap_w = 16

        # 素材图片区域（右侧）
        mx0 = self.w - PANEL_GAP - media_w
        mx1 = self.w - PANEL_GAP
        my0 = y0
        my1 = y1

        # 素材面板背景+边框
        draw.rounded_rectangle([mx0, my0, mx1, my1], radius=12,
                               fill=(255, 252, 248, 255) if not self.dark else (40, 40, 55, 255),
                               outline="#1A1A2E", width=BORDER_W)

        try:
            media_img = Image.open(media_path).convert("RGB")
            mw = media_w - 20
            mh = content_h - 20
            media_img.thumbnail((mw, mh), Image.LANCZOS)
            px = mx0 + (media_w - media_img.width) // 2
            py = my0 + (content_h - media_img.height) // 2
            img.paste(media_img, (px, py))
            draw.rectangle([px - 3, py - 3, px + media_img.width + 3, py + media_img.height + 3],
                           outline="#1A1A2E", width=3)
        except Exception:
            ph_font = _get_font(24, "body")
            draw.text((mx0 + 40, my0 + content_h // 2 - 16),
                      "素材暂无", fill="#A0A0B0", font=ph_font)

        # 文字要点区（左侧）
        lx0, lx1 = PANEL_GAP, mx0 - gap_w
        text_h = content_h
        n = len(bullets)

        if n == 1:
            self._draw_bullet_panel(draw, bullets[0], lx0, y0, lx1, y1, accent, 0)
        elif n == 2:
            h0 = text_h // 2 - 8
            self._draw_bullet_panel(draw, bullets[0], lx0, y0, lx1, y0 + h0, accent, 0)
            self._draw_bullet_panel(draw, bullets[1], lx0, y0 + h0 + 16, lx1, y1, accent, 1)
        elif n >= 3:
            h0 = text_h // 3 - 6
            h1 = text_h // 3 - 6
            h2 = text_h - h0 - h1 - 18
            self._draw_bullet_panel(draw, bullets[0], lx0, y0, lx1, y0 + h0, accent, 0)
            if n >= 2:
                self._draw_bullet_panel(draw, bullets[1], lx0, y0 + h0 + 10, lx1, y0 + h0 + 10 + h1, accent, 1)
            if n >= 3:
                self._draw_bullet_panel(draw, bullets[2], lx0, y0 + h0 + h1 + 20, lx1, y1, accent, 2)

    # ── 文字换行 ────────────────────────────────────────

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """按像素宽度自动换行。"""
        lines = []
        current = ""
        for ch in text:
            test = current + ch
            w = font.getlength(test) if hasattr(font, 'getlength') else len(test) * (font.size // 2)
            if w > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
        return lines if lines else [text]

    # ── 批量生成 ────────────────────────────────────────

    def render_storyboard(self,
                          storyboard: List[dict],
                          script_content: str,
                          work_dir: str,
                          materials: dict = None) -> List[str]:
        """为整个分镜批量生成漫画帧。

        Args:
            storyboard: 分镜列表，每项含 title/subtitle/bullets
            script_content: 完整脚本文本
            work_dir: 输出目录
            materials: {scene_index: file_path} 素材映射

        Returns:
            生成的 PNG 路径列表
        """
        materials = materials or {}
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        outputs = []

        scenes = storyboard if storyboard else [
            {"title": f"场景 {i+1}", "subtitle": s, "bullets": self._extract_bullets(s)}
            for i, s in enumerate(self._split_sentences(script_content))
        ]
        if not scenes:
            scenes = [{"title": "讲解", "subtitle": script_content[:60], "bullets": ["内容概要"]}]

        for i, scene in enumerate(scenes):
            title = str(scene.get("title") or f"场景 {i+1}")[:24]
            subtitle = str(scene.get("subtitle") or "")
            bullets = scene.get("bullets") if isinstance(scene.get("bullets"), list) else self._extract_bullets(subtitle or script_content)
            bullets = [str(x).strip() for x in bullets if str(x).strip()][:4] or ["要点讲解"]
            sfx = str(scene.get("sfx") or "")
            mp = materials.get(str(i)) or scene.get("material_url")

            out = work_dir / f"manga_scene_{i:03d}.png"
            self.render_frame(
                title=title,
                bullets=bullets,
                output_path=str(out),
                subtitle=subtitle[:44],
                media_path=mp,
                scene_index=i,
                total_scenes=len(scenes),
                sfx_text=sfx,
            )
            outputs.append(str(out))

        return outputs

    @staticmethod
    def _extract_bullets(text: str, max_items: int = 4) -> list:
        import re
        candidates = [s.strip("，。；;、 ") for s in re.split(r"[，。；;、\n]", text or "") if s.strip("，。；;、 ")]
        return candidates[:max_items] if candidates else [text.strip()[:24]] if text.strip() else []

    @staticmethod
    def _split_sentences(text: str) -> list:
        import re
        return [s.strip() for s in re.split(r'(?<=[。！？!?])\s*|\n+', text or "") if s.strip()]


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

_instance = None

def get_manga_renderer(dark_mode: bool = False) -> MangaFrameRenderer:
    global _instance
    if _instance is None:
        _instance = MangaFrameRenderer(dark_mode=dark_mode)
    return _instance
