# -*- coding: utf-8 -*-
"""
Tech 风格渲染器
科技霓虹风格 - 深色背景、霓虹点缀、网格装饰、等宽字体
"""
from typing import List, Dict, Optional
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from core.style_renderer import StyleRenderer, register_renderer


class TechStyleRenderer(StyleRenderer):
    """科技风格渲染器"""

    def __init__(self, width: int = 1080, height: int = 1920,
                 style_config: dict = None):
        super().__init__(width, height, style_config)

        self.colors = self.style_config.get("colors", {})
        self.typography = self.style_config.get("typography", {})
        self.layout = self.style_config.get("layout", {})

        self.bg_color = self.colors.get("background", "#0D1117")  # GitHub深色
        self.primary_color = self.colors.get("primary", "#C9D1D9")
        self.accent_color = self.colors.get("accent", "#58A6FF")
        self.accent_secondary = self.colors.get("accent_secondary", "#FF7B72")
        self.card_bg = self.colors.get("card_bg", "#161B22")
        self.card_border = self.colors.get("card_border", "#30363D")

        self.padding = self.layout.get("padding", 50)
        self.card_radius = self.layout.get("card_radius", 6)
        self.card_border_width = self.layout.get("card_border_width", 1)

        # 字体配置（等宽字体用于代码）
        self.title_size = self.typography.get("title_size", 44)
        self.body_size = self.typography.get("body_size", 22)
        self.code_size = self.typography.get("code_size", 18)
        self.line_height = self.typography.get("line_height", 1.5)

        # 网格配置
        self.bg_grid = self.style_config.get("bg_grid", False)
        self.bg_grid_color = self.style_config.get("bg_grid_color", (0, 255, 255, 8))
        self.bg_grid_spacing = self.style_config.get("bg_grid_spacing", 40)

        # 霓虹效果
        glow_config = self.style_config.get("glow", {})
        self.glow_enabled = glow_config.get("enabled", True)
        self.glow_intensity = glow_config.get("intensity", 0.6)
        self.glow_color = glow_config.get("color", "#58A6FF")

        # 代码高亮
        self.code_highlight = self.style_config.get("code_highlight", {})

        # 装饰开关
        decorations = self.style_config.get("decorations", {})
        self.enable_progress_dots = decorations.get("enable_progress_dots", True)
        self.enable_numbered_circles = decorations.get("enable_numbered_circles", True)

        # 加载字体
        self._fonts = {}
        self._load_fonts()

    def _load_fonts(self):
        """加载字体（优先等宽字体）"""
        font_roots = [
            "C:/Windows/Fonts",
            "/System/Library/Fonts",
            "/usr/share/fonts",
        ]
        # 等宽字体优先
        candidates = {
            "title": ["msyhbd.ttc", "consola.ttf", "Consolas.ttf", "simhei.ttf"],
            "body": ["consola.ttf", "Consolas.ttf", "msyh.ttc", "simsun.ttc"],
            "code": ["consola.ttf", "Consolas.ttf", "courier.ttf"],
        }

        for style, names in candidates.items():
            for name in names:
                for root in font_roots:
                    fp = Path(root) / name
                    if fp.exists():
                        try:
                            if style == "title":
                                size = self.title_size
                            elif style == "code":
                                size = self.code_size
                            else:
                                size = self.body_size
                            self._fonts[style] = ImageFont.truetype(str(fp), size)
                            break
                        except Exception:
                            continue
                if style in self._fonts:
                    break

        if "title" not in self._fonts:
            self._fonts["title"] = ImageFont.load_default()
        if "body" not in self._fonts:
            self._fonts["body"] = ImageFont.load_default()
        if "code" not in self._fonts:
            self._fonts["code"] = self._fonts.get("body", ImageFont.load_default())

    def _get_font(self, style: str = "body", size: int = None):
        """获取字体"""
        if size and style in self._fonts and hasattr(self._fonts[style], 'path'):
            try:
                return ImageFont.truetype(self._fonts[style].path, size)
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
        """渲染科技风格帧"""
        if not HAS_PIL:
            raise RuntimeError("PIL is required for rendering")

        # 创建画布
        img = Image.new("RGB", (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # 绘制网格背景
        if self.bg_grid:
            self._draw_grid(draw)

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

    def _draw_grid(self, draw):
        """绘制科技感网格"""
        spacing = self.bg_grid_spacing
        r, g, b, a = self.bg_grid_color if isinstance(self.bg_grid_color, tuple) else (0, 255, 255, 8)

        # 垂直线
        for x in range(0, self.width, spacing):
            draw.line([(x, 0), (x, self.height)], fill=(r, g, b, a), width=1)

        # 水平线
        for y in range(0, self.height, spacing):
            draw.line([(0, y), (self.width, y)], fill=(r, g, b, a), width=1)

    def _draw_title(self, draw, title: str, subtitle: str) -> int:
        """绘制标题区（科技风格）"""
        y = self.padding
        x = self.padding
        max_w = self.width - 2 * self.padding

        # 风格标签
        tag_text = self.style_config.get("tag_text", "TECH")
        if tag_text:
            tag_font = self._get_font("body", int(self.body_size * 0.8))
            tw = tag_font.getlength(tag_text)
            draw.rounded_rectangle([x, y, x + tw + 16, y + 24],
                                  radius=4, outline=self.accent_color, width=1)
            draw.text((x + 8, y + 4), tag_text, fill=self.accent_color,
                     font=tag_font)
            y += 36

        # 标题（使用强调色）
        title_font = self._get_font("title", self.title_size)
        lines = self._wrap_text(title, title_font, max_w)
        line_h = int(self.title_size * self.line_height)

        for i, line in enumerate(lines[:2]):
            # 霓虹发光效果
            if self.glow_enabled:
                for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                    draw.text((x + ox, y + i * line_h + oy), line,
                             fill=self.glow_color, font=title_font)
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
                         fill=self.colors.get("secondary", "#8B949E"),
                         font=body_font)
            y += sub_h + 10

        # 科技感分隔线
        y += 20
        draw.line([(x, y), (x + 150, y)], fill=self.accent_color, width=2)

        return y + 20

    def _draw_content_text_only(self, draw, bullets, y0, y1):
        """绘制纯文字内容（科技风格）"""
        if not bullets:
            bullets = ["技术讲解"]

        content_h = y1 - y0 - 60
        n = min(len(bullets), 6)

        gap = 12
        item_h = (content_h - gap * (n - 1)) // n

        x = self.padding
        w = self.width - 2 * self.padding

        for i, bullet in enumerate(bullets[:n]):
            item_y = y0 + i * (item_h + gap)

            # 绘制卡片背景
            card_x = x
            card_y = item_y
            card_w = w
            card_h = item_h - gap
            draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                                  radius=self.card_radius,
                                  outline=self.card_border,
                                  width=self.card_border_width)

            # 绘制序号
            if self.enable_numbered_circles:
                radius = 10
                cx = card_x + radius + 8
                cy = card_y + radius + 4
                draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                           fill=self.accent_color)
                num_font = self._get_font("body", 12)
                num = str(i + 1)
                draw.text((cx - 3, cy - 7), num, fill=self.bg_color,
                         font=num_font)
                text_x = cx + radius + 12
            else:
                text_x = card_x + 16

            # 绘制要点文字
            body_font = self._get_font("body", self.body_size)
            max_text_w = card_w - (text_x - card_x) - 16
            lines = self._wrap_text(bullet, body_font, max_text_w)
            line_h = int(self.body_size * self.line_height)

            for li, line in enumerate(lines[:2]):
                if card_y + 4 + li * line_h > card_y + card_h - 4:
                    break
                draw.text((text_x, card_y + 4 + li * line_h), line,
                         fill=self.primary_color, font=body_font)

    def _draw_content_with_media(self, draw, img, bullets, media_path, y0, y1):
        """绘制带素材的内容（左侧文字，右侧代码/截图）"""
        media_w = 400
        gap = 16

        # 右侧素材区（类似代码窗口）
        mx0 = self.width - self.padding - media_w
        my0 = y0
        my1 = y1

        # 绘制代码窗口边框
        draw.rounded_rectangle([mx0, my0, mx0 + media_w, my1],
                              radius=self.card_radius,
                              outline=self.card_border,
                              width=self.card_border_width)

        # 窗口标题栏
        title_h = 24
        draw.rectangle([mx0, my0, mx0 + media_w, my0 + title_h],
                      fill=self.card_bg)
        draw.text((mx0 + 8, my0 + 4), "CODE REF", fill=self.accent_secondary,
                 font=self._get_font("body", 12))

        try:
            from PIL import Image
            media = Image.open(media_path).convert("RGBA")
            mw = media_w - 4
            mh = y1 - y0 - title_h - 4
            media.thumbnail((mw, mh), Image.LANCZOS)
            px = mx0 + 2
            py = my0 + title_h + 2
            img.paste(media, (px, py), media if media.mode == "RGBA" else None)
        except Exception:
            pass

        # 左侧文字区
        lx0, lx1 = self.padding, mx0 - gap
        lw = lx1 - lx0

        if not bullets:
            bullets = ["技术讲解"]

        n = min(len(bullets), 4)
        item_h = (y1 - y0 - 20) // n

        for i, bullet in enumerate(bullets[:n]):
            item_y = y0 + 10 + i * item_h
            body_font = self._get_font("body", self.body_size)
            lines = self._wrap_text(bullet, body_font, lw - 20)
            line_h = int(self.body_size * self.line_height)

            for li, line in enumerate(lines[:2]):
                if item_y + li * line_h > y1 - 20:
                    break
                draw.text((lx0 + 20, item_y + li * line_h), line,
                         fill=self.primary_color, font=body_font)

    def _draw_footer(self, draw, idx: int, total: int, y: int):
        """绘制底部信息（科技风格）"""
        # 进度条样式
        body_font = self._get_font("body", int(self.body_size * 0.85))
        marker = f"[{idx + 1}/{total}]"
        draw.text((self.padding, y), marker, fill=self.colors.get("secondary", "#8B949E"),
                 font=body_font)

        # 霓虹进度条
        if self.enable_progress_dots and total > 1:
            bar_x = self.padding + 80
            bar_w = self.width - 2 * self.padding - 80
            dot_w = bar_w / total
            dot_radius = 5

            for i in range(total):
                cx = bar_x + i * dot_w + dot_w / 2
                cy = y + 8
                color = self.accent_color if i <= idx else self.card_border
                # 发光效果
                if i <= idx and self.glow_enabled:
                    for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        draw.ellipse([cx - dot_radius - 1 + ox, cy - dot_radius - 1 + oy,
                                   cx + dot_radius + 1 + ox, cy + dot_radius + 1 + oy],
                                   fill=self.glow_color)
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
            title = scene.get("title", f"module_{i+1}")
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
register_renderer("tech", TechStyleRenderer)
