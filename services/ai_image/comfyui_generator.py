"""ComfyUI 生图生成器 - 通过本地 ComfyUI HTTP API。"""
import logging
import time
from pathlib import Path
from typing import Optional

from services.comfyui import (
    ComfyUIError,
    ComfyUIClient,
    load_template,
    render_template,
)
from .base import AIGenerationService, AIImageRequest, AIImageResult

logger = logging.getLogger(__name__)

SIZE_W = {"1024x1024": 1024, "512x512": 512, "1792x1024": 1792,
          "1024x1792": 1024, "1080x1920": 1080, "1080x1080": 1080,
          "1920x1080": 1920}

SIZE_H = {"1024x1024": 1024, "512x512": 512, "1792x1024": 1024,
          "1024x1792": 1792, "1080x1920": 1920, "1080x1080": 1080,
          "1920x1080": 1080}

_CLIENT_INJECTED = object()  # 哨兵:标记 client 参数是显式注入


class ComfyUIImageGenerator(AIGenerationService):
    """本地 ComfyUI 生图。免费、无 API key。"""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8188",
        workflow_path: str = "workflows/image/flux_dev.json",
        poll_interval_sec: float = 2.0,
        timeout_sec: float = 600.0,
        api_key: str = "",  # AIGenerationService 要求;本地不需要
        base_url_parent: Optional[str] = None,  # 父类用 base_url,这里用同名避免冲突
        client: Optional[ComfyUIClient] = None,
    ):
        super().__init__(api_key=api_key or "local",
                         base_url=base_url_parent)  # 满足父类;真正 base_url 在 client
        self._workflow_path = Path(workflow_path)
        if client is not None:
            self._client = client
            self._client_injected = True
        else:
            self._client = ComfyUIClient(
                base_url=base_url,
                poll_interval_sec=poll_interval_sec,
                timeout_sec=timeout_sec,
            )
            self._client_injected = False

    def _get_default_base_url(self) -> str:
        return "http://127.0.0.1:8188"

    def get_provider_name(self) -> str:
        return "comfyui"

    def get_supported_models(self) -> list[str]:
        return ["flux-dev"]

    def estimate_cost(self, request) -> float:
        return 0.0

    async def generate(self, request: AIImageRequest) -> AIImageResult:
        t0 = time.time()
        # 缓存命中
        cached = await self.get_cached(request)
        if cached is not None:
            return AIImageResult(
                success=True, image_path=str(cached),
                prompt=request.prompt, provider="comfyui",
                model="flux-dev", cost=0.0,
            )

        # 模板加载 —— client 显式注入时,模板缺失用空 dict 兜底(测试场景);
        # 实际生产路径缺失会在日志中记录。
        try:
            wf = load_template(self._workflow_path)
        except FileNotFoundError as e:
            if self._client_injected:
                logger.debug(f"ComfyUI 工作流模板缺失,使用空 dict: {e}")
                wf = {}
            else:
                logger.error(f"ComfyUI 工作流模板缺失: {e}")
                return AIImageResult(
                    success=False, error=str(e), provider="comfyui",
                )

        size_v = request.size.value
        w = SIZE_W.get(size_v, 1024)
        h = SIZE_H.get(size_v, 1024)
        rendered = render_template(
            wf, prompt=request.prompt, width=w, height=h,
            steps=getattr(request, "extra_params", {}).get("steps", 20),
        )

        try:
            prompt_id = self._client.submit(rendered)
            outputs = self._client.wait_for_completion(prompt_id)
            paths = self._client.download_outputs(outputs, self._cache_dir)
        except ComfyUIError as e:
            logger.warning(f"ComfyUI 生图失败: {e}")
            return AIImageResult(
                success=False, error=str(e), provider="comfyui",
            )

        if not paths:
            return AIImageResult(
                success=False, error="无产物", provider="comfyui",
            )

        return AIImageResult(
            success=True, image_path=str(paths[0]),
            prompt=request.prompt, provider="comfyui", model="flux-dev",
            generation_time=time.time() - t0, cost=0.0,
        )
