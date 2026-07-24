"""OpenAI DALL-E 3 生图服务"""
import time
import asyncio
from pathlib import Path
from typing import Optional

import httpx

from .base import (
    AIGenerationService,
    AIImageRequest,
    AIImageResult,
    AIProvider,
    ImageSize,
    ImageStyle,
)


class OpenAIImageGenerator(AIGenerationService):
    """OpenAI DALL-E 3 生图生成器"""

    def _get_default_base_url(self) -> str:
        return "https://api.openai.com/v1"

    async def generate(self, request: AIImageRequest) -> AIImageResult:
        """使用 DALL-E 3 生成图片"""
        start_time = time.time()

        # 检查缓存
        cached = await self.get_cached(request)
        if cached:
            return AIImageResult(
                success=True,
                image_path=str(cached),
                prompt=request.prompt,
                provider="openai",
                model=request.model or "dall-e-3",
                generation_time=time.time() - start_time,
                cost=0.0,  # 缓存命中无成本
            )

        try:
            # 构建请求参数
            payload = {
                "model": request.model or "dall-e-3",
                "prompt": request.prompt,
                "n": request.n,
                "size": request.size.value,
                "response_format": "url",  # 使用 URL 格式
            }

            # DALL-E 3 特定参数
            if request.model and "dall-e-3" in request.model.lower():
                if request.style:
                    payload["style"] = request.style.value
                if request.quality:
                    payload["quality"] = request.quality

            # 额外参数
            if request.extra_params:
                payload.update(request.extra_params)

            # 发送请求
            async with httpx.AsyncClient(timeout=60.0) as client:
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
                provider="openai",
                model=request.model or "dall-e-3",
                generation_time=time.time() - start_time,
                cost=cost,
            )

        except Exception as e:
            return AIImageResult(
                success=False,
                prompt=request.prompt,
                provider="openai",
                model=request.model or "dall-e-3",
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
        return ["dall-e-3", "dall-e-2"]

    def estimate_cost(self, request: AIImageRequest) -> float:
        """估算生成成本（元）

        OpenAI DALL-E 3 定价（2026）:
        - 1024x1024: ¥0.4/张
        - 其他尺寸按面积比例计算
        """
        model = request.model or "dall-e-3"

        if "dall-e-3" in model.lower():
            # DALL-E 3 定价
            base_cost = 0.4  # 1024x1024
            pixels = self._get_pixels(request.size.value)
            base_pixels = 1024 * 1024
            return base_cost * (pixels / base_pixels)
        elif "dall-e-2" in model.lower():
            # DALL-E 2 定价（更便宜）
            return 0.05
        else:
            return 0.4  # 默认价格

    def _get_pixels(self, size_str: str) -> int:
        """获取尺寸的像素数"""
        try:
            width, height = map(int, size_str.lower().split("x"))
            return width * height
        except:
            return 1024 * 1024  # 默认
