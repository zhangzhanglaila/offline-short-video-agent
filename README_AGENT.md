# 🎬 AI短视频自动生成系统 (Agent版)

输入一句需求，自动生成配真实素材和文字字幕的短视频。

基于**多Agent协作架构**：主控Agent通过消息总线编排内容分析、
素材检索、视频合成三个子Agent，完成"需求 → 视频"的全自动流程。

---

## ✨ 特性

- 📝 **智能内容分析**: LLM(DeepSeek/Ollama)将需求拆解为分镜脚本
- 🖼️ **真实素材检索**: 自动从Pexels/Pixabay/Unsplash匹配高清配图
- 🎨 **素材+文字配合**: 内容场景=素材背景+底部字幕条，讲解清晰
- 🎞️ **视频合成**: FFmpeg合成含转场的竖屏/横屏视频
- 🛡️ **三级容错**: 每个环节都有降级方案，保证始终有输出
- 🎭 **5种视觉风格**: 极简/活力/电影/科技/漫画

---

## 🚀 快速开始

### 1. 配置API密钥

复制并编辑 `.env`（不会被git跟踪）：

```bash
# 云端LLM (DeepSeek示例)
OPENAI_API_KEY=sk-your-deepseek-key
OPENAI_API_BASE=https://api.deepseek.com/v1
OPENAI_API_MODEL=deepseek-chat

# 素材API (至少配一个)
PEXELS_API_KEY=your-pexels-key
UNSPLASH_ACCESS_KEY=your-unsplash-key
```

> 无LLM时自动降级为规则生成；无素材API时用渐变背景占位。

### 2. 生成视频

**命令行模式：**
```bash
python generate_video.py \
  --input "讲解什么是机器学习" \
  --category 教育讲解 \
  --style tech \
  --duration 30
```

**交互式模式：**
```bash
python generate_video.py
# 按提示输入需求、选择分类/风格/时长
```

### 3. 查看结果

生成的视频默认保存在 `output/agent_videos/`，
或用 `--output path/to/video.mp4` 指定路径。

---

## 📖 参数说明

| 参数 | 简写 | 说明 | 可选值 |
|------|------|------|--------|
| `--input` | `-i` | 视频内容需求 | 任意文本 |
| `--category` | `-c` | 视频分类 | 教育讲解/短视频/纪录片/商业宣传 |
| `--style` | `-s` | 视觉风格 | minimal/vibrant/cinematic/tech/manga |
| `--duration` | `-d` | 时长(秒) | 5-300 |
| `--output` | `-o` | 输出路径 | 文件路径 |
| `--horizontal` | | 横屏1920x1080 | (默认竖屏) |

---

## 🏗️ 系统架构

```
用户需求
   ↓
主控Agent (Coordinator)
   ├─ 通过MessageBus下发任务
   ├─ 超时/重试/降级
   └─ 汇总VideoResult
   ↓
┌────────────┬────────────┬────────────┐
│ 内容分析   │ 素材检索   │ 视频合成   │
│ Agent      │ Agent      │ Agent      │
│ LLM分镜    │ 多源检索   │ 渲染+FFmpeg│
└────────────┴────────────┴────────────┘
```

详见 `docs/01-architecture-design.md`。

### 场景类型

| 类型 | 画面 | 用途 |
|------|------|------|
| `title_card` | 整屏大字+装饰线 | 开头点题 |
| `content` | 素材背景+底部字幕条 | 讲解主体 |
| `conclusion` | 整屏文字 | 结尾总结 |

---

## 🧩 编程接口

```python
import asyncio
from core.agents import CoordinatorAgent
from core.agents.message_bus import MessageBus
from core.models import UserRequest

async def main():
    coordinator = CoordinatorAgent(bus=MessageBus())
    request = UserRequest(
        user_input="讲解Redis为什么快",
        category="教育讲解",
        style="tech",
        duration=30,
    )
    result = await coordinator.process_request(request)
    print(result.get_summary())

asyncio.run(main())
```

---

## 📂 目录结构

```
core/
├── agents/           # Agent实现
│   ├── coordinator_agent.py     # 主控
│   ├── content_analysis_agent.py
│   ├── material_fetch_agent.py
│   ├── video_compose_agent.py
│   ├── base_agent.py
│   └── message_bus.py
├── models/           # 数据契约
│   ├── message.py / request.py / result.py
│   ├── content.py    # ContentStructure
│   └── material.py   # MaterialAsset
└── compose/          # 合成
    ├── scene_image_renderer.py  # PIL渲染
    └── ffmpeg_composer.py       # FFmpeg合成

generate_video.py     # CLI入口
docs/                 # 需求/架构/规范文档
devlog/               # 开发日志
```

---

## 🧪 测试

```bash
# 离线测试（快速，无需网络）
python -m pytest test_*.py -k "not Real and not real" -q

# 全部测试（含真实API冒烟）
python -m pytest test_*.py -q
```

---

## ⚙️ 依赖

- Python 3.10+
- FFmpeg (视频合成)
- Pillow (图像渲染)
- requests, python-dotenv

---

## 📋 已知局限

- 内容场景为静态素材（暂无Ken Burns动效）
- 暂无TTS旁白和背景音乐（narration字段已预留）
- 字幕整段显示（暂无逐句时间轴对齐）

---

*基于多Agent架构 | 详细开发记录见 devlog/*
