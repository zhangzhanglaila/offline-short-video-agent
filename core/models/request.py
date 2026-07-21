"""
用户请求数据模型 - 定义用户的视频生成需求格式。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class UserRequest:
    """用户的视频生成需求。

    Attributes:
        request_id: 请求ID (自动生成)
        user_input: 用户需求文本
        category: 视频分类 (教育讲解/短视频/纪录片/商业宣传等)
        style: 视频风格 (minimal/vibrant/cinematic/tech/manga)
        duration: 目标视频时长 (秒)
        tags: 可选的标签列表
        metadata: 其他元数据
    """

    user_input: str
    category: str
    style: str
    duration: int

    request_id: str = field(default_factory=lambda: f"req_{id(object())}")
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> bool:
        """验证请求的有效性。

        Returns:
            True如果请求有效
        """
        # 验证必需字段
        if not self.user_input or not self.user_input.strip():
            return False

        if not self.category:
            return False

        if not self.style:
            return False

        if self.duration <= 0:
            return False

        # 验证分类
        valid_categories = {"教育讲解", "短视频", "纪录片", "商业宣传"}
        if self.category not in valid_categories:
            return False

        # 验证风格
        valid_styles = {"minimal", "vibrant", "cinematic", "tech", "manga"}
        if self.style not in valid_styles:
            return False

        # 验证时长范围（5-300秒）
        if not (5 <= self.duration <= 300):
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。

        Returns:
            请求字典
        """
        return {
            "request_id": self.request_id,
            "user_input": self.user_input,
            "category": self.category,
            "style": self.style,
            "duration": self.duration,
            "tags": self.tags,
            "metadata": self.metadata
        }
