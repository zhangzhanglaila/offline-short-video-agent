"""DashScope Wan 2.7 生图服务"""
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


class DashscopeImageGenerator(AIGenerationService):
    """DashScope Wan 2.7 T2I 生图生成器"""

    def _get_default_base_url(self) -> str:
        return "https://dashscope.aliyuncs.com/api/v1"

    async def generate(self, request: AIImageRequest) -> AIImageResult:
        """使用 Wan 2.7 生成图片"""
        start_time = time.time()

        # 检查缓存
        cached = await self.get_cached(request)
        if cached:
            return AIImageResult(
                success=True,
                image_path=str(cached),
                prompt=request.prompt,
                provider="dashscope",
                model=request.model or "wan2.7-t2i",
                generation_time=time.time() - start_time,
                cost=0.0,
            )

        try:
            # DashScope 使用不同的 API 格式
            payload = {
                "model": request.model or "wan2.7-t2i",
                "input": {
                    "prompt": request.prompt,
                },
                "parameters": {
                    "size": request.size.value,
                    "n": request.n,
                },
            }

            # 额外参数
            if request.extra_params:
                payload["parameters"].update(request.extra_params)

            # 发送请求
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/services/aigc/text2image/synthesis",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "X-DashScope-Async": "enable",  # 启用异步模式
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            # DashScope 返回任务 ID，需要轮询结果
            task_id = data.get("output", {}).get("task_id")
            if not task_id:
                raise ValueError(f"Invalid response: {data}")

            # 轮询任务结果
            image_url = await self._poll_result(task_id)

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
                provider="dashscope",
                model=request.model or "wan2.7-t2i",
                generation_time=time.time() - start_time,
                cost=cost,
            )

        except Exception as e:
            return AIImageResult(
                success=False,
                prompt=request.prompt,
                provider="dashscope",
                model=request.model or "wan2.7-t2i",
                error=str(e),
                generation_time=time.time() - start_time,
            )

    async def _poll_result(self, task_id: str, max_wait: int = 180) -> str:
        """轮询异步任务结果

        Args:
            task_id: 任务 ID
            max_wait: 最大等待时间（秒）

        Returns:
            图片 URL
        """
        import asyncio

        start = time.time()
        while time.time() - start < max_wait:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        f"{self.base_url}/tasks/{task_id}",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    # 检查任务状态
                    task_status = data.get("output", {}).get("task_status")
                    if task_status == "SUCCEEDED":
                        # 返回图片 URL
                        results = data.get("output", {}).get("results", [])
                        if results and len(results) > 0:
                            return results[0].get("url", "")
                    elif task_status in ["FAILED", "CANCELED"]:
                        raise ValueError(f"Task failed: {data}")

                    # 继续等待
                    await asyncio.sleep(2)

            except Exception as e:
                raise

        raise TimeoutError(f"Task timeout after {max_wait}s")

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
        return ["wan2.7-t2i", "wan2.6-t2i"]

    def estimate_cost(self, request: AIImageRequest) -> float:
        """估算生成成本（元）

        DashScope Wan 2.7 定价（2026）:
        - 1024x1024: ¥0.1/张
        """
        model = request.model or "wan2.7-t2i"

        if "wan2.7" in model.lower():
            # Wan 2.7 定价
            base_cost = 0.1  # 1024x1024
            pixels = self._get_pixels(request.size.value)
            base_pixels = 1024 * 1024
            return base_cost * (pixels / base_pixels)
        elif "wan2.6" in model.lower():
            # Wan 2.6 更便宜
            return 0.05
        else:
            return 0.1  # 默认价格

    def _get_pixels(self, size_str: str) -> int:
        """获取尺寸的像素数"""
        try:
            width, height = map(int, size_str.lower().split("x"))
            return width * height
        except:
            return 1024 * 1024  # 默认
