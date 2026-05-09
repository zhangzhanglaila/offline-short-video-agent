"""Compiler Passes — IR-to-IR transformations.

Each pass is a pure function: InputIR → OutputIR.

    IntentIR → [intent_to_narrative] → NarrativeIR
    NarrativeIR → [narrative_to_scene] → SceneIR[]
    SceneIR[] → [scene_to_timeline] → TimelineIR
    TimelineIR → [timeline_to_render] → RenderIR

Passes are:
  - Deterministic (same input → same output)
  - Cacheable (by input content hash)
  - Composable (pass pipeline)
  - Testable (without LLM)
"""

from compiler.base import CompilerPass, PassResult, PassPipeline
from compiler.pass_intent_to_narrative import IntentToNarrativePass
from compiler.pass_narrative_to_scene import NarrativeToScenePass, SceneIR
from compiler.pass_scene_to_timeline import SceneToTimelinePass
from compiler.pass_timeline_to_render import TimelineToRenderPass
from compiler.pass_tts import TTSPass
from compiler.pass_asset import AssetPass
