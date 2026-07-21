"""
场景图渲染器 - 将场景文字和素材合成为单张画面图。

这是"素材+文字配合展示"的核心：
- 标题卡/结尾卡: 风格背景色 + 居中大字
- 内容场景: 素材图cover-fit为背景 + 底部字幕条 + 讲解文字

输出的每张图对应视频的一个场景画面。
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# 中文字体候选路径（按优先级）
_CJK_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
    "C:/Windows/Fonts/msyhbd.ttc",    # 微软雅黑粗体
    "C:/Windows/Fonts/simhei.ttf",    # 黑体
    "C:/Windows/Fonts/simsun.ttc",    # 宋体
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

# 默认竖屏分辨率（短视频）
DEFAULT_SIZE = (1080, 1920)


def _find_cjk_font_path() -> Optional[str]:
    """查找可用的中文字体路径。

    Returns:
        字体文件路径，找不到返回None
    """
    for path in _CJK_FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """将十六进制颜色转为RGB元组。

    Args:
        hex_color: 如 "#FFFFFF"

    Returns:
        (r, g, b)
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    try:
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except (ValueError, IndexError):
        return (0, 0, 0)


class SceneImageRenderer:
    """场景画面渲染器。

    根据场景类型和风格配置，将文字与素材合成为单张画面图。

    Attributes:
        size: 画面尺寸 (宽, 高)
        style: 风格配置字典
        font_path: 中文字体路径
    """

    def __init__(
        self,
        style: Optional[Dict[str, Any]] = None,
        size: Tuple[int, int] = DEFAULT_SIZE,
        font_path: Optional[str] = None,
    ):
        """初始化渲染器。

        Args:
            style: 风格配置字典（含colors/typography）。None时用默认。
            size: 画面尺寸
            font_path: 中文字体路径。None时自动查找。
        """
        self.size = size
        self.style = style or self._default_style()
        self.font_path = font_path or _find_cjk_font_path()

    @staticmethod
    def _default_style() -> Dict[str, Any]:
        """默认风格（极简）。"""
        return {
            "colors": {
                "background": "#FFFFFF",
                "primary": "#1A1A1A",
                "secondary": "#666666",
                "accent": "#3B82F6",
            },
        }

    # ---------- 字体 ----------

    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        """加载指定字号的字体。

        Args:
            size: 字号

        Returns:
            字体对象
        """
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    # ---------- 公开渲染入口 ----------

    def render_scene(
        self,
        scene_type: str,
        text: str,
        output_path: str,
        material_path: Optional[str] = None,
    ) -> bool:
        """渲染单个场景为图片。

        Args:
            scene_type: 场景类型 (title_card/content/conclusion)
            text: 场景文字
            output_path: 输出图片路径
            material_path: 素材图路径（内容场景用；None则用背景色）

        Returns:
            True如果渲染成功
        """
        try:
            if scene_type == "content":
                img = self._render_content(text, material_path)
            else:
                # title_card / conclusion 都是整屏文字卡
                img = self._render_text_card(text, scene_type)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.convert("RGB").save(output_path)
            return True
        except Exception:
            return False

    # ---------- 分层渲染(D1: 背景与字幕分离) ----------

    def render_gradient_bg(self, output_path: str) -> bool:
        """渲染纯渐变背景(内容场景无素材时的运镜背景)。

        Args:
            output_path: 输出路径

        Returns:
            True如果成功
        """
        try:
            img = self._gradient_background()
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.convert("RGB").save(output_path)
            return True
        except Exception:
            return False

    def render_subtitle_overlay(self, text: str, output_path: str) -> bool:
        """渲染透明字幕覆盖层(轻量lower-third，叠加在运镜背景上)。

        相比旧版整块30%暗条，改为更轻盈的底部渐变，
        让素材画面露出更多(≥90%可视)。

        Args:
            text: 字幕文字
            output_path: 输出PNG路径(带透明通道)

        Returns:
            True如果成功
        """
        try:
            w, h = self.size
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))

            # 底部轻量渐变条(约22%高，最大透明度更低)
            bar_h = int(h * 0.22)
            bar_top = h - bar_h
            odraw = ImageDraw.Draw(overlay)
            max_alpha = 165  # 比旧版220更轻
            for y in range(bar_h):
                alpha = int(max_alpha * (y / bar_h) ** 1.3)
                odraw.rectangle([(0, bar_top + y), (w, bar_top + y + 1)],
                                fill=(0, 0, 0, alpha))

            # 字幕文字(白色描边，靠下居中)
            font_size = int(w * 0.058)
            font = self._font(font_size)
            lines = self._wrap_text(text, font, int(w * 0.86), odraw)
            line_height = int(font_size * 1.35)
            total_h = line_height * len(lines)
            y = h - int(bar_h * 0.5) - total_h // 2

            for line in lines:
                bbox = odraw.textbbox((0, 0), line, font=font)
                line_w = bbox[2] - bbox[0]
                x = (w - line_w) // 2
                self._draw_text_with_outline(
                    odraw, (x, y), line, font,
                    fill=(255, 255, 255), outline=(0, 0, 0),
                )
                y += line_height

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            overlay.save(output_path)
            return True
        except Exception:
            return False

    # ---------- 文字卡（标题/结尾） ----------

    def _render_text_card(self, text: str, scene_type: str) -> Image.Image:
        """渲染整屏文字卡。

        Args:
            text: 文字内容
            scene_type: 类型（决定强调色）

        Returns:
            PIL图像
        """
        colors = self.style.get("colors", {})
        bg = _hex_to_rgb(colors.get("background", "#FFFFFF"))
        primary = _hex_to_rgb(colors.get("primary", "#1A1A1A"))
        accent = _hex_to_rgb(colors.get("accent", "#3B82F6"))

        img = Image.new("RGB", self.size, bg)
        draw = ImageDraw.Draw(img)

        w, h = self.size
        # 标题卡用大字，结尾卡稍小
        font_size = int(w * 0.11) if scene_type == "title_card" else int(w * 0.09)
        font = self._font(font_size)

        # 文字换行
        lines = self._wrap_text(text, font, int(w * 0.82), draw)
        line_height = int(font_size * 1.35)
        total_h = line_height * len(lines)
        y = (h - total_h) // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            x = (w - line_w) // 2
            draw.text((x, y), line, font=font, fill=primary)
            y += line_height

        # 标题卡下方装饰线（强调色）
        if scene_type == "title_card":
            line_y = (h + total_h) // 2 + int(h * 0.03)
            line_w = int(w * 0.2)
            draw.rectangle(
                [(w - line_w) // 2, line_y, (w + line_w) // 2, line_y + 8],
                fill=accent,
            )

        return img

    # ---------- 内容场景（素材+字幕条） ----------

    def _render_content(
        self, text: str, material_path: Optional[str]
    ) -> Image.Image:
        """渲染内容场景：素材背景 + 底部字幕条。

        Args:
            text: 讲解文字
            material_path: 素材图路径

        Returns:
            PIL图像
        """
        w, h = self.size

        # 1. 背景：素材cover-fit，或渐变背景（占位）
        if material_path and os.path.exists(material_path):
            bg = self._cover_fit(material_path)
        else:
            bg = self._gradient_background()

        # 2. 底部字幕条（半透明黑色渐变）
        bg = self._add_subtitle_bar(bg, text)

        return bg

    def _cover_fit(self, image_path: str) -> Image.Image:
        """将素材图cover-fit到画面尺寸（保持比例，居中裁剪）。

        Args:
            image_path: 素材图路径

        Returns:
            填满画面的图像
        """
        w, h = self.size
        try:
            src = Image.open(image_path).convert("RGB")
        except Exception:
            return self._gradient_background()

        src_w, src_h = src.size
        # 计算缩放比例（取较大值以覆盖整个画面）
        scale = max(w / src_w, h / src_h)
        new_w, new_h = int(src_w * scale) + 1, int(src_h * scale) + 1
        src = src.resize((new_w, new_h), Image.LANCZOS)

        # 居中裁剪
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        return src.crop((left, top, left + w, top + h))

    def _gradient_background(self) -> Image.Image:
        """生成渐变背景（素材缺失时的占位）。

        Returns:
            渐变图像
        """
        w, h = self.size
        colors = self.style.get("colors", {})
        top_color = _hex_to_rgb(colors.get("accent", "#3B82F6"))
        bottom_color = _hex_to_rgb(colors.get("primary", "#1A1A1A"))

        base = Image.new("RGB", (1, h))
        for y in range(h):
            ratio = y / h
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            base.putpixel((0, y), (r, g, b))
        return base.resize(self.size)

    def _add_subtitle_bar(self, bg: Image.Image, text: str) -> Image.Image:
        """在底部添加半透明字幕条和文字。

        Args:
            bg: 背景图
            text: 字幕文字

        Returns:
            叠加字幕后的图像
        """
        w, h = self.size
        bg = bg.convert("RGB")

        # 字幕区域高度约占画面下方30%
        bar_h = int(h * 0.30)
        bar_top = h - bar_h

        # 半透明黑色渐变遮罩（顶部透明→底部不透明）
        overlay = Image.new("RGBA", (w, bar_h), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        for y in range(bar_h):
            alpha = int(220 * (y / bar_h))  # 0→220
            odraw.rectangle([(0, y), (w, y + 1)], fill=(0, 0, 0, alpha))

        bg_rgba = bg.convert("RGBA")
        bg_rgba.alpha_composite(overlay, (0, bar_top))
        bg = bg_rgba.convert("RGB")

        # 字幕文字（白色，靠下居中）
        draw = ImageDraw.Draw(bg)
        font_size = int(w * 0.06)
        font = self._font(font_size)
        lines = self._wrap_text(text, font, int(w * 0.86), draw)
        line_height = int(font_size * 1.4)
        total_h = line_height * len(lines)
        # 文字放在字幕条下部
        y = h - int(bar_h * 0.55) - total_h // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            x = (w - line_w) // 2
            # 描边增强可读性
            self._draw_text_with_outline(draw, (x, y), line, font,
                                          fill=(255, 255, 255),
                                          outline=(0, 0, 0))
            y += line_height

        return bg

    # ---------- 文字工具 ----------

    def _draw_text_with_outline(
        self, draw, pos, text, font, fill, outline, outline_width: int = 2
    ) -> None:
        """绘制带描边的文字（增强可读性）。

        Args:
            draw: ImageDraw对象
            pos: (x, y) 位置
            text: 文字
            font: 字体
            fill: 填充色
            outline: 描边色
            outline_width: 描边宽度
        """
        x, y = pos
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline)
        draw.text((x, y), text, font=font, fill=fill)

    def _wrap_text(
        self, text: str, font, max_width: int, draw
    ) -> List[str]:
        """按最大宽度对文字换行（支持中英文）。

        Args:
            text: 原始文字
            font: 字体
            max_width: 最大行宽（像素）
            draw: ImageDraw对象（用于测量）

        Returns:
            换行后的行列表
        """
        # 先按显式换行符切分
        result: List[str] = []
        for raw_line in text.split("\n"):
            if not raw_line:
                result.append("")
                continue
            current = ""
            for char in raw_line:
                test = current + char
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] > max_width and current:
                    result.append(current)
                    current = char
                else:
                    current = test
            if current:
                result.append(current)
        return result or [""]
