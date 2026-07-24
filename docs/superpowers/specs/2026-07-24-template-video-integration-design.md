# E1 Week 3 计划: 模板引擎接入视频主流程

**创建时间**: 2026-07-24
**前置**: E1 Week 2 完成（template rendering engine）
**目标**: 让用户能选择用 HTML 模板生成视频场景，看到端到端效果

---

## Context

E1 Week 2 完成了模板渲染引擎（Playwright + Jinja2 → PNG），但**目前没有 caller**。
`render_template_frame()` 函数已存在于 `core/compose/scene_image_renderer.py:652`，但 `VideoComposeAgent` 完全没有调用它。

本周目标：**让用户能在生成视频时指定 `template="image_default"`，并看到带模板外观的完整视频**。

---

## 关键发现（已调研）

1. **集成点是 `_build_scene_spec()`** —— `core/agents/video_compose_agent.py:268`
   - 内容场景分支在 line 314-326，目前用 asset 或 gradient bg
   - 这里插入 `if scene.template:` 分支最自然

2. **数据模型需要扩展** —— `Scene` 数据类（`core/models/content.py:26`）
   - 当前字段：scene_id, scene_type, text, duration, keywords, narration
   - 需要加：`template: Optional[str] = None` + `from_dict` 读取

3. **上下文构造** —— 模板需要的参数（从 `templates/1080x1920/image_default.html`）
   - `title`：来自 `content.title`
   - `image`：来自素材的 `local_path`，或 fallback 到 SVG 占位
   - `text`：来自 `scene.text`
   - `author`/`describe`/`brand`：可选，从 `content.metadata` 或 defaults

4. **异步兼容** —— `VideoComposeAgent.execute` 已是 `async`，`_build_scene_spec` 当前是 sync
   - 需要把 `_build_scene_spec` 改成 async
   - 所有 caller（line 130）加 `await`

5. **FFmpeg 无影响** —— 下游 `_render_scene_clip` 只看 `background_path` 是否有效 PNG
   - 模板生成的 PNG 直接喂给 FFmpeg，零改动

---

## 设计决策

| 项 | 决策 |
|----|------|
| 触发条件 | `scene.template` 非空时启用模板路径 |
| 默认行为 | 不指定 `template` 时保持现有逻辑（asset/gradient bg） |
| 失败降级 | `render_template_frame` 失败 → 降级到现有 gradient bg 路径 |
| 上下文来源 | 从 Scene + ContentStructure + Material 提取 |
| 模板覆盖素材 | 模板路径下，素材图作为 `{{image}}`，不开 Ken Burns（模板已自含视觉） |
| 跨测试 | 复用现有 `test_video_compose_agent.py` |

---

## 文件变更清单

| 文件 | 变更 |
|------|------|
| `core/models/content.py` | 加 `template` 字段，更新 `from_dict` 和 `to_dict` |
| `core/agents/video_compose_agent.py` | `_build_scene_spec` 改 async，加模板分支 |
| `core/compose/scene_image_renderer.py` | `render_template_frame` 加 fallback 参数 |
| `generate_video.py` | 加 `--template` CLI 参数 |
| `tests/template/test_video_integration.py` | 新增端到端测试 |
| `tests/test_video_compose_agent.py` | 新增模板路径测试 |

---

## 验证

1. `python -m pytest tests/template/test_video_integration.py tests/test_video_compose_agent.py -v`
2. CLI 测试：`python generate_video.py --input "Python异步编程" --template image_default --duration 10`
3. 打开生成的 mp4 看效果
4. 不指定 `--template` 时行为不变（向后兼容）

---

## 风险

- `_build_scene_spec` 改 async 影响范围大 → 用 `git grep` 确认 caller 只有一处（line 130）
- 模板渲染 ~2 秒/场景，5 场景视频约多 10 秒 → 用户可接受
- 模板路径不走 Ken Burns，静态图 → 但模板本身有装饰元素弥补

---

## YAGNI（不做）

- ❌ 模板按分辨率自动选择（用户先固定 1080x1920）
- ❌ 模板池管理 UI（前端 Week 4 再做）
- ❌ 模板预览图（CLI 阶段不做）
- ❌ 多模板混搭（一个视频一个模板）

---

*设计完成，下一步：writing-plans 输出实现计划*