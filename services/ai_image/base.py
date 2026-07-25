"""AI 生图服务基础接口和模型"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any


class AIProvider(str, Enum):
    """AI 生图供应商"""
    OPENAI = "openai"
    DASHSCOPE = "dashscope"
    BAILIAN = "bailian"
    COMFYUI = "comfyui"


class ImageSize(str, Enum):
    """标准图片尺寸"""
    SQUARE_1024 = "1024x1024"
    SQUARE_512 = "512x512"
    LANDSCAPE_1792x1024 = "1792x1024"
    PORTRAIT_1024x1792 = "1024x1792"
    # 短视频常用
    PORTRAIT_1080x1920 = "1080x1920"
    SQUARE_1080 = "1080x1080"
    LANDSCAPE_1920x1080 = "1920x1080"


class ImageStyle(str, Enum):
    """图片风格（DALL-E 3）"""
    VIVID = "vivid"  # 鲜艳
    NATURAL = "natural"  # 自然


@dataclass
class AIImageRequest:
    """AI 生图请求"""
    prompt: str  # 提示词
    provider: AIProvider  # 供应商
    model: Optional[str] = None  # 模型（如 dall-e-3，默认使用供应商默认模型）
    size: ImageSize = ImageSize.SQUARE_1024  # 尺寸
    style: Optional[ImageStyle] = None  # 风格（DALL-E 3）
    n: int = 1  # 生成数量
    quality: str = "standard"  # 质量 standard/hd
    extra_params: Dict[str, Any] = None  # 额外参数

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


@dataclass
class AIImageResult:
    """AI 生图结果"""
    success: bool
    image_path: Optional[str] = None  # 本地保存路径
    image_url: Optional[str] = None  # 原始 URL
    prompt: str = ""
    provider: str = ""
    model: str = ""
    error: Optional[str] = None
    generation_time: float = 0.0  # 生成耗时（秒）
    cost: float = 0.0  # 成本（元）


class AIGenerationService(ABC):
    """AI 生图服务抽象基类"""

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
    async def generate(self, request: AIImageRequest) -> AIImageResult:
        """生成图片"""
        pass

    @abstractmethod
    def get_supported_models(self) -> list[str]:
        """获取支持的模型列表"""
        pass

    @abstractmethod
    def estimate_cost(self, request: AIImageRequest) -> float:
        """估算生成成本（元）"""
        pass

    def _get_cache_path(self, prompt: str, size: str) -> Path:
        """生成缓存路径（基于 prompt hash）

        将 size 中的 * 替换为 x 以兼容 Windows 文件系统
        """
        import hashlib
        # WanX 使用 W*H 格式，Windows 文件名不允许 *
        size_safe = size.replace("*", "x")
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        filename = f"{self.get_provider_name()}_{size_safe}_{prompt_hash}.png"
        return self._cache_dir / filename

    def get_provider_name(self) -> str:
        """获取供应商名称"""
        return self.__class__.__name__.replace("ImageGenerator", "").lower()

    async def get_cached(self, request: AIImageRequest) -> Optional[Path]:
        """检查缓存中是否已有该图片"""
        cache_path = self._get_cache_path(request.prompt, request.size.value)
        if cache_path.exists():
            return cache_path
        return None
