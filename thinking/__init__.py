"""Thinking module — Interactive Video Agent Runtime.

Transforms the system from a one-shot pipeline into a human-in-the-loop
collaborative video creation environment.
"""

from thinking.state import (
    VideoProjectState,
    ModuleState,
    ScriptSentence,
    GraphSpec,
    GraphNode,
    GraphEdge,
    ShotPlan,
    AudioTrack,
    RenderJob,
    AgentAction,
    ThinkingPhase,
    Clip,
    Track,
    Timeline,
    ConstraintType,
    Constraint,
    Anchor,
)

from thinking.session import ThinkingSession

from thinking.agent_loop import ThinkingAgent

from thinking.event_bus import EventBus, Event, get_event_bus

from thinking.patch import (
    PatchOperation, PatchHistory,
    EditSentencePatch, AddSentencePatch, RemoveSentencePatch,
    ApproveModulePatch, EditGraphNodePatch, BatchPatch,
)

from thinking.branch import (
    BranchManager, MergeEngine, MergeConflict, MergeResult,
    ConflictType, ResolutionStrategy,
)

from thinking.ir_layers import (
    SemanticIR, TemporalIR, RenderIR, ExecutionIR,
    IRTransformer, DeterminismConfig, DeterminismChecker,
)

__all__ = [
    "VideoProjectState",
    "ModuleState",
    "ScriptSentence",
    "GraphSpec",
    "GraphNode",
    "GraphEdge",
    "ShotPlan",
    "AudioTrack",
    "RenderJob",
    "AgentAction",
    "ThinkingPhase",
    "Clip",
    "Track",
    "Timeline",
    "ConstraintType",
    "Constraint",
    "Anchor",
    "ThinkingSession",
    "ThinkingAgent",
    "EventBus",
    "Event",
    "get_event_bus",
    "PatchOperation",
    "PatchHistory",
    "EditSentencePatch",
    "AddSentencePatch",
    "RemoveSentencePatch",
    "ApproveModulePatch",
    "EditGraphNodePatch",
    "BatchPatch",
    # Branch & Merge
    "BranchManager",
    "MergeEngine",
    "MergeConflict",
    "MergeResult",
    "ConflictType",
    "ResolutionStrategy",
    # IR Layers
    "SemanticIR",
    "TemporalIR",
    "RenderIR",
    "ExecutionIR",
    "IRTransformer",
    "DeterminismConfig",
    "DeterminismChecker",
]
