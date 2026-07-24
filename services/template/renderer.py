"""模板渲染引擎主入口"""
from pathlib import Path
from typing import Any, Dict, Optional

from .browser import BrowserManager
from .exceptions import TemplateError
from .html_generator import HTMLFrameGenerator
from .registry import TemplateRegistry


class TemplateRenderer:
    """模板渲染引擎主类"""

    def __init__(self, templates_dir: Path = Path("templates")):
        self.registry = TemplateRegistry(templates_dir)
        self.registry.scan()
        self.browser_manager = BrowserManager()

    async def render(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> Path:
        """渲染指定模板为 PNG（不带降级）"""
        info = self.registry.get(template_name)  # 触发 TemplateNotFoundError
        generator = HTMLFrameGenerator(info)
        return await generator.generate_frame(context, output_path)

    async def render_with_fallback(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: Optional[Path] = None,
        fallback_func=None,
    ) -> Path:
        """渲染模板，失败时调用 fallback_func

        Args:
            template_name: 模板名称
            context: 模板参数
            output_path: 输出路径
            fallback_func: 降级函数 async (output_path) -> Path
        """
        try:
            return await self.render(template_name, context, output_path)
        except TemplateError as e:
            if fallback_func is None:
                raise
            if output_path is None:
                output_path = Path(f"output/fallback_{template_name}.png")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            return await fallback_func(output_path)

    async def close(self):
        """关闭浏览器"""
        await self.browser_manager.close()
