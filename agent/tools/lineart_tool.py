# -*- coding: utf-8 -*-
"""
线条插画视频工具 — Agent 可调用

输入一段文字，自动生成线条插画手绘视频。
LLM 负责分析文案、选择场景、决定构图。
"""
import sys
import os
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agent.tools.tool_base import BaseTool, ToolDefinition, ToolParameter, ToolCategory, ToolResult


class LineartVideoTool(BaseTool):
    """线条插画视频生成工具"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="generate_lineart_video",
            category=ToolCategory.VIDEO,
            description=(
                "根据文案生成线条插画手绘视频。"
                "每句文案会自动转换为一个场景画面（如：人物+电脑+勾选），"
                "场景之间有流动的连接线，整体是白板手绘风格。"
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
        """执行生成"""
        import time
        start = time.time()

        try:
            from core.lineart_renderer import generate_lineart_video
            import config

            if not output_path:
                output_path = str(config.OUTPUT_DIR / "lineart_output.mp4")

            # 确保输出目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            result_path = generate_lineart_video(
                script_lines=script_lines,
                output_path=output_path,
                draw_duration=draw_duration,
                hold_duration=hold_duration,
            )

            elapsed = time.time() - start

            return ToolResult(
                success=True,
                data={
                    "output_path": result_path,
                    "scenes_count": len(script_lines),
                    "duration": len(script_lines) * (draw_duration + hold_duration),
                },
                message=f"已生成线条插画视频，{len(script_lines)}个场景，耗时{elapsed:.1f}秒",
                elapsed=elapsed,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message=f"生成失败: {e}",
            )
