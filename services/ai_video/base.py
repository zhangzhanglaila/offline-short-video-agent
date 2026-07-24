"""AI 生视频服务基础接口和模型"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, AsyncGenerator


class VideoProvider(str, Enum):
    """AI 生视频供应商"""
    DASHSCOPE = "dashscope"  # 通义万相
    KLING = "kling"  # 可灵


class VideoSize(str, Enum):
    """视频尺寸（画幅比例）"""
    PORTRAIT_9_16 = "9:16"  # 竖屏 1080x1920
    LANDSCAPE_16_9 = "16:9"  # 横屏 1920x1080
    SQUARE_1_1 = "1:1"  # 方形 1080x1080


class VideoResolution(str, Enum):
    """视频分辨率"""
    RES_720P = "720P"
    RES_1080P = "1080P"


class VideoTaskStatus(str, Enum):
    """视频生成任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class VideoGenerationRequest:
    """AI 生视频请求"""
    prompt: str  # 提示词
    provider: VideoProvider  # 供应商
    model: Optional[str] = None  # 模型（如 wan2.7-t2v）
    size: VideoSize = VideoSize.PORTRAIT_9_16  # 画幅
    resolution: VideoResolution = VideoResolution.RES_1080P  # 分辨率
    duration: int = 5  # 时长（秒）
    image_path: Optional[str] = None  # 图生视频时的输入图片
    n: int = 1  # 生成数量
    extra_params: Dict[str, Any] = None  # 额外参数

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


@dataclass
class VideoGenerationProgress:
    """视频生成进度"""
    task_id: str
    status: VideoTaskStatus
    progress: float = 0.0  # 0.0 - 1.0
    video_path: Optional[str] = None
    video_url: Optional[str] = None
    error: Optional[str] = None
    created_time: float = 0.0
    updated_time: float = 0.0


@dataclass
class VideoGenerationResult:
    """AI 生视频结果"""
    success: bool
    video_path: Optional[str] = None  # 本地保存路径
    video_url: Optional[str] = None  # 原始 URL
    prompt: str = ""
    provider: str = ""
    model: str = ""
    task_id: str = ""
    error: Optional[str] = None
    generation_time: float = 0.0  # 生成耗时（秒）
    cost: float = 0.0  # 成本（元）


class AIVideoGenerationService(ABC):
    """AI 生视频服务抽象基类"""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or self._get_default_base_url()
        self._cache_dir = Path("output/ai_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def _get_default_base_url(self) -> str:
        """获取默认 API 地址"""
        pass

    @abstractmethod
    async def generate(
        self, request: VideoGenerationRequest
    ) -> AsyncGenerator[VideoGenerationProgress, None]:
        """生成视频（异步生成器，返回进度）"""
        pass

    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """取消生成任务"""
        pass

    @abstractmethod
    def get_status(self, task_id: str) -> Optional[VideoGenerationProgress]:
        """查询任务状态"""
        pass

    @abstractmethod
    def get_supported_models(self) -> list[str]:
        """获取支持的模型列表"""
        pass

    @abstractmethod
    def estimate_cost(self, request: VideoGenerationRequest) -> float:
        """估算生成成本（元）"""
        pass

    def _get_cache_path(self, prompt: str, size: str) -> Path:
        """生成缓存路径（基于 prompt hash）"""
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        filename = f"{self.get_provider_name()}_video_{size}_{prompt_hash}.mp4"
        return self._cache_dir / filename

    def get_provider_name(self) -> str:
        """获取供应商名称"""
        return self.__class__.__name__.replace("VideoGenerator", "").lower()

    async def get_cached(self, request: VideoGenerationRequest) -> Optional[Path]:
        """检查缓存中是否已有该视频"""
        cache_path = self._get_cache_path(request.prompt, request.size.value)
        if cache_path.exists():
            return cache_path
        return None
