"""HTMLFrameGenerator 测试"""
import asyncio
from pathlib import Path

from services.template.html_generator import HTMLFrameGenerator
from services.template.models import TemplateInfo


def create_test_template(tmp: Path) -> TemplateInfo:
    """创建测试模板"""
    html_content = """
    <html>
    <head><style>body { background: #fafafa; }</style></head>
    <body>
        <h1>{{title}}</h1>
        <p>{{text}}</p>
    </body>
    </html>
    """
    template_file = tmp / "test.html"
    template_file.write_text(html_content, encoding="utf-8")

    return TemplateInfo(
        name="test",
        path=template_file,
        aspect_ratio="1080x1920",
        width=1080,
        height=1920,
        template_type="static",
        style="default",
        parameters=["title", "text"],
    )


def test_extract_parameters():
    """测试参数提取"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        info = create_test_template(Path(tmp))
        gen = HTMLFrameGenerator(info)
        params = gen.extract_parameters()
        assert "title" in params
        assert "text" in params


def test_render_jinja():
    """测试 Jinja2 渲染"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        info = create_test_template(Path(tmp))
        gen = HTMLFrameGenerator(info)
        html = gen.render_jinja({"title": "Hello", "text": "World"})
        assert "Hello" in html
        assert "World" in html
        assert "{{title}}" not in html


def test_generate_frame():
    """测试完整渲染流程（需要 Playwright）"""
    import tempfile

    async def _run():
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            info = create_test_template(tmp_path)
            output = tmp_path / "output.png"

            gen = HTMLFrameGenerator(info)
            result = await gen.generate_frame(
                context={"title": "Test", "text": "Hello"},
                output_path=output,
            )
            assert result.exists()
            assert result.suffix == ".png"
            assert result.stat().st_size > 0

    asyncio.run(_run())