# E3 阶段：AI 生视频集成

**阶段目标**: 集成通义 WAN 和可灵 API 进行 AI 生视频。

**预计周期**: 4 周

**状态**: ⏳ 待开始

---

## 技术方案

### 支持的供应商

| 供应商 | 模型 | 能力 |
|--------|------|------|
| **DashScope** | Wan 2.7 T2V/I2V/R2V | 文生视频/图生视频/重绘 |
| **DashScope** | HappyHorse 1.0 | 高质量视频 |
| **Kling** | Kling V3/V2.6/V2.5 | 高质量视频 |

### 降级策略

```
AI 生视频失败 → 使用 Ken Burns 运镜处理静态图片
```

---

## 开发计划

### Week 1: 视频服务设计

**任务**:
- [ ] 设计 `VideoGenerationService` 接口
- [ ] 创建任务队列机制（视频生成耗时较长）
- [ ] 实现进度回调机制
- [ ] 添加超时与取消支持

**核心接口**:
```python
class VideoGenerationService:
    async def generate(self, prompt: str, **kwargs) -> AsyncGenerator[Progress, None]
    async def cancel(self, task_id: str)
    def get_status(self, task_id: str) -> TaskStatus
```

### Week 2: 通义 WAN 集成

**任务**:
- [ ] 实现 DashScope WAN API 调用
- [ ] 支持 T2V（文生视频）
- [ ] 支持 I2V（图生视频）
- [ ] 实现视频下载与缓存
- [ ] 错误处理与重试

**模型能力**:
```python
VIDEO_MODEL_CAPABILITIES = {
    "wan2.7-t2v": {
        "duration": (2, 15),  # 秒
        "resolutions": ["720P", "1080P"],
        "ratios": ["16:9", "9:16", "1:1"],
        "fps": 30
    }
}
```

### Week 3: 可灵集成

**任务**:
- [ ] 实现可灵 API 调用
- [ ] 参数适配（分辨率/时长/画幅）
- [ ] 单元测试

### Week 4: 前端集成与测试

**任务**:
- [ ] 创建 AI 生视频配置页面
- [ ] 添加进度条显示
- [ ] 添加取消按钮
- [ ] 集成到视频生成流程
- [ ] 完整端到端测试
- [ ] E3 阶段总结

---

## API 接口设计

### 后端 API

```python
# 生成视频
POST /api/ai/generate-video
{
    "prompt": "一只猫在玩毛线球",
    "provider": "dashscope",
    "model": "wan2.7-t2v",
    "duration": 5,
    "ratio": "9:16"
}
→ { "task_id": "xxx", "status": "processing" }

# 查询进度
GET /api/ai/video-status/{task_id}
→ { "status": "processing", "progress": 0.5, "video_path": null }

# 取消任务
DELETE /api/ai/video-task/{task_id}
→ { "status": "cancelled" }
```

---

## 成本估算

| 供应商 | 模型 | 时长 | 价格（元/分钟） |
|--------|------|------|----------------|
| DashScope | Wan 2.7 T2V | 5秒 | ~1-2 |
| Kling | V2.5 Turbo | 5秒 | ~0.5-1 |

---

*创建时间: 2026-07-24*
