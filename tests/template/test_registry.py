"""TemplateRegistry 测试"""
import os
import tempfile
from pathlib import Path
from services.template.registry import TemplateRegistry


def test_scan_templates():
    """测试扫描模板目录"""
    with tempfile.TemporaryDirectory() as tmp:
        # 创建测试模板结构
        tmp_path = Path(tmp)
        (tmp_path / "1080x1920").mkdir()
        (tmp_path / "1080x1920" / "image_default.html").write_text("<html></html>")
        (tmp_path / "1080x1920" / "image_modern.html").write_text("<html></html>")
        (tmp_path / "1920x1080").mkdir()
        (tmp_path / "1920x1080" / "image_film.html").write_text("<html></html>")

        registry = TemplateRegistry(templates_dir=tmp_path)
        templates = registry.scan()

        assert len(templates) == 3
        names = {t.name for t in templates}
        assert names == {"image_default", "image_modern", "image_film"}


def test_get_template():
    """测试获取指定模板"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "1080x1920").mkdir()
        (tmp_path / "1080x1920" / "image_default.html").write_text("<html></html>")

        registry = TemplateRegistry(templates_dir=tmp_path)
        registry.scan()
        template = registry.get("image_default")

        assert template.name == "image_default"
        assert template.width == 1080
        assert template.height == 1920


def test_get_nonexistent_raises():
    """测试不存在的模板抛出异常"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "1080x1920").mkdir()

        registry = TemplateRegistry(templates_dir=tmp_path)
        registry.scan()

        from services.template.exceptions import TemplateNotFoundError
        import pytest

        with pytest.raises(TemplateNotFoundError):
            registry.get("nonexistent")


def test_list_by_aspect():
    """测试按画幅筛选"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "1080x1920").mkdir()
        (tmp_path / "1920x1080").mkdir()
        (tmp_path / "1080x1920" / "image_default.html").write_text("")
        (tmp_path / "1920x1080" / "image_film.html").write_text("")

        registry = TemplateRegistry(templates_dir=tmp_path)
        registry.scan()
        portrait = registry.list_by_aspect("1080x1920")

        assert len(portrait) == 1
        assert portrait[0].name == "image_default"