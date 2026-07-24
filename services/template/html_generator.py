"""HTML → PNG 单帧生成器"""
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Template

from .browser import BrowserManager
from .exceptions import TemplateRenderError
from .models import TemplateInfo


class HTMLFrameGenerator:
    """HTML 模板 → PNG 单帧生成"""

    PARAM_PATTERN = re.compile(r"\{\{(\w+)\}\}")

    def __init__(self, template_info: TemplateInfo):
        self.template_info = template_info
        self.template_html = template_info.path.read_text(encoding="utf-8")

    def extract_parameters(self) -> List[str]:
        """提取模板中的 {{var}} 参数"""
        return list(set(self.PARAM_PATTERN.findall(self.template_html)))

    def render_jinja(self, context: Dict[str, Any]) -> str:
        """用 Jinja2 渲染 HTML"""
        try:
            tmpl = Template(self.template_html)
            return tmpl.render(**context)
        except Exception as e:
            raise TemplateRenderError(f"Jinja2 render failed: {e}")

    async def generate_frame(
        self,
        context: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> Path:
        """生成单帧 PNG"""
        rendered_html = self.render_jinja(context)
        return await self._screenshot(rendered_html, output_path)

    async def _screenshot(self, html: str, output_path: Optional[Path]) -> Path:
        """用 Playwright 截图"""
        browser_manager = BrowserManager()
        browser = await browser_manager.get_browser()

        page = await browser.new_page()
        try:
            await page.set_viewport_size(
                {
                    "width": self.template_info.width,
                    "height": self.template_info.height,
                }
            )
            await page.set_content(html, wait_until="load")
            # 等待字体和 CSS 加载
            await page.wait_for_timeout(500)

            if output_path is None:
                output_path = Path(f"output/frame_{self.template_info.name}.png")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(
                path=str(output_path),
                full_page=False,
            )
            return output_path
        except Exception as e:
            raise TemplateRenderError(f"Screenshot failed: {e}")
        finally:
            await page.close()