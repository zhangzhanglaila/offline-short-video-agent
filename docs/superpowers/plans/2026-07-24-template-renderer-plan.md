# E1 Week 2: 模板渲染引擎 - 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 HTML 模板渲染引擎，让 31 个已迁移的 HTML 模板能通过 Playwright 输出为 PNG 帧，集成到现有视频生成流程。

**Architecture:** 单例 BrowserManager + TemplateRegistry 索引 + HTMLFrameGenerator 单帧生成 + TemplateRenderer 主入口（带 PIL 降级）。

**Tech Stack:** Python 3.10+, Playwright (已安装), Jinja2 (已安装), PIL (Pillow, 已安装), pytest

---

## Global Constraints

- Python 3.10+（项目最低版本）
- 必须在 `D:\Offline-ShortVideo-Agent` 工作目录下执行
- 所有新代码必须有单元测试
- 每个 Task 完成后立即提交 git commit
- 模板渲染失败必须降级到 PIL（不能直接抛错）
- BrowserManager 单例同步（不并发）
- 文件路径使用 `pathlib.Path`，不用字符串拼接
- 类型提示完整（Python 3.10+ 风格）

---

## Task 1: 创建模块骨架与异常定义

**Files:**
- Create: `services/__init__.py`
- Create: `services/template/__init__.py`
- Create: `services/template/exceptions.py`
- Create: `tests/__init__.py`
- Create: `tests/template/__init__.py`

**Interfaces:**
- Produces: `services.template.exceptions.TemplateNotFoundError`
- Produces: `services.template.exceptions.TemplateRenderError`
- Produces: `services.template.exceptions.BrowserNotAvailableError`

- [ ] **Step 1: 创建 `services/__init__.py`**

```python
"""服务层：高级功能服务模块"""
```

- [ ] **Step 2: 创建 `services/template/__init__.py`**

```python
"""模板渲染服务模块"""

from .renderer import TemplateRenderer
from .registry import TemplateRegistry
from .models import TemplateInfo

__all__ = ["TemplateRenderer", "TemplateRegistry", "TemplateInfo"]
```

- [ ] **Step 3: 创建 `services/template/exceptions.py`**

```python
"""模板渲染相关异常"""


class TemplateError(Exception):
    """模板系统基础异常"""
    pass


class TemplateNotFoundError(TemplateError):
    """模板不存在"""
    pass


class TemplateRenderError(TemplateError):
    """模板渲染失败"""
    pass


class BrowserNotAvailableError(TemplateError):
    """浏览器不可用"""
    pass
```

- [ ] **Step 4: 创建测试目录 `tests/__init__.py` 和 `tests/template/__init__.py`**

```python
# tests/__init__.py
"""测试模块根"""
```

```python
# tests/template/__init__.py
"""模板渲染服务测试"""
```

- [ ] **Step 5: 验证目录结构**

```bash
cd D:/Offline-ShortVideo-Agent && find services tests -type f -name "*.py" | sort
```

Expected:
```
services/__init__.py
services/template/__init__.py
services/template/exceptions.py
tests/__init__.py
tests/template/__init__.py
```

- [ ] **Step 6: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add services/ tests/ && git commit -m "feat(template): create module skeleton and exceptions"
```

---

## Task 2: 实现 TemplateInfo 数据模型

**Files:**
- Create: `services/template/models.py`
- Test: `tests/template/test_models.py`

**Interfaces:**
- Produces: `services.template.models.TemplateInfo`

- [ ] **Step 1: 写失败的测试 `tests/template/test_models.py`**

```python
"""TemplateInfo 数据模型测试"""
from pathlib import Path
from services.template.models import TemplateInfo


def test_template_info_basic():
    """测试基本字段"""
    info = TemplateInfo(
        name="image_default",
        path=Path("templates/1080x1920/image_default.html"),
        aspect_ratio="1080x1920",
        width=1080,
        height=1920,
        template_type="image",
        style="default",
        parameters=["title", "text", "image"],
    )
    assert info.name == "image_default"
    assert info.width == 1080
    assert info.height == 1920
    assert "title" in info.parameters


def test_template_info_aspect_to_size():
    """测试画幅解析：1080x1920 → (1080, 1920)"""
    info = TemplateInfo.from_aspect(
        name="test",
        path=Path("test.html"),
        aspect_ratio="1080x1920",
        template_type="image",
        style="default",
    )
    assert info.width == 1080
    assert info.height == 1920
    assert info.aspect_ratio == "1080x1920"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_models.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'services.template.models'"

- [ ] **Step 3: 实现 `services/template/models.py`**

```python
"""模板数据模型"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class TemplateInfo:
    """模板信息数据类"""

    name: str
    path: Path
    aspect_ratio: str
    width: int
    height: int
    template_type: str  # image / static / video / asset
    style: str
    parameters: List[str] = field(default_factory=list)

    @classmethod
    def from_aspect(
        cls,
        name: str,
        path: Path,
        aspect_ratio: str,
        template_type: str,
        style: str,
        parameters: List[str] = None,
    ) -> "TemplateInfo":
        """从画幅字符串创建，自动解析宽高"""
        parts = aspect_ratio.split("x")
        width = int(parts[0])
        height = int(parts[1])
        return cls(
            name=name,
            path=path,
            aspect_ratio=aspect_ratio,
            width=width,
            height=height,
            template_type=template_type,
            style=style,
            parameters=parameters or [],
        )
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_models.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 5: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add services/template/models.py tests/template/test_models.py && git commit -m "feat(template): add TemplateInfo data model"
```

---

## Task 3: 实现 TemplateRegistry（模板扫描）

**Files:**
- Create: `services/template/registry.py`
- Test: `tests/template/test_registry.py`

**Interfaces:**
- Produces: `services.template.registry.TemplateRegistry`
- Consumes: `services.template.models.TemplateInfo`
- Consumes: `services.template.exceptions.TemplateNotFoundError`

- [ ] **Step 1: 写失败的测试 `tests/template/test_registry.py`**

```python
"""TemplateRegistry 测试"""
import os
import tempfile
from pathlib import Path
from services.template.registry import TemplateRegistry


def test_scan_templates():
    """测试扫描模板目录"""
    with tempfile.TemporaryDirectory() as tmp:
        # 创建测试模板结构
        tmp_path = Path(tmp)
        (tmp_path / "1080x1920").mkdir()
        (tmp_path / "1080x1920" / "image_default.html").write_text("<html></html>")
        (tmp_path / "1080x1920" / "image_modern.html").write_text("<html></html>")
        (tmp_path / "1920x1080").mkdir()
        (tmp_path / "1920x1080" / "image_film.html").write_text("<html></html>")

        registry = TemplateRegistry(templates_dir=tmp_path)
        templates = registry.scan()

        assert len(templates) == 3
        names = {t.name for t in templates}
        assert names == {"image_default", "image_modern", "image_film"}


def test_get_template():
    """测试获取指定模板"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "1080x1920").mkdir()
        (tmp_path / "1080x1920" / "image_default.html").write_text("<html></html>")

        registry = TemplateRegistry(templates_dir=tmp_path)
        registry.scan()
        template = registry.get("image_default")

        assert template.name == "image_default"
        assert template.width == 1080
        assert template.height == 1920


def test_get_nonexistent_raises():
    """测试不存在的模板抛出异常"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "1080x1920").mkdir()

        registry = TemplateRegistry(templates_dir=tmp_path)
        registry.scan()

        from services.template.exceptions import TemplateNotFoundError
        import pytest

        with pytest.raises(TemplateNotFoundError):
            registry.get("nonexistent")


def test_list_by_aspect():
    """测试按画幅筛选"""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "1080x1920").mkdir()
        (tmp_path / "1920x1080").mkdir()
        (tmp_path / "1080x1920" / "image_default.html").write_text("")
        (tmp_path / "1920x1080" / "image_film.html").write_text("")

        registry = TemplateRegistry(templates_dir=tmp_path)
        registry.scan()
        portrait = registry.list_by_aspect("1080x1920")

        assert len(portrait) == 1
        assert portrait[0].name == "image_default"
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_registry.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'services.template.registry'"

- [ ] **Step 3: 实现 `services/template/registry.py`**

```python
"""模板注册表：扫描、索引、查询"""
import re
from pathlib import Path
from typing import Dict, List

from .exceptions import TemplateNotFoundError
from .models import TemplateInfo


# 模板元数据正则
META_REGEX = re.compile(
    r'<meta\s+name="template:(\w+)"\s+content="([^"]+)"\s*/?>'
)


class TemplateRegistry:
    """模板注册表"""

    def __init__(self, templates_dir: Path = Path("templates")):
        self.templates_dir = templates_dir
        self._cache: Dict[str, TemplateInfo] = {}

    def scan(self) -> List[TemplateInfo]:
        """扫描 templates_dir 下所有 HTML 模板"""
        self._cache.clear()

        if not self.templates_dir.exists():
            return []

        # 支持的画幅目录
        for aspect_dir in self.templates_dir.iterdir():
            if not aspect_dir.is_dir():
                continue
            aspect_ratio = aspect_dir.name
            if "x" not in aspect_ratio:
                continue

            # 扫描该画幅下的所有 HTML
            for html_file in aspect_dir.glob("*.html"):
                info = self._parse_template(html_file, aspect_ratio)
                self._cache[info.name] = info

        return list(self._cache.values())

    def get(self, name: str) -> TemplateInfo:
        """根据模板名称获取信息"""
        if name not in self._cache:
            raise TemplateNotFoundError(f"Template not found: {name}")
        return self._cache[name]

    def list_by_aspect(self, aspect: str) -> List[TemplateInfo]:
        """按画幅筛选"""
        return [t for t in self._cache.values() if t.aspect_ratio == aspect]

    def list_by_type(self, template_type: str) -> List[TemplateInfo]:
        """按类型筛选"""
        return [t for t in self._cache.values() if t.template_type == template_type]

    def _parse_template(self, path: Path, aspect_ratio: str) -> TemplateInfo:
        """解析单个模板文件"""
        content = path.read_text(encoding="utf-8")

        # 默认值
        template_type = "image"
        style = "default"
        parameters = []

        # 解析元数据
        for match in META_REGEX.finditer(content):
            key, value = match.group(1), match.group(2)
            if key == "type":
                template_type = value
            elif key == "style":
                style = value

        # 提取 {{var}} 参数
        param_pattern = re.compile(r"\{\{(\w+)\}\}")
        parameters = list(set(param_pattern.findall(content)))

        # 从文件名推断模板类型
        name = path.stem
        if name.startswith("video_"):
            template_type = "video"
        elif name.startswith("static_"):
            template_type = "static"
        elif name.startswith("asset_"):
            template_type = "asset"

        return TemplateInfo.from_aspect(
            name=name,
            path=path,
            aspect_ratio=aspect_ratio,
            template_type=template_type,
            style=style,
            parameters=parameters,
        )
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_registry.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: 对真实模板目录验证**

```bash
cd D:/Offline-ShortVideo-Agent && python -c "
from services.template.registry import TemplateRegistry
reg = TemplateRegistry()
templates = reg.scan()
print(f'Found {len(templates)} templates')
for t in templates[:3]:
    print(f'  - {t.name}: {t.aspect_ratio} ({t.template_type})')
"
```

Expected:
```
Found 31 templates
  - asset_default: 1080x1920 (asset)
  - image_default: 1080x1920 (image)
  - image_modern: 1080x1920 (image)
```

- [ ] **Step 6: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add services/template/registry.py tests/template/test_registry.py && git commit -m "feat(template): implement TemplateRegistry with scan and query"
```

---

## Task 4: 实现 BrowserManager（Playwright 单例）

**Files:**
- Create: `services/template/browser.py`
- Test: `tests/template/test_browser.py`

**Interfaces:**
- Produces: `services.template.browser.BrowserManager`

- [ ] **Step 1: 写失败的测试 `tests/template/test_browser.py`**

```python
"""BrowserManager 测试"""
import asyncio
from services.template.browser import BrowserManager


def test_browser_manager_singleton():
    """测试单例模式"""
    m1 = BrowserManager()
    m2 = BrowserManager()
    assert m1 is m2


def test_browser_manager_initial_state():
    """测试初始状态"""
    m = BrowserManager()
    assert m._browser is None
    assert m._playwright is None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_browser.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 实现 `services/template/browser.py`**

```python
"""Playwright 浏览器单例管理"""
from typing import Optional

from playwright.async_api import Browser, Playwright, async_playwright

from .exceptions import BrowserNotAvailableError


class BrowserManager:
    """Playwright 浏览器单例（同步使用，不并发）"""

    _instance: Optional["BrowserManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    async def get_browser(self) -> Browser:
        """获取浏览器实例（懒初始化）"""
        if self._browser is None or not self._browser.is_connected():
            await self._start_browser()
        return self._browser

    async def _start_browser(self):
        """启动 Playwright"""
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        except Exception as e:
            raise BrowserNotAvailableError(f"Failed to start browser: {e}")

    async def close(self):
        """关闭浏览器"""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_browser.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 5: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add services/template/browser.py tests/template/test_browser.py && git commit -m "feat(template): add BrowserManager singleton"
```

---

## Task 5: 实现 HTMLFrameGenerator（单帧生成）

**Files:**
- Create: `services/template/html_generator.py`
- Test: `tests/template/test_html_generator.py`

**Interfaces:**
- Produces: `services.template.html_generator.HTMLFrameGenerator`
- Consumes: `services.template.models.TemplateInfo`
- Consumes: `services.template.browser.BrowserManager`

- [ ] **Step 1: 写失败的测试 `tests/template/test_html_generator.py`**

```python
"""HTMLFrameGenerator 测试"""
import asyncio
from pathlib import Path

from services.template.html_generator import HTMLFrameGenerator
from services.template.models import TemplateInfo


def create_test_template(tmp: Path) -> TemplateInfo:
    """创建测试模板"""
    html_content = """
    <html>
    <head><style>body { background: #fafafa; }</style></head>
    <body>
        <h1>{{title}}</h1>
        <p>{{text}}</p>
    </body>
    </html>
    """
    template_file = tmp / "test.html"
    template_file.write_text(html_content, encoding="utf-8")

    return TemplateInfo(
        name="test",
        path=template_file,
        aspect_ratio="1080x1920",
        width=1080,
        height=1920,
        template_type="static",
        style="default",
        parameters=["title", "text"],
    )


def test_extract_parameters():
    """测试参数提取"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        info = create_test_template(Path(tmp))
        gen = HTMLFrameGenerator(info)
        params = gen.extract_parameters()
        assert "title" in params
        assert "text" in params


def test_render_jinja():
    """测试 Jinja2 渲染"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        info = create_test_template(Path(tmp))
        gen = HTMLFrameGenerator(info)
        html = gen.render_jinja({"title": "Hello", "text": "World"})
        assert "Hello" in html
        assert "World" in html
        assert "{{title}}" not in html


def test_generate_frame():
    """测试完整渲染流程（需要 Playwright）"""
    import tempfile

    async def _run():
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            info = create_test_template(tmp_path)
            output = tmp_path / "output.png"

            gen = HTMLFrameGenerator(info)
            result = await gen.generate_frame(
                context={"title": "Test", "text": "Hello"},
                output_path=output,
            )
            assert result.exists()
            assert result.suffix == ".png"
            assert result.stat().st_size > 0

    asyncio.run(_run())
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_html_generator.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 实现 `services/template/html_generator.py`**

```python
"""HTML → PNG 单帧生成器"""
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Template

from .browser import BrowserManager
from .exceptions import TemplateRenderError
from .models import TemplateInfo


class HTMLFrameGenerator:
    """HTML 模板 → PNG 单帧生成"""

    PARAM_PATTERN = re.compile(r"\{\{(\w+)\}\}")

    def __init__(self, template_info: TemplateInfo):
        self.template_info = template_info
        self.template_html = template_info.path.read_text(encoding="utf-8")

    def extract_parameters(self) -> List[str]:
        """提取模板中的 {{var}} 参数"""
        return list(set(self.PARAM_PATTERN.findall(self.template_html)))

    def render_jinja(self, context: Dict[str, Any]) -> str:
        """用 Jinja2 渲染 HTML"""
        try:
            tmpl = Template(self.template_html)
            return tmpl.render(**context)
        except Exception as e:
            raise TemplateRenderError(f"Jinja2 render failed: {e}")

    async def generate_frame(
        self,
        context: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> Path:
        """生成单帧 PNG"""
        rendered_html = self.render_jinja(context)
        return await self._screenshot(rendered_html, output_path)

    async def _screenshot(self, html: str, output_path: Optional[Path]) -> Path:
        """用 Playwright 截图"""
        browser_manager = BrowserManager()
        browser = await browser_manager.get_browser()

        page = await browser.new_page()
        try:
            await page.set_viewport_size(
                {
                    "width": self.template_info.width,
                    "height": self.template_info.height,
                }
            )
            await page.set_content(html, wait_until="load")
            # 等待字体和 CSS 加载
            await page.wait_for_timeout(500)

            if output_path is None:
                output_path = Path(f"output/frame_{self.template_info.name}.png")

            output_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(
                path=str(output_path),
                full_page=False,
            )
            return output_path
        except Exception as e:
            raise TemplateRenderError(f"Screenshot failed: {e}")
        finally:
            await page.close()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_html_generator.py -v
```

Expected: PASS (3 tests) — 如果 Playwright 浏览器未安装，会在 test_generate_frame 失败，需要先 `playwright install chromium`

- [ ] **Step 5: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add services/template/html_generator.py tests/template/test_html_generator.py && git commit -m "feat(template): implement HTMLFrameGenerator for single frame"
```

---

## Task 6: 实现 TemplateRenderer（主入口 + 降级）

**Files:**
- Create: `services/template/renderer.py`
- Test: `tests/template/test_renderer.py`

**Interfaces:**
- Produces: `services.template.renderer.TemplateRenderer`
- Consumes: `services.template.registry.TemplateRegistry`
- Consumes: `services.template.html_generator.HTMLFrameGenerator`
- Consumes: `services.template.browser.BrowserManager`

- [ ] **Step 1: 写失败的测试 `tests/template/test_renderer.py`**

```python
"""TemplateRenderer 测试"""
import asyncio
from pathlib import Path

from services.template.renderer import TemplateRenderer


def test_renderer_init():
    """测试初始化"""
    r = TemplateRenderer()
    assert r.registry is not None
    assert r.browser_manager is not None


def test_render_with_fallback_to_pil():
    """测试降级到 PIL 渲染（使用不存在模板触发降级）"""
    async def _run():
        with tempfile.TemporaryDirectory() as tmp:
            r = TemplateRenderer(templates_dir=Path(tmp))
            r.registry.scan()

            # 用不存在的模板测试降级路径
            from services.template.exceptions import TemplateNotFoundError
            import pytest
            with pytest.raises(TemplateNotFoundError):
                # 这里测的是没有降级的情况
                await r.render("nonexistent", {}, Path(tmp) / "out.png")

    import tempfile
    asyncio.run(_run())
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_renderer.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 实现 `services/template/renderer.py`**

```python
"""模板渲染引擎主入口"""
from pathlib import Path
from typing import Any, Dict, Optional

from .browser import BrowserManager
from .exceptions import TemplateNotFoundError, TemplateRenderError
from .html_generator import HTMLFrameGenerator
from .registry import TemplateRegistry


class TemplateRenderer:
    """模板渲染引擎主类"""

    def __init__(self, templates_dir: Path = Path("templates")):
        self.registry = TemplateRegistry(templates_dir)
        self.registry.scan()
        self.browser_manager = BrowserManager()

    async def render(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> Path:
        """渲染指定模板为 PNG（不带降级）"""
        info = self.registry.get(template_name)  # 触发 TemplateNotFoundError
        generator = HTMLFrameGenerator(info)
        return await generator.generate_frame(context, output_path)

    async def render_with_fallback(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: Optional[Path] = None,
        fallback_func=None,
    ) -> Path:
        """渲染模板，失败时调用 fallback_func

        Args:
            template_name: 模板名称
            context: 模板参数
            output_path: 输出路径
            fallback_func: 降级函数 async (output_path) -> Path
        """
        try:
            return await self.render(template_name, context, output_path)
        except (TemplateNotFoundError, TemplateRenderError) as e:
            if fallback_func is None:
                raise
            if output_path is None:
                output_path = Path(f"output/fallback_{template_name}.png")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            return await fallback_func(output_path)

    async def close(self):
        """关闭浏览器"""
        await self.browser_manager.close()
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_renderer.py -v
```

Expected: PASS (2 tests)

- [ ] **Step 5: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add services/template/renderer.py tests/template/test_renderer.py && git commit -m "feat(template): add TemplateRenderer main entry with fallback"
```

---

## Task 7: 端到端集成测试

**Files:**
- Create: `tests/template/test_integration.py`

- [ ] **Step 1: 写集成测试 `tests/template/test_integration.py`**

```python
"""端到端集成测试：用真实模板渲染"""
import asyncio
from pathlib import Path

from services.template.renderer import TemplateRenderer


async def test_render_image_default_template():
    """测试用真实的 image_default 模板渲染"""
    r = TemplateRenderer()

    # 输出路径
    output = Path("output/test_image_default_rendered.png")
    output.parent.mkdir(parents=True, exist_ok=True)

    context = {
        "title": "测试标题",
        "image": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='800'%3E%3Crect width='800' height='800' fill='%234A90E2'/%3E%3C/svg%3E",
        "text": "这是一段测试文本",
        "author": "测试作者",
        "describe": "测试描述",
        "brand": "测试品牌",
    }

    result = await r.render("image_default", context, output)

    assert result.exists()
    assert result.stat().st_size > 1000  # 至少 1KB

    # 关闭浏览器
    await r.close()


def test_render_e2e():
    asyncio.run(test_render_image_default_template())
```

- [ ] **Step 2: 运行集成测试**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/test_integration.py -v -s
```

Expected: PASS（可能慢 2-5 秒，因为启动 Chromium）

- [ ] **Step 3: 在浏览器中查看渲染结果**

```bash
cd D:/Offline-ShortVideo-Agent && powershell -Command "Start-Process 'output/test_image_default_rendered.png'"
```

Expected: 在图片查看器中看到 1080x1920 的 PNG，包含测试标题和文本

- [ ] **Step 4: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add tests/template/test_integration.py output/test_image_default_rendered.png && git commit -m "feat(template): add end-to-end integration test"
```

---

## Task 8: 更新 __init__.py 导出

**Files:**
- Modify: `services/template/__init__.py`

- [ ] **Step 1: 更新导出**

确保 `services/template/__init__.py` 已经导出所有公开接口：

```python
"""模板渲染服务模块"""

from .renderer import TemplateRenderer
from .registry import TemplateRegistry
from .models import TemplateInfo
from .exceptions import (
    TemplateError,
    TemplateNotFoundError,
    TemplateRenderError,
    BrowserNotAvailableError,
)

__all__ = [
    "TemplateRenderer",
    "TemplateRegistry",
    "TemplateInfo",
    "TemplateError",
    "TemplateNotFoundError",
    "TemplateRenderError",
    "BrowserNotAvailableError",
]
```

- [ ] **Step 2: 运行全部模板测试**

```bash
cd D:/Offline-ShortVideo-Agent && python -m pytest tests/template/ -v
```

Expected: All tests PASS

- [ ] **Step 3: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add services/template/__init__.py && git commit -m "feat(template): update module exports"
```

---

## Task 9: 编写使用文档

**Files:**
- Create: `docs/28-template-renderer-usage.md`

- [ ] **Step 1: 创建使用文档**

```markdown
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
```

- [ ] **Step 2: 提交**

```bash
cd D:/Offline-ShortVideo-Agent && git add docs/28-template-renderer-usage.md && git commit -m "docs(template): add usage guide for template renderer"
```

---

## Task 10: E1 Week 2 阶段总结

**Files:**
- Create: `devlog/phase-E1-week2-summary.md`

- [ ] **Step 1: 创建阶段总结**

```markdown
# E1 Week 2 阶段总结：模板渲染引擎

## 完成情况

✅ **Task 1**: 模块骨架与异常定义
✅ **Task 2**: TemplateInfo 数据模型
✅ **Task 3**: TemplateRegistry（扫描 31 个模板）
✅ **Task 4**: BrowserManager 单例
✅ **Task 5**: HTMLFrameGenerator 单帧生成
✅ **Task 6**: TemplateRenderer 主入口 + 降级
✅ **Task 7**: 端到端集成测试
✅ **Task 8**: 模块导出更新
✅ **Task 9**: 使用文档
✅ **Task 10**: 阶段总结

## 产出文件

- `services/template/` (5 个 Python 文件)
- `tests/template/` (5 个测试文件)
- `docs/28-template-renderer-usage.md`
- 端到端集成测试输出 PNG

## 性能指标

| 指标 | 实测 |
|------|------|
| 单帧渲染时间 | ~2-3 秒（首次）<br>~1 秒（后续） |
| 浏览器复用 | ✅ 单例 |
| 降级路径 | ✅ PIL 保底 |

## 下一步

E1 Week 3: 前端模板选择器
```

- [ ] **Step 2: 提交并更新任务状态**

```bash
cd D:/Offline-ShortVideo-Agent && git add devlog/phase-E1-week2-summary.md && git commit -m "docs: E1 Week 2 stage summary"
```

---

## 验收清单

完成所有 Task 后，逐项验证：

- [ ] 31 个模板都被 `TemplateRegistry.scan()` 索引到
- [ ] 选择任意模板（如 `image_default`）能渲染出正确尺寸的 PNG
- [ ] 模板不存在时抛出 `TemplateNotFoundError`
- [ ] 模板渲染失败时 `render_with_fallback` 调用降级函数
- [ ] 浏览器单例：连续 10 次渲染只启动一次 Chromium
- [ ] 所有测试通过：`pytest tests/template/ -v`
- [ ] 文档完整：`docs/28-template-renderer-usage.md`

---

**计划创建时间**: 2026-07-24
**预计完成时间**: 2 周（保守节奏）
**下一步**: 执行计划