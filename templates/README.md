# Templates 目录

视频模板系统，按分辨率分类。

## 目录结构

```
templates/
├── 1080x1920/    # 竖屏 9:16（抖音/小红书）
├── 1920x1080/    # 横屏 16:9（B站/YouTube）
└── 1080x1080/    # 方形 1:1（Instagram）
```

## 模板命名规范

- `image_*.html` — 使用 AI 生图或真实图片作为背景
- `video_*.html` — 使用 AI 生视频或真实视频作为背景
- `static_*.html` — 纯文字样式，无需媒体资源

## 使用方式

模板通过 `services/template_service.py` 加载和渲染。

## 添加新模板

1. 将 HTML 文件放入对应分辨率目录
2. 添加预览缩略图（300x500px）
3. 在模板中添加元数据注释

模板元数据示例：
```html
<!--
Template: 现代风格
Type: image
Style: modern
Author: System
-->
```
