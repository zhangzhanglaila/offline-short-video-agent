# -*- coding: utf-8 -*-
"""
风格渲染器测试
验证所有风格的渲染器是否正常工作
"""
import sys
import os
from pathlib import Path

# 设置UTF-8输出（Windows兼容）
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.style_renderers import get_available_styles, render_frame


def test_all_styles():
    """测试所有风格的渲染器"""

    print("=" * 60)
    print("  风格渲染器测试")
    print("=" * 60)

    # 获取所有可用风格
    styles = get_available_styles()
    print(f"\n可用风格: {styles}\n")

    # 测试数据
    test_data = {
        "title": "Python异步编程完全指南",
        "bullets": [
            "async/await 语法糖的使用方法",
            "事件循环 EventLoop 的工作原理",
            "协程并发 vs 多线程性能对比",
            "实战案例：爬虫与API请求优化",
        ],
        "subtitle": "从零掌握Python异步编程核心概念",
    }

    # 测试每种风格
    output_dir = Path(__file__).parent / "output" / "style_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for style_id in styles:
        print(f"[{style_id.upper()}] 渲染测试...")

        output_path = output_dir / f"test_{style_id}.png"

        try:
            result = render_frame(
                style_id=style_id,
                title=test_data["title"],
                bullets=test_data["bullets"],
                subtitle=test_data["subtitle"],
                output_path=str(output_path),
                scene_index=0,
                total_scenes=4,
            )

            if result and Path(result).exists():
                size = Path(result).stat().st_size / 1024  # KB
                print(f"  [OK] 成功: {result} ({size:.1f} KB)")
                results[style_id] = "OK"
            else:
                print(f"  [FAIL] 失败: 未生成文件")
                results[style_id] = "FAILED"
        except Exception as e:
            print(f"  [ERROR] 错误: {e}")
            results[style_id] = f"ERROR: {e}"

    # 汇总
    print("\n" + "=" * 60)
    print("  测试汇总")
    print("=" * 60)

    ok_count = sum(1 for v in results.values() if v == "OK")
    print(f"\n通过: {ok_count}/{len(styles)}")

    for style_id, status in results.items():
        symbol = "[OK]" if status == "OK" else "[FAIL]"
        print(f"  {symbol} {style_id}: {status}")

    print(f"\n输出目录: {output_dir}")

    return ok_count == len(styles)


if __name__ == "__main__":
    success = test_all_styles()
    sys.exit(0 if success else 1)
