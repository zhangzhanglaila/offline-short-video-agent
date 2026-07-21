# -*- coding: utf-8 -*-
"""
素材库管理系统
支持多种素材源和智能推荐
"""
from typing import List, Dict, Optional, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json


class MaterialSource(Enum):
    """素材源类型"""
    LOCAL = "local"           # 本地文件
    PEXELS = "pexels"         # Pexels API
    PIXABAY = "pixabay"       # Pixabay API
    UNSPLASH = "unsplash"     # Unsplash API
    CC0 = "cc0"               # CC0协议素材


@dataclass
class Material:
    """素材对象"""
    id: str
    title: str
    source: MaterialSource
    url: str
    local_path: Optional[str] = None
    media_type: str = "image"  # image/video
    resolution: str = "1080p"  # 分辨率
    duration: Optional[float] = None  # 视频时长
    keywords: Optional[List[str]] = None
    quality_score: float = 0.5  # 质量评分 0.0-1.0
    relevance_score: float = 0.0  # 相关性评分


class MaterialLibrary:
    """素材库 - 管理和查询素材"""

    def __init__(self, library_path: str = None):
        """
        初始化素材库

        Args:
            library_path: 素材库配置文件路径
        """
        self.library_path = Path(library_path) if library_path else Path.cwd() / "data" / "materials.json"
        self.materials: List[Material] = []
        self.keywords_index: Dict[str, List[int]] = {}  # 关键词索引

        self._load_library()

    def _load_library(self):
        """加载素材库"""
        if self.library_path.exists():
            try:
                with open(self.library_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for item in data.get("materials", []):
                    material = Material(
                        id=item["id"],
                        title=item["title"],
                        source=MaterialSource[item.get("source", "LOCAL").upper()],
                        url=item["url"],
                        local_path=item.get("local_path"),
                        media_type=item.get("media_type", "image"),
                        resolution=item.get("resolution", "1080p"),
                        duration=item.get("duration"),
                        keywords=item.get("keywords", []),
                        quality_score=item.get("quality_score", 0.5)
                    )
                    self.materials.append(material)

                self._build_indexes()
            except Exception as e:
                print(f"[MaterialLibrary] Failed to load library: {e}")

    def _build_indexes(self):
        """构建搜索索引"""
        self.keywords_index = {}

        for i, material in enumerate(self.materials):
            if material.keywords:
                for keyword in material.keywords:
                    if keyword not in self.keywords_index:
                        self.keywords_index[keyword] = []
                    self.keywords_index[keyword].append(i)

    def add_material(
        self,
        title: str,
        source: MaterialSource,
        url: str,
        keywords: List[str] = None,
        quality_score: float = 0.5,
        media_type: str = "image",
        local_path: str = None,
        **kwargs
    ) -> str:
        """
        添加素材到库

        Args:
            title: 素材标题
            source: 素材源
            url: 素材URL
            keywords: 关键词列表
            quality_score: 质量评分
            media_type: 媒体类型
            local_path: 本地路径
            **kwargs: 其他属性

        Returns:
            素材ID
        """
        material_id = f"{source.value}_{len(self.materials)}"

        material = Material(
            id=material_id,
            title=title,
            source=source,
            url=url,
            keywords=keywords or [],
            quality_score=quality_score,
            media_type=media_type,
            local_path=local_path,
            **kwargs
        )

        self.materials.append(material)
        self._build_indexes()

        return material_id

    def search_by_keywords(
        self,
        keywords: List[str],
        media_type: str = None,
        source: MaterialSource = None,
        top_k: int = 10
    ) -> List[Material]:
        """
        按关键词搜索素材

        Args:
            keywords: 搜索关键词
            media_type: 筛选媒体类型
            source: 筛选素材源
            top_k: 返回前K个结果

        Returns:
            材料列表
        """
        results = []

        for material in self.materials:
            # 筛选媒体类型
            if media_type and material.media_type != media_type:
                continue

            # 筛选素材源
            if source and material.source != source:
                continue

            # 计算关键词匹配度
            if material.keywords:
                overlap = len(set(keywords) & set(material.keywords))
                if overlap > 0:
                    relevance = overlap / len(keywords)
                    material.relevance_score = relevance
                    results.append(material)

        # 按相关性排序
        results.sort(
            key=lambda m: (m.relevance_score, m.quality_score),
            reverse=True
        )

        return results[:top_k]

    def search_by_title(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Material]:
        """按标题搜索"""
        results = []

        for material in self.materials:
            if query.lower() in material.title.lower():
                results.append(material)

        return results[:top_k]

    def get_random_materials(
        self,
        count: int = 5,
        media_type: str = None
    ) -> List[Material]:
        """获取随机素材"""
        import random

        filtered = self.materials
        if media_type:
            filtered = [m for m in filtered if m.media_type == media_type]

        return random.sample(filtered, min(count, len(filtered)))

    def save_library(self):
        """保存素材库到文件"""
        self.library_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "materials": [
                {
                    "id": m.id,
                    "title": m.title,
                    "source": m.source.value.upper(),
                    "url": m.url,
                    "local_path": m.local_path,
                    "media_type": m.media_type,
                    "resolution": m.resolution,
                    "duration": m.duration,
                    "keywords": m.keywords,
                    "quality_score": m.quality_score
                }
                for m in self.materials
            ]
        }

        with open(self.library_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_stats(self) -> Dict:
        """获取库统计信息"""
        media_types = {}
        sources = {}

        for material in self.materials:
            media_types[material.media_type] = media_types.get(material.media_type, 0) + 1
            sources[material.source.value] = sources.get(material.source.value, 0) + 1

        return {
            "total": len(self.materials),
            "media_types": media_types,
            "sources": sources,
            "avg_quality": sum(m.quality_score for m in self.materials) / len(self.materials) if self.materials else 0
        }


class QualityEvaluator:
    """素材质量评估器"""

    def evaluate_image(
        self,
        image_path: str,
        metadata: Dict = None
    ) -> float:
        """
        评估图像质量

        Args:
            image_path: 图像路径
            metadata: 图像元数据

        Returns:
            质量评分 (0.0-1.0)
        """
        score = 0.5  # 默认评分

        try:
            from PIL import Image
            img = Image.open(image_path)

            # 分辨率评分
            width, height = img.size
            resolution = max(width, height)
            resolution_score = min(1.0, resolution / 2160)  # 基于4K分辨率

            # 颜色多样性评分 (简化)
            colors = img.getcolors(maxcolors=256)
            color_score = min(1.0, len(colors) / 256) if colors else 0.5

            # 综合评分
            score = resolution_score * 0.6 + color_score * 0.4

        except Exception as e:
            print(f"[QualityEvaluator] Failed to evaluate image: {e}")

        return score

    def evaluate_video(
        self,
        video_path: str,
        metadata: Dict = None
    ) -> float:
        """
        评估视频质量

        Args:
            video_path: 视频路径
            metadata: 视频元数据

        Returns:
            质量评分 (0.0-1.0)
        """
        score = 0.5  # 默认评分

        try:
            # 尝试使用ffprobe获取视频信息
            import subprocess
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", "-show_streams", video_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)

                # 检查分辨率
                for stream in data.get("streams", []):
                    if stream.get("codec_type") == "video":
                        width = stream.get("width", 1080)
                        height = stream.get("height", 720)
                        resolution = max(width, height)
                        score = min(1.0, resolution / 2160)
                        break

        except Exception as e:
            print(f"[QualityEvaluator] Failed to evaluate video: {e}")

        return score


# 便捷函数
def create_material_library(library_path: str = None) -> MaterialLibrary:
    """创建素材库"""
    return MaterialLibrary(library_path)


def create_quality_evaluator() -> QualityEvaluator:
    """创建质量评估器"""
    return QualityEvaluator()
