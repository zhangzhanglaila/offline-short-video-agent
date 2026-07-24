"""模板 API 测试"""
import pytest
import asyncio
from pathlib import Path


@pytest.mark.asyncio
async def test_template_list():
    """测试获取模板列表"""
    from api.template_api import get_registry

    registry = get_registry()
    templates = registry.scan()

    # 验证至少有一些模板
    assert len(templates) > 0

    # 验证模板结构
    template = templates[0]
    assert hasattr(template, 'name')
    assert hasattr(template, 'aspect_ratio')
    assert hasattr(template, 'template_type')


@pytest.mark.asyncio
async def test_template_filters():
    """测试模板筛选功能"""
    from api.template_api import get_registry

    registry = get_registry()
    registry.scan()

    # 按画幅筛选
    portrait_templates = registry.list_by_aspect('1080x1920')
    assert all(t.aspect_ratio == '1080x1920' for t in portrait_templates)

    # 按类型筛选
    image_templates = registry.list_by_type('image')
    assert all(t.template_type == 'image' for t in image_templates)


@pytest.mark.asyncio
async def test_template_get():
    """测试获取单个模板"""
    from api.template_api import get_registry
    from services.template.exceptions import TemplateNotFoundError

    registry = get_registry()
    registry.scan()

    # 获取存在的模板
    first_template = list(registry._cache.values())[0]
    template = registry.get(first_template.name)
    assert template.name == first_template.name

    # 获取不存在的模板应抛出异常
    with pytest.raises(TemplateNotFoundError):
        registry.get('nonexistent_template')


def test_template_api_module():
    """测试模板 API 模块加载"""
    import api.template_api
    from api.template_api import router, get_registry, get_renderer

    # 验证路由已定义
    assert router is not None
    assert len(router.routes) > 0

    # 验证单例函数
    registry1 = get_registry()
    registry2 = get_registry()
    assert registry1 is registry2  # 应该是同一个实例


if __name__ == '__main__':
    # 简单运行测试
    import sys

    async def run_tests():
        print("测试模板列表...")
        await test_template_list()
        print("✅ 模板列表测试通过")

        print("测试模板筛选...")
        await test_template_filters()
        print("✅ 模板筛选测试通过")

        print("测试获取单个模板...")
        await test_template_get()
        print("✅ 获取单个模板测试通过")

        print("测试 API 模块...")
        test_template_api_module()
        print("✅ API 模块测试通过")

        print("\n✅ 所有测试通过！")

    asyncio.run(run_tests())
