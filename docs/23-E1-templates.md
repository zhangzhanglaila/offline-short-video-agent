# E1 阶段：模板系统

**阶段目标**: 迁移全部 HTML 模板并建立模板渲染系统。

**预计周期**: 4 周

**状态**: ⏳ 待开始

---

## 模板清单（共 25+ 个）

### 1080x1920（竖屏 9:16）

| 模板文件 | 类型 | 风格描述 |
|---------|------|---------|
| `image_default.html` | 图像 | 默认样式 |
| `image_modern.html` | 图像 | 现代风格 |
| `image_elegant.html` | 图像 | 优雅风格 |
| `image_neon.html` | 图像 | 霓虹风格 |
| `image_blur_card.html` | 图像 | 模糊卡片 |
| `image_book.html` | 图像 | 书籍风格 |
| `image_cartoon.html` | 图像 | 卡通风格 |
| `image_excerpt.html` | 图像 | 摘录风格 |
| `image_fashion_vintage.html` | 图像 | 复古时尚 |
| `image_full.html` | 图像 | 全屏 |
| `image_healing.html` | 图像 | 治愈风格 |
| `image_health_preservation.html` | 图像 | 养生风格 |
| `image_life_insights.html` | 图像 | 人生感悟 |
| `image_life_insights_light.html` | 图像 | 清新人生感悟 |
| `image_long_text.html` | 图像 | 长文本 |
| `image_psychology_card.html` | 图像 | 心理卡片 |
| `image_purple.html` | 图像 | 紫色主题 |
| `image_satirical_cartoon.html` | 图像 | 讽刺漫画 |
| `image_simple_black.html` | 图像 | 简约黑色 |
| `image_simple_line_drawing.html` | 图像 | 简约线条 |
| `static_default.html` | 静态 | 默认静态 |
| `static_excerpt.html` | 静态 | 摘录静态 |
| `video_default.html` | 视频 | 默认视频 |
| `video_healing.html` | 视频 | 治愈视频 |
| `asset_default.html` | 素材 | 默认素材 |

### 1920x1080（横屏 16:9）

| 模板文件 | 类型 | 风格描述 |
|---------|------|---------|
| `image_film.html` | 图像 | 电影风格 |
| `image_full.html` | 图像 | 全屏 |

### 1080x1080（方形 1:1）

| 模板文件 | 类型 | 风格描述 |
|---------|------|---------|
| `image_minimal_framed.html` | 图像 | 极简框式 |

---

## 开发计划

### Week 1: 模板迁移

**任务**:
- [ ] 从源复制所有 HTML 文件到 `templates/` 对应目录
- [ ] 为每个模板创建预览缩略图（300x500px）
- [ ] 创建 `templates/README.md` 说明文件
- [ ] 验证所有模板文件完整性

**输出**:
- `templates/` 完整结构
- 每个模板的预览缩略图

### Week 2: 模板渲染引擎

**任务**:
- [ ] 创建 `services/template_service.py`
- [ ] 实现模板参数解析（支持 Jinja2 变量）
- [ ] 实现模板渲染函数
- [ ] 集成到 `core/compose/scene_image_renderer.py`

**核心接口**:
```python
class TemplateService:
    def list_templates(self, aspect_ratio: str) -> List[TemplateInfo]
    def render_template(self, template_path: str, context: dict) -> Image
    def get_template_preview(self, template_path: str) -> str
```

### Week 3: 前端模板选择器

**任务**:
- [ ] 创建 `frontend/src/pages/TemplateGallery.tsx`
- [ ] 实现模板网格展示
- [ ] 实现模板筛选（按尺寸/类型/风格）
- [ ] 实现模板预览弹窗
- [ ] 集成到 `GenerateVideo` 页面

### Week 4: 测试与文档

**任务**:
- [ ] 完整测试每个模板渲染
- [ ] 编写模板使用文档
- [ ] 创建模板效果图画廊
- [ ] E1 阶段总结

---

## 模板参数规范

每个模板应支持以下标准参数：

```python
{
    "title": "场景标题",
    "narration": "旁白文本",
    "image_path": "背景图片路径",
    "duration": "时长（秒）",
    "aspect_ratio": "画幅比例",
    "style_params": {
        # 模板特定参数
    }
}
```

---

## 兼容性

- 现有场景类型（`title_card`/`content`/`conclusion`）保持兼容
- 模板作为可选的高级功能
- 默认行为不变

---

*创建时间: 2026-07-24*
