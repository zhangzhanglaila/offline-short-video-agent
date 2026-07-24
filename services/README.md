# Services 目录

服务层，新增的高级功能服务。

## 目录结构

```
services/
├── template/     # 模板渲染服务
├── ai_media/     # AI 生图/生视频服务
└── history/      # 历史记录管理服务
```

## 各服务说明

### template/
模板渲染服务，负责加载、解析、渲染 HTML 模板。

### ai_media/
AI 媒体生成服务，支持多个供应商（OpenAI/DashScope/Kling/ComfyUI）。

### history/
历史记录服务，管理视频生成记录和任务状态。

## 使用方式

各服务通过 FastAPI 路由暴露给前端调用。
