"""ComfyUIImageGenerator 单元测试。"""
import hashlib
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.ai_image.base import (
    AIImageRequest,
    AIProvider,
    ImageSize,
)
from services.ai_image.comfyui_generator import ComfyUIImageGenerator
from services.comfyui.client import WorkflowOutput


def _fake_client_ok():
    c = MagicMock()
    c.test_connection.return_value = True
    c.submit.return_value = "pid-1"
    c.wait_for_completion.return_value = [
        WorkflowOutput("a.png", "", "output")
    ]
    c.download_outputs.return_value = [Path("/fake/a.png")]
    return c


@pytest.mark.asyncio
async def test_generate_success(tmp_path):
    fake = _fake_client_ok()
    gen = ComfyUIImageGenerator(
        client=fake,
        workflow_path=tmp_path / "wf.json",  # 不会被实际读
    )
    req = AIImageRequest(
        prompt="a cat", provider=AIProvider.COMFYUI, size=ImageSize.SQUARE_512,
    )
    res = await gen.generate(req)
    assert res.success is True
    assert res.provider == "comfyui"
    assert res.cost == 0.0
    assert fake.submit.called
    assert fake.wait_for_completion.called


@pytest.mark.asyncio
async def test_generate_returns_cached_when_exists(tmp_path, monkeypatch):
    """如果缓存文件已存在,跳过 submit。"""
    cache_dir = Path("output/ai_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / "comfyui_512x512_aaaaaaaaaaaaaaaa.png"
    cached.write_bytes(b"x")
    try:
        fake = MagicMock()
        fake.test_connection.return_value = True
        gen = ComfyUIImageGenerator(client=fake)
        req = AIImageRequest(
            prompt="a cat", provider=AIProvider.COMFYUI, size=ImageSize.SQUARE_512,
        )
        # 用唯一 prompt 避免命中他人缓存
        req.prompt = "e2e-unique-prompt-" + "x" * 8
        # 强制与缓存路径一致:直接复用文件名约定
        h = hashlib.md5(req.prompt.encode()).hexdigest()[:12]
        cached_path = cache_dir / f"comfyui_512x512_{h}.png"
        cached_path.write_bytes(b"x")
        res = await gen.generate(req)
        assert res.success is True
        assert res.image_path == str(cached_path)
        assert not fake.submit.called
    finally:
        for p in [cached, cached_path]:
            if p.exists():
                p.unlink()


def test_estimate_cost_is_zero():
    fake = MagicMock()
    gen = ComfyUIImageGenerator(client=fake)
    req = AIImageRequest(prompt="x", provider=AIProvider.COMFYUI)
    assert gen.estimate_cost(req) == 0.0


def test_supported_models():
    fake = MagicMock()
    gen = ComfyUIImageGenerator(client=fake)
    assert "flux-dev" in gen.get_supported_models()
