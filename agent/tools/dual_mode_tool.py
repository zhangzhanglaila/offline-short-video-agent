# -*- coding: utf-8 -*-
"""
素材智能剪辑工具
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from agent.tools.tool_base import BaseTool, ToolDefinition, ToolParameter, ToolCategory, ToolResult


class DualModeGenerateTool(BaseTool):
    """素材智能剪辑工具"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="generate_clip",
            category=ToolCategory.VIDEO,
            description="素材智能剪辑：上传图片/视频素材，自动拼接+转场+字幕",
            parameters=[
                ToolParameter(
                    name="material_paths",
                    type="list",
                    description="素材路径列表",
                    required=True
                ),
                ToolParameter(
                    name="platform",
                    type="str",
                    description="目标平台",
                    required=False,
                    default="抖音",
                    enum_values=["抖音", "小红书", "B站"]
                ),
                ToolParameter(
                    name="duration_per_image",
                    type="int",
                    description="每张图片持续秒数",
                    required=False,
                    default=4
                ),
                ToolParameter(
                    name="add_bgm",
                    type="bool",
                    description="是否添加BGM",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="add_subtitles",
                    type="bool",
                    description="是否添加字幕",
                    required=False,
                    default=True
                )
            ]
        )

    def execute(self, material_paths: list = None,
                platform: str = "抖音", duration_per_image: int = 4,
                add_bgm: bool = True, add_subtitles: bool = True,
                **kwargs) -> ToolResult:
        """素材智能剪辑"""
        import time
        start_time = time.time()

        try:
            if not material_paths:
                return ToolResult(
                    tool_name=self.definition.name,
                    success=False,
                    error="material_paths 不能为空",
                    execution_time=time.time() - start_time
                )

            from core.dual_mode_module import get_dual_mode_generator

            generator = get_dual_mode_generator()

            result = generator.generate_mode_b(
                material_paths=material_paths,
                platform=platform,
                add_bgm=add_bgm,
                add_subtitles=add_subtitles,
                duration_per_image=duration_per_image,
            )

            return ToolResult(
                tool_name=self.definition.name,
                success=result.get("success", False),
                result=result,
                error=result.get("error"),
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.definition.name,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
