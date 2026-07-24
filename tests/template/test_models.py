"""TemplateInfo 数据模型测试"""
from pathlib import Path
from services.template.models import TemplateInfo


def test_template_info_basic():
    """测试基本字段"""
    info = TemplateInfo(
        name="image_default",
        path=Path("templates/1080x1920/image_default.html"),
        aspect_ratio="1080x1920",
        width=1080,
        height=1920,
        template_type="image",
        style="default",
        parameters=["title", "text", "image"],
    )
    assert info.name == "image_default"
    assert info.width == 1080
    assert info.height == 1920
    assert "title" in info.parameters


def test_template_info_aspect_to_size():
    """测试画幅解析：1080x1920 → (1080, 1920)"""
    info = TemplateInfo.from_aspect(
        name="test",
        path=Path("test.html"),
        aspect_ratio="1080x1920",
        template_type="image",
        style="default",
    )
    assert info.width == 1080
    assert info.height == 1920
    assert info.aspect_ratio == "1080x1920"