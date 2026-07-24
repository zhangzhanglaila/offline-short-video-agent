# -*- coding: utf-8 -*-
"""
AI 生图 API 路由
"""
import sys
import os
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_image.base import (
    AIProvider,
    ImageSize,
    ImageStyle,
    AIImageRequest,
    AIImageResult,
)
from services.ai_image.openai_generator import OpenAIImageGenerator
from services.ai_image.dashscope_generator import DashscopeImageGenerator

router = APIRouter()

# 全局生成器实例
_generators: Dict[AIProvider, Any] = None


def _get_generators() -> Dict[AIProvider, Any]:
    """获取所有生成器实例（懒加载）"""
    global _generators
    if _generators is None:
        _generators = {}
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            _generators[AIProvider.OPENAI] = OpenAIImageGenerator(
                api_key=openai_key,
                base_url=os.getenv("OPENAI_BASE_URL"),
            )
        # DashScope
        dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
        if dashscope_key:
            _generators[AIProvider.DASHSCOPE] = DashscopeImageGenerator(
                api_key=dashscope_key,
                base_url=os.getenv("DASHSCOPE_BASE_URL"),
            )
    return _generators


# ---------- 数据模型 ----------


class GenerateImageRequest(BaseModel):
    """AI 生图请求"""
    prompt: str = Field(..., description="提示词", min_length=1)
    provider: str = Field("openai", description="供应商 (openai/dashscope)")
    model: Optional[str] = Field(None, description="模型名称")
    size: str = Field("1024x1024", description="图片尺寸")
    style: Optional[str] = Field(None, description="风格 (vivid/natural)")
    quality: str = Field("standard", description="质量 (standard/hd)")
    n: int = Field(1, description="生成数量", ge=1, le=10)


class GenerateImageResponse(BaseModel):
    """AI 生图响应"""
    success: bool
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    prompt: str = ""
    provider: str = ""
    model: str = ""
    error: Optional[str] = None
    generation_time: float = 0.0
    cost: float = 0.0


class ModelsResponse(BaseModel):
    """支持的模型响应"""
    providers: List[str]
    models: Dict[str, List[str]]


class CostEstimateRequest(BaseModel):
    """成本估算请求"""
    prompt: str = Field(..., description="提示词")
    provider: str = Field("openai", description="供应商")
    model: Optional[str] = Field(None, description="模型")
    size: str = Field("1024x1024", description="尺寸")


class CostEstimateResponse(BaseModel):
    """成本估算响应"""
    estimated_cost: float
    currency: str = "CNY"
    notes: Optional[str] = None


# ---------- API 路由 ----------


@router.post("/api/ai/generate-image", response_model=GenerateImageResponse)
async def generate_image(request: GenerateImageRequest):
    """
    生成 AI 图片

    参数:
        prompt: 提示词
        provider: 供应商 (openai/dashscope)
        model: 模型名称（可选）
        size: 图片尺寸
        style: 风格 (vivid/natural, 仅 DALL-E 3)
        quality: 质量 (standard/hd)
        n: 生成数量

    返回:
        生成的图片信息
    """
    try:
        # 验证供应商
        try:
            provider = AIProvider(request.provider)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider: {request.provider}. Supported: openai, dashscope",
            )

        # 获取生成器
        generators = _get_generators()
        generator = generators.get(provider)
        if not generator:
            # 尝试动态创建（使用环境变量）
            if provider == AIProvider.OPENAI:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise HTTPException(
                        status_code=400,
                        detail="OpenAI API key not configured. Set OPENAI_API_KEY environment variable.",
                    )
                generator = OpenAIImageGenerator(api_key=api_key)
            elif provider == AIProvider.DASHSCOPE:
                api_key = os.getenv("DASHSCOPE_API_KEY")
                if not api_key:
                    raise HTTPException(
                        status_code=400,
                        detail="DashScope API key not configured. Set DASHSCOPE_API_KEY environment variable.",
                    )
                generator = DashscopeImageGenerator(api_key=api_key)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Provider {request.provider} not configured.",
                )

        # 解析图片尺寸
        try:
            size = ImageSize(request.size)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid size: {request.size}. Supported: 1024x1024, 512x512, 1792x1024, 1024x1792, 1080x1920, 1080x1080, 1920x1080",
            )

        # 解析风格
        style = None
        if request.style:
            try:
                style = ImageStyle(request.style)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid style: {request.style}. Supported: vivid, natural",
                )

        # 构建请求
        ai_request = AIImageRequest(
            prompt=request.prompt,
            provider=provider,
            model=request.model,
            size=size,
            style=style,
            n=request.n,
            quality=request.quality,
        )

        # 生成图片
        result = await generator.generate(ai_request)

        return GenerateImageResponse(
            success=result.success,
            image_path=result.image_path,
            image_url=result.image_url,
            prompt=result.prompt,
            provider=result.provider,
            model=result.model,
            error=result.error,
            generation_time=result.generation_time,
            cost=result.cost,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.get("/api/ai/models", response_model=ModelsResponse)
async def get_models():
    """
    获取支持的模型列表

    返回:
        供应商列表和每个供应商支持的模型
    """
    generators = _get_generators()

    providers = []
    models = {}

    for provider, generator in generators.items():
        providers.append(provider.value)
        models[provider.value] = generator.get_supported_models()

    return ModelsResponse(providers=providers, models=models)


@router.post("/api/ai/estimate-cost", response_model=CostEstimateResponse)
async def estimate_cost(request: CostEstimateRequest):
    """
    估算生成成本

    参数:
        prompt: 提示词
        provider: 供应商
        model: 模型
        size: 尺寸

    返回:
        估算成本（元）
    """
    try:
        # 验证供应商
        try:
            provider = AIProvider(request.provider)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider: {request.provider}",
            )

        # 获取生成器
        generators = _get_generators()
        generator = generators.get(provider)
        if not generator:
            # 尝试动态创建（仅用于估算，不需要真实 API key）
            if provider == AIProvider.OPENAI:
                generator = OpenAIImageGenerator(api_key="dummy")
            elif provider == AIProvider.DASHSCOPE:
                generator = DashscopeImageGenerator(api_key="dummy")
            else:
                raise HTTPException(status_code=400, detail=f"Provider {request.provider} not supported")

        # 解析尺寸
        try:
            size = ImageSize(request.size)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid size: {request.size}")

        # 构建请求并估算
        ai_request = AIImageRequest(
            prompt=request.prompt,
            provider=provider,
            model=request.model,
            size=size,
        )

        cost = generator.estimate_cost(ai_request)

        notes = f"Estimated cost for {provider.value} ({request.model or 'default model'})"

        return CostEstimateResponse(estimated_cost=cost, currency="CNY", notes=notes)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost estimation failed: {str(e)}")
