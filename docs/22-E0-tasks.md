# E0 阶段：基础设施准备

**阶段目标**: 建立规范的目录结构、文档体系、开发日志和工作标准，为后续开发奠定坚实基础。

**预计周期**: 3-5 天

**状态**: 🔄 进行中

---

## 📋 本阶段任务清单

### 1. 目录结构规范
- [ ] 创建 `templates/` 目录（按分辨率分类）
- [ ] 创建 `workflows/` 目录（存放 TTS/图像/视频工作流配置）
- [ ] 创建 `services/` 目录（新增服务层）
- [ ] 规范 `docs/` 子目录结构
- [ ] 确认 `devlog/daily/` 日志模板

### 2. 文档体系完善
- [ ] 创建 `docs/20-architecture-v2.md`（新架构设计）
- [ ] 创建 `docs/21-phase-E-plan.md`（E 系列阶段总规划）
- [ ] 创建 `docs/22-E0-tasks.md`（E0 详细任务）
- [ ] 创建 `docs/23-E1-templates.md`（E1 模板系统设计）
- [ ] 创建 `docs/24-E2-ai-image.md`（E2 AI 生图设计）
- [ ] 创建 `docs/25-E3-ai-video.md`（E3 AI 生视频设计）
- [ ] 创建 `docs/26-E4-history-ui.md`（E4 历史管理 UI 设计）
- [ ] 创建 `docs/27-E5-comfyui.md`（E5 ComfyUI 集成设计）

### 3. 开发日志体系
- [ ] 确认 `devlog/daily/YYYY-MM-DD.md` 模板格式
- [ ] 创建今日日志 `devlog/daily/2026-07-24.md`
- [ ] 建立每日完成/待办记录规范

### 4. CLAUDE.md 更新
- [ ] 添加新阶段（E 系列）指引
- [ ] 添加文档路径索引
- [ ] 添加工作说明

### 5. 测试环境验证
- [ ] 确认所有单元测试可运行
- [ ] 确认前端构建环境正常
- [ ] 确认后端 API 可启动

---

## 📂 目标目录结构

```
Offline-ShortVideo-Agent/
├── templates/                    # 新增：视频模板系统
│   ├── 1080x1920/               # 竖屏 9:16
│   ├── 1920x1080/               # 横屏 16:9
│   └── 1080x1080/               # 方形 1:1
├── workflows/                    # 新增：AI 工作流配置
│   ├── tts/                     # TTS 工作流
│   ├── image/                   # 图像生成工作流
│   └── video/                   # 视频生成工作流
├── services/                     # 新增/扩展：服务层
│   ├── template_service.py      # 模板渲染服务
│   ├── ai_media_service.py      # AI 媒体生成服务
│   └── history_service.py       # 历史记录服务
├── docs/
│   ├── 00-requirement-spec.md
│   ├── 01-architecture-design.md
│   ├── 02-development-phases.md  # 原 Phase 0-5
│   ├── 03-coding-standards.md
│   ├── 10-dynamic-requirements.md
│   ├── 11-dynamic-design.md
│   ├── 12-dynamic-phases.md      # 原 D1-D6
│   ├── 20-architecture-v2.md    # 新增：新架构设计
│   ├── 21-phase-E-plan.md       # 新增：E 系列总规划
│   ├── 22-E0-tasks.md           # 新增：E0 详细任务
│   ├── 23-E1-templates.md        # 新增：E1 模板系统
│   ├── 24-E2-ai-image.md        # 新增：E2 AI 生图
│   ├── 25-E3-ai-video.md        # 新增：E3 AI 生视频
│   ├── 26-E4-history-ui.md      # 新增：E4 历史管理
│   └── 27-E5-comfyui.md         # 新增：E5 ComfyUI
├── devlog/
│   ├── daily/                   # 每日日志
│   │   ├── 2026-07-24.md
│   │   └── ...
│   ├── phase-E0-summary.md      # E0 总结
│   ├── phase-E1-summary.md      # E1 总结
│   └── ...
├── frontend/                     # React 前端（保持）
├── api/                         # FastAPI 后端（保持）
└── core/                        # 核心逻辑（保持）
```

---

## ✅ 验收标准

1. 所有新增目录已创建并包含 README 说明
2. 所有新增文档已创建并包含必要内容
3. `CLAUDE.md` 已更新包含新阶段指引
4. 今日日志已创建并记录今日工作
5. 所有测试可正常运行
6. 前端可正常构建启动

---

## 📝 本阶段输出

- 目录结构：`templates/`、`workflows/`、`services/`
- 文档：`docs/20-27.md`
- 日志：`devlog/daily/2026-07-24.md`
- 更新：`CLAUDE.md`

---

*创建时间: 2026-07-24*
