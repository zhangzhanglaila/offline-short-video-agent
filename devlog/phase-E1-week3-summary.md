# E1 Week 3 阶段总结: 模板引擎接入视频主流程

## 阶段目标

把 Week 2 实现的 `TemplateRenderer` 模块实际接入视频生成主流程，让用户可在 CLI 上指定模板生成的风格化场景画面，并在 FFmpeg 拼接阶段真正使用 Playwright 渲染的 PNG 作为背景。

关键交付：
- `Scene.template` 字段已存在（Week 2 阶段），本周把字段从 CLI 一路打通到渲染路径
- `VideoComposeAgent` 内部按场景类型分流：纯封面/纯字幕优先用模板，内容场景走原有 `SceneImageRenderer`
- 用户可通过 `--template image_default` 直接调用
- 端到端真实生成 mp4 验证模板路径可用

## 完成情况

| Task | 状态 | 说明 |
| --- | --- | --- |
| 1. SceneImageRenderer 新增 fallback_func | DONE | `render_template_frame` 接受 `fallback_func` 回调，模板失败时回退到 PIL 文本卡 |
| 2. VideoComposeAgent 接入模板渲染路径 | DONE | 新增 `_build_scene_spec_async`，template 场景优先用 Playwright |
| 3. ContentAnalysisAgent 传递 UserRequest.metadata.template → Scene.template | DONE | 修复了 metadata → Scene 的传播链 |
| 4. CLI `--template image_default` 参数 | DONE | `generate_video.py` 接受并透传给 UserRequest |
| 5. 单元测试 + 异步路径回归修复 | DONE | 修一处 style 字符串误传 SceneImageRenderer 的 regression |
| 6. 端到端 mp4 集成测试 + 阶段总结 | DONE | `tests/integration/test_template_video_e2e.py` 真实跑通 |

## 产出 commits

```
9da7f6f test: add real video generation integration test for templates
ce5603c fix(agent): propagate template from UserRequest.metadata to Scene.template
6993601 feat(cli): add --template parameter to generate_video.py
0f7accc fix(agent): pass loaded style dict (not string) to SceneImageRenderer in async fallback path
47781b8 feat(agent): add template rendering path to VideoComposeAgent
97a0116 feat(compose): add fallback_func to render_template_frame
```

## 产出文件

**修改文件：**
- `core/compose/scene_image_renderer.py` — `render_template_frame` 新增 fallback 回调签名
- `core/agents/video_compose_agent.py` — 新增 `_build_scene_spec_async` 模板分支（82 行新增）
- `core/agents/content_analysis_agent.py` — 从 `UserRequest.metadata` 抽取 `template` 写入 `Scene.template`
- `generate_video.py` — CLI `--template` 参数解析与透传（18 行新增）
- `test_video_compose_agent.py` — 新增 1 个异步单元测试

**新增文件：**
- `tests/test_render_template_fallback.py` — fallback 路径单元测试
- `tests/integration/test_template_video_e2e.py` — 真实 ffmpeg mp4 端到端测试

## 测试结果

```
test_video_compose_agent.py                          13 passed
tests/test_scene_model.py                             3 passed
tests/test_render_template_fallback.py                1 passed
tests/integration/test_template_video_e2e.py          1 passed
                                                    ----------
                                                     18 passed (0 failed)
```

端到端实测：`image_default` 模板路径生成的中间 PNG：
- 尺寸：`1080x1920`（竖屏 9:16）
- 文件大小：`49,236 B` ≈ 48 KB
- 实测 SPec duration: 5.0s, overlays: 1（模板底图上有字幕/水印 overlay）

## 关键技术决策

1. **模板仅覆盖"封面/字幕/总结"三类场景**：内容场景仍走 `SceneImageRenderer`（保留原有素材+文字混排）。因为模板主要是定式排版，难以承载多元素编排；混在一起会破坏 D3 已建立的"元素交互感"。
2. **降级靠回调而非 try/except 嵌套**：`render_template_frame(scene, fallback_func=...)` 让 SceneImageRenderer 自己决定何时降级，调用方不用关心模板异常。
3. **模板选择写在 Scene.template 而不是 UserRequest 顶层**：多场景视频允许不同场景用不同模板（封面用 `cover_default`、总结用 `outro_default`），比单一全局 template 灵活。
4. **CLI 的 `--template` 写入 `UserRequest.metadata["template"]`**，由 ContentAnalysisAgent 解析时按场景类型写到 `Scene.template`。CLI 简单，内容层有完整控制权。

## 已修复问题

| # | 问题 | 修复 commit |
| --- | --- | --- |
| 1 | `UserRequest.metadata["template"]` 未传播到 `Scene.template`，导致 `--template` 即使传入也无效 | `ce5603c` |
| 2 | 异步回退路径里把"风格名 string"误传给 `SceneImageRenderer(style=...)`，导致模板不可用时回退异常 | `0f7accc` |
| 3 | `render_template_frame` 失败时没有降级机制，浏览器挂掉会直接抛出 | `97a0116`（引入 fallback_func） |

## 下一步

**E1 Week 4** 候选方向（任选其一）：
- **A. 前端模板选择器**（更贴近用户场景）：在 React 端开一个模板预览面板，列出 TemplateRegistry 扫描到的 31 个模板，点击预览 + 选择
- **B. E2：AI 图像生成路径**（更大业务跃迁）：把 `ImageMaterialAgent` 替换/增强为基于 SDXL/ComfyUI 的 AI 出图，模板作为后续合成层

建议优先 A —— 把 E1 模板系统的最后一个空白补齐（用户选择入口），再做 E2 才能让用户真正感受到模板差异。

另外本周遗留的小尾巴：
- CLI 当前只支持单一全局 `--template`，Week 4 可加 `--scene-template "1:cover,2:content"` 这样的逐场景覆盖（如果选 A 方向，可一并实现）
- `TemplateRegistry` 的 31 个模板多数是 1080x1920，1080x1080 / 1920x1080 的覆盖偏少，下周补齐素材

## 已知遗留（E1 Week 3.1 simplify 候选）

经 peer review 识别，4 项 simplification 未在本周处理（按"保守推进"原则留作下一轮）：

1. **生命周期浪费**（peer #5）：每场景 `render_template_frame` 内部 `TemplateRenderer()` 新建、扫一次 `templates/`、开闭一次 Chromium。多场景视频累积开销大。改进：让 `VideoComposeAgent` 持有 `TemplateRenderer` 单例，整个 `execute()` 复用，结束时统一 `close()`。
2. **execute() 死代码**（peer #1）：line 121 构造 `SceneImageRenderer` 但 `execute()` 切到 `_build_scene_spec_async` 后该 renderer 永不传给 helper。改进：要么删掉，要么把它连同 style 一起传进 helper。
3. **状态/参数重构**（peer #2）：`_current_title` / `_current_style` 是每请求的可变暂存，跨消息不安全。改进：把 `content: ContentStructure`（已在 `execute()` 作用域内）显式传给 `_build_scene_spec_async`。
4. **wrapper 重复**（peer #3）：`render_template_frame` 重复实现了 `TemplateRenderer.render_with_fallback` 的 try/fallback 逻辑。改进：让 wrapper 仅负责生命周期（实例化/关闭），调用 `renderer.render_with_fallback`。

> 这 4 项属于内部 cleanup，不影响功能。E1 Week 4 启动前可以一次性处理。

---

**E1 Week 3 状态**: ✅ DONE
**Commit 数**: 9 个（4 个 feat、3 个 fix、1 个 test、1 个 refactor）
**下一里程碑**: Week 4 — 前端模板选择器 / E2 AI 出图
