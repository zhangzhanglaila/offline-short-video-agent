# -*- coding: utf-8 -*-
"""
Vibrant 风格渲染器
活力时尚风格 - 高饱和渐变、圆润形状、动态阴影
"""
from typing import List, Dict, Optional
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from core.style_renderer import StyleRenderer, register_renderer
from core.renderers.minimal_renderer import MinimalStyleRenderer


class VibrantStyleRenderer(MinimalStyleRenderer):
    """活力风格渲染器 - 继承极简风格，修改配色和装饰"""

    def __init__(self, width: int = 1080, height: int = 1920,
                 style_config: dict = None):
        # 先用父类初始化
        super().__init__(width, height, style_config)

        # 覆盖为活力风格的配置
        self.bg_color = "#FFF5F5"  # 淡粉底色

        # 渐变背景（简化为纯色，复杂渐变在 post_render 处理）
        gradient = self.colors.get("background", {})
        if isinstance(gradient, dict) and gradient.get("type") == "gradient":
            # 取渐变首色作为底色
            colors = gradient.get("value", ["#FF9A9E"])
            self.bg_color = colors[0] if colors else "#FF9A9E"

        self.primary_color = self.colors.get("primary", "#FFFFFF")
        self.accent_color = self.colors.get("accent", "#FF6B6B")
        self.card_bg = self.colors.get("card_bg", "#FFFFFF")
        # 修复：transparent 替换为实际颜色
        card_border = self.colors.get("card_border", "")
        self.card_border = card_border if card_border and card_border != "transparent" else "#FFB4B4"

        self.padding = self.layout.get("padding", 40)
        self.card_radius = self.layout.get("card_radius", 20)

        # 装饰开关
        decorations = self.style_config.get("decorations", {})
        self.enable_progress_dots = decorations.get("enable_progress_dots", True)
        self.enable_numbered_circles = decorations.get("enable_numbered_circles", True)
        self.enable_decorative_lines = decorations.get("enable_decorative_lines", True)

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
        """渲染活力风格帧"""
        if not HAS_PIL:
            raise RuntimeError("PIL is required for rendering")

        # 创建画布（支持渐变背景）
        img = self._create_canvas()
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

    def _create_canvas(self):
        """创建画布（支持渐变）"""
        # 简化渐变：创建纯色画布
        img = Image.new("RGB", (self.width, self.height), self.bg_color)

        # 可选：添加微妙的渐变效果
        gradient = self.colors.get("background", {})
        if isinstance(gradient, dict) and gradient.get("type") == "gradient":
            colors = gradient.get("value", ["#FF9A9E", "#FECFEF"])
            if len(colors) >= 2:
                # 创建垂直渐变
                from PIL import ImageDraw
                draw = ImageDraw.Draw(img)
                h = self.height
                for y in range(h):
                    ratio = y / h
                    # 简单的线性插值
                    r1, g1, b1 = self._hex_to_rgb(colors[0])
                    r2, g2, b2 = self._hex_to_rgb(colors[1])
                    r = int(r1 + (r2 - r1) * ratio)
                    g = int(g1 + (g2 - g1) * ratio)
                    b = int(b1 + (b2 - b1) * ratio)
                    draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        return img

    def _hex_to_rgb(self, hex_str: str) -> tuple:
        """十六进制转RGB"""
        h = hex_str.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _draw_title(self, draw, title: str, subtitle: str) -> int:
        """绘制标题区（活力风格）"""
        y = self.padding
        x = self.padding
        max_w = self.width - 2 * self.padding

        # 标题（使用强调色）
        title_font = self._get_font("title", self.title_size)
        lines = self._wrap_text(title, title_font, max_w)
        line_h = int(self.title_size * self.line_height)

        for i, line in enumerate(lines[:2]):
            # 描边效果
            for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                draw.text((x + ox, y + i * line_h + oy), line,
                         fill=self.bg_color, font=title_font)
            draw.text((x, y + i * line_h), line, fill=self.accent_color,
                     font=title_font)
        y += len(lines) * line_h

        # 副标题
        if subtitle:
            body_font = self._get_font("body", int(self.body_size * 0.9))
            sub_lines = self._wrap_text(subtitle[:100], body_font, max_w)
            sub_h = int(self.body_size * 0.9 * self.line_height)
            for i, line in enumerate(sub_lines[:1]):
                draw.text((x, y + 10 + i * sub_h), line,
                         fill=self.colors.get("secondary", "#666"),
                         font=body_font)
            y += sub_h + 10

        # 装饰线
        if self.enable_decorative_lines:
            y += 20
            draw.line([(x, y), (x + 200, y)], fill=self.accent_color, width=3)

        return y + 20


# 注册渲染器
register_renderer("vibrant", VibrantStyleRenderer)
