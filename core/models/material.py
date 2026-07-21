"""
素材资产数据模型 - 素材检索Agent的输出契约。

定义了检索到的素材及其与场景的映射关系，是素材检索Agent、
视频合成Agent之间传递的核心数据结构。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class MaterialAsset:
    """单个素材资产。

    Attributes:
        asset_id: 素材唯一标识
        scene_id: 所属场景ID
        source: 素材来源 (pexels/pixabay/unsplash/local/placeholder)
        media_type: 媒体类型 (image/video)
        url: 素材原始URL（预览页或来源页）
        download_url: 素材下载URL
        local_path: 本地缓存路径 (下载成功后)
        width: 宽度（像素）
        height: 高度（像素）
        quality_score: 质量评分 (0-1)
        keywords: 检索时使用的关键词
        is_placeholder: 是否为占位符（降级素材）
    """

    asset_id: str
    scene_id: int
    source: str
    media_type: str = "image"
    url: str = ""
    download_url: str = ""
    local_path: Optional[str] = None
    width: int = 0
    height: int = 0
    quality_score: float = 0.0
    keywords: List[str] = field(default_factory=list)
    is_placeholder: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "asset_id": self.asset_id,
            "scene_id": self.scene_id,
            "source": self.source,
            "media_type": self.media_type,
            "url": self.url,
            "download_url": self.download_url,
            "local_path": self.local_path,
            "width": self.width,
            "height": self.height,
            "quality_score": self.quality_score,
            "keywords": self.keywords,
            "is_placeholder": self.is_placeholder,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MaterialAsset":
        """从字典创建MaterialAsset对象。"""
        return cls(
            asset_id=data["asset_id"],
            scene_id=int(data["scene_id"]),
            source=data.get("source", "unknown"),
            media_type=data.get("media_type", "image"),
            url=data.get("url", ""),
            download_url=data.get("download_url", ""),
            local_path=data.get("local_path"),
            width=int(data.get("width", 0)),
            height=int(data.get("height", 0)),
            quality_score=float(data.get("quality_score", 0.0)),
            keywords=list(data.get("keywords", [])),
            is_placeholder=bool(data.get("is_placeholder", False)),
        )

    @property
    def is_available(self) -> bool:
        """判断素材是否可用（有本地文件或为占位符）。"""
        return self.is_placeholder or bool(self.local_path)


@dataclass
class SceneMaterialMap:
    """场景-素材映射。

    素材检索Agent的核心输出，记录每个场景匹配到的素材。

    Attributes:
        scene_materials: 场景ID -> 素材列表
        metadata: 统计元数据
    """

    scene_materials: Dict[int, List[MaterialAsset]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add(self, scene_id: int, asset: MaterialAsset) -> None:
        """为场景添加素材。

        Args:
            scene_id: 场景ID
            asset: 素材资产
        """
        if scene_id not in self.scene_materials:
            self.scene_materials[scene_id] = []
        self.scene_materials[scene_id].append(asset)

    def get(self, scene_id: int) -> List[MaterialAsset]:
        """获取场景的素材列表。

        Args:
            scene_id: 场景ID

        Returns:
            素材列表（可能为空）
        """
        return self.scene_materials.get(scene_id, [])

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（键转为字符串以兼容JSON）。"""
        return {
            "scene_materials": {
                str(sid): [a.to_dict() for a in assets]
                for sid, assets in self.scene_materials.items()
            },
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneMaterialMap":
        """从字典创建SceneMaterialMap对象。"""
        scene_materials: Dict[int, List[MaterialAsset]] = {}
        for sid, assets in data.get("scene_materials", {}).items():
            scene_materials[int(sid)] = [
                MaterialAsset.from_dict(a) for a in assets
            ]
        return cls(
            scene_materials=scene_materials,
            metadata=data.get("metadata", {}),
        )

    @property
    def total_assets(self) -> int:
        """素材总数。"""
        return sum(len(assets) for assets in self.scene_materials.values())

    @property
    def placeholder_count(self) -> int:
        """占位符数量。"""
        count = 0
        for assets in self.scene_materials.values():
            count += sum(1 for a in assets if a.is_placeholder)
        return count

    @property
    def real_count(self) -> int:
        """真实素材数量（非占位符）。"""
        return self.total_assets - self.placeholder_count

    def match_rate(self, total_scenes_needing_material: int) -> float:
        """计算素材匹配率。

        Args:
            total_scenes_needing_material: 需要素材的场景总数

        Returns:
            匹配率 (0-1)，即成功匹配真实素材的场景占比
        """
        if total_scenes_needing_material <= 0:
            return 1.0
        matched_scenes = sum(
            1 for assets in self.scene_materials.values()
            if any(not a.is_placeholder for a in assets)
        )
        return matched_scenes / total_scenes_needing_material

    def get_summary(self) -> str:
        """获取映射摘要。"""
        lines = [
            f"🎬 素材映射: {len(self.scene_materials)}个场景",
            f"   总素材: {self.total_assets} (真实{self.real_count} / 占位{self.placeholder_count})",
        ]
        for sid in sorted(self.scene_materials.keys()):
            assets = self.scene_materials[sid]
            for a in assets:
                tag = "📁" if a.is_placeholder else "🖼️"
                lines.append(
                    f"   {tag} 场景{sid}: [{a.source}] "
                    f"{a.width}x{a.height} q={a.quality_score:.2f} "
                    f"{a.keywords}"
                )
        return "\n".join(lines)
