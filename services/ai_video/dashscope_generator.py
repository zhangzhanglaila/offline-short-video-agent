"""通义万相 AI 生视频服务"""
import asyncio
import time
from pathlib import Path
from typing import AsyncGenerator, Optional
import httpx

from .base import (
    VideoGenerationRequest,
    VideoGenerationProgress,
    VideoTaskStatus,
)


class DashScopeVideoGenerator:
    """通义万相视频生成器

    支持:
    - T2V: 文生视频 (wan2.7-t2v)
    - I2V: 图生视频 (wan2.7-i2v)
    - R2V: 重绘视频 (wan2.7-r2v)
    """

    # 模型配置
    MODELS = {
        "wan2.7-t2v": {
            "display_name": "Wan 2.7 文生视频",
            "type": "t2v",
            "duration_range": (2, 15),
            "resolutions": ["720P", "1080P"],
            "ratios": ["16:9", "9:16", "1:1"],
            "fps": 30,
        },
        "wan2.7-i2v": {
            "display_name": "Wan 2.7 图生视频",
            "type": "i2v",
            "duration_range": (2, 10),
            "resolutions": ["720P", "1080P"],
            "ratios": ["16:9", "9:16"],
            "fps": 30,
        },
        "wan2.7-r2v": {
            "display_name": "Wan 2.7 重绘视频",
            "type": "r2v",
            "duration_range": (2, 10),
            "resolutions": ["720P", "1080P"],
            "ratios": ["16:9", "9:16"],
            "fps": 30,
        },
    }

    # 成本估算（元/分钟）
    COST_PER_MINUTE = {
        "wan2.7-t2v": 12.0,  # 约 1-2 元/5秒
        "wan2.7-i2v": 15.0,
        "wan2.7-r2v": 18.0,
    }

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """初始化通义万相视频生成器

        Args:
            api_key: DashScope API Key
            base_url: API 地址，默认使用官方地址
        """
        self.api_key = api_key
        self.base_url = base_url or "https://dashscope.aliyuncs.com/api/v1"

        # HTTP 客户端
        self._client: Optional[httpx.AsyncClient] = None

        # 缓存目录
        from pathlib import Path
        self._cache_dir = Path("output/ai_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # 任务状态缓存（模拟轮询）
        self._tasks: dict = {}

    def _get_default_base_url(self) -> str:
        """获取默认 API 地址"""
        return "https://dashscope.aliyuncs.com/api/v1"

    @property
    def client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（惰性创建）"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=120.0,
            )
        return self._client

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate(
        self, request: VideoGenerationRequest
    ) -> AsyncGenerator[VideoGenerationProgress, None]:
        """生成视频

        Args:
            request: VideoGenerationRequest

        Yields:
            VideoGenerationProgress
        """
        start_time = time.time()
        task_id = f"task_{int(start_time)}"

        # 生成任务 ID
        import hashlib
        task_id = hashlib.md5(f"{request.prompt}{start_time}".encode()).hexdigest()[:16]

        try:
            # 检查缓存
            cached = await self.get_cached(request)
            if cached:
                yield VideoGenerationProgress(
                    task_id=task_id,
                    status=VideoTaskStatus.SUCCEEDED,
                    progress=1.0,
                    video_path=str(cached),
                )
                return

            # 开始生成
            yield VideoGenerationProgress(
                task_id=task_id,
                status=VideoTaskStatus.PENDING,
                progress=0.0,
            )

            # 调用 API（同步模式，简化实现）
            model = request.model or "wan2.7-t2v"
            video_url = await self._call_api(request)

            if video_url:
                # 下载视频
                video_path = await self._download_video(video_url, request)

                yield VideoGenerationProgress(
                    task_id=task_id,
                    status=VideoTaskStatus.SUCCEEDED,
                    progress=1.0,
                    video_path=video_path,
                    video_url=video_url,
                )
            else:
                yield VideoGenerationProgress(
                    task_id=task_id,
                    status=VideoTaskStatus.FAILED,
                    error="视频生成失败",
                )

        except Exception as e:
            yield VideoGenerationProgress(
                task_id=task_id,
                status=VideoTaskStatus.FAILED,
                error=str(e),
            )

    async def _call_api(self, request: VideoGenerationRequest) -> Optional[str]:
        """调用通义万相 API

        Args:
            request: VideoGenerationRequest

        Returns:
            视频下载 URL，失败返回 None
        """
        model = request.model or "wan2.7-t2v"

        # 构建请求体
        payload = {
            "model": model,
            "input": {
                "prompt": request.prompt,
            },
            "parameters": {
                "size": self._format_size(request.size.value),
                "duration": request.duration,
            },
        }

        # 如果是图生视频
        if request.image_path:
            payload["input"]["image"] = request.image_path

        try:
            response = await self.client.post(
                "/services/aigc/video-generation/generation",
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                # 解析响应
                if data.get("output"):
                    url = data["output"].get("video_url")
                    if url:
                        return url
                else:
                    # 检查错误
                    if "error" in data or "message" in data:
                        error_msg = data.get("error", data.get("message", "Unknown error"))
                        raise Exception(f"API 错误: {error_msg}")

            return None

        except Exception as e:
            self._log_error(f"API 调用失败: {e}")
            return None

    async def _download_video(self, url: str, request: VideoGenerationRequest) -> Optional[str]:
        """下载视频到本地

        Args:
            url: 视频 URL
            request: 原始请求

        Returns:
            本地路径，失败返回 None
        """
        from pathlib import Path

        cache_path = self._get_cache_path(request.prompt, request.size.value)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=120.0)
                response.raise_for_status()

                cache_path.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_path, "wb") as f:
                    f.write(response.content)

                return str(cache_path)

        except Exception as e:
            self._log_error(f"下载失败: {e}")
            return None

    def _format_size(self, size: str) -> str:
        """格式化尺寸参数

        Args:
            size: 画幅比例 (9:16, 16:9, 1:1)

        Returns:
            API 需要的格式
        """
        # 通义万相使用比例格式
        size_map = {
            "9:16": "9:16",
            "16:9": "16:9",
            "1:1": "1:1",
        }
        return size_map.get(size, "9:16")

    def _get_cache_path(self, prompt: str, size: str) -> Path:
        """生成缓存路径"""
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        filename = f"dashscope_video_{size.replace(':', 'x')}_{prompt_hash}.mp4"
        return self._cache_dir / filename

    async def get_cached(self, request: VideoGenerationRequest) -> Optional[Path]:
        """检查缓存"""
        cache_path = self._get_cache_path(request.prompt, request.size.value)
        if cache_path.exists():
            return cache_path
        return None

    async def cancel(self, task_id: str) -> bool:
        """取消任务（简化实现）"""
        # 通义万相可能需要任务队列支持
        return False

    def get_status(self, task_id: str) -> Optional[VideoGenerationProgress]:
        """查询任务状态（简化实现）"""
        return self._tasks.get(task_id)

    def get_supported_models(self) -> list[str]:
        """获取支持的模型列表"""
        return list(self.MODELS.keys())

    def estimate_cost(self, request: VideoGenerationRequest) -> float:
        """估算成本（元）"""
        model = request.model or "wan2.7-t2v"
        cost_per_min = self.COST_PER_MINUTE.get(model, 12.0)
        duration_minutes = request.duration / 60.0
        return round(cost_per_min * duration_minutes, 2)

    def get_provider_name(self) -> str:
        """获取供应商名称"""
        return "dashscope"

    def _log_error(self, msg: str):
        """记录错误"""
        print(f"[DashScope] {msg}")
