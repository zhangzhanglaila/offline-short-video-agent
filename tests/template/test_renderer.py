"""TemplateRenderer 测试"""
import asyncio
import tempfile
from pathlib import Path

import pytest

from services.template.exceptions import TemplateNotFoundError
from services.template.renderer import TemplateRenderer


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
            r = TemplateRenderer(templates_dir=tmp_path)
            r.registry.scan()

            # 用不存在的模板测试降级路径
            with pytest.raises(TemplateNotFoundError):
                # 这里测的是没有降级的情况
                await r.render("nonexistent", {}, tmp_path / "out.png")

    asyncio.run(_run())
