# -*- coding: utf-8 -*-
"""
动效渲染器集成测试
验证动效渲染器的完整工作流程
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

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[ERROR] PIL not available")
    sys.exit(1)

from core.renderers.animated_renderers import (
    AnimatedMinimalRenderer,
    AnimatedVibrantRenderer,
    AnimatedCinematicRenderer,
    AnimatedTechRenderer,
    AnimatedMangaRenderer
)


def test_animated_renderers():
    """测试动效渲染器"""
    print("=" * 60)
    print("  动效渲染器集成测试")
    print("=" * 60)

    output_dir = Path(__file__).parent / "output" / "animated_renderer_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 测试数据
    test_data = {
        "title": "动效渲染器测试",
        "subtitle": "验证动效系统完整性",
        "bullets": [
            "动效引擎集成",
            "视频合成功能",
            "完整工作流程"
        ]
    }

    # 测试渲染器
    renderers = [
        ("animated_minimal", AnimatedMinimalRenderer),
        ("animated_vibrant", AnimatedVibrantRenderer),
        ("animated_cinematic", AnimatedCinematicRenderer),
        ("animated_tech", AnimatedTechRenderer),
        ("animated_manga", AnimatedMangaRenderer)
    ]

    results = {}

    for renderer_id, renderer_class in renderers:
        print(f"\n[{renderer_id.upper()}] 测试...")

        try:
            # 创建渲染器
            renderer = renderer_class(width=1080, height=1920)

            # 静态渲染
            output_path = output_dir / f"{renderer_id}_static.png"
            result = renderer.render_frame(
                title=test_data["title"],
                bullets=test_data["bullets"],
                output_path=str(output_path),
                subtitle=test_data["subtitle"],
                enable_animations=False,  # 静态模式
                scene_index=0,
                total_scenes=1
            )

            if result and Path(result).exists():
                size = Path(result).stat().st_size / 1024  # KB
                print(f"  [OK] 静态渲染: {size:.1f} KB")
                results[f"{renderer_id}_static"] = "OK"
            else:
                print(f"  [FAIL] 静态渲染失败")
                results[f"{renderer_id}_static"] = "FAILED"

        except Exception as e:
            print(f"  [ERROR] {e}")
            results[f"{renderer_id}_static"] = f"ERROR: {e}"

    # 汇总
    print("\n" + "=" * 60)
    print("  测试汇总")
    print("=" * 60)

    ok_count = sum(1 for v in results.values() if v == "OK")
    print(f"\n通过: {ok_count}/{len(results)}")

    for test, status in results.items():
        symbol = "[OK]" if status == "OK" else "[FAIL]"
        print(f"  {symbol} {test}")

    return ok_count == len(results)


def test_video_workflow():
    """测试完整视频工作流程"""
    print("\n" + "=" * 60)
    print("  完整视频工作流程测试")
    print("=" * 60)

    try:
        from core.video_composer import VideoGenerator

        # 创建测试分镜
        storyboard = [
            {
                "title": "动效系统介绍",
                "subtitle": "Phase 1.3 & 1.4 成果",
                "bullets": ["文字动效引擎", "视频合成功能", "完整集成"]
            },
            {
                "title": "技术实现",
                "subtitle": "核心功能展示",
                "bullets": ["5种动效类型", "多风格支持", "FFmpeg合成"]
            }
        ]

        output_dir = Path(__file__).parent / "output" / "animated_renderer_tests"
        output_path = output_dir / "workflow_test.mp4"

        print(f"\n生成为 {len(storyboard)} 场景视频...")

        # 创建视频生成器
        generator = VideoGenerator(style_id="minimal", fps=30)

        # 生成视频
        success = generator.generate_video(
            storyboard=storyboard,
            output_path=str(output_path),
            enable_animations=False,
            scene_duration=2.0,
            progress_callback=lambda p: print(f"  进度: {p*100:.0f}%")
        )

        if success and output_path.exists():
            size = output_path.stat().st_size / (1024 * 1024)  # MB
            print(f"\n[OK] 工作流程测试成功: {size:.2f} MB")
            return True
        else:
            print(f"\n[FAIL] 工作流程测试失败")
            return False

    except Exception as e:
        print(f"\n[ERROR] 工作流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 测试1: 动效渲染器
    test1_pass = test_animated_renderers()

    # 测试2: 完整工作流程
    test2_pass = test_video_workflow()

    # 汇总
    print("\n" + "=" * 60)
    print("  最终汇总")
    print("=" * 60)

    results = [
        ("动效渲染器", test1_pass),
        ("完整工作流程", test2_pass)
    ]

    for test_name, passed in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {test_name}")

    ok_count = sum(1 for _, passed in results if passed)
    print(f"\n通过: {ok_count}/{len(results)}")

    sys.exit(0 if ok_count == len(results) else 1)
