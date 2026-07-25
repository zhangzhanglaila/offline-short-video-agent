"""ComfyUI video generation service."""
import asyncio
import logging
import time
from pathlib import Path
from typing import AsyncGenerator, Optional

from services.comfyui import ComfyUIClient, ComfyUIError, load_template, render_template

from .base import (
    AIVideoGenerationService,
    VideoGenerationProgress,
    VideoGenerationRequest,
    VideoTaskStatus,
)

logger = logging.getLogger(__name__)

SIZE_PRESETS = {
    "9:16": (720, 1280),
    "16:9": (1280, 720),
    "1:1": (1024, 1024),
}


class ComfyUIVideoGenerator(AIVideoGenerationService):
    """Generate videos locally through a ComfyUI workflow."""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8188",
        workflow_path: str = "workflows/video/wan22_t2v.json",
        poll_interval_sec: float = 5.0,
        timeout_sec: float = 1800.0,
        api_key: str = "",
        client: Optional[ComfyUIClient] = None,
    ):
        super().__init__(api_key=api_key or "local", base_url=base_url)
        self._workflow_path = Path(workflow_path)
        self._client = client or ComfyUIClient(
            base_url=base_url,
            poll_interval_sec=poll_interval_sec,
            timeout_sec=timeout_sec,
        )
        self._progress_map: dict[str, VideoGenerationProgress] = {}

    def _get_default_base_url(self) -> str:
        return "http://127.0.0.1:8188"

    def get_provider_name(self) -> str:
        return "comfyui"

    def get_supported_models(self) -> list[str]:
        return ["wan2.2-t2v"]

    def estimate_cost(self, request: VideoGenerationRequest) -> float:
        return 0.0

    async def cancel(self, task_id: str) -> bool:
        logger.info("ComfyUI does not support cancelling task %s", task_id)
        return False

    def get_status(self, task_id: str) -> Optional[VideoGenerationProgress]:
        return self._progress_map.get(task_id)

    async def generate(
        self, request: VideoGenerationRequest
    ) -> AsyncGenerator[VideoGenerationProgress, None]:
        created_time = time.time()
        pending = VideoGenerationProgress(
            task_id="pending",
            status=VideoTaskStatus.PENDING,
            progress=0.0,
            created_time=created_time,
        )
        self._progress_map[pending.task_id] = pending

        cached = await self.get_cached(request)
        if cached is not None:
            yield VideoGenerationProgress(
                task_id="cached",
                status=VideoTaskStatus.SUCCEEDED,
                progress=1.0,
                video_path=str(cached),
                created_time=created_time,
                updated_time=time.time(),
            )
            return

        try:
            workflow = load_template(self._workflow_path)
        except FileNotFoundError as exc:
            yield self._failed("missing-template", str(exc))
            return

        width, height = SIZE_PRESETS.get(request.size.value, (1024, 1024))
        rendered = render_template(
            workflow,
            prompt=request.prompt,
            width=width,
            height=height,
            steps=20,
        )

        try:
            prompt_id = self._client.submit(rendered)
        except ComfyUIError as exc:
            yield self._failed("submit-failed", str(exc))
            return

        pending.task_id = prompt_id
        pending.status = VideoTaskStatus.PROCESSING
        pending.updated_time = time.time()
        self._progress_map[prompt_id] = pending
        yield pending

        try:
            outputs = await asyncio.to_thread(
                self._client.wait_for_completion, prompt_id
            )
        except ComfyUIError as exc:
            yield self._failed(prompt_id, str(exc))
            return

        try:
            paths = await asyncio.to_thread(
                self._client.download_outputs, outputs, self._cache_dir
            )
        except ComfyUIError as exc:
            yield self._failed(prompt_id, str(exc))
            return

        if not paths:
            yield self._failed(prompt_id, "无产物")
            return

        final = VideoGenerationProgress(
            task_id=prompt_id,
            status=VideoTaskStatus.SUCCEEDED,
            progress=1.0,
            video_path=paths[0].as_posix(),
            created_time=created_time,
            updated_time=time.time(),
        )
        self._progress_map[prompt_id] = final
        yield final

    def _failed(self, task_id: str, error: str) -> VideoGenerationProgress:
        progress = VideoGenerationProgress(
            task_id=task_id,
            status=VideoTaskStatus.FAILED,
            error=error,
            updated_time=time.time(),
        )
        self._progress_map[task_id] = progress
        return progress
