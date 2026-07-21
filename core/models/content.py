"""
内容结构数据模型 - 内容分析Agent的输出契约。

定义了视频的结构化内容，是内容分析Agent、素材检索Agent、视频合成Agent
之间传递的核心数据结构。
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from enum import Enum


class SceneType(str, Enum):
    """场景类型枚举。

    - TITLE_CARD: 标题卡（整屏文字，通常用于开头/过渡）
    - CONTENT: 内容场景（素材 + 字幕条，讲解主体）
    - CONCLUSION: 结尾卡（整屏文字，总结/号召）
    """

    TITLE_CARD = "title_card"
    CONTENT = "content"
    CONCLUSION = "conclusion"


@dataclass
class Scene:
    """单个场景的定义。

    Attributes:
        scene_id: 场景序号 (从1开始)
        scene_type: 场景类型 (title_card/content/conclusion)
        text: 场景文字内容
        duration: 场景时长 (秒)
        keywords: 场景关键词 (用于素材检索)
        narration: 可选的旁白文本 (用于TTS)
    """

    scene_id: int
    scene_type: str
    text: str
    duration: float
    keywords: List[str] = field(default_factory=list)
    narration: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "scene_id": self.scene_id,
            "scene_type": self.scene_type,
            "text": self.text,
            "duration": self.duration,
            "keywords": self.keywords,
            "narration": self.narration,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scene":
        """从字典创建Scene对象。

        Args:
            data: 场景字典

        Returns:
            Scene对象
        """
        return cls(
            scene_id=int(data["scene_id"]),
            scene_type=data.get("scene_type", data.get("type", SceneType.CONTENT.value)),
            text=data.get("text", ""),
            duration=float(data.get("duration", 3.0)),
            keywords=list(data.get("keywords", [])),
            narration=data.get("narration"),
        )

    def is_text_only(self) -> bool:
        """判断是否为纯文字场景（不需要素材）。

        Returns:
            True如果是标题卡或结尾卡
        """
        return self.scene_type in (SceneType.TITLE_CARD.value, SceneType.CONCLUSION.value)


@dataclass
class ContentStructure:
    """视频的完整内容结构。

    这是内容分析Agent的核心输出，定义了整个视频的结构、
    场景划分、文字内容和素材需求。

    Attributes:
        title: 视频标题
        category: 视频分类
        style: 视频风格
        total_duration: 目标总时长 (秒)
        scenes: 场景列表
        source: 生成来源 (llm/fallback)，用于追踪质量
        metadata: 额外元数据
    """

    title: str
    category: str
    style: str
    total_duration: int
    scenes: List[Scene] = field(default_factory=list)
    source: str = "llm"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "title": self.title,
            "category": self.category,
            "style": self.style,
            "total_duration": self.total_duration,
            "scenes": [s.to_dict() for s in self.scenes],
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentStructure":
        """从字典创建ContentStructure对象。

        Args:
            data: 内容结构字典

        Returns:
            ContentStructure对象
        """
        scenes = [Scene.from_dict(s) for s in data.get("scenes", [])]
        return cls(
            title=data.get("title", ""),
            category=data.get("category", ""),
            style=data.get("style", ""),
            total_duration=int(data.get("total_duration", 30)),
            scenes=scenes,
            source=data.get("source", "llm"),
            metadata=data.get("metadata", {}),
        )

    @property
    def scene_count(self) -> int:
        """场景总数。"""
        return len(self.scenes)

    @property
    def computed_duration(self) -> float:
        """根据场景累加的实际总时长。"""
        return sum(s.duration for s in self.scenes)

    def validate(self) -> tuple[bool, Optional[str]]:
        """验证内容结构的有效性。

        Returns:
            (是否有效, 错误信息)
        """
        if not self.title or not self.title.strip():
            return False, "标题为空"

        if not self.scenes:
            return False, "场景列表为空"

        # 验证每个场景
        for scene in self.scenes:
            if not scene.text or not scene.text.strip():
                return False, f"场景 {scene.scene_id} 文字为空"

            if scene.duration <= 0:
                return False, f"场景 {scene.scene_id} 时长无效: {scene.duration}"

            valid_types = {t.value for t in SceneType}
            if scene.scene_type not in valid_types:
                return False, f"场景 {scene.scene_id} 类型无效: {scene.scene_type}"

        # 验证时长偏差（允许±20%）
        computed = self.computed_duration
        if self.total_duration > 0:
            deviation = abs(computed - self.total_duration) / self.total_duration
            if deviation > 0.5:  # 偏差超过50%视为无效
                return False, (
                    f"时长偏差过大: 目标{self.total_duration}s, "
                    f"实际{computed:.1f}s"
                )

        return True, None

    def get_content_scenes(self) -> List[Scene]:
        """获取所有内容场景（需要素材的场景）。

        Returns:
            内容场景列表
        """
        return [s for s in self.scenes if not s.is_text_only()]

    def get_summary(self) -> str:
        """获取内容结构摘要。

        Returns:
            摘要文本
        """
        lines = [
            f"📄 《{self.title}》",
            f"   分类: {self.category} | 风格: {self.style}",
            f"   时长: {self.computed_duration:.1f}s / 目标{self.total_duration}s",
            f"   场景: {self.scene_count}个 (来源: {self.source})",
        ]
        for scene in self.scenes:
            kw = f" [{', '.join(scene.keywords[:3])}]" if scene.keywords else ""
            lines.append(
                f"   {scene.scene_id}. [{scene.scene_type}] "
                f"{scene.duration:.1f}s: {scene.text[:20]}{kw}"
            )
        return "\n".join(lines)
