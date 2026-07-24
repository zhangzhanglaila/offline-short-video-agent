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