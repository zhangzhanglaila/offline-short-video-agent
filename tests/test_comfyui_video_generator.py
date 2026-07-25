"""ComfyUI video generator tests."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.ai_video.base import (
    VideoGenerationProgress,
    VideoGenerationRequest,
    VideoProvider,
    VideoSize,
    VideoTaskStatus,
)
from services.ai_video.comfyui_generator import ComfyUIVideoGenerator
from services.comfyui.client import WorkflowOutput


def _fake_client_ok():
    client = MagicMock()
    client.submit.return_value = "pid-1"
    client.wait_for_completion.return_value = [
        WorkflowOutput("v.mp4", "", "output")
    ]
    client.download_outputs.return_value = [Path("/fake/v.mp4")]
    return client


@pytest.mark.asyncio
async def test_generate_yields_progress_and_succeeds(monkeypatch):
    fake = _fake_client_ok()
    monkeypatch.setattr(
        "services.ai_video.comfyui_generator.load_template", lambda path: {}
    )
    gen = ComfyUIVideoGenerator(client=fake, workflow_path="ignored")
    req = VideoGenerationRequest(
        prompt="a dog runs", provider=VideoProvider.COMFYUI,
        size=VideoSize.PORTRAIT_9_16, duration=5,
    )
    progresses = [progress async for progress in gen.generate(req)]
    final = progresses[-1]
    assert final.status == VideoTaskStatus.SUCCEEDED
    assert final.video_path == "/fake/v.mp4"
    assert fake.submit.called
    assert fake.wait_for_completion.called


@pytest.mark.asyncio
async def test_generate_yields_failed_on_error(monkeypatch):
    from services.comfyui.errors import ComfyUIExecutionError

    fake = MagicMock()
    fake.submit.return_value = "pid"
    fake.wait_for_completion.side_effect = ComfyUIExecutionError("bad")
    monkeypatch.setattr(
        "services.ai_video.comfyui_generator.load_template", lambda path: {}
    )
    gen = ComfyUIVideoGenerator(client=fake, workflow_path="ignored")
    req = VideoGenerationRequest(prompt="x", provider=VideoProvider.COMFYUI)
    progresses = [progress async for progress in gen.generate(req)]
    assert progresses[-1].status == VideoTaskStatus.FAILED
    assert "bad" in (progresses[-1].error or "")


def test_estimate_cost_zero():
    gen = ComfyUIVideoGenerator(client=MagicMock())
    req = VideoGenerationRequest(prompt="x", provider=VideoProvider.COMFYUI)
    assert gen.estimate_cost(req) == 0.0


def test_supported_models_contains_wan():
    gen = ComfyUIVideoGenerator(client=MagicMock())
    assert any("wan" in model for model in gen.get_supported_models())
