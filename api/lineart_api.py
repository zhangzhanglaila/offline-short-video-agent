# -*- coding: utf-8 -*-
"""
线条插画视频 API（LLM 全流程驱动）
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
    use_llm: bool = Field(default=True, description="是否使用 LLM 规划场景")


def _get_llm_fn():
    """获取 LLM 调用函数"""
    try:
        import config
        import requests

        ollama_url = f"{config.OLLAMA_BASE_URL}/api/generate"

        def llm_fn(prompt: str) -> str:
            resp = requests.post(
                ollama_url,
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 1000},
                },
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json().get("response", "")

        # 测试
        try:
            llm_fn("test")
            return llm_fn
        except Exception:
            pass

        # 回退到云端
        cloud_config = config.get_cloud_llm_config()
        if cloud_config.get("api_key"):
            def cloud_llm_fn(prompt: str) -> str:
                resp = requests.post(
                    f"{cloud_config['api_base']}/chat/completions",
                    headers={"Authorization": f"Bearer {cloud_config['api_key']}"},
                    json={
                        "model": cloud_config["model"],
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 1000,
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            return cloud_llm_fn

        return None
    except Exception:
        return None


@router.post("/generate", summary="生成线条插画视频")
async def generate_lineart(req: LineartRequest):
    """
    根据文案生成线条插画手绘视频。

    LLM 会分析每句文案，自动决定：
    - 用什么画面元素（人物、电脑、大脑等）
    - 如何布局（位置、大小）
    - 用什么环境元素（流动线、桌面等）
    """
    try:
        from core.lineart_renderer import generate_lineart_video
        import config

        output_path = req.output_path or str(config.OUTPUT_DIR / "lineart_output.mp4")

        # 获取 LLM
        llm_fn = _get_llm_fn() if req.use_llm else None

        result = await asyncio.to_thread(
            generate_lineart_video,
            script_lines=req.script_lines,
            output_path=output_path,
            draw_duration=req.draw_duration,
            hold_duration=req.hold_duration,
            llm_fn=llm_fn,
        )

        return {
            "success": True,
            "output_path": result,
            "scenes_count": len(req.script_lines),
            "llm_used": llm_fn is not None,
            "message": f"已生成 {len(req.script_lines)} 个场景的线条插画视频",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/presets", summary="获取预设文案模板")
async def get_presets():
    """获取预设的文案模板"""
    return {
        "presets": [
            {
                "name": "AI Agent 架构",
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
