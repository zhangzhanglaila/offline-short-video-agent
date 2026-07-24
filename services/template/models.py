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