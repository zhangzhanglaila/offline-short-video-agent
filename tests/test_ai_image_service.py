"""AI 生图服务测试"""
import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_openai_generator():
    """测试 OpenAI 生图生成器"""
    from services.ai_image.openai_generator import OpenAIImageGenerator
    from services.ai_image.base import AIImageRequest, AIProvider, ImageSize

    # 使用 dummy API key 测试接口
    generator = OpenAIImageGenerator(api_key="dummy")

    # 验证基础属性
    assert generator.api_key == "dummy"
    assert generator.base_url == "https://api.openai.com/v1"

    # 验证支持的模型
    models = generator.get_supported_models()
    assert "dall-e-3" in models
    assert "dall-e-2" in models

    # 验证成本估算
    request = AIImageRequest(
        prompt="a cat",
        provider=AIProvider.OPENAI,
        size=ImageSize.SQUARE_1024,
    )
    cost = generator.estimate_cost(request)
    assert cost > 0


@pytest.mark.asyncio
async def test_dashscope_generator():
    """测试 DashScope 生图生成器"""
    from services.ai_image.dashscope_generator import DashscopeImageGenerator
    from services.ai_image.base import AIImageRequest, AIProvider, ImageSize

    # 使用 dummy API key 测试接口
    generator = DashscopeImageGenerator(api_key="dummy")

    # 验证基础属性
    assert generator.api_key == "dummy"
    assert "dashscope" in generator.base_url.lower()

    # 验证支持的模型
    models = generator.get_supported_models()
    assert "wan2.7-t2i" in models
    assert "wan2.6-t2i" in models

    # 验证成本估算
    request = AIImageRequest(
        prompt="a cat",
        provider=AIProvider.DASHSCOPE,
        size=ImageSize.SQUARE_1024,
    )
    cost = generator.estimate_cost(request)
    assert cost > 0
    # DashScope 应该比 OpenAI 便宜
    assert cost < 0.4


@pytest.mark.asyncio
async def test_image_size_enum():
    """测试图片尺寸枚举"""
    from services.ai_image.base import ImageSize

    # 验证标准尺寸
    assert ImageSize.SQUARE_1024.value == "1024x1024"
    assert ImageSize.SQUARE_512.value == "512x512"
    assert ImageSize.LANDSCAPE_1792x1024.value == "1792x1024"
    assert ImageSize.PORTRAIT_1024x1792.value == "1024x1792"

    # 验证短视频常用尺寸
    assert ImageSize.PORTRAIT_1080x1920.value == "1080x1920"
    assert ImageSize.SQUARE_1080.value == "1080x1080"
    assert ImageSize.LANDSCAPE_1920x1080.value == "1920x1080"


@pytest.mark.asyncio
async def test_cache_path_generation():
    """测试缓存路径生成"""
    from services.ai_image.openai_generator import OpenAIImageGenerator

    generator = OpenAIImageGenerator(api_key="test")

    # 测试缓存路径生成
    path1 = generator._get_cache_path("test prompt", "1024x1024")
    path2 = generator._get_cache_path("test prompt", "1024x1024")
    path3 = generator._get_cache_path("different prompt", "1024x1024")

    # 相同 prompt 应该生成相同路径
    assert path1 == path2
    # 不同 prompt 应该生成不同路径
    assert path1 != path3
    # 路径应该在 output/ai_cache 目录下
    assert "ai_cache" in str(path1)


def test_ai_image_request_validation():
    """测试 AI 生图请求验证"""
    from services.ai_image.base import AIImageRequest, AIProvider, ImageSize

    # 基本请求
    request = AIImageRequest(
        prompt="a beautiful sunset",
        provider=AIProvider.OPENAI,
        size=ImageSize.SQUARE_1024,
    )

    assert request.prompt == "a beautiful sunset"
    assert request.provider == AIProvider.OPENAI
    assert request.size == ImageSize.SQUARE_1024
    assert request.n == 1  # 默认值
    assert request.quality == "standard"  # 默认值


def test_ai_image_result_validation():
    """测试 AI 生图结果验证"""
    from services.ai_image.base import AIImageResult

    # 成功结果
    result = AIImageResult(
        success=True,
        image_path="/path/to/image.png",
        prompt="a cat",
        provider="openai",
        model="dall-e-3",
        generation_time=5.0,
        cost=0.4,
    )

    assert result.success is True
    assert result.image_path == "/path/to/image.png"
    assert result.cost == 0.4

    # 失败结果
    error_result = AIImageResult(
        success=False,
        prompt="a cat",
        provider="openai",
        error="API key invalid",
        generation_time=1.0,
    )

    assert error_result.success is False
    assert error_result.error == "API key invalid"


if __name__ == "__main__":
    import asyncio

    async def run_tests():
        print("测试 OpenAI 生成器...")
        await test_openai_generator()
        print("✅ OpenAI 生成器测试通过")

        print("测试 DashScope 生成器...")
        await test_dashscope_generator()
        print("✅ DashScope 生成器测试通过")

        print("测试图片尺寸枚举...")
        await test_image_size_enum()
        print("✅ 图片尺寸枚举测试通过")

        print("测试缓存路径生成...")
        await test_cache_path_generation()
        print("✅ 缓存路径生成测试通过")

        print("测试请求验证...")
        test_ai_image_request_validation()
        print("✅ 请求验证测试通过")

        print("测试结果验证...")
        test_ai_image_result_validation()
        print("✅ 结果验证测试通过")

        print("\n✅ 所有测试通过！")

    asyncio.run(run_tests())
