"""AI 生视频服务层"""
from .base import (
    AIVideoGenerationService,
    VideoGenerationRequest,
    VideoGenerationProgress,
    VideoGenerationResult,
    VideoProvider,
    VideoSize,
    VideoResolution,
    VideoTaskStatus,
)
from .dashscope_generator import DashScopeVideoGenerator
from .comfyui_generator import ComfyUIVideoGenerator  # E5

__all__ = [
    'AIVideoGenerationService',
    'VideoGenerationRequest',
    'VideoGenerationProgress',
    'VideoGenerationResult',
    'VideoProvider',
    'VideoSize',
    'VideoResolution',
    'VideoTaskStatus',
    'DashScopeVideoGenerator',
    'ComfyUIVideoGenerator',
]
