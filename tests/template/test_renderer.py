"""TemplateRenderer 测试"""
import asyncio
import tempfile
from pathlib import Path

import pytest

from services.template.exceptions import BrowserNotAvailableError, TemplateNotFoundError
from services.template.renderer import TemplateRenderer


class BrowserUnavailableRenderer(TemplateRenderer):
    """Renderer test double that simulates an unavailable browser."""

    async def render(self, template_name, context, output_path=None):
        raise BrowserNotAvailableError("Chromium is unavailable")


def test_renderer_init():
    """测试初始化"""
    r = TemplateRenderer()
    assert r.registry is not None
    assert r.browser_manager is not None




def test_render_with_fallback_to_pil():
    """测试降级到 PIL 渲染（使用不存在模板触发降级）"""
    async def _run():
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            renderer = TemplateRenderer(templates_dir=tmp_path)
            renderer.registry.scan()

            # 用不存在的模板测试未提供 fallback 时仍抛出原始异常
            with pytest.raises(TemplateNotFoundError):
                await renderer.render("nonexistent", {}, tmp_path / "out.png")

    asyncio.run(_run())


def test_render_with_fallback_catches_browser_unavailable_error():
    """Browser failures from the template subsystem trigger the fallback path."""
    async def _run():
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "fallback.png"
            renderer = BrowserUnavailableRenderer(templates_dir=Path(tmp))
            fallback_calls = []

            async def fallback(path):
                fallback_calls.append(path)
                return path

            result = await renderer.render_with_fallback(
                "image_default",
                {},
                output_path,
                fallback,
            )

            assert result == output_path
            assert fallback_calls == [output_path]

    asyncio.run(_run())
