# E1 Week 2: 模板渲染引擎 - 设计规格

**创建时间**: 2026-07-24
**关联文档**: docs/23-E1-templates.md, docs/20-architecture-v2.md
**当前阶段**: E1 Week 2

---

## Context

用户希望在现有项目（多 Agent 系统 + D1-D6 动态化）基础上，新增 **HTML 模板渲染引擎**，让 31 个已迁移的 HTML 模板能输出为视频场景。

**核心需求**：
- HTML 模板 → 单帧 PNG（最终方案，单帧 + 现有 D1-D6 动态化模块）
- 模板参数通过 Jinja2 注入
- 使用 Playwright headless Chromium 渲染
- 与现有 `core/compose/scene_image_renderer.py` 路径集成

**为什么选单帧 PNG 而不是序列帧**：
- 性能：5s 渲染从 90s 降到 2s
- 稳定性：30fps 帧率精确，无锯齿闪烁
- 与 D1-D6 互补：模板负责静态构图，FFmpeg 负责动态效果
- Pixelle-Video 的公开示例也用单帧方案

---

## 关键设计决策（已与用户确认）

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 渲染技术 | Playwright | 现代 CSS 支持好，已在依赖中 |
| 参数注入 | Jinja2 | 模板已有 `{{var}}` 语法 |
| 输出粒度 | 单帧 PNG | 性能 + 与动态化互补 |
| 浏览器复用 | 进程级单例 | 避免重复启动开销 |

---

## 架构设计

```
┌─────────────────────────────────────────────────────┐
│           TemplateRenderer (services/template/)      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────┐    ┌──────────────────────┐  │
│  │ TemplateRegistry │───▶│ HTMLFrameGenerator   │  │
│  │  - 扫描模板       │    │  - Playwright 复用    │  │
│  │  - 元数据解析     │    │  - Jinja2 渲染        │  │
│  │  - 分类索引       │    │  - 截图输出 PNG      │  │
│  └──────────────────┘    └──────────────────────┘  │
│           │                        │                 │
│           ▼                        ▼                 │
│  ┌──────────────────┐    ┌──────────────────────┐  │
│  │ TemplateInfo     │    │ Playwright Browser   │  │
│  │  - name          │    │  (process singleton) │  │
│  │  - aspect_ratio  │    └──────────────────────┘  │
│  │  - type          │                              │
│  │  - parameters    │                              │
│  └──────────────────┘                              │
└─────────────────────────────────────────────────────┘
           │
           ▼
   集成到 core/compose/scene_image_renderer.py
```

---

## 文件结构

### 新增文件

```
services/template/
├── __init__.py              # 模块导出
├── registry.py              # TemplateRegistry: 模板扫描与索引
├── renderer.py              # TemplateRenderer: 渲染引擎主类
├── html_generator.py        # HTMLFrameGenerator: Playwright 单帧生成
├── browser.py               # BrowserManager: Playwright 浏览器单例
├── models.py                # TemplateInfo 数据模型
└── exceptions.py            # 自定义异常

tests/template/
├── __init__.py
├── test_registry.py         # 模板扫描测试
├── test_renderer.py         # 渲染引擎测试
├── test_html_generator.py   # 单帧生成测试
└── fixtures/
    └── test_template.html   # 测试模板

config/
└── template.yaml            # 模板配置（默认模板、参数映射）
```

### 修改文件

- `core/compose/scene_image_renderer.py` — 增加模板渲染路径
- `core/compose/__init__.py` — 暴露新接口
- `requirements.txt` — 确认 Playwright 依赖

---

## 接口定义

### TemplateRegistry

```python
class TemplateRegistry:
    """模板注册表：扫描、索引、查询"""

    def __init__(self, templates_dir: Path = Path("templates")):
        self.templates_dir = templates_dir
        self._cache: Dict[str, TemplateInfo] = {}

    def scan(self) -> List[TemplateInfo]:
        """扫描所有模板，返回 TemplateInfo 列表"""

    def get(self, name: str) -> TemplateInfo:
        """根据模板名称获取信息"""

    def list_by_aspect(self, aspect: str) -> List[TemplateInfo]:
        """按画幅筛选 (1080x1920, 1920x1080, 1080x1080)"""

    def list_by_type(self, template_type: str) -> List[TemplateInfo]:
        """按类型筛选 (image, static, video, asset)"""
```

### TemplateInfo

```python
@dataclass
class TemplateInfo:
    name: str                  # 模板文件名（不含扩展名）
    path: Path                 # 模板完整路径
    aspect_ratio: str          # 1080x1920 / 1920x1080 / 1080x1080
    width: int                 # 渲染宽度
    height: int                # 渲染高度
    template_type: str         # image / static / video / asset
    style: str                 # 从元数据解析
    parameters: List[str]      # 模板需要的参数列表（从 {{var}} 提取）
```

### HTMLFrameGenerator

```python
class HTMLFrameGenerator:
    """HTML → PNG 单帧生成器"""

    def __init__(self, template_info: TemplateInfo):
        self.template_info = template_info
        self.template_html = self._load_template()

    async def generate_frame(
        self,
        context: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> Path:
        """渲染单帧，返回 PNG 文件路径"""

    def _render_jinja(self, context: Dict[str, Any]) -> str:
        """用 Jinja2 替换模板变量"""

    def _extract_parameters(self) -> List[str]:
        """从 HTML 中提取 {{var}} 占位符"""
```

### TemplateRenderer (主入口)

```python
class TemplateRenderer:
    """模板渲染引擎主类"""

    def __init__(self, templates_dir: Path = Path("templates")):
        self.registry = TemplateRegistry(templates_dir)
        self.browser_manager = BrowserManager()

    async def render(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> Path:
        """主入口：渲染指定模板为 PNG"""

    async def render_with_fallback(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> Path:
        """带降级的渲染：模板失败时回退到 PIL 渲染"""

    async def close(self):
        """关闭浏览器（程序退出时调用）"""
```

### BrowserManager

```python
class BrowserManager:
    """Playwright 浏览器单例管理"""

    _instance: Optional["BrowserManager"] = None
    _browser: Optional[Browser] = None

    def __init__(self):
        self._playwright: Optional[Playwright] = None

    async def get_browser(self) -> Browser:
        """获取浏览器实例（懒初始化）"""

    async def new_page(self) -> Page:
        """创建新页面"""

    async def close(self):
        """关闭浏览器"""
```

---

## 数据流

### 正常流程

```
1. 用户调用 TemplateRenderer.render("image_default", context, output)
2. registry.get("image_default") → TemplateInfo
3. HTMLFrameGenerator(template_info)
4. _render_jinja(context) → 渲染后的 HTML
5. browser_manager.new_page()
6. page.set_content(html)
7. page.set_viewport_size(width, height)
8. page.screenshot(path=output)
9. 返回 output 路径
```

### 降级流程

```
模板渲染失败 → fallback 到 PIL 渲染
   ↓
scene_image_renderer.render_scene() (原有逻辑)
   ↓
返回 PNG（无模板效果，但保证有输出）
```

---

## 错误处理

| 错误类型 | 处理策略 |
|---------|---------|
| 模板文件不存在 | 抛出 TemplateNotFoundError |
| Jinja2 渲染异常 | 抛出 TemplateRenderError |
| Playwright 启动失败 | 抛出 BrowserNotAvailableError |
| 截图失败 | 重试 1 次，失败则降级到 PIL |
| 浏览器崩溃 | 重建 BrowserManager 实例 |

---

## 测试策略

### 单元测试

| 测试文件 | 覆盖范围 |
|---------|---------|
| test_registry.py | 模板扫描、分类、元数据解析 |
| test_renderer.py | 主入口渲染、降级路径 |
| test_html_generator.py | Jinja2 渲染、参数提取 |

### 集成测试

- 端到端：选择一个模板（image_default）渲染为 PNG，验证输出文件
- 视觉验证：用 PIL 读取 PNG 检查尺寸正确

### 验收标准

1. ✅ 31 个模板都能被注册表扫描到
2. ✅ 选择任意模板渲染后输出 1920x1080（或对应尺寸）PNG
3. ✅ 模板渲染失败时降级到 PIL 不报错
4. ✅ 浏览器复用：连续 10 次渲染不重复启动浏览器

---

## 兼容性保证

- ✅ 现有 `core/compose/scene_image_renderer.py` 接口不变
- ✅ 模板渲染作为可选路径（通过参数 `use_template` 控制）
- ✅ 不破坏现有 CLI（`generate_video.py`）

---

## 不在本期范围（YAGNI）

- ❌ 模板预览功能（E1 Week 3）
- ❌ 前端模板选择器（E1 Week 3）
- ❌ 模板参数 Web UI 配置（E1 Week 3）
- ❌ 模板版本管理
- ❌ 自定义模板上传
- ❌ 模板缓存到 CDN

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|---------|
| Playwright 安装包大（~150MB） | 使用已安装版本（项目已有依赖） |
| Windows 字体渲染问题 | 使用 Playwright 默认 Chromium 字体 |
| Chromium 启动慢（首次 ~3s） | BrowserManager 单例复用 |
| 模板里有外部资源（CDN 字体） | 失败时降级 + 缓存 |
| 并发渲染时浏览器冲突 | 暂用单例同步，后续优化 |

---

*设计完成时间: 2026-07-24*
*下一步: writing-plans 输出实现计划*