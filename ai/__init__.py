"""AI Generation Layer — LLM-powered content creation.

Replaces deterministic templates with real AI-generated content.

    IntentIR(topic="Redis为什么快？")
    ↓ ai/narrative_planner.py (LLM)
    NarrativeIR(beats=[...])
    ↓ ai/visual_planner.py
    VisualPlan(scenes=[...])

Components:
  - NarrativePlanner: topic → NarrativeIR (LLM-powered)
  - VisualPlanner: NarrativeIR → visual scene plans
  - LLMBackend: pluggable LLM interface (OpenAI, Qwen, local, etc.)
"""

from ai.narrative_planner import (
    NarrativePlanner, LLMBackend, LLMConfig,
    TemplateBackend,
)
from ai.tts_service import TTSService, WordTiming, SegmentResult
from ai.asset_retriever import (
    AssetRetriever, AssetResult, SearchBackend,
    LocalSearchBackend, PexelsSearchBackend,
)
