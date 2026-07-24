# E5 阶段：ComfyUI 可选集成

**阶段目标**: 支持本地 ComfyUI 作为无成本 AI 生成选项。

**预计周期**: 4 周

**状态**: ⏳ 待开始

---

## 技术方案

### ComfyUI 集成方式

使用 `ComfyKit` SDK（类似 Pixelle-Video 的集成方式）调用本地 ComfyUI 服务。

### 支持的工作流类型

| 类型 | 工作流位置 | 功能 |
|------|-----------|------|
| **TTS** | `workflows/tts/` | 文字转语音（Edge-TTS/Index-TTS） |
| **图像** | `workflows/image/` | AI 生图（Flux/SDXL） |
| **视频** | `workflows/video/` | AI 生视频（WAN/可灵本地版） |

### 配置方式

```yaml
comfyui:
  # 本地 ComfyUI 服务
  local_url: "http://127.0.0.1:8188"
  api_key: ""  # 可选

  # 云端 RunningHub（可选）
  runninghub_api_key: ""
  runninghub_concurrent_limit: 1
```

---

## 开发计划

### Week 1: ComfyUI 基础集成

**任务**:
- [ ] 添加 `comfykit` 依赖
- [ ] 创建 `services/comfyui_service.py`
- [ ] 实现本地服务连接
- [ ] 实现工作流加载与执行
- [ ] 错误处理

**核心接口**:
```python
class ComfyUIService:
    async def execute_workflow(self, workflow_path: str, inputs: dict) -> dict
    async def test_connection(self) -> bool
    def get_workflow_info(self, workflow_path: str) -> WorkflowInfo
```

### Week 2: TTS 工作流

**任务**:
- [ ] 创建默认 TTS 工作流 `workflows/tts/edge_tts.json`
- [ ] 集成到现有 `core/tts_module.py`
- [ ] 添加工作流配置页面
- [ ] 测试

### Week 3: 图像/视频工作流

**任务**:
- [ ] 创建默认图像工作流 `workflows/image/flux_default.json`
- [ ] 创建默认视频工作流 `workflows/video/wan_default.json`
- [ ] 集成到 `services/ai_media_service.py`
- [ ] 测试

### Week 4: 配置页面与文档

**任务**:
- [ ] 添加 ComfyUI 配置页面
- [ ] 添加连接状态显示
- [ ] 编写 ComfyUI 部署文档
- [ ] 编写工作流自定义文档
- [ ] 完整测试
- [ ] E5 阶段总结

---

## 工作流示例

### TTS 工作流 (`workflows/tts/edge_tts.json`)

```json
{
    "nodes": [
        {
            "type": "EdgeTTSTextToSpeech",
            "inputs": {
                "text": "{{text}}",
                "voice": "{{voice}}"
            }
        }
    ]
}
```

### 图像工作流 (`workflows/image/flux_default.json`)

```json
{
    "nodes": [
        {
            "type": "FluxTextToImage",
            "inputs": {
                "prompt": "{{prompt}}",
                "width": 1024,
                "height": 1024
            }
        }
    ]
}
```

---

## 降级策略

```
ComfyUI 不可用 → 降级到 API 直连
API 直连失败 → 降级到真实素材库
```

---

## 优势

- ✅ 完全免费（本地运行）
- ✅ 支持自定义工作流
- ✅ 离线可用
- ⚠️ 需要本地 GPU
- ⚠️ 需要手动部署 ComfyUI

---

*创建时间: 2026-07-24*
