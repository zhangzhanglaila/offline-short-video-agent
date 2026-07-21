# -*- coding: utf-8 -*-
"""
API集成测试
验证Pexels/Pixabay等API的集成功能
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

from core.material_api import (
    PexelsAPI, PixabayAPI, UnsplashAPI,
    APIManager, CacheManager
)
from core.material_downloader import DownloadManager, MaterialFetcher


def test_api_framework():
    """测试API框架"""
    print("=" * 60)
    print("  API框架测试")
    print("=" * 60)

    # 测试API类是否可实例化
    print("\n[1] API客户端实例化...")

    try:
        # 这些需要真实的API密钥才能测试
        pexels = PexelsAPI("test_key")
        print(f"  [OK] Pexels API: {pexels.__class__.__name__}")

        pixabay = PixabayAPI("test_key")
        print(f"  [OK] Pixabay API: {pixabay.__class__.__name__}")

        unsplash = UnsplashAPI("test_key")
        print(f"  [OK] Unsplash API: {unsplash.__class__.__name__}")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_api_manager():
    """测试API管理器"""
    print("\n" + "=" * 60)
    print("  API管理器测试")
    print("=" * 60)

    try:
        manager = APIManager()
        print(f"\n[OK] API管理器创建成功")

        # 注册API
        pexels = PexelsAPI("test_key")
        pixabay = PixabayAPI("test_key")

        manager.register_api("pexels", pexels)
        manager.register_api("pixabay", pixabay)

        print(f"  已注册API数量: {len(manager.apis)}")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_cache_manager():
    """测试缓存管理器"""
    print("\n" + "=" * 60)
    print("  缓存管理器测试")
    print("=" * 60)

    try:
        cache_dir = Path(__file__).parent / "output" / "cache_test"
        cache = CacheManager(str(cache_dir))

        print(f"\n[1] 缓存目录: {cache.cache_dir}")

        # 测试缓存路径
        test_url = "https://example.com/image.jpg"
        cache_path = cache.get_cache_path(test_url)
        print(f"[2] 缓存路径: {cache_path}")

        # 测试缓存索引
        print(f"[3] 测试添加到缓存...")
        cache.add_to_cache(test_url, str(cache_path))
        print(f"  已缓存URL数: {len(cache.cache_index)}")

        # 测试统计
        stats = cache.get_stats()
        print(f"[4] 缓存统计:")
        print(f"  缓存URL数: {stats['cached_urls']}")
        print(f"  总大小(MB): {stats['total_size_mb']:.2f}")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_download_manager():
    """测试下载管理器"""
    print("\n" + "=" * 60)
    print("  下载管理器测试")
    print("=" * 60)

    try:
        cache_dir = Path(__file__).parent / "output" / "download_test"
        manager = DownloadManager(str(cache_dir))

        print(f"\n[1] 下载管理器创建成功")
        print(f"  缓存目录: {manager.cache_dir}")
        print(f"  最大并发: {manager.max_workers}")

        # 添加测试任务 (使用本地文件URL)
        # 注意: 这些是模拟任务，不会实际下载
        test_tasks = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg"
        ]

        for url in test_tasks:
            task_id = manager.add_task(url)
            print(f"[2] 添加任务: {task_id}")

        # 获取统计
        stats = manager.get_stats()
        print(f"\n[3] 下载统计:")
        print(f"  总任务数: {stats['total']}")
        print(f"  已完成: {stats['completed']}")
        print(f"  已缓存: {stats['cached']}")
        print(f"  待处理: {stats['pending']}")
        print(f"  失败: {stats['failed']}")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def test_integration():
    """测试集成"""
    print("\n" + "=" * 60)
    print("  集成测试")
    print("=" * 60)

    try:
        # 测试数据流
        print("\n[1] 测试API → 下载 → 库 的完整流程")
        print("  (模拟流程，不实际下载)")

        # 创建API管理器
        api_manager = APIManager()
        pexels = PexelsAPI("mock_key")
        api_manager.register_api("pexels", pexels)

        # 创建下载管理器
        download_manager = DownloadManager()

        # 创建缓存管理器
        cache_manager = CacheManager()

        print(f"\n[2] 组件初始化:")
        print(f"  API管理器: {len(api_manager.apis)} 个API")
        print(f"  下载管理器: 最多{download_manager.max_workers}并发")
        print(f"  缓存管理器: {cache_manager.get_stats()['cached_urls']}个缓存")

        print(f"\n[OK] 集成框架完整")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_result_parsing():
    """测试API结果解析"""
    print("\n" + "=" * 60)
    print("  API结果解析测试")
    print("=" * 60)

    try:
        from core.material_api import APIResult

        # 创建测试结果
        result = APIResult(
            id="test_001",
            title="Test Image",
            url="https://example.com/test.jpg",
            download_url="https://example.com/test_full.jpg",
            width=1920,
            height=1080,
            media_type="image",
            tags=["test", "example"]
        )

        print(f"\n[OK] APIResult创建成功")
        print(f"  ID: {result.id}")
        print(f"  标题: {result.title}")
        print(f"  分辨率: {result.width}x{result.height}")
        print(f"  标签: {result.tags}")

        return True

    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


if __name__ == "__main__":
    print("API集成系统测试")
    print("=" * 60)

    results = {}

    # 测试1: API框架
    results["API框架"] = test_api_framework()

    # 测试2: API管理器
    results["API管理器"] = test_api_manager()

    # 测试3: 缓存管理器
    results["缓存管理器"] = test_cache_manager()

    # 测试4: 下载管理器
    results["下载管理器"] = test_download_manager()

    # 测试5: API结果解析
    results["API结果解析"] = test_api_result_parsing()

    # 测试6: 集成
    results["集成测试"] = test_integration()

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
