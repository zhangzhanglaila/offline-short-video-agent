# 🏗️ Agent系统架构设计

## 系统整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户接口层                               │
│                     (CLI / Web API)                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    主控Agent (Coordinator)                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • 需求拆解                                              │   │
│  │ • 任务分发 → 子Agent                                    │   │
│  │ • 结果汇总 & 校验                                       │   │
│  │ • 流程控制 & 重试                                       │   │
│  │ • 异常处理 & 降级                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
   ┌─────────┐          ┌──────────┐         ┌──────────────┐
   │ 内容分析 │          │ 素材检索 │         │  视频合成    │
   │  Agent  │          │  Agent   │         │    Agent     │
   │         │          │          │         │              │
   │ • 需求理解 │          │ • 关键词提取│         │ • 场景渲染   │
   │ • 大纲生成 │          │ • 素材搜索 │         │ • 素材集成   │
   │ • 场景划分 │          │ • 质量评分 │         │ • 文字叠加   │
   │ • 文字编写 │          │ • 缓存管理 │         │ • 视频合成   │
   └─────────┘          └──────────┘         └──────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    消息总线 (MessageBus)                         │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │ • 异步消息传递                                           │ │
│   │ • 消息队列管理                                           │ │
│   │ • 结果聚合                                               │ │
│   │ • 错误回调                                               │ │
│   └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬───────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
    ┌──────┐            ┌──────────┐         ┌─────────────┐
    │ 素材库│            │ LLM接口  │         │ FFmpeg引擎  │
    │      │            │          │         │             │
    │ •本地 │            │ • Ollama │         │ • 渲染      │
    │ •缓存 │            │ • 云API  │         │ • 编码      │
    │ •索引 │            │ • 降级   │         │ • 合成      │
    └──────┘            └──────────┘         └─────────────┘
```

---

## 核心模块设计

### 1. 主控Agent (CoordinatorAgent)

**文件**: `core/agents/coordinator_agent.py`

**职责**:
- 解析用户需求
- 拆解为子任务
- 分发给子Agent
- 等待结果
- 校验与汇总
- 异常处理

**核心方法**:
```python
class CoordinatorAgent:
    async def process_request(request: UserRequest) -> VideoResult
    async def dispatch_task(task: Task) -> None
    async def collect_results(agent_id: str, timeout: int) -> Result
    async def validate_result(result: Result) -> bool
    async def handle_error(error: Exception, task: Task) -> RetryDecision
```

**数据流**:
```
UserRequest 
  ↓ (拆解)
Tasks[ContentAnalysis, MaterialFetch, VideoCompose]
  ↓ (分发)
SubAgents (并行/顺序)
  ↓ (汇总)
VideoResult
```

---

### 2. 内容分析Agent (ContentAnalysisAgent)

**文件**: `core/agents/content_analysis_agent.py`

**职责**:
- 理解用户需求
- 提取关键信息
- 生成内容大纲
- 划分场景
- 编写文字内容

**输入**:
```json
{
  "user_request": "讲解Python异步编程",
  "category": "教育讲解",
  "style": "minimal",
  "duration": 30
}
```

**输出**:
```json
{
  "title": "Python异步编程完全指南",
  "category": "教育讲解",
  "style": "minimal",
  "total_duration": 30,
  "scenes": [
    {
      "scene_id": 1,
      "type": "title_card",
      "duration": 3,
      "text": "Python异步编程\n高效并发编程",
      "keywords": []
    },
    {
      "scene_id": 2,
      "type": "content",
      "duration": 8,
      "text": "async/await是什么？",
      "keywords": ["async", "await", "异步"]
    }
  ]
}
```

---

### 3. 素材检索Agent (MaterialFetchAgent)

**文件**: `core/agents/material_fetch_agent.py`

**职责**:
- 提取场景关键词
- 搜索匹配素材
- 下载并缓存
- 评分质量
- 返回素材清单

**输入**:
```json
{
  "scenes": [
    {
      "scene_id": 2,
      "keywords": ["async", "await", "异步"],
      "material_type": "image",
      "quantity": 3
    }
  ]
}
```

**输出**:
```json
{
  "scene_materials": {
    "2": [
      {
        "id": "mat_001",
        "url": "file:///cache/...",
        "type": "image",
        "source": "pixabay",
        "quality_score": 0.92,
        "size": "1920x1080"
      }
    ]
  }
}
```

---

### 4. 视频合成Agent (VideoComposeAgent)

**文件**: `core/agents/video_compose_agent.py`

**职责**:
- 加载风格配置
- 加载素材
- 渲染每个场景
- 应用转场效果
- 合成最终视频
- 生成报告

**输入**:
```json
{
  "content": { ... },
  "materials": { ... },
  "style_config": "minimal",
  "output_path": "output/video_001.mp4"
}
```

**输出**:
```json
{
  "success": true,
  "video_path": "output/video_001.mp4",
  "duration": 30,
  "resolution": "1920x1080",
  "file_size": "5.2MB",
  "quality_score": 0.87
}
```

---

## 消息通信协议

### 消息格式

```json
{
  "msg_id": "msg_20260721_001",
  "timestamp": "2026-07-21T10:30:45.123Z",
  "sender": "coordinator",
  "receiver": "content_analysis",
  "msg_type": "task",
  "task_type": "analyze",
  "priority": 1,
  "timeout": 300,
  "payload": {
    "user_request": "...",
    "category": "教育讲解"
  },
  "status": "pending",
  "result": null,
  "error": null
}
```

### 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| **task** | Coordinator → SubAgent | 下发任务 |
| **result** | SubAgent → Coordinator | 返回结果 |
| **error** | SubAgent → Coordinator | 错误回报 |
| **heartbeat** | SubAgent → Coordinator | 定期心跳 |
| **cancel** | Coordinator → SubAgent | 取消任务 |

### 消息状态机

```
pending (等待处理)
  ↓
processing (处理中) → heartbeat (定期汇报)
  ↓
success (成功) → result (返回结果)
  ├─ failed (失败) → error (返回错误)
  └─ timeout (超时) → error (返回超时错误)
```

---

## MessageBus 设计

**文件**: `core/agents/message_bus.py`

```python
class MessageBus:
    async def send(msg: Message) -> None
    async def subscribe(receiver: str, callback: Callable) -> None
    async def wait_result(msg_id: str, timeout: int) -> Result
    async def broadcast_error(error: Exception) -> None
```

**特性**:
- 异步事件驱动
- 支持请求-响应和发布-订阅
- 内置超时和重试机制
- 消息持久化（可选）

---

## 流程执行顺序

### 标准流程（三个Agent串行）

```
1. 用户提交需求
     ↓
2. Coordinator 接收请求
     ↓
3. [Task-1] 分发给 ContentAnalysisAgent
     ├─ Agent分析需求
     ├─ 生成内容结构
     └─ 返回结果
     ↓
4. [Task-2] 分发给 MaterialFetchAgent
     ├─ 根据内容提取关键词
     ├─ 搜索和下载素材
     └─ 返回素材清单
     ↓
5. [Task-3] 分发给 VideoComposeAgent
     ├─ 加载素材和风格
     ├─ 逐场景渲染
     ├─ 视频合成
     └─ 返回视频路径
     ↓
6. Coordinator 汇总结果
     ├─ 校验视频质量
     ├─ 生成报告
     └─ 返回用户
     ↓
7. 完成，输出视频 ✅
```

### 异常恢复流程

```
Task失败
  ↓
Coordinator 收到 error 消息
  ↓
判断可重试？
  ├─ YES → 重试（最多N次）
  │         ├─ 成功 → 继续
  │         └─ 失败 → 降级
  └─ NO → 直接降级
     ↓
降级方案（见异常处理表）
  ├─ 纯文本卡
  ├─ 占位符素材
  └─ 简化渲染
     ↓
继续流程或终止
```

---

## 文件结构

```
core/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Agent基类
│   ├── message_bus.py          # 消息总线
│   ├── coordinator_agent.py    # 主控Agent
│   ├── content_analysis_agent.py    # 内容分析
│   ├── material_fetch_agent.py      # 素材检索
│   └── video_compose_agent.py       # 视频合成
│
├── models/
│   ├── request.py              # 请求数据模型
│   ├── message.py              # 消息数据模型
│   └── result.py               # 结果数据模型
│
└── utils/
    └── agent_utils.py          # Agent工具函数
```

---

## 扩展点

### 新增Agent
实现 `BaseAgent` 接口，注册到消息总线

### 新增素材源
在 `MaterialFetchAgent` 中扩展API接口

### 新增风格模板
在 `VideoComposeAgent` 中添加风格配置

---

*最后更新: 2026-07-21*
*架构版本: 1.0*
