# -*- coding: utf-8 -*-
"""
线条插画视频 API
"""
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

router = APIRouter(prefix="/api/lineart", tags=["线条插画"])


class LineartRequest(BaseModel):
    """线条插画视频请求"""
    script_lines: List[str] = Field(..., description="文案列表，每行一个场景")
    output_path: Optional[str] = Field(default=None, description="输出路径")
    draw_duration: float = Field(default=4.0, ge=1.0, le=10.0, description="绘制时长（秒）")
    hold_duration: float = Field(default=2.0, ge=0.5, le=5.0, description="停留时长（秒）")


@router.post("/generate", summary="生成线条插画视频")
async def generate_lineart(req: LineartRequest):
    """
    根据文案生成线条插画手绘视频。

    每句文案会自动转换为一个场景画面，场景之间有流动的连接线。
    整体是白板手绘风格（#F8F8F8背景 + #1F1F1F线条 + #FF6B5A强调）。
    """
    try:
        from core.lineart_renderer import generate_lineart_video
        import config

        output_path = req.output_path or str(config.OUTPUT_DIR / "lineart_output.mp4")

        result = await asyncio.to_thread(
            generate_lineart_video,
            script_lines=req.script_lines,
            output_path=output_path,
            draw_duration=req.draw_duration,
            hold_duration=req.hold_duration,
        )

        return {
            "success": True,
            "output_path": result,
            "scenes_count": len(req.script_lines),
            "duration": len(req.script_lines) * (req.draw_duration + req.hold_duration),
            "message": f"已生成 {len(req.script_lines)} 个场景的线条插画视频",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/presets", summary="获取预设文案模板")
async def get_presets():
    """获取预设的文案模板，可直接用于生成视频"""
    return {
        "presets": [
            {
                "name": "AI Agent 架构",
                "description": "展示 AI Agent 的工作流程",
                "script_lines": [
                    "AI Agent 是一种智能系统",
                    "Agent 使用 Tool 获取信息",
                    "数据存储在 Database 中",
                    "Brain 处理并生成决策",
                    "Robot 执行最终任务",
                ],
            },
            {
                "name": "Redis 缓存",
                "description": "展示 Redis 缓存工作原理",
                "script_lines": [
                    "Redis 是高性能缓存系统",
                    "请求经过 App 到达 Redis",
                    "缓存命中直接返回结果",
                    "缓存未命中查询 Database",
                    "数据写入 Redis 缓存层",
                ],
            },
            {
                "name": "机器学习流程",
                "description": "展示 ML Pipeline",
                "script_lines": [
                    "数据采集是第一步",
                    "数据清洗去除噪声",
                    "特征工程提取关键信息",
                    "Brain 训练模型",
                    "评估并部署到生产环境",
                ],
            },
        ]
    }
