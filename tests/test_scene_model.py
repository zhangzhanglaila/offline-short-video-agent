"""Scene 数据模型扩展测试"""
from core.models.content import Scene


def test_scene_template_default_none():
    """默认无 template 字段"""
    s = Scene(scene_id=1, scene_type="content", text="x", duration=3.0)
    assert s.template is None


def test_scene_template_roundtrip():
    """template 字段 to_dict/from_dict 往返"""
    s = Scene(scene_id=1, scene_type="content", text="x", duration=3.0, template="image_default")
    d = s.to_dict()
    assert d["template"] == "image_default"
    s2 = Scene.from_dict(d)
    assert s2.template == "image_default"


def test_scene_from_dict_without_template():
    """旧数据（无 template 字段）也能正常解析"""
    s = Scene.from_dict({"scene_id": 1, "scene_type": "content", "text": "x", "duration": 3.0})
    assert s.template is None
