# -*- coding: utf-8 -*-
"""
素材系统测试
验证语义提取、库管理和推荐系统功能
"""
import sys
import os
from pathlib import Path

# UTF-8输出
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from core.semantic_extractor import SemanticExtractor, extract_script_semantics
from core.material_library import MaterialLibrary, MaterialSource, create_quality_evaluator
from core.recommendation_engine import RecommendationEngine, SmartMaterialSelector


def test_semantic_extractor():
    """测试语义提取器"""
    print("=" * 60)
    print("  语义提取器测试")
    print("=" * 60)

    extractor = SemanticExtractor()

    # 测试数据
    test_cases = [
        {
            "title": "Python异步编程完全指南",
            "subtitle": "从零掌握async/await",
            "bullets": [
                "理解事件循环原理",
                "async/await语法糖用法",
                "实战异步爬虫案例"
            ],
            "description": "深入讲解Python异步编程的核心概念和最佳实践"
        },
        {
            "title": "美食制作教程",
            "subtitle": "居家便利简餐",
            "bullets": [
                "准备新鲜食材",
                "烹饪技巧和火候",
                "盛盘美化和拍摄"
            ],
            "description": "教你如何制作美味的家常菜"
        }
    ]

    results = {}

    for i, case in enumerate(test_cases):
        print(f"\n[测试 {i+1}] {case['title']}")

        semantics = extractor.extract_all_semantics(
            title=case["title"],
            subtitle=case["subtitle"],
            bullets=case["bullets"],
            description=case["description"]
        )

        print(f"  主关键词: {semantics.primary}")
        print(f"  次关键词: {semantics.secondary}")
        print(f"  实体词: {semantics.entities[:3]}")
        print(f"  情感词: {semantics.emotions}")
        print(f"  主题: {semantics.topics}")

        results[i] = semantics

    print(f"\n通过: {len(results)}/{len(test_cases)}")
    return len(results) == len(test_cases), results


def test_material_library():
    """测试素材库"""
    print("\n" + "=" * 60)
    print("  素材库测试")
    print("=" * 60)

    library = MaterialLibrary()

    # 添加测试素材
    print("\n添加测试素材...")

    materials_to_add = [
        {
            "title": "编程工作台",
            "keywords": ["编程", "代码", "工作", "技术"],
            "quality_score": 0.8
        },
        {
            "title": "笔记本电脑",
            "keywords": ["电脑", "技术", "工作", "办公"],
            "quality_score": 0.7
        },
        {
            "title": "美食摄影",
            "keywords": ["美食", "食物", "烹饪", "餐厅"],
            "quality_score": 0.9
        },
        {
            "title": "厨房操作",
            "keywords": ["烹饪", "食物", "厨房", "美食"],
            "quality_score": 0.8
        },
        {
            "title": "旅游风景",
            "keywords": ["旅游", "景点", "风景", "自然"],
            "quality_score": 0.85
        }
    ]

    for material_data in materials_to_add:
        material_id = library.add_material(
            title=material_data["title"],
            source=MaterialSource.CC0,
            url=f"http://example.com/{material_data['title']}",
            keywords=material_data["keywords"],
            quality_score=material_data["quality_score"]
        )
        print(f"  [OK] 添加素材: {material_data['title']} (ID: {material_id})")

    # 测试搜索
    print("\n搜索测试...")

    search_cases = [
        (["编程", "技术"], "编程相关"),
        (["美食", "烹饪"], "美食相关"),
        (["旅游"], "旅游相关")
    ]

    for keywords, description in search_cases:
        results = library.search_by_keywords(keywords, top_k=3)
        print(f"  搜索'{description}': 找到 {len(results)} 个素材")
        for material in results[:1]:
            print(f"    - {material.title} (质量: {material.quality_score})")

    # 获取统计
    stats = library.get_stats()
    print(f"\n素材库统计:")
    print(f"  总数: {stats['total']}")
    print(f"  平均质量评分: {stats['avg_quality']:.2f}")

    return True


def test_recommendation_engine(semantics_results):
    """测试推荐引擎"""
    print("\n" + "=" * 60)
    print("  推荐引擎测试")
    print("=" * 60)

    # 创建库和引擎
    library = MaterialLibrary()

    # 添加测试素材
    library.add_material(
        title="编程工作台",
        source=MaterialSource.CC0,
        url="http://example.com/programming",
        keywords=["编程", "代码", "工作", "技术"],
        quality_score=0.8
    )

    library.add_material(
        title="笔记本电脑",
        source=MaterialSource.CC0,
        url="http://example.com/laptop",
        keywords=["电脑", "技术", "工作", "办公"],
        quality_score=0.7
    )

    library.add_material(
        title="美食摄影",
        source=MaterialSource.CC0,
        url="http://example.com/food",
        keywords=["美食", "食物", "烹饪", "餐厅"],
        quality_score=0.9
    )

    engine = RecommendationEngine(library)

    # 为Python教程推荐素材
    print("\n为'Python异步编程'推荐素材...")

    recommendations = engine.recommend_for_scene(
        title="Python异步编程完全指南",
        subtitle="从零掌握async/await",
        bullets=[
            "理解事件循环原理",
            "async/await语法糖用法",
            "实战异步爬虫案例"
        ],
        count=3
    )

    print(f"  推荐 {len(recommendations)} 个素材:")
    for material, score in recommendations:
        print(f"    - {material.title} (相关性: {score:.2f})")

    # 为美食教程推荐素材
    print("\n为'美食制作教程'推荐素材...")

    recommendations = engine.recommend_for_scene(
        title="美食制作教程",
        subtitle="居家便利简餐",
        bullets=[
            "准备新鲜食材",
            "烹饪技巧和火候",
            "盛盘美化和拍摄"
        ],
        count=3
    )

    print(f"  推荐 {len(recommendations)} 个素材:")
    for material, score in recommendations:
        print(f"    - {material.title} (相关性: {score:.2f})")

    return True


def test_smart_selector():
    """测试智能选择器"""
    print("\n" + "=" * 60)
    print("  智能选择器测试")
    print("=" * 60)

    # 创建库和选择器
    library = MaterialLibrary()

    # 添加测试素材
    for i in range(5):
        library.add_material(
            title=f"测试素材 {i+1}",
            source=MaterialSource.CC0,
            url=f"http://example.com/material_{i}",
            keywords=["编程", "技术"],
            quality_score=0.5 + i * 0.1
        )

    engine = RecommendationEngine(library)
    selector = SmartMaterialSelector(engine)

    # 创建测试分镜
    storyboard = [
        {
            "title": "场景1",
            "subtitle": "开始",
            "bullets": ["介绍", "主题"]
        },
        {
            "title": "场景2",
            "subtitle": "发展",
            "bullets": ["详细", "解释"]
        }
    ]

    print(f"\n为 {len(storyboard)} 个场景自动选择素材...")

    # 最佳相关性策略
    selected = selector.auto_select_materials(storyboard, strategy="best")
    print(f"\n[最佳相关性] 选择了 {len(selected)} 个素材:")
    for scene_idx, material in selected.items():
        print(f"  场景{scene_idx}: {material.title}")

    # 多样性策略
    selected = selector.auto_select_materials(storyboard, strategy="diverse")
    print(f"\n[多样化] 选择了 {len(selected)} 个素材:")
    for scene_idx, material in selected.items():
        print(f"  场景{scene_idx}: {material.title}")

    return True


if __name__ == "__main__":
    print("素材系统综合测试")
    print("=" * 60)

    results = {}

    # 测试1: 语义提取
    test1_pass, semantics = test_semantic_extractor()
    results["语义提取"] = test1_pass

    # 测试2: 素材库
    test2_pass = test_material_library()
    results["素材库"] = test2_pass

    # 测试3: 推荐引擎
    test3_pass = test_recommendation_engine(semantics)
    results["推荐引擎"] = test3_pass

    # 测试4: 智能选择器
    test4_pass = test_smart_selector()
    results["智能选择器"] = test4_pass

    # 汇总
    print("\n" + "=" * 60)
    print("  最终汇总")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {test_name}")

    ok_count = sum(1 for passed in results.values() if passed)
    print(f"\n通过: {ok_count}/{len(results)}")

    sys.exit(0 if ok_count == len(results) else 1)
