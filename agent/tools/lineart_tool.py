# -*- coding: utf-8 -*-
"""
线条插画视频工具 — Agent 可调用，LLM 全流程驱动

输入一段文字，LLM 自动分析并生成场景布局，然后渲染成视频。
"""
import sys
import os
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agent.tools.tool_base import BaseTool, ToolDefinition, ToolParameter, ToolCategory, ToolResult


class LineartVideoTool(BaseTool):
    """线条插画视频生成工具（LLM 全流程驱动）"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="generate_lineart_video",
            category=ToolCategory.VIDEO,
            description=(
                "根据文案生成线条插画手绘视频。"
                "LLM 会分析每句文案，自动决定用什么画面来表达（如：人物+电脑+勾选），"
                "以及如何布局（位置、大小、环境元素）。"
                "适合知识讲解、概念解释、流程说明类视频。"
            ),
            parameters=[
                ToolParameter(
                    name="script_lines",
                    type="list",
                    description="文案列表，每行一个场景。例如：['AI Agent是智能系统', 'Agent调用Tool获取信息']",
                    required=True,
                ),
                ToolParameter(
                    name="output_path",
                    type="str",
                    description="输出视频路径（可选）",
                    required=False,
                    default="",
                ),
                ToolParameter(
                    name="draw_duration",
                    type="float",
                    description="每场景绘制时长（秒），默认4秒",
                    required=False,
                    default=4.0,
                ),
                ToolParameter(
                    name="hold_duration",
                    type="float",
                    description="绘制完成后停留时长（秒），默认2秒",
                    required=False,
                    default=2.0,
                ),
            ],
        )

    def execute(
        self,
        script_lines: List[str],
        output_path: str = "",
        draw_duration: float = 4.0,
        hold_duration: float = 2.0,
    ) -> ToolResult:
        """执行生成（LLM 全流程）"""
        import time
        start = time.time()

        try:
            from core.lineart_renderer import generate_lineart_video
            import config

            if not output_path:
                output_path = str(config.OUTPUT_DIR / "lineart_output.mp4")

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # 获取 LLM 函数
            llm_fn = self._get_llm_fn()

            result_path = generate_lineart_video(
                script_lines=script_lines,
                output_path=output_path,
                draw_duration=draw_duration,
                hold_duration=hold_duration,
                llm_fn=llm_fn,
            )

            elapsed = time.time() - start

            return ToolResult(
                success=True,
                data={
                    "output_path": result_path,
                    "scenes_count": len(script_lines),
                    "duration": len(script_lines) * (draw_duration + hold_duration),
                    "llm_used": llm_fn is not None,
                },
                message=f"已生成线条插画视频，{len(script_lines)}个场景，LLM={'是' if llm_fn else '否'}，耗时{elapsed:.1f}秒",
                elapsed=elapsed,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"生成失败: {e}",
            )

    def _get_llm_fn(self):
        """获取 LLM 调用函数"""
        try:
            import config
            import requests

            # 优先使用 Ollama 本地模型
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

            # 测试是否可用
            try:
                llm_fn("test")
                return llm_fn
            except Exception:
                pass

            # 回退到云端 API
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
