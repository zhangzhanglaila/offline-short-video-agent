# E5 阶段：ComfyUI 集成

**阶段目标**: 通过本地 ComfyUI 提供零成本、可控的 AI 生图与生视频能力。
**状态**: ✅ 已完成

---

## 概述

E5 阶段在已有 Agent 系统和动态化管线基础上,接入本地 ComfyUI 作为
默认的 AI 媒体生成后端(图像 + 视频),通过 HTTP API 提交 workflow
JSON,轮询任务状态,获取生成的图像/视频产物并接入统一生成管线。
上游调用方只需声明 provider 即可透明切换(`ai.image_provider` /
`ai.video_provider`)。

完整设计见 spec:
[`docs/superpowers/specs/2026-08-02-e5-comfyui-integration-design.md`](../superpowers/specs/2026-08-02-e5-comfyui-integration-design.md)

---

## 前置条件

| 组件 | 要求 |
|------|------|
| **ComfyUI 服务** | 本机 `http://127.0.0.1:8188`,通过 `python main.py` 或桌面版启动 |
| **GPU** | NVIDIA 显卡,显存 ≥ 12 GB(Flux Dev / WAN 2.2 推荐 24 GB) |
| **模型清单** | 见 `workflows/` 下每个 JSON 的 `CheckpointLoaderSimple` / `VAELoader` 节点 |
| **Python 依赖** | `requests`(`urllib` 即可,无第三方 SDK 强依赖) |

启动 ComfyUI 后访问 `http://127.0.0.1:8188/system_stats` 应返回队列与设备信息,
否则 `load_config` 之后的 `client.test_connection()` 会抛 `ComfyUIConnectionError`。

---

## 配置示例

`config.yaml` 关键片段:

```yaml
ai:
  image_provider: comfyui   # comfyui | bailian | openai
  video_provider: comfyui   # comfyui | dashscope | kling

comfyui:
  base_url: "http://127.0.0.1:8188"
  poll_interval_sec: 2
  timeout_sec: 600
  workflows:
    image: "workflows/image/flux_dev.json"
    video_t2v: "workflows/video/wan22_t2v.json"
    video_i2v: "workflows/video/wan22_i2v.json"
```

> provider 字段可独立切换: `image_provider: bailian` + `video_provider: comfyui` 也合法。

---

## 工作流模板

| 路径 | 类型 | 占位符 |
|------|------|--------|
| `workflows/image/flux_dev.json` | Flux Dev 文生图 | `{{prompt}}` |
| `workflows/video/wan22_t2v.json` | WAN 2.2 文生视频 | `{{prompt}}` |
| `workflows/video/wan22_i2v.json` | WAN 2.2 图生视频 | `{{image}}`、`{{prompt}}` |

模板使用 `{{key}}` 占位符,由 `services/comfyui/workflow.py` 在提交前插值。

---

## 故障排查

| 症状 | 原因 | 处置 |
|------|------|------|
| `ComfyUIConnectionError: refused` | 本机未启动 ComfyUI 或端口被占用 | 启动 ComfyUI,确认 8188 端口 |
| `WorkflowTemplateNotFound` | `workflows/` 下缺模板 | 检查 `comfyui.workflows.*` 路径是否相对项目根 |
| `ComfyUIJobTimeoutError` | 模型加载慢 / 任务超时 | 增大 `timeout_sec`,或简化 workflow |
| 生成图全黑 | Checkpoint / VAE 路径错 | 检查 ComfyUI 控制台模型加载日志 |
| 占位符未替换 | `{{xxx}}` 在 JSON 中含空格或大小写不符 | 工作流模板与代码常量必须完全一致 |

---

## 降级策略

`ComfyUIJobError` 抛出时,generator 层根据 `ai.*_provider` 配置自动回退:
`comfyui` → `bailian`/`dashscope` → 真实素材库。详见 spec §6。

---

*最后更新: 2026-07-25*