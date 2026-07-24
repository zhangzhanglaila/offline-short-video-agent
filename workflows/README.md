# Workflows 目录

AI 工作流配置，用于 ComfyUI 集成。

## 目录结构

```
workflows/
├── tts/        # 文字转语音工作流
├── image/      # AI 生图工作流
└── video/      # AI 生视频工作流
```

## 工作流格式

JSON 格式，使用 Jinja2 模板语法支持参数替换。

## 示例

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

## 使用方式

工作流通过 `services/comfyui_service.py` 加载和执行。

## 添加新工作流

1. 将 JSON 文件放入对应类型目录
2. 使用 `{{variable}}` 语法定义可替换参数
3. 在配置文件中注册
