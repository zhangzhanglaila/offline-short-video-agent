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


def test_same_name_different_aspects_both_registered():
    """同名模板在不同画幅下都应被注册(回归测试:修复前因_dict_key冲突仅保留一个)"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "1080x1920").mkdir()
        (tmp_path / "1920x1080").mkdir()
        # 关键:两个画幅下都有 image_book.html
        (tmp_path / "1080x1920" / "image_book.html").write_text("<html></html>")
        (tmp_path / "1920x1080" / "image_book.html").write_text("<html></html>")

        registry = TemplateRegistry(templates_dir=tmp_path)
        templates = registry.scan()

        # 必须有两个模板(修复前会因为 name 冲突只保留一个)
        assert len(templates) == 2
        aspects = {t.aspect_ratio for t in templates}
        assert aspects == {"1080x1920", "1920x1080"}
        # 两个模板同名
        assert all(t.name == "image_book" for t in templates)