"""阿里云百炼 OpenAI 兼容接口生图生成器"""
import time
from pathlib import Path
from typing import Optional

import httpx

from .base import (
    AIGenerationService,
    AIImageRequest,
    AIImageResult,
    ImageSize,
)


class BailianImageGenerator(AIGenerationService):
    """阿里云百炼生图生成器（使用 OpenAI 兼容接口）"""

    def _get_default_base_url(self) -> str:
        # 百炼使用 DashScope 兼容接口
        return "https://dashscope.aliyuncs.com/compatible-mode/v1"

    async def generate(self, request: AIImageRequest) -> AIImageResult:
        """使用百炼生成图片"""
        start_time = time.time()

        # 检查缓存
        cached = await self.get_cached(request)
        if cached:
            return AIImageResult(
                success=True,
                image_path=str(cached),
                prompt=request.prompt,
                provider="bailian",
                model=request.model or "wanx-v1",
                generation_time=time.time() - start_time,
                cost=0.0,
            )

        try:
            # 百炼使用 OpenAI 兼容的 images/generations 接口
            payload = {
                "model": request.model or "wanx-v1",
                "prompt": request.prompt,
                "n": request.n,
                "size": request.size.value,
            }

            # 发送请求
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            # 获取图片 URL
            image_url = data["data"][0]["url"]

            # 下载并保存到本地
            local_path = await self._download_and_save(
                image_url,
                request.prompt,
                request.size.value,
            )

            # 计算成本
            cost = self.estimate_cost(request)

            return AIImageResult(
                success=True,
                image_path=local_path,
                image_url=image_url,
                prompt=request.prompt,
                provider="bailian",
                model=request.model or "wanx-v1",
                generation_time=time.time() - start_time,
                cost=cost,
            )

        except Exception as e:
            return AIImageResult(
                success=False,
                prompt=request.prompt,
                provider="bailian",
                model=request.model or "wanx-v1",
                error=str(e),
                generation_time=time.time() - start_time,
            )

    async def _download_and_save(
        self, url: str, prompt: str, size: str
    ) -> str:
        """下载图片并保存到本地"""
        cache_path = self._get_cache_path(prompt, size)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            cache_path.write_bytes(response.content)

        return str(cache_path)

    def get_supported_models(self) -> list[str]:
        """获取支持的模型列表"""
        return ["wanx-v1", "wanx-v2"]

    def estimate_cost(self, request: AIImageRequest) -> float:
        """估算生成成本（元）"""
        # 百炼生图成本（参考）
        return 0.05  # 估算价格
