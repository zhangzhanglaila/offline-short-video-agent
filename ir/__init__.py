"""Multi-Level IR — Intermediate Representations for Media Compilation.

The IR pipeline:
    Intent IR → Narrative IR → Scene IR → Timeline IR → Render IR

Each level is:
  - Deterministically canonicalizable
  - Content-hashable
  - Validated (structural constraints)
  - Independently cacheable
"""

from ir.intent_ir import IntentIR, Tone, Platform, AspectRatio
from ir.narrative_ir import (
    NarrativeIR, Beat, BeatType,
    HookBeat, ProblemBeat, RevealBeat, CTABeat,
)
from ir.timeline_ir import (
    TimelineIR, Track, TrackType, Transition, TransitionEffect,
)
from ir.render_ir import (
    RenderIR, RenderCommand, RenderInput, RenderBackend, CommandType,
)
