# E5 ComfyUI 集成 — 设计文档

**阶段**: E5(本项目最后阶段)
**目标**: 把本地 ComfyUI 作为 AI 生图/生视频的首选 provider,云端 API 保留为可手动切换的降级路径
**状态**: ⏳ 待实施(本 spec 经用户批准后由 writing-plans 拆解实施计划)
**日期**: 2026-08-02

---

## 1. 范围

**做**:
- 新增 `ComfyUIImageGenerator` 和 `ComfyUIVideoGenerator`,实现项目已有的 `AIGenerationService` / `AIVideoGenerationService` 抽象基类
- 新增 `ComfyUIClient`(纯 HTTP,基于 `requests`),实现提交-轮询工作流 + 下载产物
- 在 `AIProvider` / `VideoProvider` 枚举里加 `COMFYUI`
- `MaterialFetchAgent` 的 lazy 属性根据 `config.yaml` 里的 provider 键选择生成器
- 内置 3 个手写工作流模板(`flux_dev.json` / `wan22_t2v.json` / `wan22_i2v.json`)
- 全局开关 `ai_image_provider` / `ai_video_provider`(`comfyui` / `bailian` / `dashscope` 等)

**不做**(YAGNI):
- ❌ TTS 模块改动(明确排除)
- ❌ RunningHub 云端适配
- ❌ 工作流可视化编辑器
- ❌ WebSocket 实时进度(用轮询)
- ❌ 新依赖(`requests` 已存在)
- ❌ 删除现有云端生成器代码(保留为可手动切换)

---

## 2. 架构

```
config.yaml
  ai_image_provider: comfyui | bailian | openai
  ai_video_provider: comfyui | dashscope | kling
  comfyui:
    base_url: http://127.0.0.1:8188
    poll_interval_sec: 2
    timeout_sec: 600
          │
          ▼
core/agents/material_fetch_agent.py
   _ai_generator (lazy)        _ai_video_generator (lazy)
          │                            │
          ▼                            ▼
services/ai_image/             services/ai_video/
├ ComfyUIImageGenerator       ├ ComfyUIVideoGenerator
│   └ uses ComfyUIClient      │   └ uses ComfyUIClient
├ BailianImageGenerator       ├ DashScopeVideoGenerator
└ OpenAIImageGenerator        └ (KlingVideoGenerator 未来)
          │                            │
          └────────────┬───────────────┘
                       ▼
          services/comfyui/client.py
          ├ POST /prompt       (提交工作流,得 prompt_id)
          ├ GET  /history/{id} (轮询 status)
          ├ GET  /view         (下载产物 PNG/MP4)
          └ GET  /system_stats (test_connection)
                       │
                       ▼
          workflows/image/flux_dev.json
          workflows/video/wan22_t2v.json
          workflows/video/wan22_i2v.json
```

**降级链路**(沿用 E2/E3,不改 agent 代码):
```
ComfyUI 不可用 (test_connection=False / 超时 / 5xx)
   → 改用 AIProvider.BAILIAN (image) / VideoProvider.DASHSCOPE (video)
   → 改用 stock_image_module (Pexels/Pixabay 真实素材库)
```

MaterialFetchAgent 的 lazy 属性已有 fail-safe:捕获子异常后返回 None → 主流程走 stock 图片。E5 不引入新降级逻辑,只是把"hardcode Bailian"改成"读 config 选"。

---

## 3. 文件清单

### 新增

| 文件 | 行数估计 | 说明 |
|------|---------|------|
| `services/comfyui/__init__.py` | 5 | 暴露 `ComfyUIClient` |
| `services/comfyui/client.py` | 220 | 纯 HTTP 客户端:submit / wait_for_completion / download_outputs / test_connection |
| `services/comfyui/errors.py` | 30 | `ComfyUIConnectionError` / `ComfyUIExecutionError` / `ComfyUITimeoutError` |
| `services/comfyui/template.py` | 60 | 工作流模板加载 + `{{prompt}}` `{{width}}` `{{height}}` `{{steps}}` `{{seed}}` 插值 |
| `services/ai_image/comfyui_generator.py` | 90 | 实现 `AIGenerationService.generate()` |
| `services/ai_video/comfyui_generator.py` | 140 | 实现 `AIVideoGenerationService.generate()`(AsyncGenerator 进度) |
| `workflows/image/flux_dev.json` | 80 | Flux Dev 1024x1024 文生图 |
| `workflows/video/wan22_t2v.json` | 120 | Wan 2.2 文生视频 720P 5s |
| `workflows/video/wan22_i2v.json` | 120 | Wan 2.2 图生视频(可选,Week 3 用) |
| `tests/test_comfyui_client.py` | 200 | 用 `requests-mock` 模拟 HTTP |
| `tests/test_comfyui_image_generator.py` | 150 | 注入 fake client |
| `tests/test_comfyui_video_generator.py` | 150 | 同上 |
| `tests/test_comfyui_integration.py` | 80 | `pytest.mark.integration` 真实 ComfyUI 跑通 |

### 修改

| 文件 | 改动 |
|------|------|
| `services/ai_image/base.py` | `AIProvider` 枚举加 `COMFYUI = "comfyui"` |
| `services/ai_video/base.py` | `VideoProvider` 枚举加 `COMFYUI = "comfyui"` |
| `services/ai_image/__init__.py` | 导出 `ComfyUIImageGenerator` |
| `services/ai_video/__init__.py` | 导出 `ComfyUIVideoGenerator` |
| `core/agents/material_fetch_agent.py` | lazy 属性读 `config.ai_image_provider` 决定实例化哪个 generator |
| `config.yaml` | 新增 `ai_image_provider` / `ai_video_provider` / `comfyui:` 三键 |
| `docs/27-E5-comfyui.md` | 把本 spec 概要写进去,标注"设计见 superpowers/specs/..." |
| `docs/CLAUDE.md` | E5 状态改 ✅,概述已交付能力 |

### 不改

- `core/tts_module.py`(明确排除)
- `services/template/`、`services/history/`、`api/` 目录

---

## 4. 核心接口

### `ComfyUIClient`

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class WorkflowOutput:
    filename: str       # ComfyUI 端 filename
    subfolder: str      # 通常空
    type: str           # "output" / "temp"
    local_path: Path    # 下载后落盘路径

class ComfyUIClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        poll_interval_sec: float = 2.0,
        timeout_sec: float = 600.0,
    ): ...

    def test_connection(self) -> bool:
        """GET /system_stats,5xx 或连接失败返回 False"""

    def submit(self, workflow: dict) -> str:
        """POST /prompt,返回 prompt_id;失败抛 ComfyUIConnectionError"""

    def wait_for_completion(self, prompt_id: str) -> list[WorkflowOutput]:
        """循环 GET /history/{prompt_id},直到 status 终态;
        终态 = (outputs 非空,视为成功) 或 (status==error / 无 outputs,抛 ComfyUIExecutionError);
        超时抛 ComfyUITimeoutError"""

    def download_outputs(
        self, outputs: list[WorkflowOutput], save_dir: Path
    ) -> list[Path]:
        """GET /view?filename=...&subfolder=...&type=...,
        落 save_dir 下,返回本地路径列表"""
```

### Generator 适配

`ComfyUIImageGenerator(AIGenerationService)`:

```python
async def generate(self, request: AIImageRequest) -> AIImageResult:
    if cached := await self.get_cached(request):
        return AIImageResult(success=True, image_path=str(cached), provider="comfyui", ...)

    workflow_path = Path("workflows/image/flux_dev.json")
    workflow = load_template(workflow_path).render(
        prompt=request.prompt,
        width=_parse_w(request.size.value),
        height=_parse_h(request.size.value),
        steps=20, seed=random.randint(0, 2**31),
    )
    prompt_id = self.client.submit(workflow)
    outputs = self.client.wait_for_completion(prompt_id)
    paths = self.client.download_outputs(outputs, self._cache_dir)
    return AIImageResult(
        success=True,
        image_path=str(paths[0]),
        provider="comfyui",
        generation_time=elapsed,
        cost=0.0,
    )
```

`ComfyUIVideoGenerator(AIVideoGenerationService)` 同模式,`generate()` 是 `AsyncGenerator[VideoGenerationProgress]` —— 轮询过程中定期 `yield VideoGenerationProgress(progress=...)`,终态 yield `SUCCEEDED`。

---

## 5. 错误处理

| 失败场景 | 检测点 | 处理 |
|---------|--------|------|
| ComfyUI 服务未启动 | `test_connection()` 抛 ConnectionError | `ai_generator` lazy 属性捕获,返回 None → MaterialFetchAgent 主流程降级 stock 图片 |
| 工作流执行失败 | `/history/{id}` 无 outputs 或 `status["error"]` 非空 | generator 内捕获 `ComfyUIExecutionError` → 重试 1 次(等 5s)→ 仍失败抛给 lazy 属性 |
| 产物下载失败 | `GET /view` 返回 404/500 | 同上,重试 1 次 → 失败抛 |
| 超时 | `time.time() - start > timeout_sec` | 抛 `ComfyUITimeoutError` → lazy 属性降级 |
| 工作流模板文件缺失 | `load_template()` 抛 `FileNotFoundError` | 启动时(实际是首次调用时)在日志 ERROR 级别报错,**不**降级——模板缺失是部署错误,不应静默 |

**关键设计**:lazy 属性捕获所有 `ComfyUI*Error` 并 `logger.warning(...)` 后返回 None。Agent 层完全不感知 ComfyUI 存在,只是"AI 生成这次失败了用 stock 图片"。

---

## 6. 工作流模板插值约定

仅支持占位符 `{{prompt}}` `{{width}}` `{{height}}` `{{steps}}` `{{seed}}`:

- 字符串字段(`CLIPTextEncode.text` 等)直接 `str(value)` 替换
- 数字字段(`EmptyLatentImage.width` 等)用 `int(value)` 替换
- 未识别的占位符保留原样 + DEBUG 日志(避免模板改版后静默失效)

**防 LLM 注入**:`prompt` 内的 `{{` `}}` 转义为 `\{` `\}` 防止误触发二次插值。

`workflows/image/flux_dev.json` 内容大纲(Flux Dev 基本工作流):
- `UNETLoader` → `DualCLIPLoader` → `CLIPTextEncode`(正/反向 prompt) → `KSampler` → `VAEDecode` → `SaveImage`

`workflows/video/wan22_t2v.json` 内容大纲(Wan 2.2 T2V):
- `WanVideoModelLoader` → `CLIPLoader` → `CLIPTextEncode` → `WanVideoSampler` → `WanVideoDecode` → `SaveVideo`

(具体节点细节由实施时根据本地已部署模型调整,本 spec 不锁定节点 id。)

---

## 7. 配置

`config.yaml` 新增:

```yaml
ai:
  image_provider: comfyui   # comfyui | bailian | openai
  video_provider: comfyui   # comfyui | dashscope | kling

comfyui:
  base_url: "http://127.0.0.1:8188"
  poll_interval_sec: 2
  timeout_sec: 600
  # 工作流模板路径(相对项目根)
  workflows:
    image: "workflows/image/flux_dev.json"
    video_t2v: "workflows/video/wan22_t2v.json"
    video_i2v: "workflows/video/wan22_i2v.json"
```

读取:沿用项目现有 config 加载模式(由 `core/agents/material_fetch_agent.py` 启动时读 `.env`/yaml)。具体加载器在实施时确认是否需新增辅助函数。

---

## 8. 测试策略

| 层 | 工具 | 覆盖目标 |
|----|------|---------|
| **单元 (离线)** | `pytest` + `requests-mock`(已存在的依赖?需确认) | 模板插值、超时、重试、HTTP 错误码、降级路径 |
| **Generator 单测** | 注入 `FakeComfyUIClient` | `ComfyUIImageGenerator.generate` / `ComfyUIVideoGenerator.generate` 各路径 |
| **Agent 集成** | MaterialFetchAgent 注入 mock generator | `provider=comfyui` 时主流程行为、降级是否触发 |
| **E2E (有 GPU 时)** | `pytest.mark.integration`,真实 ComfyUI | 提交→等待→下载→落盘完整路径 |
| **CI 守门** | 默认只跑离线 | 集成测试需 `--run-integration` 标记(与 `test_ai_image_service.py` 一致) |

**新增 `requests-mock` 依赖**(待 writing-plans 阶段确认项目是否已有等价物;若无则 `pip install requests-mock` 或用 `monkeypatch` + `unittest.mock`)。

**离线测试目标**:`tests/test_comfyui_*.py` 新增 ≥ 12 个用例;项目总离线测试目标保持全绿。

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 工作流 JSON 节点 id/字段在不同 ComfyUI 版本下不兼容 | 用户本地 ComfyUI 升级后工作流失效 | 模板用最保守的官方节点类型;文档注明 "for ComfyUI ≥ X.Y";失败有清晰错误信息指向工作流加载 |
| 单 GPU 串行调用,生成慢 | 用户等待时长增加 | 文档提示 ComfyUI 是单设备串行;长视频生成 timeout_sec 默认 600s;MaterialFetchAgent 不并发调用 |
| `requests-mock` 不可用 / 引入新依赖 | 增加 CI 复杂度 | 实施时先看 `pytest-mock` 是否已在用;否则引入;最坏方案 `monkeypatch` 内置 `requests.Session.send` |
| 工作流模板占位符与本地实际节点不匹配 | 用户首次跑报错 | 文档+ README 说明:本地 ComfyUI 需装 Flux Dev + Wan 2.2;内置模板是最小可运行配置,可按需替换 |

---

## 10. 实施节奏(4 周,沿用 E5 原计划)

| 周 | 内容 |
|----|------|
| W1 | `ComfyUIClient` + `ComfyUIClient` 测试 + `ComfyUIImageGenerator` + `flux_dev.json` 模板 |
| W2 | `ComfyUIVideoGenerator` + `wan22_t2v.json` 模板 + `wan22_i2v.json` |
| W3 | `MaterialFetchAgent` 集成(config 读取、provider 切换、降级路径) |
| W4 | 文档(`docs/27-E5-comfyui.md` 改写、`CLAUDE.md` 更新)、E2E 集成测试、阶段总结 |

每周结束:更新 `devlog/daily/`,更新测试统计,git commit。

---

## 11. 不在 E5 范围(显式排除)

- TTS 模块的 ComfyUI 适配(用户在澄清环节明确排除)
- RunningHub 云端 ComfyUI 服务
- ComfyUI 工作流可视化编辑 UI
- 实时 WebSocket 进度推送
- 对现有云端生成器代码的任何功能改动
- 任何新的第三方 SDK 依赖

---

*以上为完整设计 spec。自审:无 TBD、无内部矛盾(降级路径与 E2/E3 一致)、范围聚焦单次实施可完成、术语唯一。等待用户审阅。*