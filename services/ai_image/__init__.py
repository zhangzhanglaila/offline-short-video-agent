"""AI 生图服务层"""
from .base import AIGenerationService, AIImageRequest, AIImageResult
from .openai_generator import OpenAIImageGenerator
from .dashscope_generator import DashscopeImageGenerator

__all__ = [
    'AIGenerationService',
    'AIImageRequest',
    'AIImageResult',
    'OpenAIImageGenerator',
    'DashscopeImageGenerator',
]
