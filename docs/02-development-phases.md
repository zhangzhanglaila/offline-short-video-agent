# 📅 开发阶段规划 (稳健增量式)

## 总体策略

**原则**: 每个Phase完整、可验证、可交付
- 不跨越依赖关系
- 每周1-2个Phase
- 每个Phase有明确的验收标准
- 定期同步和审查

---

## Phase 0: Agent框架与通信基础 (1-2天)

### 目标
- 搭建Agent运行框架
- 实现消息总线
- 定义数据模型

### 交付物
```
core/agents/
├── __init__.py
├── base_agent.py           ← BaseAgent抽象类
├── message_bus.py          ← MessageBus实现
├── coordinator_agent.py    ← 主控Agent框架

core/models/
├── message.py             ← 消息数据模型
├── request.py             ← 请求数据模型
└── result.py              ← 结果数据模型

test_agent_framework.py     ← 框架测试
```

### 验收标准
- [x] BaseAgent可以子类化
- [x] MessageBus可以发送/接收消息
- [x] 消息格式符合规范
- [x] 异步流程通畅
- [x] 框架测试通过（3个测试）

### 预计时间
1-2天

---

## Phase 1: 内容分析Agent (2-3天)

### 目标
- 实现ContentAnalysisAgent
- 支持需求拆解和大纲生成
- 集成LLM（Ollama优先）

### 交付物
```
core/agents/content_analysis_agent.py
├── 需求解析
├── 大纲生成
├── 场景划分
└── 文字编写

core/prompts/
└── content_analysis_prompts.py  ← LLM提示词

test_content_analysis_agent.py
├── 测试用例1: 教育讲解
├── 测试用例2: 短视频
└── 测试用例3: 纪录片

devlog/daily/2026-07-XX.md  ← 每日日志
```

### 验收标准
- [x] Agent可单独运行
- [x] 输出内容结构符合规范
- [x] 支持多个分类
- [x] 生成质量检查（3个测试用例）
- [x] 异常处理完善
- [x] 性能 < 30秒/请求

### 预计时间
2-3天

### 关键风险
- LLM响应质量不稳定 → 配置prompt，多轮优化
- 内容结构不规范 → JSON Schema验证

---

## Phase 2: 素材检索Agent (3-4天)

### 目标
- 实现MaterialFetchAgent
- 支持多源素材获取（本地+API+降级）
- 实现缓存和质量评分

### 交付物
```
core/agents/material_fetch_agent.py
├── 关键词提取
├── 多源搜索（本地/API）
├── 缓存管理
└── 质量评分

core/utils/material_source.py
├── LocalMaterialSource
├── PexelsSource
├── PixabaySource
└── FallbackSource

test_material_fetch_agent.py
├── 测试用例1: 本地素材
├── 测试用例2: API素材
├── 测试用例3: 缓存命中
└── 测试用例4: 降级方案
```

### 验收标准
- [x] Agent可单独运行
- [x] 支持本地素材检索
- [x] 支持API素材检索（Pexels/Pixabay）
- [x] 缓存命中率 > 80%
- [x] 质量评分算法合理
- [x] 降级方案可用
- [x] 性能 < 60秒/请求

### 预计时间
3-4天

### 关键风险
- API限流 → 实现请求队列和重试
- 素材质量差 → 多轮搜索，用户评分反馈
- 网络不稳定 → 本地缓存优先

---

## Phase 3: 视频合成Agent (4-5天)

### 目标
- 实现VideoComposeAgent
- 支持多种场景渲染
- 集成转场和动效

### 交付物
```
core/agents/video_compose_agent.py
├── 场景渲染器
├── 素材集成
├── 文字叠加
├── 转场管理
└── FFmpeg调用

core/compose/
├── scene_renderer.py
├── text_overlay.py
├── transition_manager.py
└── ffmpeg_wrapper.py

test_video_compose_agent.py
├── 测试用例1: 纯文字卡
├── 测试用例2: 图文混合
├── 测试用例3: 多场景连接
└── 测试用例4: 多素材拼接
```

### 验收标准
- [x] Agent可单独运行
- [x] 支持标题卡渲染
- [x] 支持字幕条渲染
- [x] 支持多素材集成
- [x] 转场效果正常
- [x] 生成视频可播放
- [x] 文字清晰可读
- [x] 性能 < 90秒/30s视频

### 预计时间
4-5天

### 关键风险
- FFmpeg缺失 → 自动检测+错误提示
- 内存溢出 → 分批处理+流式渲染
- 渲染速度慢 → GPU加速（可选）

---

## Phase 4: 主控Agent与集成 (2-3天)

### 目标
- 实现CoordinatorAgent完整逻辑
- 整合三个子Agent
- 实现异常处理和重试

### 交付物
```
core/agents/coordinator_agent.py
├── 需求接收
├── 任务分发
├── 结果汇总
├── 异常处理
└── 重试逻辑

test_integration.py
├── 端到端测试1: 教育讲解完整流程
├── 端到端测试2: 短视频完整流程
├── 端到端测试3: 异常恢复
└── 端到端测试4: 性能压力测试
```

### 验收标准
- [x] 完整流程可正常运行
- [x] 三个子Agent协作正常
- [x] 消息传递无丢失
- [x] 异常处理有效（模拟各种失败）
- [x] 重试机制正常
- [x] 性能 < 3分钟/视频（包含所有环节）
- [x] 端到端测试 4/4 通过

### 预计时间
2-3天

---

## Phase 5: 用户接口与部署 (2-3天)

### 目标
- 实现用户交互接口
- 完善文档和日志
- 性能优化和测试

### 交付物
```
main.py or app.py
├── CLI接口
└── 参数处理

web_api.py (可选)
├── FastAPI接口
└── 请求响应定义

README.md
└── 使用说明

性能报告.md
└── 基准测试结果

test_performance.py
└── 性能测试
```

### 验收标准
- [x] CLI接口可用
- [x] 输入验证完善
- [x] 输出格式清晰
- [x] 文档完整准确
- [x] 日志详细可追踪
- [x] 性能满足需求
- [x] 集成测试全通过

### 预计时间
2-3天

---

## 完整时间线

```
Week 1:
  Mon-Tue   : Phase 0 (框架)
  Wed-Thu   : Phase 1 (内容分析)
  Fri       : Phase 1 review & Phase 2 start

Week 2:
  Mon-Tue   : Phase 2 (素材检索)
  Wed-Thu   : Phase 3 (视频合成) start
  Fri       : Phase 3 continue

Week 3:
  Mon-Tue   : Phase 3 complete
  Wed-Thu   : Phase 4 (集成)
  Fri       : Phase 5 (接口) start

Week 4:
  Mon-Tue   : Phase 5 complete
  Wed       : 性能优化
  Thu-Fri   : 最终测试 & 修复

总计: 3-4周
```

---

## 每日工作流程

### 每天开始
1. 更新 `devlog/daily/YYYY-MM-DD.md`
2. 检查前一天的代码审查意见
3. 明确今天的目标任务

### 每天结束
1. 更新每日日志
   - ✅ 完成事项
   - 📊 数据（测试覆盖率、代码行数等）
   - 🔄 待办事项
   - 🚨 问题和风险

2. 提交代码
   - 清晰的commit message
   - 功能完整的单元测试
   - 代码审查（如有合作者）

### 每周评审
- 周五进行15-30分钟的周评
- 检查是否按计划完成
- 识别风险和问题
- 调整下周计划

---

## 质量关卡

### 代码关卡
- [x] 单元测试通过率 ≥ 95%
- [x] 代码注释完善
- [x] 没有重大代码异味
- [x] 日志覆盖关键流程

### 功能关卡
- [x] 需求验收标准全通过
- [x] 集成测试通过
- [x] 异常场景验证

### 性能关卡
- [x] 响应时间符合要求
- [x] 内存占用正常
- [x] 无内存泄漏

---

## 风险应对

| 风险 | 触发条件 | 应对方案 |
|------|---------|--------|
| Phase延期 | 进度<50% | 降低该Phase范围，迁移到后续Phase |
| 质量不达标 | 测试覆盖<80% | 暂停，专注修复和完善测试 |
| 性能瓶颈 | 响应时间>目标2倍 | 分析瓶颈，采用缓存或异步优化 |
| 依赖问题 | 库版本不兼容 | 更换备选库或降级需求 |

---

*最后更新: 2026-07-21*
*计划版本: 1.0*
