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


def draw_crosshatch(draw: ImageDraw.Draw, x0: int, y0: int, x1: int, y1: int,
                    spacing: int = 10, opacity: int = 15, angle: float = 45):
    """纯PIL交叉排线 — 漫画阴影纹理，不依赖numpy。"""
    import math
    color = (0, 0, 0, opacity)
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    # 计算覆盖范围
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    half_diag = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2) / 2 + 20

    # 画平行线
    n_lines = int(half_diag * 2 / spacing)
    for i in range(-n_lines, n_lines):
        offset = i * spacing
        # 线通过中心点，垂直于角度方向
        sx = cx + offset * cos_a - half_diag * (-sin_a)
        sy = cy + offset * sin_a - half_diag * cos_a
        ex = cx + offset * cos_a + half_diag * (-sin_a)
        ey = cy + offset * sin_a + half_diag * cos_a
        draw.line([(int(sx), int(sy)), (int(ex), int(ey))], fill=color, width=1)

    # 第二组交叉线（90度）
    rad2 = rad + math.pi / 2
    cos_a2, sin_a2 = math.cos(rad2), math.sin(rad2)
    for i in range(-n_lines, n_lines):
        offset = i * spacing
        sx = cx + offset * cos_a2 - half_diag * (-sin_a2)
        sy = cy + offset * sin_a2 - half_diag * cos_a2
        ex = cx + offset * cos_a2 + half_diag * (-sin_a2)
        ey = cy + offset * sin_a2 + half_diag * cos_a2
        draw.line([(int(sx), int(sy)), (int(ex), int(ey))], fill=color, width=1)


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
# 漫画帧渲染器主类
# ═══════════════════════════════════════════════════════════════

class MangaFrameRenderer:
    """漫画帧渲染器 — 生成真正的漫画风格讲解帧。"""

    def __init__(self, width: int = None, height: int = None,
                 dark_mode: bool = False):
        self.w = width or W
        self.h = height or H
        self.orientation = "landscape" if self.w > self.h else "portrait"
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
        """渲染单帧漫画讲解图 — 网点纸+气泡框+速度线+分镜格全开。

        布局 (1080×1920)：
        ┌────────────────────────┐
        │  标题面板 + 网点背景   │  ~260px
        │  ▸ SFX + 副标题       │
        ├────────────┬──────────┤
        │  气泡框1   │          │
        │  ────────  │  素材图  │  主内容区 ~1420px
        │  气泡框2   │  (可选)  │
        │  ────────  │          │
        │  气泡框3   │          │
        ├────────────┴──────────┤
        │  要点总结 + 场景编号   │  ~180px
        │  速度线装饰           │
        └────────────────────────┘
        """
        accent = accent_color or (RED if not self.dark else "#FF6B6B")

        if self.orientation == "landscape":
            return self._render_frame_landscape(title, bullets, output_path,
                                                subtitle, media_path,
                                                scene_index, total_scenes,
                                                sfx_text, accent)

        # RGBA画布 — 支持网点纸alpha合成 + 速度线透明度
        img = Image.new("RGBA", (self.w, self.h), self.paper + "FF" if len(self.paper) == 7 else self.paper)
        draw = ImageDraw.Draw(img, "RGBA")

        # ── 背景纹理（纸张纤维 + 网点纸）──
        self._draw_bg_texture(draw, img)
        # 全画布微妙网点纸叠加（漫画影印质感）
        apply_halftone(img, (PANEL_GAP, PANEL_GAP, self.w - PANEL_GAP, self.h - PANEL_GAP),
                      dot_size=2, spacing=8, angle=45, opacity=0.04)

        # ── 1. 顶部标题区 ──
        title_y1 = self._draw_title_header(draw, title, sfx_text, subtitle, accent)

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

        # 转回RGB保存
        rgb = Image.new("RGB", (self.w, self.h), self.paper)
        rgb.paste(img, (0, 0), img)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        rgb.save(output_path, quality=92)
        return output_path

    def _draw_bg_texture(self, draw, img: Image.Image = None):
        """全画布微妙纹理：漫画纸质感 + 随机淡色斑点 + 网点纸。"""
        # 纸张纤维纹理 — 随机微小淡灰斑点
        import random as _random
        for _ in range(80):
            x, y = _random.randint(0, self.w - 1), _random.randint(0, self.h - 1)
            s = _random.randint(1, 3)
            shade = _random.randint(0, 15)
            draw.ellipse([x, y, x + s, y + s], fill=(0, 0, 0, shade))

    # ── 标题头 ──────────────────────────────────────────

    def _draw_title_header(self, draw, title: str, sfx: str, subtitle: str, accent: str) -> int:
        """顶部标题面板 — 网点背景+粗双线框+SFX+标题+副标题+装饰线。"""
        header_h = 220
        y0, y1 = PANEL_GAP, PANEL_GAP + header_h
        x0, x1 = PANEL_GAP, self.w - PANEL_GAP

        # 面板背景
        draw.rounded_rectangle([x0, y0, x1, y1], radius=18,
                               fill=self.panel_bg, outline="#1A1A2E", width=BORDER_W)

        # 交叉排线纹理
        draw_crosshatch(draw, x0 + 14, y0 + 14, x1 - 14, y0 + 180,
                      spacing=22, opacity=7, angle=30)

        # 内边框
        draw.rounded_rectangle([x0 + BORDER_W + 3, y0 + BORDER_W + 3,
                                x1 - BORDER_W - 3, y1 - BORDER_W - 3],
                               radius=14, outline="#1A1A2E", width=2)

        # SFX 拟声词 — 右上角大字描边
        if sfx:
            sfx_font = _get_font(68, "sfx")
            sfx_w = draw.textlength(sfx, font=sfx_font)
            sfx_x = x1 - 60 - int(sfx_w)
            sfx_y = y0 + 24
            for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)]:
                draw.text((sfx_x + ox, sfx_y + oy), sfx, fill=(0, 0, 0, 255), font=sfx_font)
            draw.text((sfx_x, sfx_y), sfx, fill=accent, font=sfx_font)

        # 标题 — 大字+描边
        title_font = _get_font(56, "title")
        tx = x0 + 34
        ty = y0 + 40
        display_title = title[:22]
        for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
            draw.text((tx + ox, ty + oy), display_title, fill=(0, 0, 0, 255), font=title_font)
        draw.text((tx, ty), display_title, fill=accent, font=title_font)

        # 副标题/导读行
        info_font = _get_font(28, "body")
        if subtitle:
            info_text = subtitle[:50]
        else:
            info_text = "详细讲解 · 建议收藏反复观看"
        iw = draw.textlength(info_text, font=info_font)
        ix = (self.w - int(iw)) // 2
        draw.text((ix, ty + 90), info_text, fill=(80, 80, 90, 255), font=info_font)

        # 装饰线 — 标题下方
        deco_y = ty + 130
        draw.line([(tx, deco_y), (tx + 300, deco_y)], fill=(0, 0, 0, 255), width=3)
        draw.line([(tx, deco_y + 8), (tx + 180, deco_y + 8)], fill=accent, width=2)

        # 右下角小标签
        tag_font = _get_font(20, "body")
        tag_text = "MANGA EXPLAIN"
        tag_w = draw.textlength(tag_text, font=tag_font)
        draw.text((x1 - int(tag_w) - 30, y1 - 40), tag_text, fill=(150, 150, 160, 255), font=tag_font)

        return y1

    # ── 底栏 ────────────────────────────────────────────

    def _draw_bottom_bar(self, draw, subtitle: str, idx: int, total: int, accent: str) -> int:
        """底部信息栏 — 速度线+页码+总结+装饰。"""
        bar_h = 140
        y1 = self.h - PANEL_GAP
        y0 = y1 - bar_h
        x0, x1 = PANEL_GAP, self.w - PANEL_GAP

        draw.rounded_rectangle([x0, y0, x1, y1], radius=14,
                               fill=self.panel_bg, outline="#1A1A2E", width=BORDER_W)

        # 速度线装饰（底部微妙的动感）
        draw_parallel_speed_lines(draw, x0 + 30, y0 + 140, x1 - 30, y0 + 140, count=12, opacity=20)

        # 场景编号 + 进度条
        num_font = _get_font(22, "body")
        num_text = f"第{idx+1}/{total}话"
        draw.text((x0 + 24, y0 + 14), num_text, fill=(120, 120, 140, 255), font=num_font)

        # 进度点
        dot_y = y0 + 20
        bar_x0 = x0 + 140
        bar_x1 = x1 - 140
        bar_cx = (bar_x0 + bar_x1) // 2
        seg_w = (bar_x1 - bar_x0) // max(total, 1)
        for i in range(total):
            sx = bar_x0 + i * seg_w + 2
            ex = bar_x0 + (i + 1) * seg_w - 2
            fill_c = accent if i <= idx else (200, 200, 210, 255)
            draw.rounded_rectangle([sx, dot_y - 4, ex, dot_y + 4], radius=3, fill=fill_c)

        # 中间总结文字
        if subtitle:
            sub_font = _get_font(30, "body")
            sub = subtitle[:48]
            sub_w = draw.textlength(sub, font=sub_font)
            sub_x = (self.w - int(sub_w)) // 2
            draw.text((sub_x, y0 + 52), sub, fill=self.text_c, font=sub_font)

        # 底部标签行
        tag_font = _get_font(22, "body")
        tags = ["收藏", "点赞", "转发"]
        tag_x = x0 + 24
        for tag in tags:
            tw = draw.textlength(tag, font=tag_font)
            draw.rounded_rectangle([tag_x, y0 + 108, tag_x + int(tw) + 24, y0 + 138],
                                   radius=8, fill=None, outline=(180, 180, 190, 255), width=1)
            draw.text((tag_x + 12, y0 + 112), tag, fill=(130, 130, 150, 255), font=tag_font)
            tag_x += int(tw) + 36

        # 右侧"▶ NEXT"
        next_font = _get_font(20, "body")
        draw.text((x1 - 100, y0 + 14), "▶ NEXT", fill=accent, font=next_font)

        return y0

    def _draw_content_text_only(self, draw, img, bullets: List[str],
                                y0: int, y1: int, accent: str):
        """文字流式布局 — 大字号连续排版，填满整个内容区。"""
        n = len(bullets)
        if n == 0:
            return

        content_h = y1 - y0
        margin = PANEL_GAP + 10

        # 限制每帧最多4个要点，保证每个足够大
        bullets = bullets[:4]
        n = len(bullets)

        # 每个要点获取均等高度
        gap = 16
        card_h = (content_h - gap * (n - 1)) // n

        for i in range(n):
            cy0 = y0 + i * (card_h + gap)
            cy1 = cy0 + card_h if i < n - 1 else y1
            self._draw_fullwidth_card(draw, bullets[i], margin, cy0,
                                      self.w - margin, cy1, accent, i)
            # 分隔线
            if i < n - 1:
                sep_y = cy1 + gap // 2
                draw.line([(margin + 60, sep_y), (self.w - margin - 60, sep_y)],
                         fill=(200, 200, 210, 255), width=1)

    def _draw_fullwidth_card(self, draw, text: str,
                           x0: int, y0: int, x1: int, y1: int,
                           accent: str, index: int):
        """大字卡片 — 用最大的字号填满卡片，漫画冲击力排版。"""
        panel_w = x1 - x0
        panel_h = y1 - y0
        if panel_w < 100 or panel_h < 60:
            return

        # 极简边框
        draw.rounded_rectangle([x0, y0, x1, y1], radius=10,
                               fill=None, outline=(180, 180, 190, 100), width=1)

        pad = 24
        text_w = panel_w - pad * 2
        text_h = panel_h - pad * 2

        # ── 拆分冒号引导词 ──
        if '：' in text:
            lead_raw, body_raw = text.split('：', 1)
            lead = lead_raw + '：'
            body = body_raw
        elif ':' in text:
            lead_raw, body_raw = text.split(':', 1)
            lead = lead_raw + ':'
            body = body_raw
        else:
            lead = ''
            body = text

        # ── 找最大能放下的字号（含大行距）──
        best_size = 20
        for size in [56, 50, 44, 40, 36, 34, 32, 30, 28, 26, 24, 22, 20]:
            body_f = _get_font(size, "body")
            lead_f = _get_font(size + 4, "title")
            line_spacing = max(8, size // 3)  # 大字多留行距
            lh = size + line_spacing

            total = 0
            if lead:
                total += len(self._wrap_text(lead, lead_f, text_w)) * (lh + 6)
            total += len(self._wrap_text(body, body_f, text_w)) * lh
            if total <= text_h:
                best_size = size
                break

        body_font = _get_font(best_size, "body")
        lead_font = _get_font(best_size + 4, "title")
        line_spacing = max(8, best_size // 3)
        lh = best_size + line_spacing

        # ── 按冒号拆分排版 → 引导词（彩色）+ 正文（黑色）──
        all_segments = []
        if lead:
            all_segments.append(('lead', lead))
        all_segments.append(('body', body))

        # 计算总行数用于垂直居中
        total_lines = 0
        for seg_type, seg_text in all_segments:
            f = lead_font if seg_type == 'lead' else body_font
            slh = lh + 6 if seg_type == 'lead' else lh
            total_lines += len(self._wrap_text(seg_text, f, text_w))
        total_text_px = 0
        for seg_type, seg_text in all_segments:
            f = lead_font if seg_type == 'lead' else body_font
            slh = lh + 6 if seg_type == 'lead' else lh
            total_text_px += len(self._wrap_text(seg_text, f, text_w)) * slh

        start_y = y0 + pad + (text_h - total_text_px) // 2
        text_y = max(y0 + pad, start_y)

        for seg_type, seg_text in all_segments:
            f = lead_font if seg_type == 'lead' else body_font
            slh = lh + 6 if seg_type == 'lead' else lh
            lines = self._wrap_text(seg_text, f, text_w)
            for ln in lines:
                if text_y + slh > y1 - pad:
                    break
                color = accent if seg_type == 'lead' else self.text_c
                draw.text((x0 + pad, text_y), ln, fill=color, font=f)
                text_y += slh

        # ── 序号圆圈（左上角）──
        cr = 12
        ccx, ccy = x0 + pad + cr, y0 + pad + cr
        draw.ellipse([ccx - cr, ccy - cr, ccx + cr, ccy + cr], fill=accent)
        nf = _get_font(13, "title")
        ns = str(index + 1)
        nw = draw.textlength(ns, font=nf)
        draw.text((ccx - int(nw)//2, ccy - 8), ns, fill=(255,255,255,255), font=nf)

    # ── 带素材的内容区 ──────────────────────────────────

    def _draw_content_with_media(self, draw, img, bullets: List[str],
                                 media_path: str, y0: int, y1: int, accent: str):
        """文字+素材混合 — 左文字面板(网点+速度线) + 右素材图(漫画框)。"""
        content_h = y1 - y0
        media_w = 380
        gap_w = 16

        # 素材图片区域（右侧）
        mx0 = self.w - PANEL_GAP - media_w
        mx1 = self.w - PANEL_GAP
        my0 = y0
        my1 = y1

        # 素材面板 — 双线漫画框
        draw.rounded_rectangle([mx0, my0, mx1, my1], radius=14,
                               fill=(248, 246, 242, 255) if not self.dark else (40, 40, 55, 255),
                               outline=(26, 26, 46, 255), width=BORDER_W)
        # 内框
        draw.rounded_rectangle([mx0 + 6, my0 + 6, mx1 - 6, my1 - 6], radius=10,
                               outline=(26, 26, 46, 255), width=2)
        # 图标签
        img_label = _get_font(20, "title")
        draw.text((mx0 + 16, my0 + 12), "素材参考", fill=accent, font=img_label)

        try:
            media_img = Image.open(media_path).convert("RGBA")
            mw = media_w - 36
            mh = content_h - 60
            media_img.thumbnail((mw, mh), Image.LANCZOS)
            px = mx0 + (media_w - media_img.width) // 2
            py = my0 + 44
            img.paste(media_img, (px, py), media_img if media_img.mode == "RGBA" else None)
            draw.rounded_rectangle([px - 3, py - 3, px + media_img.width + 3, py + media_img.height + 3],
                                   radius=6, outline=(26, 26, 46, 255), width=3)
        except Exception:
            ph_font = _get_font(22, "body")
            no_img_text = "暂无素材"
            nw = draw.textlength(no_img_text, font=ph_font)
            draw.text((mx0 + (media_w - int(nw)) // 2, my0 + content_h // 2 - 14),
                      no_img_text, fill=(150, 150, 165, 255), font=ph_font)

        # 文字要点区（左侧）— 面板间速度线
        lx0, lx1 = PANEL_GAP, mx0 - gap_w
        n = len(bullets)

        if n == 1:
            self._draw_fullwidth_card(draw, bullets[0], lx0, y0, lx1, y1, accent, 0)
        elif n == 2:
            h0 = (content_h - gap_w) // 2
            self._draw_fullwidth_card(draw, bullets[0], lx0, y0, lx1, y0 + h0, accent, 0)
            m_y = y0 + h0 + gap_w // 2
            draw_parallel_speed_lines(draw, lx0 + 40, m_y, lx1 - 40, m_y, count=8, opacity=20)
            self._draw_fullwidth_card(draw, bullets[1], lx0, y0 + h0 + gap_w, lx1, y1, accent, 1)
        elif n >= 3:
            h_each = (content_h - gap_w * 2) // 3
            for j in range(min(n, 3)):
                py0 = y0 + j * (h_each + gap_w)
                py1 = py0 + h_each
                self._draw_fullwidth_card(draw, bullets[j], lx0, py0, lx1, min(py1, y1), accent, j)
                if j < min(n, 3) - 1:
                    m_y = py1 + gap_w // 2
                    draw_parallel_speed_lines(draw, lx0 + 40, m_y, lx1 - 40, m_y, count=6, opacity=20)

    # ── 横屏布局 (1920×1080) ─────────────────────────────

    def _render_frame_landscape(self, title, bullets, output_path, subtitle,
                                 media_path, scene_index, total_scenes, sfx_text, accent):
        """横屏漫画帧渲染 — 左侧标题栏 + 右侧3列分镜格。"""
        img = Image.new("RGBA", (self.w, self.h),
                       self.paper + "FF" if len(self.paper) == 7 else self.paper)
        draw = ImageDraw.Draw(img, "RGBA")

        self._draw_bg_texture(draw, img)
        apply_halftone(img, (PANEL_GAP, PANEL_GAP, self.w - PANEL_GAP, self.h - PANEL_GAP),
                      dot_size=2, spacing=8, angle=45, opacity=0.04)

        # 左侧标题栏
        sidebar_w = 280
        self._draw_title_sidebar(draw, title, sfx_text, subtitle, accent, sidebar_w)

        # 底部信息条
        bottom_y0 = self._draw_bottom_bar_landscape(draw, subtitle, scene_index, total_scenes, accent)

        # 右侧主内容区
        content_x0 = sidebar_w + PANEL_GAP * 2
        content_y0 = PANEL_GAP
        content_y1 = bottom_y0 - PANEL_GAP

        has_media = media_path and Path(media_path).exists()
        if has_media:
            self._draw_content_landscape(draw, img, bullets, content_x0, content_y0,
                                        self.w - PANEL_GAP, content_y1, accent, media_path)
        else:
            self._draw_content_landscape(draw, img, bullets, content_x0, content_y0,
                                        self.w - PANEL_GAP, content_y1, accent)

        rgb = Image.new("RGB", (self.w, self.h), self.paper)
        rgb.paste(img, (0, 0), img)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        rgb.save(output_path, quality=92)
        return output_path

    def _draw_title_sidebar(self, draw, title, sfx, subtitle, accent, sidebar_w):
        """横屏左侧标题栏 — 窄竖条，标题竖排/缩排。"""
        x0, y0 = PANEL_GAP, PANEL_GAP
        x1 = x0 + sidebar_w
        y1 = self.h - PANEL_GAP

        # 面板背景
        draw.rounded_rectangle([x0, y0, x1, y1], radius=18,
                               fill=self.panel_bg, outline="#1A1A2E", width=BORDER_W)
        draw_crosshatch(draw, x0 + 14, y0 + 14, x1 - 14, y1 - 14,
                      spacing=22, opacity=7, angle=30)

        # 内边框
        draw.rounded_rectangle([x0 + BORDER_W + 3, y0 + BORDER_W + 3,
                                x1 - BORDER_W - 3, y1 - BORDER_W - 3],
                               radius=14, outline="#1A1A2E", width=2)

        # SFX拟声词 — 顶部居中
        if sfx:
            sfx_font = _get_font(48, "sfx")
            sfx_w = draw.textlength(sfx, font=sfx_font)
            sfx_x = (x0 + x1 - int(sfx_w)) // 2
            sfx_y = y0 + 30
            for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                draw.text((sfx_x + ox, sfx_y + oy), sfx, fill=(0, 0, 0, 255), font=sfx_font)
            draw.text((sfx_x, sfx_y), sfx, fill=accent, font=sfx_font)

        # 标题 — 窄栏内大字号折行
        title_font = _get_font(34, "title")
        inner_x0 = x0 + 24
        inner_x1 = x1 - 24
        inner_w = inner_x1 - inner_x0
        title_lines = self._wrap_text(title[:28], title_font, inner_w)
        ty = sfx_y + 70 if sfx else y0 + 40

        for ln in title_lines[:4]:
            draw.text((inner_x0, ty), ln, fill=accent, font=title_font)
            ty += 42

        # 装饰线
        deco_y = ty + 16
        draw.line([(inner_x0, deco_y), (inner_x0 + 160, deco_y)], fill=(0, 0, 0, 255), width=3)
        draw.line([(inner_x0, deco_y + 6), (inner_x0 + 90, deco_y + 6)], fill=accent, width=2)

        # 副标题
        info_font = _get_font(22, "body")
        info_lines = self._wrap_text(subtitle[:40] or "详细讲解", info_font, inner_w)
        iy = deco_y + 30
        for ln in info_lines[:3]:
            draw.text((inner_x0, iy), ln, fill=(80, 80, 90, 255), font=info_font)
            iy += 30

        # 底部标签
        tag_font = _get_font(18, "body")
        tag_text = "MANGA"
        tw = draw.textlength(tag_text, font=tag_font)
        draw.text(((x0 + x1 - int(tw)) // 2, y1 - 40), tag_text,
                 fill=(150, 150, 160, 255), font=tag_font)

        return x1

    def _draw_content_landscape(self, draw, img, bullets, x0, y0, x1, y1, accent,
                                media_path=None):
        """横屏主内容区 — 水平多列分镜格布局。"""
        n = len(bullets)
        if n == 0:
            return

        content_w = x1 - x0
        content_h = y1 - y0
        gap = PANEL_GAP

        # 有图片时：左侧3列文字 + 右侧图片
        has_media = media_path and Path(media_path).exists()
        if has_media:
            media_w = min(420, content_w // 3)
            text_w = content_w - media_w - gap
            text_x0, text_x1 = x0, x0 + text_w
            media_x0, media_x1 = text_x1 + gap, x1

            # 绘制图片区域
            try:
                photo = Image.open(media_path).convert("RGBA")
                pw, ph = photo.size
                scale = min((media_x1 - media_x0) / pw, (y1 - y0 - 20) / ph)
                nw, nh = int(pw * scale), int(ph * scale)
                photo = photo.resize((nw, nh), Image.LANCZOS)
                px = media_x0 + (media_x1 - media_x0 - nw) // 2
                py = y0 + (y1 - y0 - nh) // 2
                img.paste(photo, (px, py), photo)
            except Exception:
                pass

            # 文字区域
            self._layout_landscape_grid(draw, bullets[:min(n, 4)], text_x0, y0, text_x1, y1, accent)
        else:
            self._layout_landscape_grid(draw, bullets, x0, y0, x1, y1, accent)

    def _layout_landscape_grid(self, draw, bullets, x0, y0, x1, y1, accent):
        """横屏分镜格布局 — 根据子弹数量自适应列/行。"""
        n = len(bullets)
        if n == 0:
            return
        gap = PANEL_GAP
        content_w = x1 - x0
        content_h = y1 - y0

        if n == 1:
            # 单面板全宽
            self._draw_fullwidth_card(draw, bullets[0], x0, y0, x1, y1, accent, 0)
        elif n == 2:
            # 左右两栏
            hw = (content_w - gap) // 2
            self._draw_fullwidth_card(draw, bullets[0], x0, y0, x0 + hw, y1, accent, 0)
            self._draw_fullwidth_card(draw, bullets[1], x0 + hw + gap, y0, x1, y1, accent, 1)
        elif n == 3:
            # 三列
            cw = (content_w - gap * 2) // 3
            for i in range(3):
                cx0 = x0 + i * (cw + gap) if i > 0 else x0
                self._draw_fullwidth_card(draw, bullets[i], cx0, y0, cx0 + cw, y1, accent, i)
        elif n == 4:
            # 2x2网格
            cw = (content_w - gap) // 2
            rh = (content_h - gap) // 2
            for i in range(4):
                col, row = i % 2, i // 2
                cx0 = x0 + col * (cw + gap) if col > 0 else x0
                cy0 = y0 + row * (rh + gap) if row > 0 else y0
                self._draw_fullwidth_card(draw, bullets[i], cx0, cy0, cx0 + cw, cy0 + rh, accent, i)
        else:
            # 5-6: 3列×2行
            cw = (content_w - gap * 2) // 3
            rh = (content_h - gap) // 2
            for i in range(n):
                col, row = i % 3, i // 2
                cx0 = x0 + col * (cw + gap) if col > 0 else x0
                cy0 = y0 + row * (rh + gap) if row > 0 else y0
                self._draw_fullwidth_card(draw, bullets[i], cx0, cy0, cx0 + cw, cy0 + rh, accent, i)

    def _draw_bottom_bar_landscape(self, draw, subtitle, idx, total, accent):
        """横屏底部紧凑信息栏。"""
        bar_h = 100
        y1 = self.h - PANEL_GAP
        y0 = y1 - bar_h
        x0, x1 = PANEL_GAP, self.w - PANEL_GAP

        # 速度线背景
        draw_parallel_speed_lines(draw, x0, y0 + bar_h // 2, x1, y0 + bar_h // 2,
                                count=12, opacity=12)

        # 半透明底条
        draw.rectangle([x0, y0, x1, y1], fill=(255, 252, 246, 220))

        # 分隔线
        draw.line([(x0, y0), (x1, y0)], fill="#1A1A2E", width=2)

        # 页码 + 总结
        page_font = _get_font(24, "body")
        page_text = f"{idx+1}/{total}"
        draw.text((x0 + 20, y0 + 16), page_text, fill=accent, font=page_font)

        summary = subtitle[:50] if subtitle else "详细讲解 · 建议收藏"
        sum_font = _get_font(22, "body")
        sw = draw.textlength(summary, font=sum_font)
        draw.text(((self.w - int(sw)) // 2, y0 + 18), summary,
                 fill=(80, 80, 90, 255), font=sum_font)

        # 右侧进度点
        dot_r = 6
        total_dots = min(total, 10)
        start_dx = x1 - 30 - total_dots * 20
        for d in range(total_dots):
            dx = start_dx + d * 20
            fill_c = accent if d == idx else (200, 200, 205, 255)
            draw.ellipse([dx, y0 + bar_h // 2 - dot_r, dx + dot_r * 2, y0 + bar_h // 2 + dot_r],
                        fill=fill_c)

        return y0

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
            bullets = [str(x).strip() for x in bullets if str(x).strip()] or ["要点讲解"]
            # 每帧最多4个要点，保证每个足够大；短要点合并加长
            bullets = bullets[:4]
            if len(bullets) > 1 and all(len(b) < 20 for b in bullets):
                # 短要点合并为更大的文本块
                bullets = ["，".join(bullets[:2]), "，".join(bullets[2:])] if len(bullets) >= 4 else ["，".join(bullets)]
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
    def _extract_bullets(text: str, max_items: int = 6) -> list:
        import re
        parts = re.split(r'(?<=[。！？!?])\s*|\n+', text or "")
        candidates = [s.strip() for s in parts if s.strip()]
        if candidates:
            return candidates[:max_items]
        if text and text.strip():
            return [text.strip()]
        return []

    @staticmethod
    def _split_sentences(text: str) -> list:
        import re
        return [s.strip() for s in re.split(r'(?<=[。！？!?])\s*|\n+', text or "") if s.strip()]




