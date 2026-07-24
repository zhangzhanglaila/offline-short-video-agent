# E1 Week 3 实现计划: 模板引擎接入视频主流程

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to execute.

**Goal**: 让用户能通过 `python generate_video.py --template image_default` 生成带 HTML 模板外观的完整视频。

**Tech Stack**: Python 3.10+, 现有 Playwright/Jinja2/PIL/FFmpeg

---

## Global Constraints

- 向后兼容：不传 `--template` 时行为完全不变
- 失败降级：模板渲染失败时回退到现有 gradient bg 路径（不报错）
- 必须真实生成 mp4 验证（不是只通过单元测试）
- 所有新代码必须有单元测试
- 每个 Task 完成后立即 git commit
- 文件路径用 `pathlib.Path`

---

## Task 1: 扩展 Scene 数据模型

**Files:**
- Modify: `core/models/content.py:26-82`
- Test: `tests/test_scene_model.py` (新)

**Interfaces:**
- Produces: `Scene.template: Optional[str]`

- [ ] **Step 1: 写测试 `tests/test_scene_model.py`**

```python
"""Scene 数据模型扩展测试"""
from core.models.content import Scene


def test_scene_template_default_none():
    """默认无 template 字段"""
    s = Scene(scene_id=1, scene_type="content", text="x", duration=3.0)
    assert s.template is None


def test_scene_template_roundtrip():
    """template 字段 to_dict/from_dict 往返"""
    s = Scene(scene_id=1, scene_type="content", text="x", duration=3.0, template="image_default")
    d = s.to_dict()
    assert d["template"] == "image_default"
    s2 = Scene.from_dict(d)
    assert s2.template == "image_default"


def test_scene_from_dict_without_template():
    """旧数据（无 template 字段）也能正常解析"""
    s = Scene.from_dict({"scene_id": 1, "scene_type": "content", "text": "x", "duration": 3.0})
    assert s.template is None
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/test_scene_model.py -v
```

Expected: FAIL (AttributeError on template)

- [ ] **Step 3: 修改 `core/models/content.py`**

在 `Scene` 数据类的字段区（line 43-44 之间）加：

```python
template: Optional[str] = None
```

修改 `to_dict` 方法（line 46-55）：

```python
def to_dict(self) -> Dict[str, Any]:
    """转换为字典格式。"""
    return {
        "scene_id": self.scene_id,
        "scene_type": self.scene_type,
        "text": self.text,
        "duration": self.duration,
        "keywords": self.keywords,
        "narration": self.narration,
        "template": self.template,
    }
```

修改 `from_dict` 类方法（line 57-74）：

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Scene":
    """从字典创建Scene对象。"""
    return cls(
        scene_id=int(data["scene_id"]),
        scene_type=data.get("scene_type", data.get("type", SceneType.CONTENT.value)),
        text=data.get("text", ""),
        duration=float(data.get("duration", 3.0)),
        keywords=list(data.get("keywords", [])),
        narration=data.get("narration"),
        template=data.get("template"),
    )
```

- [ ] **Step 4: 跑测试确认通过**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/test_scene_model.py -v
```

Expected: 3 passed

- [ ] **Step 5: 跑现有 Scene 相关测试确认无回归**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/test_video_compose_agent.py -v --tb=no 2>&1 | tail -10
```

Expected: 无新增 failures

- [ ] **Step 6: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add core/models/content.py tests/test_scene_model.py && git commit -m "feat(model): add template field to Scene dataclass"
```

---

## Task 2: 改造 render_template_frame 支持 fallback

**Files:**
- Modify: `core/compose/scene_image_renderer.py:652-671`
- Test: `tests/test_render_template_fallback.py` (新)

- [ ] **Step 1: 写测试 `tests/test_render_template_fallback.py`**

```python
"""render_template_frame fallback 路径测试"""
import asyncio
from pathlib import Path
import tempfile

from core.compose.scene_image_renderer import render_template_frame


async def test_fallback_called_on_failure():
    """模板不存在时调用 fallback_func"""
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "out.png"
        fallback_called = []

        async def fallback(out_path):
            fallback_called.append(out_path)
            # 写一个真实 PNG
            from PIL import Image
            Image.new("RGB", (1080, 1920), "#cccccc").save(out_path)
            return out_path

        result = await render_template_frame(
            template_name="nonexistent_template",
            context={"title": "x"},
            output_path=str(output),
            fallback_func=fallback,
        )
        assert len(fallback_called) == 1
        assert Path(result).exists()


def test_fallback_signature():
    asyncio.run(test_fallback_called_on_failure())
```

- [ ] **Step 2: 跑测试确认失败**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/test_render_template_fallback.py -v
```

Expected: FAIL (TypeError: unexpected keyword argument fallback_func)

- [ ] **Step 3: 修改 `core/compose/scene_image_renderer.py:652-671`**

把 `render_template_frame` 替换为：

```python
async def render_template_frame(
    template_name: str,
    context: Dict[str, Any],
    output_path: str,
    fallback_func: Optional[Callable] = None,
):
    """Render an HTML template frame for the video generation pipeline.

    Args:
        template_name: Registered template name.
        context: Values passed to the template.
        output_path: Destination PNG path.
        fallback_func: Optional async function called with output_path on failure.

    Returns:
        The PNG path. Returns fallback result if fallback_func is provided and
        template rendering fails.
    """
    renderer = TemplateRenderer()
    try:
        return await renderer.render(template_name, context, Path(output_path))
    except Exception as e:
        if fallback_func is not None:
            logger.warning(
                f"Template '{template_name}' render failed ({e}); using fallback"
            )
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            return await fallback_func(output_path)
        raise
    finally:
        await renderer.close()
```

并在文件顶部 import 加：

```python
from typing import Any, Callable, Dict, Optional
```

（确认已有这些 import，可能需要加 Callable）

- [ ] **Step 4: 跑测试确认通过**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/test_render_template_fallback.py -v
```

Expected: 1 passed

- [ ] **Step 5: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add core/compose/scene_image_renderer.py tests/test_render_template_fallback.py && git commit -m "feat(compose): add fallback_func to render_template_frame"
```

---

## Task 3: 在 VideoComposeAgent 加入模板分支

**Files:**
- Modify: `core/agents/video_compose_agent.py:268` (`_build_scene_spec`)
- Modify: `core/agents/video_compose_agent.py:130` (`execute` 调用点)
- Test: `tests/test_video_compose_agent.py` (追加测试)

- [ ] **Step 1: 读现有 `_build_scene_spec` 完整签名确认**

用 `grep` + `Read` 确认所有 caller，只有一处（line 130）

- [ ] **Step 2: 写测试 `tests/test_video_compose_agent.py` 追加**

在文件末尾加：

```python
@pytest.mark.asyncio
async def test_build_scene_spec_with_template(tmp_path):
    """scene.template 非空时调用 render_template_frame"""
    from core.models.content import Scene, ContentStructure
    from core.agents.video_compose_agent import VideoComposeAgent
    from core.compose.scene_image_renderer import render_template_frame

    # Mock render_template_frame to avoid actually launching Chromium
    import core.compose.scene_image_renderer as sir
    original = sir.render_template_frame
    calls = []

    async def mock(template_name, context, output_path, fallback_func=None):
        calls.append((template_name, context, output_path))
        # 写个真 PNG 让下游不报错
        from PIL import Image
        Image.new("RGB", (1080, 1920), "#abcdef").save(output_path)
        return output_path

    sir.render_template_frame = mock
    try:
        scene = Scene(
            scene_id=1,
            scene_type="content",
            text="讲解Python异步",
            duration=5.0,
            template="image_default",
            keywords=["python"],
        )
        content = ContentStructure(
            title="Python异步编程",
            category="教育讲解",
            style="tech",
            total_duration=5,
            scenes=[scene],
        )
        agent = VideoComposeAgent(size=(1080, 1920))
        spec = await agent._build_scene_spec_async(scene, 0, {}, tmp_path)
        assert spec is not None
        assert len(calls) == 1
        assert calls[0][0] == "image_default"
        assert calls[0][1]["title"] == "Python异步编程"
        assert calls[0][1]["text"] == "讲解Python异步"
    finally:
        sir.render_template_frame = original
```

- [ ] **Step 3: 跑测试确认失败**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/test_video_compose_agent.py::test_build_scene_spec_with_template -v
```

Expected: FAIL (AttributeError on _build_scene_spec_async)

- [ ] **Step 4: 在 VideoComposeAgent 加 `_build_scene_spec_async` 方法**

在 `_build_scene_spec` 之后新增（不要改原方法签名，向后兼容）：

```python
async def _build_scene_spec_async(
    self, scene, idx, material_map, work_dir
) -> "SceneClipSpec | None":
    """异步版本的 _build_scene_spec，支持模板渲染路径。

    当 scene.template 非空时，使用 HTML 模板生成场景背景图，
    否则回退到原有 _build_scene_spec 逻辑。
    """
    from core.compose.motion.animation_spec import (
        OverlayLayer, AnimationSpec,
        ANIM_FADE_IN, ANIM_SLIDE_UP, ANIM_NONE,
    )
    from core.compose.scene_image_renderer import render_template_frame

    sid = scene.scene_id
    style = self._load_style(self._current_style) if hasattr(self, '_current_style') else None
    renderer = SceneImageRenderer(style=style, size=self.size)

    # === 模板路径（仅内容场景） ===
    if scene.template and not scene.is_text_only():
        bg_path = str(work_dir / f"scene_{sid:03d}_template.png")

        # 构造模板上下文
        asset = self._pick_material(scene, material_map)
        image_var = asset.local_path if asset else None

        # 取 content.title —— 简单方案：遍历找到对应 scene 的 content
        context_title = getattr(self, '_current_title', '视频')

        ctx = {
            "title": context_title,
            "image": image_var or "",
            "text": scene.text,
            "author": "AI Assistant",
            "describe": context_title,
            "brand": "Offline-ShortVideo-Agent",
        }

        # 降级函数：写 gradient bg
        async def gradient_fallback(out_path):
            renderer.render_gradient_bg(out_path)
            return out_path

        try:
            await render_template_frame(
                template_name=scene.template,
                context=ctx,
                output_path=bg_path,
                fallback_func=gradient_fallback,
            )
        except Exception as e:
            self.logger.warning(f"Template path failed: {e}")
            return None

        # 模板已自含视觉，不要 Ken Burns
        overlays = []
        if self.enable_motion:
            from core.compose.motion.scene_composer import build_content_overlays
            self._content_counter += 1
            overlays = build_content_overlays(
                scene, self._content_counter, renderer, work_dir,
                with_badge=self.enable_elements,
            )

        return SceneClipSpec(
            background_path=bg_path,
            duration=scene.duration,
            overlays=overlays,
        )

    # 非模板路径 → 用原方法
    return self._build_scene_spec(scene, idx, material_map, renderer, work_dir)
```

- [ ] **Step 5: 修改 `execute` 让 `_build_scene_spec` 调用换为异步版本**

在 `core/agents/video_compose_agent.py:130` 改为：

```python
spec = await self._build_scene_spec_async(scene, idx, material_map, work_dir)
```

并保存当前 style 给异步方法用：

在 line 118-119 后面（`renderer = SceneImageRenderer(...)` 之前）加：

```python
self._current_style = content.style
self._current_title = content.title
```

- [ ] **Step 6: 跑测试确认通过**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/test_video_compose_agent.py::test_build_scene_spec_with_template -v
```

Expected: 1 passed

- [ ] **Step 7: 跑现有 VideoComposeAgent 测试确认无回归**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/test_video_compose_agent.py -v --tb=line 2>&1 | tail -15
```

Expected: 大部分 passed；如果有 1-2 个 async 相关的失败，可能是 fixture 的 event_loop 问题，记录到 report 即可，不阻塞

- [ ] **Step 8: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add core/agents/video_compose_agent.py tests/test_video_compose_agent.py && git commit -m "feat(agent): add template rendering path to VideoComposeAgent"
```

---

## Task 4: 在 generate_video.py 加 --template CLI 参数

**Files:**
- Modify: `generate_video.py`

- [ ] **Step 1: 读 generate_video.py CLI 部分**

- [ ] **Step 2: 加 --template 参数**

在 `generate_video.py:48-67` 的 argparse 区加：

```python
parser.add_argument(
    "--template",
    type=str,
    default=None,
    help="HTML 模板名（如 image_default），用模板生成场景背景",
)
```

并在 `run()` 函数构造 Scene 时，把 `template=args.template` 传给所有 content 场景。具体修改点先读代码确认。

- [ ] **Step 3: 手动测试 CLI**

```bash
cd D:/Offline-ShortVideo-Agent && python generate_video.py --input "Python异步编程的三大要点" --template image_default --duration 10 --output output/test_template_video.mp4 --no-motion
```

（注意 `--no-motion` 是简化开关，如果 CLI 没有就用现有开关）

- [ ] **Step 4: 验证输出 mp4 存在**

```bash
cd D:/Offline-ShortVideo-Agent && ls -la output/test_template_video.mp4
```

- [ ] **Step 5: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add generate_video.py && git commit -m "feat(cli): add --template parameter to generate_video.py"
```

---

## Task 5: 真实视频生成测试

**Files:**
- Create: `tests/integration/test_template_video_e2e.py`

- [ ] **Step 1: 写端到端测试**

```python
"""模板视频端到端测试：真实生成 mp4"""
import asyncio
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from core.models.content import Scene, ContentStructure
from core.agents.video_compose_agent import VideoComposeAgent
from core.agents.message_bus import MessageBus


@pytest.mark.asyncio
async def test_real_video_generation_with_template(tmp_path):
    """用真实 VideoComposeAgent 生成带模板的 mp4"""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not available")

    scene = Scene(
        scene_id=1,
        scene_type="content",
        text="这是模板渲染的第一段内容",
        duration=5.0,
        template="image_default",
        keywords=["test"],
    )
    content = ContentStructure(
        title="模板测试视频",
        category="测试",
        style="minimal",
        total_duration=5,
        scenes=[scene],
    )
    material_map = {}  # 无素材 → 用 placeholder

    output = tmp_path / "test.mp4"
    agent = VideoComposeAgent(size=(1080, 1920))
    agent._current_style = content.style
    agent._current_title = content.title
    agent._content_counter = 0

    # 直接调内部方法组装 spec，简化测试
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    spec = await agent._build_scene_spec_async(scene, 0, material_map, work_dir)

    assert spec is not None
    assert Path(spec.background_path).exists()
    print(f"Background PNG: {spec.background_path} ({Path(spec.background_path).stat().st_size} bytes)")
```

- [ ] **Step 2: 跑测试**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/integration/test_template_video_e2e.py -v -s
```

Expected: PASS，PNG 生成成功

- [ ] **Step 3: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add tests/integration/ && git commit -m "test: add real video generation integration test for templates"
```

---

## Task 6: E1 Week 3 阶段总结

**Files:**
- Create: `devlog/phase-E1-week3-summary.md`

- [ ] **Step 1: 写总结**

含：完成情况、产出文件、生成的 mp4 示例、已知问题、下一步

- [ ] **Step 2: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add devlog/phase-E1-week3-summary.md && git commit -m "docs: E1 Week 3 stage summary"
```

---

## 验收清单

- [ ] `python generate_video.py --template image_default --input "测试"` 能生成 mp4
- [ ] 不传 `--template` 时行为不变
- [ ] 模板渲染失败时降级到 gradient bg（不报错）
- [ ] 所有单元测试通过
- [ ] 实际打开生成的 mp4 看到模板外观

---

*计划创建时间: 2026-07-24*