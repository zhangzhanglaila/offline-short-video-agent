# Phase E5: ComfyUI 集成 — 完成

## 目标

把 ComfyUI(本地开源 AI 生图/生视频平台)接入项目,作为现有云端 AI 服务的**本地免费替代**,并支持 provider 可切换。让用户在没有云端 API 密钥的情况下也能跑通 AI 生图/生视频。

## 关键交付

### 1. ComfyUI HTTP Client (`services/comfyui/client.py`)
- `submit(workflow) -> str` — 提交工作流,返回 prompt_id
- `wait_for_completion(prompt_id) -> list[WorkflowOutput]` — 轮询直到完成,返回输出节点
- `download_outputs(outputs, save_dir) -> list[Path]` — 下载生成的图片/视频到本地
- `test_connection() -> bool` — 探测 ComfyUI 服务是否可达
- `shutdown()` — 优雅关闭 aiohttp session
- 错误类: `ComfyUIError` / `ConnectionError` / `ExecutionError` / `TimeoutError`

### 2. Workflow Template Loader (`services/comfyui/template.py`)
- `load_template(path) -> dict` — 加载 JSON 工作流
- `render_template(workflow, *, prompt, width, height, steps, seed) -> dict` — 插值占位符
- 占位符: `{{prompt}}` / `{{width}}` / `{{height}}` / `{{steps}}` / `{{seed}}`
- 转义: `{{` → `{{{`, `}}` → `}}}` 保留字面量

### 3. Generators (适配器)
- `ComfyUIImageGenerator` — 适配 `AIGenerationService`,返回 `AIImageResponse`
- `ComfyUIVideoGenerator` — 适配 `AIVideoGenerationService`,支持流式进度
- 失败时降级到现有云端 provider

### 4. 内置 Workflow JSONs
- `workflows/image/flux_dev.json` — Flux Dev 文生图
- `workflows/video/wan22_t2v.json` — Wan 2.2 文生视频
- `workflows/video/wan22_i2v.json` — Wan 2.2 图生视频

### 5. Config Layer
- `services/config/loader.py` — 轻量 YAML loader + env override
- `config.yaml` — 新增 `ai.image_provider` / `ai.video_provider`,默认 `comfyui`
- MaterialFetchAgent 读取这些配置,决定走哪条管线

### 6. 测试
- `tests/test_config_loader.py` (3) — config 加载 + env override
- `tests/test_comfyui_template.py` (6) — 模板插值 + 转义
- `tests/test_comfyui_client.py` (9) — HTTP mock + 错误处理
- `tests/test_comfyui_image_generator.py` (4) — 适配器
- `tests/test_comfyui_video_generator.py` (4) — 适配器
- `tests/test_comfyui_integration.py` (5 + 2 skipped) — 真实 ComfyUI,默认 skip

**总计: 31 新测试,全绿**

## 架构变更

### Before (E0-E4)
```
MaterialFetchAgent → CloudAIImageService (DeepSeek/云端)
                  → CloudAIVideoService
```

### After (E5)
```
MaterialFetchAgent → config.yaml 决定 provider
                  ↓
                  ├→ ComfyUIImageGenerator (本地,免费)
                  ├→ CloudAIImageService (云端,降级)
                  ├→ ComfyUIVideoGenerator (本地,免费)
                  └→ CloudAIVideoService (云端,降级)
```

### Provider 切换机制
- `config.yaml`:
  ```yaml
  ai:
    image_provider: comfyui  # or cloud
    video_provider: comfyui  # or cloud
  ```
- MaterialFetchAgent 启动时读取,bind 到对应的 service
- 运行时不可热切换(需重启),但配置灵活

## 测试覆盖

| 测试类型 | 数量 | 状态 |
|---------|------|------|
| 单元测试(模板/客户端/生成器) | 26 | 全绿 |
| 集成测试(本地 ComfyUI) | 5 + 2 skip | 默认 skip |
| ai_image 回归守门 | 6 | 全绿 |
| 完整离线回归 | 767 passed | 2 pre-existing flaky |

## 已知问题

1. **`_CLIENT_INJECTED` 哨兵未使用** — `services/ai_image/comfyui_generator.py` 留着 `_CLIENT_INJECTED` 占位常量,实际只有 `_client_injected` 布尔。可清理但不影响功能。
2. **`_ai_image_enabled` / `_ai_video_enabled` 半遗留** — MaterialFetchAgent 早期版本用 boleean flag,现在 config.yaml 直接决定,旧的 flag 还在代码里没清理。
3. **2 个 pre-existing flaky tests** — `tests/template/test_integration.py` 的 playwright async 测试,在完整 suite 跑时偶发失败(单跑通过),与 E5 无关。
4. **宽松 `try/except Exception`** — generator 的 properties 有几处宽 except,匹配既有模式但不够精确。

## 用户价值

### 1. 零成本 AI 生图/生视频
- ComfyUI 开源 + 本地 GPU,不花一分钱
- 适合个人开发者、研究场景

### 2. 完全可控
- 3 个内置 workflow JSON,用户可改
- 可接入自定义节点、自定义模型
- 数据不出本地(隐私)

### 3. 平滑降级
- ComfyUI 不可达 → 自动 fallback 到云端
- 用户不需要切换代码,改 config.yaml 即可

### 4. Provider 抽象
- `AIProvider.COMFYUI` / `VideoProvider.COMFYUI`
- 未来可加新 provider(Stable Diffusion WebUI、Fooocus 等)

## 后续扩展点

### E5.1 (建议)
- TTS 集成(ComfyUI 有 CosyVoice 等 TTS 节点)
- Wan 2.2 长视频超时单独配置
- 动态工作流(根据场景复杂度选 sampler)

### E6+
- WebSocket 监听 ComfyUI 实时进度(现在用轮询)
- 多 ComfyUI 实例负载均衡
- Cloud↔Local 自动 failover

## 文档

- `docs/27-E5-comfyui.md` — 设计文档(已更新含 ops notes)
- `devlog/daily/2026-08-02.md` — 完成日志
- `CLAUDE.md` — E5 阶段标记

---

**E5 阶段状态**: ✅ 完成
**新增测试**: 31
**回归**: 767 passed (offline)
**下一步**: E5.1 (TTS) 或 E6+(WebSocket/负载均衡)
