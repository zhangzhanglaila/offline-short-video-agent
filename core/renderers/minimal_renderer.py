# -*- coding: utf-8 -*-
"""
Minimal 风格渲染器
极简清新风格 - 大量留白、大字号、极简装饰
"""
import math
from typing import List, Dict, Optional
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from core.style_renderer import StyleRenderer, register_renderer


class MinimalStyleRenderer(StyleRenderer):
    """极简风格渲染器"""

    def __init__(self, width: int = 1080, height: int = 1920,
                 style_config: dict = None):
        super().__init__(width, height, style_config)

        # 从配置获取参数
        self.colors = self.style_config.get("colors", {})
        self.typography = self.style_config.get("typography", {})
        self.layout = self.style_config.get("layout", {})

        self.bg_color = self.colors.get("background", "#FFFFFF")
        self.primary_color = self.colors.get("primary", "#1A1A1A")
        self.accent_color = self.colors.get("accent", "#3B82F6")
        self.card_bg = self.colors.get("card_bg", "#FAFAFA")
        self.card_border = self.colors.get("card_border", "#E5E5E5")

        self.padding = self.layout.get("padding", 80)
        self.card_radius = self.layout.get("card_radius", 8)
        self.card_border_width = self.layout.get("card_border_width", 1)

        # 字体配置
        self.title_size = self.typography.get("title_size", 56)
        self.body_size = self.typography.get("body_size", 28)
        self.line_height = self.typography.get("line_height", 1.4)

        # 装饰开关
        decorations = self.style_config.get("decorations", {})
        self.enable_progress_dots = decorations.get("enable_progress_dots", True)
        self.enable_numbered_circles = decorations.get("enable_numbered_circles", True)

        # 加载字体
        self._fonts = {}
        self._load_fonts()

    def _load_fonts(self):
        """加载字体"""
        font_roots = [
            "C:/Windows/Fonts",
            "/System/Library/Fonts",
            "/usr/share/fonts",
        ]
        candidates = {
            "title": ["msyhbd.ttc", "Arial-Bold.ttf", "simhei.ttf"],
            "body": ["msyh.ttc", "Arial.ttf", "simsun.ttc"],
        }

        for style, names in candidates.items():
            for name in names:
                for root in font_roots:
                    fp = Path(root) / name
                    if fp.exists():
                        try:
                            size = self.title_size if style == "title" else self.body_size
                            self._fonts[style] = ImageFont.truetype(str(fp), size)
                            break
                        except Exception:
                            continue
                if style in self._fonts:
                    break

        # 降级
        if "title" not in self._fonts:
            self._fonts["title"] = ImageFont.load_default()
        if "body" not in self._fonts:
            self._fonts["body"] = ImageFont.load_default()

    def _get_font(self, style: str = "body", size: int = None):
        """获取字体"""
        if size and style in self._fonts:
            # 重新创建指定大小
            font_path = self._fonts[style].path
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return self._fonts.get(style, ImageFont.load_default())

    def render_frame(
        self,
        title: str,
        bullets: List[str],
        output_path: str,
        subtitle: str = "",
        media_path: str = None,
        scene_index: int = 0,
        total_scenes: int = 1,
        sfx_text: str = "",
        **kwargs
    ) -> str:
        """渲染极简风格帧"""
        if not HAS_PIL:
            raise RuntimeError("PIL is required for rendering")

        # 创建画布
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # 绘制标题区
        title_y = self._draw_title(draw, title, subtitle)

        # 绘制内容区
        content_y = title_y + self.padding // 2
        bottom_y = self.height - self.padding

        if media_path and Path(media_path).exists():
            self._draw_content_with_media(draw, img, bullets, media_path,
                                        content_y, bottom_y)
        else:
            self._draw_content_text_only(draw, bullets, content_y, bottom_y)

        # 绘制底部信息
        self._draw_footer(draw, scene_index, total_scenes, bottom_y)

        # 保存
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, quality=95)
        return output_path

    def _draw_title(self, draw, title: str, subtitle: str) -> int:
        """绘制标题区"""
        y = self.padding
        x = self.padding
        max_w = self.width - 2 * self.padding

        # 标题（支持多行）
        title_font = self._get_font("title", self.title_size)
        lines = self._wrap_text(title, title_font, max_w)
        line_h = int(self.title_size * self.line_height)

        for i, line in enumerate(lines[:2]):  # 最多2行
            draw.text((x, y + i * line_h), line, fill=self.primary_color,
                     font=title_font)
        y += len(lines) * line_h

        # 副标题
        if subtitle:
            body_font = self._get_font("body", int(self.body_size * 0.9))
            sub_lines = self._wrap_text(subtitle[:100], body_font, max_w)
            sub_h = int(self.body_size * 0.9 * self.line_height)
            for i, line in enumerate(sub_lines[:1]):  # 最多1行
                draw.text((x, y + 10 + i * sub_h), line, fill=self.colors.get("secondary", "#666"),
                         font=body_font)
            y += sub_h + 10

        # 分隔线
        y += 20
        draw.line([(x, y), (x + 200, y)], fill=self.accent_color, width=2)

        return y + 20

    def _draw_content_text_only(self, draw, bullets, y0, y1):
        """绘制纯文字内容"""
        if not bullets:
            bullets = ["内容讲解"]

        content_h = y1 - y0 - 60
        n = min(len(bullets), 6)  # 最多6个要点

        # 计算每个要点高度
        gap = 16
        item_h = (content_h - gap * (n - 1)) // n

        x = self.padding
        w = self.width - 2 * self.padding

        for i, bullet in enumerate(bullets[:n]):
            item_y = y0 + i * (item_h + gap)
            item_bottom = min(item_y + item_h, y1 - 60)

            # 绘制序号（如果有）
            if self.enable_numbered_circles:
                radius = 12
                cx = x + radius
                cy = item_y + radius
                draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                           fill=self.accent_color)
                num_font = self._get_font("body", 14)
                num = str(i + 1)
                nw = num_font.getlength(num)
                draw.text((cx - nw // 2, cy - 8), num, fill="white",
                         font=num_font)
                text_x = cx + radius + 12
            else:
                text_x = x

            # 绘制要点文字
            body_font = self._get_font("body", self.body_size)
            max_text_w = w - (text_x - x)
            lines = self._wrap_text(bullet, body_font, max_text_w)
            line_h = int(self.body_size * self.line_height)

            for li, line in enumerate(lines[:3]):  # 每个要点最多3行
                if item_y + li * line_h > item_bottom:
                    break
                draw.text((text_x, item_y + li * line_h), line,
                         fill=self.primary_color, font=body_font)

    def _draw_content_with_media(self, draw, img, bullets, media_path, y0, y1):
        """绘制带素材的内容（左文右图）"""
        media_w = 360
        gap = 20

        # 右侧素材区
        mx0 = self.width - self.padding - media_w
        my0 = y0
        my1 = y1

        # 绘制素材框
        draw.rounded_rectangle([mx0, my0, mx0 + media_w, my1],
                              radius=self.card_radius,
                              outline=self.card_border,
                              width=self.card_border_width)

        try:
            from PIL import Image
            media = Image.open(media_path).convert("RGBA")
            mw = media_w - 40
            mh = y1 - y0 - 40
            media.thumbnail((mw, mh), Image.LANCZOS)
            px = mx0 + (media_w - media.width) // 2
            py = y0 + 20
            img.paste(media, (px, py), media if media.mode == "RGBA" else None)
        except Exception as e:
            print(f"[MinimalRenderer] Failed to load media: {e}")

        # 左侧文字区
        lx0, lx1 = self.padding, mx0 - gap
        lw = lx1 - lx0

        if not bullets:
            bullets = ["内容讲解"]

        n = min(len(bullets), 4)
        item_h = (y1 - y0 - 20) // n

        for i, bullet in enumerate(bullets[:n]):
            item_y = y0 + 10 + i * item_h
            body_font = self._get_font("body", self.body_size)
            lines = self._wrap_text(bullet, body_font, lw - 40)
            line_h = int(self.body_size * self.line_height)

            for li, line in enumerate(lines[:2]):
                if item_y + li * line_h > y1 - 20:
                    break
                draw.text((lx0 + 20, item_y + li * line_h), line,
                         fill=self.primary_color, font=body_font)

    def _draw_footer(self, draw, idx: int, total: int, y: int):
        """绘制底部信息"""
        # 场景编号
        body_font = self._get_font("body", int(self.body_size * 0.85))
        text = f"{idx + 1}/{total}"
        tw = body_font.getlength(text)
        draw.text((self.padding, y), text, fill=self.colors.get("secondary", "#666"),
                 font=body_font)

        # 进度条
        if self.enable_progress_dots and total > 1:
            bar_x = self.padding + 80
            bar_w = self.width - 2 * self.padding - 80
            dot_w = bar_w / total
            dot_radius = 4

            for i in range(total):
                cx = bar_x + i * dot_w + dot_w / 2
                cy = y + 8
                color = self.accent_color if i <= idx else self.card_border
                draw.ellipse([cx - dot_radius, cy - dot_radius,
                           cx + dot_radius, cy + dot_radius],
                           fill=color)

    def render_storyboard(
        self,
        storyboard: List[dict],
        script_content: str,
        work_dir: str,
        materials: dict = None
    ) -> List[str]:
        """批量渲染分镜"""
        materials = materials or {}
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

        outputs = []
        for i, scene in enumerate(storyboard):
            title = scene.get("title", f"场景{i+1}")
            subtitle = scene.get("subtitle", "")
            bullets = scene.get("bullets", [])
            if not isinstance(bullets, list):
                bullets = [bullets]
            bullets = [str(b).strip() for b in bullets if str(b).strip()][:6]

            media = materials.get(str(i)) or scene.get("material_url")
            output = work_dir / f"scene_{i:03d}.png"

            self.render_frame(
                title=title,
                bullets=bullets,
                output_path=str(output),
                subtitle=subtitle,
                media_path=media,
                scene_index=i,
                total_scenes=len(storyboard)
            )
            outputs.append(str(output))

        return outputs

    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """文字换行"""
        lines = []
        current = ""
        for ch in text:
            test = current + ch
            w = font.getlength(test) if hasattr(font, 'getlength') else len(test) * 10
            if w > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
        return lines if lines else [text]


# 注册渲染器
register_renderer("minimal", MinimalStyleRenderer)
