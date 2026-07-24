# 模板渲染引擎使用指南

## 快速开始

```python
import asyncio
from pathlib import Path
from services.template import TemplateRenderer

async def main():
    renderer = TemplateRenderer()
    try:
        output = await renderer.render(
            template_name="image_default",
            context={
                "title": "Python异步编程",
                "image": "path/to/image.jpg",
                "text": "异步编程是...",
            },
            output_path=Path("output/scene1.png"),
        )
        print(f"Rendered: {output}")
    finally:
        await renderer.close()

asyncio.run(main())
```

## 模板查询

```python
from services.template import TemplateRegistry

registry = TemplateRegistry()
registry.scan()

# 列出所有模板
for t in registry._cache.values():
    print(f"{t.name}: {t.aspect_ratio} ({t.template_type})")

# 按画幅筛选
portrait = registry.list_by_aspect("1080x1920")

# 按类型筛选
image_templates = registry.list_by_type("image")
```

## 降级渲染

```python
async def pil_fallback(output_path):
    """PIL 降级渲染（保证输出）"""
    from PIL import Image
    img = Image.new("RGB", (1080, 1920), "#fafafa")
    img.save(output_path)
    return output_path

output = await renderer.render_with_fallback(
    template_name="image_default",
    context={...},
    output_path=Path("output.png"),
    fallback_func=pil_fallback,
)
```

## 可用模板

详见 `templates/README.md`