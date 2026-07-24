"""render_template_frame fallback 路径测试"""
import asyncio
from pathlib import Path
import tempfile

from core.compose.scene_image_renderer import render_template_frame


async def test_fallback_called_on_failure():
    """模板不存在时调用 fallback_func"""
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "out.png"
        fallback_called = []

        async def fallback(out_path):
            fallback_called.append(out_path)
            # 写一个真实 PNG
            from PIL import Image
            Image.new("RGB", (1080, 1920), "#cccccc").save(out_path)
            return out_path

        result = await render_template_frame(
            template_name="nonexistent_template",
            context={"title": "x"},
            output_path=str(output),
            fallback_func=fallback,
        )
        assert len(fallback_called) == 1
        assert Path(result).exists()


test_fallback_called_on_failure.__test__ = False


def test_fallback_signature():
    asyncio.run(test_fallback_called_on_failure())
