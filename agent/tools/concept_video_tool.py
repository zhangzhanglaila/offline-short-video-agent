# -*- coding: utf-8 -*-
"""Agent tool for concept explainer videos backed by the graph pipeline."""
import os
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.tools.tool_base import BaseTool, ToolDefinition, ToolParameter, ToolCategory, ToolResult


class ConceptVideoTool(BaseTool):
    """Generate an agent-traceable concept explainer video."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="generate_concept_video",
            category=ToolCategory.VIDEO,
            description=(
                "Generate an agent-driven concept explainer video from a topic. "
                "The tool plans graph scenes, captions, voiceover, and self-drawn illustrations, "
                "then renders through Remotion. Outputs include provenance.source=agent_tool."
            ),
            parameters=[
                ToolParameter(
                    name="topic",
                    type="str",
                    description="Topic or user question to explain.",
                    required=True,
                ),
                ToolParameter(
                    name="output_path",
                    type="str",
                    description="Optional output mp4 path.",
                    required=False,
                    default="",
                ),
                ToolParameter(
                    name="duration_ms",
                    type="int",
                    description="Target duration in milliseconds.",
                    required=False,
                    default=12000,
                ),
                ToolParameter(
                    name="enable_audio",
                    type="bool",
                    description="Generate TTS narration and synced subtitles.",
                    required=False,
                    default=True,
                ),
                ToolParameter(
                    name="use_llm_director",
                    type="bool",
                    description="Use the optional LLM director layer for shot planning.",
                    required=False,
                    default=False,
                ),
                ToolParameter(
                    name="agent_id",
                    type="str",
                    description="Agent instance id for provenance.",
                    required=False,
                    default="",
                ),
            ],
        )

    def execute(
        self,
        topic: str,
        output_path: str = "",
        duration_ms: int = 12000,
        enable_audio: bool = True,
        use_llm_director: bool = False,
        agent_id: str = "",
    ) -> ToolResult:
        start_time = time.time()
        try:
            from engine.bridge.graph_pipeline import render_graph_video

            run_id = uuid.uuid4().hex[:8]
            output_dir = Path("output") / "agent"
            output_dir.mkdir(parents=True, exist_ok=True)

            layout_path = str(output_dir / f"concept_{run_id}_layout.json")
            video_path = output_path or str(output_dir / f"concept_{run_id}.mp4")

            layout_out, video_out = render_graph_video(
                topic,
                layout_out=layout_path,
                video_out=video_path,
                total_ms=int(duration_ms),
                enable_audio=bool(enable_audio),
                use_llm_director=bool(use_llm_director),
                provenance_source="agent_tool",
                provenance_agent_id=agent_id,
            )

            return ToolResult(
                tool_name=self.definition.name,
                success=True,
                result={
                    "layout_path": layout_out,
                    "output_path": video_out,
                    "topic": topic,
                    "agent_generated": True,
                    "provenance_source": "agent_tool",
                },
                execution_time=time.time() - start_time,
                metadata={
                    "agent_id": agent_id,
                    "duration_ms": int(duration_ms),
                    "enable_audio": bool(enable_audio),
                    "use_llm_director": bool(use_llm_director),
                },
            )
        except Exception as exc:
            return ToolResult(
                tool_name=self.definition.name,
                success=False,
                error=str(exc),
                execution_time=time.time() - start_time,
            )
