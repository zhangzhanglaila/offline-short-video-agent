"""E5 ComfyUI 集成测试。

默认 skip（ComfyUI 在大多数 CI 环境不可达）。
本地 GPU + ComfyUI 服务(127.0.0.1:8188)运行时,本测试会自动启用并真实跑通生图/生视频。
"""
import asyncio
from pathlib import Path

import pytest


@pytest.mark.integration
def test_real_comfyui_image_end_to_end():
    """真实 ComfyUI 跑通(需本地服务 + GPU)。默认 skip。"""
    from services.comfyui import ComfyUIClient
    c = ComfyUIClient()
    if not c.test_connection():
        pytest.skip("本地 ComfyUI 不可达")
    from services.ai_image.comfyui_generator import ComfyUIImageGenerator
    from services.ai_image.base import AIImageRequest, AIProvider, ImageSize

    gen = ComfyUIImageGenerator()
    req = AIImageRequest(
        prompt="a small red apple", provider=AIProvider.COMFYUI,
        size=ImageSize.SQUARE_512,
    )
    res = asyncio.run(gen.generate(req))
    assert res.success
    assert Path(res.image_path).exists()


@pytest.mark.integration
def test_real_comfyui_video_end_to_end():
    """真实 ComfyUI 跑通生视频(需本地服务 + GPU)。默认 skip。"""
    from services.comfyui import ComfyUIClient
    c = ComfyUIClient()
    if not c.test_connection():
        pytest.skip("本地 ComfyUI 不可达")
    from services.ai_video.comfyui_generator import ComfyUIVideoGenerator
    from services.ai_video.base import (
        VideoGenerationRequest,
        VideoProvider,
        VideoSize,
    )

    gen = ComfyUIVideoGenerator()

    async def _collect():
        results = []
        async for progress in gen.generate(
            VideoGenerationRequest(
                prompt="a cat walks on grass",
                provider=VideoProvider.COMFYUI,
                size=VideoSize.PORTRAIT_9_16,
                duration=3,
            )
        ):
            results.append(progress)
            if progress.video_path:
                return results
        return results

    progresses = asyncio.run(_collect())
    final = progresses[-1]
    assert final.video_path
    assert Path(final.video_path).exists()


def test_agent_uses_comfyui_when_configured(tmp_path, monkeypatch):
    """config 配 image_provider=comfyui 时,MaterialFetchAgent.ai_generator 选 ComfyUIImageGenerator。"""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("ai:\n  image_provider: comfyui\n")
    monkeypatch.chdir(tmp_path)

    from core.agents.material_fetch_agent import MaterialFetchAgent
    from services.config import load_config

    # 跳过 __init__ 副作用,直接测试 lazy 属性 + config 注入
    agent = MaterialFetchAgent.__new__(MaterialFetchAgent)
    agent._ai_generator = None
    agent._config = load_config("config.yaml")
    gen = agent.ai_generator
    assert gen.__class__.__name__ == "ComfyUIImageGenerator"


def test_agent_uses_comfyui_video_when_configured(tmp_path, monkeypatch):
    """config 配 video_provider=comfyui 时,ai_video_generator 选 ComfyUIVideoGenerator。"""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("ai:\n  video_provider: comfyui\n")
    monkeypatch.chdir(tmp_path)

    from core.agents.material_fetch_agent import MaterialFetchAgent
    from services.config import load_config

    agent = MaterialFetchAgent.__new__(MaterialFetchAgent)
    agent._ai_video_generator = None
    agent._config = load_config("config.yaml")
    gen = agent.ai_video_generator
    assert gen.__class__.__name__ == "ComfyUIVideoGenerator"


def test_agent_defaults_to_bailian_when_no_key(tmp_path, monkeypatch):
    """无 config / 无 key → 默认 bailian 但因无 BAILIAN_API_KEY 返回 None。"""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("")  # 空 config
    monkeypatch.chdir(tmp_path)
    # 确保无 key
    monkeypatch.delenv("BAILIAN_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    from core.agents.material_fetch_agent import MaterialFetchAgent
    from services.config import load_config

    agent = MaterialFetchAgent.__new__(MaterialFetchAgent)
    agent._ai_generator = None
    agent._config = load_config("config.yaml")
    assert agent.ai_generator is None  # 缺 key → None


def test_agent_openai_provider_returns_none_without_key(tmp_path, monkeypatch):
    """image_provider=openai 但缺 OPENAI_API_KEY → None。"""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("ai:\n  image_provider: openai\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from core.agents.material_fetch_agent import MaterialFetchAgent
    from services.config import load_config

    agent = MaterialFetchAgent.__new__(MaterialFetchAgent)
    agent._ai_generator = None
    agent._config = load_config("config.yaml")
    assert agent.ai_generator is None


def test_agent_construction_loads_config(tmp_path, monkeypatch):
    """MaterialFetchAgent.__init__ 应自动加载 config.yaml。"""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("ai:\n  image_provider: comfyui\n  video_provider: comfyui\n")
    monkeypatch.chdir(tmp_path)

    from core.agents.material_fetch_agent import MaterialFetchAgent

    agent = MaterialFetchAgent(api_manager=False, video_module=False)
    assert agent._config == {"ai": {"image_provider": "comfyui",
                                     "video_provider": "comfyui"}}