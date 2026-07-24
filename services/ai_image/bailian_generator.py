"""阿里云百炼 WanX 生图生成器（原生 DashScope API）"""
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


# WanX 尺寸映射（WanX 使用 W*H 格式）
WANX_SIZE_MAP = {
    ImageSize.SQUARE_1024: "1024*1024",
    ImageSize.PORTRAIT_1080x1920: "1080*1920",
    ImageSize.LANDSCAPE_1920x1080: "1920*1080",
    ImageSize.SQUARE_1080: "1080*1080",
    ImageSize.SQUARE_512: "512*512",
    ImageSize.PORTRAIT_1024x1792: "1024*1792",
    ImageSize.LANDSCAPE_1792x1024: "1792*1024",
}


class BailianImageGenerator(AIGenerationService):
    """阿里云百炼 WanX 生图生成器（使用原生 DashScope API）

    使用 WanX 2.6 模型进行文生图，支持同步调用。
    """

    def _get_default_base_url(self) -> str:
        # DashScope 北京地域
        return "https://dashscope.aliyuncs.com"

    async def generate(self, request: AIImageRequest) -> AIImageResult:
        """使用 WanX 生成图片（同步调用）"""
        start_time = time.time()

        # 检查缓存
        cached = await self.get_cached(request)
        if cached:
            return AIImageResult(
                success=True,
                image_path=str(cached),
                prompt=request.prompt,
                provider="bailian",
                model=request.model or "wan2.6-t2i",
                generation_time=time.time() - start_time,
                cost=0.0,
            )

        try:
            # 映射尺寸
            wanx_size = WANX_SIZE_MAP.get(request.size, "1024*1024")

            # WanX API 请求格式（wan2.6-t2i 文生图）
            payload = {
                "model": request.model or "wan2.6-t2i",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": request.prompt}]
                        }
                    ]
                },
                "parameters": {
                    "size": wanx_size,
                    "n": request.n,
                    "watermark": False,
                    "prompt_extend": True,  # 智能改写
                    "negative_prompt": "",
                }
            }

            # 发送请求（wan2.6 同步 endpoint）
            url = f"{self.base_url}/api/v1/services/aigc/multimodal-generation/generation"
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            # 检查错误
            if "code" in data and data["code"]:
                raise ValueError(f"WanX API error: {data.get('message', data['code'])}")

            # 解析响应获取图片 URL
            # WanX 格式: output.choices[0].message.content[0].image
            if "output" not in data:
                raise ValueError(f"WanX 响应缺少 output: {data}")

            output = data["output"]

            # 检查是否完成
            if not output.get("finished"):
                raise ValueError(f"WanX 任务未完成: {data}")

            choices = output.get("choices", [])
            if not choices:
                raise ValueError(f"WanX 响应无 choices: {data}")

            content = choices[0].get("message", {}).get("content", [])
            if not content:
                raise ValueError(f"WanX 响应无 content: {data}")

            image_url = None
            for item in content:
                if item.get("type") == "image":
                    image_url = item.get("image")
                    break

            if not image_url:
                raise ValueError(f"WanX 响应无 image URL: {data}")

            # 下载并保存到本地
            local_path = await self._download_and_save(
                image_url,
                request.prompt,
                wanx_size,
            )

            # 计算成本
            cost = self.estimate_cost(request)

            return AIImageResult(
                success=True,
                image_path=local_path,
                image_url=image_url,
                prompt=request.prompt,
                provider="bailian",
                model=request.model or "wan2.6-t2i",
                generation_time=time.time() - start_time,
                cost=cost,
            )

        except Exception as e:
            return AIImageResult(
                success=False,
                prompt=request.prompt,
                provider="bailian",
                model=request.model or "wan2.6-t2i",
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
        return [
            "wan2.6-t2i",      # 文生图 V2（推荐）
            "wan2.1-t2i",      # 文生图 V1
            "wan2.6-image",    # 图像编辑（需输入图）
        ]

    def estimate_cost(self, request: AIImageRequest) -> float:
        """估算生成成本（元）

        参考：WanX 按成功生成的图片张数计费
        - wan2.6-t2i: 约 0.04-0.08 元/张
        """
        # 基础成本（按张数）
        base_cost = 0.05 * request.n
        # HD 质量加价
        if request.quality == "hd":
            base_cost *= 2
        return base_cost
