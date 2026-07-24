# E2 阶段：AI 生图集成

**阶段目标**: 集成 OpenAI 和 DashScope API 进行 AI 生图。

**预计周期**: 4 周

**状态**: ⏳ 待开始

---

## 技术方案

### 支持的供应商

| 供应商 | 模型 | 用途 |
|--------|------|------|
| **OpenAI** | DALL-E 3 / GPT-Image-2 | 高质量生图 |
| **DashScope** | Wan 2.6/2.7 T2I | 国内友好，性价比高 |

### 降级策略

```
AI 生图失败 → 使用真实素材库（Pexels/Unsplash/Pixabay）
```

---

## 开发计划

### Week 1: API 设计与配置

**任务**:
- [ ] 设计 `AIGenerationService` 接口
- [ ] 创建 `config/ai_providers.yaml` 配置文件
- [ ] 实现 API 密钥管理（加密存储）
- [ ] 添加降级策略配置

**配置结构**:
```yaml
ai_providers:
  openai:
    api_key: ""
    base_url: "https://api.openai.com/v1"
    models: ["dall-e-3", "gpt-image-2"]
    enabled: true
  dashscope:
    api_key: ""
    base_url: "https://dashscope.aliyuncs.com/api/v1"
    models: ["wan2.6-t2i", "wan2.7-image"]
    enabled: true
  fallback_to_stock: true  # 失败时降级到真实素材
```

### Week 2: OpenAI 集成

**任务**:
- [ ] 实现 OpenAI 客户端封装
- [ ] 实现图片生成与下载
- [ ] 实现本地缓存（避免重复生成）
- [ ] 错误处理与重试逻辑
- [ ] 单元测试

**核心接口**:
```python
class OpenAIImageGenerator:
    async def generate(self, prompt: str, **kwargs) -> str
    async def download(self, url: str) -> bytes
    def get_cached(self, prompt_hash: str) -> Optional[str]
```

### Week 3: DashScope 集成

**任务**:
- [ ] 实现 DashScope 客户端封装
- [ ] 支持多种图片模型切换
- [ ] 参数适配（尺寸/风格/质量）
- [ ] 单元测试

### Week 4: 前端集成与测试

**任务**:
- [ ] 创建 AI 生图配置页面
- [ ] 添加模型选择器
- [ ] 添加 Prompt 前缀配置
- [ ] 集成到视频生成流程
- [ ] 完整端到端测试
- [ ] E2 阶段总结

---

## API 接口设计

### 后端 API

```python
# 生成图片
POST /api/ai/generate-image
{
    "prompt": "一只猫在玩毛线球",
    "provider": "openai",  # or "dashscope"
    "model": "dall-e-3",
    "size": "1024x1024",
    "style": "vivid"
}
→ { "image_path": "path/to/generated.jpg" }

# 获取支持的模型
GET /api/ai/models
→ { "providers": [...], "models": [...] }
```

---

## 成本估算

| 供应商 | 模型 | 分辨率 | 价格（元/张） |
|--------|------|--------|---------------|
| OpenAI | DALL-E 3 | 1024x1024 | ~0.4 |
| DashScope | Wan 2.7 | 1024x1024 | ~0.1 |

---

*创建时间: 2026-07-24*
