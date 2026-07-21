# -*- coding: utf-8 -*-
"""
素材推荐引擎
基于脚本语义推荐最相关的素材
"""
from typing import List, Dict, Optional, Tuple
from core.semantic_extractor import SemanticExtractor, SemanticKeywords, MaterialMatcher
from core.material_library import MaterialLibrary, Material, MaterialSource


class RecommendationEngine:
    """素材推荐引擎"""

    def __init__(self, library: MaterialLibrary = None):
        """
        初始化推荐引擎

        Args:
            library: 素材库实例
        """
        self.extractor = SemanticExtractor()
        self.matcher = MaterialMatcher(self.extractor)
        self.library = library or MaterialLibrary()

    def recommend_for_scene(
        self,
        title: str,
        subtitle: str = "",
        bullets: List[str] = None,
        description: str = "",
        media_type: str = "image",
        count: int = 5
    ) -> List[Tuple[Material, float]]:
        """
        为场景推荐素材

        Args:
            title: 场景标题
            subtitle: 副标题
            bullets: 要点
            description: 场景描述
            media_type: 媒体类型
            count: 推荐数量

        Returns:
            [(material, score), ...] 按相关性排序
        """
        # 提取脚本语义
        scene_keywords = self.extractor.extract_all_semantics(
            title=title,
            subtitle=subtitle,
            bullets=bullets or [],
            description=description
        )

        if not scene_keywords.primary:
            # 如果没有提取到主关键词，返回质量最高的素材
            candidates = [m for m in self.library.materials if m.media_type == media_type]
            candidates.sort(key=lambda m: m.quality_score, reverse=True)
            return [(m, m.quality_score) for m in candidates[:count]]

        # 搜索候选素材
        all_materials = self.library.materials
        candidates = [m for m in all_materials if m.media_type == media_type]

        if not candidates:
            return []

        # 为每个候选素材计算匹配分数
        recommendations = []

        for material in candidates:
            # 提取素材语义
            material_keywords = self.extractor.extract_all_semantics(
                title=material.title,
                description=" ".join(material.keywords or [])
            )

            # 计算匹配分数
            relevance_score = self.matcher.match_score(
                scene_keywords,
                material_keywords
            )

            # 综合考虑质量评分和相关性评分
            combined_score = relevance_score * 0.7 + material.quality_score * 0.3

            recommendations.append((material, combined_score))

        # 按综合得分排序
        recommendations.sort(key=lambda x: x[1], reverse=True)

        return recommendations[:count]

    def recommend_for_storyboard(
        self,
        storyboard: List[Dict],
        media_type: str = "image",
        count_per_scene: int = 3
    ) -> Dict[int, List[Tuple[Material, float]]]:
        """
        为整个分镜推荐素材

        Args:
            storyboard: 分镜列表
            media_type: 媒体类型
            count_per_scene: 每个场景推荐数量

        Returns:
            {scene_idx: [(material, score), ...]}
        """
        recommendations = {}

        for scene_idx, scene in enumerate(storyboard):
            title = scene.get("title", "")
            subtitle = scene.get("subtitle", "")
            bullets = scene.get("bullets", [])
            description = scene.get("description", "")

            recommendations[scene_idx] = self.recommend_for_scene(
                title=title,
                subtitle=subtitle,
                bullets=bullets,
                description=description,
                media_type=media_type,
                count=count_per_scene
            )

        return recommendations

    def update_material_keywords(
        self,
        material_id: str,
        keywords: List[str]
    ) -> bool:
        """
        更新素材的关键词

        Args:
            material_id: 素材ID
            keywords: 新的关键词列表

        Returns:
            成功返回True
        """
        for material in self.library.materials:
            if material.id == material_id:
                material.keywords = keywords
                self.library._build_indexes()
                return True
        return False

    def batch_evaluate_quality(
        self,
        progress_callback = None
    ) -> Dict[str, float]:
        """
        批量评估所有素材的质量

        Args:
            progress_callback: 进度回调

        Returns:
            {material_id: quality_score}
        """
        from core.material_library import QualityEvaluator

        evaluator = QualityEvaluator()
        results = {}

        for i, material in enumerate(self.library.materials):
            # 跳过已有评分的
            if material.quality_score > 0.3:
                results[material.id] = material.quality_score
                continue

            # 评估质量
            if material.media_type == "image" and material.local_path:
                score = evaluator.evaluate_image(material.local_path)
                material.quality_score = score
                results[material.id] = score

            elif material.media_type == "video" and material.local_path:
                score = evaluator.evaluate_video(material.local_path)
                material.quality_score = score
                results[material.id] = score

            # 进度回调
            if progress_callback:
                progress = (i + 1) / len(self.library.materials)
                progress_callback(progress)

        return results

    def get_recommendations_stats(
        self,
        recommendations: Dict[int, List[Tuple[Material, float]]]
    ) -> Dict:
        """
        获取推荐统计信息

        Args:
            recommendations: 推荐结果

        Returns:
            统计信息
        """
        total_recommendations = sum(len(recs) for recs in recommendations.values())
        avg_score = sum(
            score
            for scene_recs in recommendations.values()
            for _, score in scene_recs
        ) / total_recommendations if total_recommendations > 0 else 0.0

        materials_used = set()
        for scene_recs in recommendations.values():
            for material, _ in scene_recs:
                materials_used.add(material.id)

        return {
            "total_recommendations": total_recommendations,
            "avg_score": avg_score,
            "unique_materials": len(materials_used),
            "scenes_covered": len(recommendations)
        }


class SmartMaterialSelector:
    """智能素材选择器 - 自动为场景选择最合适的素材"""

    def __init__(self, engine: RecommendationEngine = None):
        """
        初始化选择器

        Args:
            engine: 推荐引擎实例
        """
        self.engine = engine or RecommendationEngine()

    def auto_select_materials(
        self,
        storyboard: List[Dict],
        strategy: str = "best"  # best/diverse/balanced
    ) -> Dict[int, Material]:
        """
        自动为分镜选择素材

        Args:
            storyboard: 分镜列表
            strategy: 选择策略
                - best: 选择最相关的素材
                - diverse: 选择多样化素材
                - balanced: 平衡相关性和多样性

        Returns:
            {scene_idx: selected_material}
        """
        recommendations = self.engine.recommend_for_storyboard(
            storyboard,
            count_per_scene=3 if strategy == "diverse" else 1
        )

        selected = {}

        for scene_idx, scene_recs in recommendations.items():
            if not scene_recs:
                continue

            if strategy == "best":
                # 选择相关性最高的
                selected[scene_idx] = scene_recs[0][0]

            elif strategy == "diverse":
                # 选择与之前选择不同的
                if len(scene_recs) > 1:
                    # 选择第二高的以增加多样性
                    selected[scene_idx] = scene_recs[1][0]
                else:
                    selected[scene_idx] = scene_recs[0][0]

            elif strategy == "balanced":
                # 平衡相关性和质量
                best = scene_recs[0]
                selected[scene_idx] = best[0]

        return selected

    def generate_material_mapping(
        self,
        storyboard: List[Dict]
    ) -> Dict[int, str]:
        """
        生成场景到素材的映射

        Args:
            storyboard: 分镜列表

        Returns:
            {scene_idx: material_path/url}
        """
        materials = self.auto_select_materials(storyboard)
        mapping = {}

        for scene_idx, material in materials.items():
            # 优先使用本地路径，其次使用URL
            mapping[scene_idx] = material.local_path or material.url

        return mapping


# 便捷函数
def create_recommendation_engine(library: MaterialLibrary = None) -> RecommendationEngine:
    """创建推荐引擎"""
    return RecommendationEngine(library)


def create_material_selector(engine: RecommendationEngine = None) -> SmartMaterialSelector:
    """创建智能选择器"""
    return SmartMaterialSelector(engine)
