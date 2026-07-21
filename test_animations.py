# -*- coding: utf-8 -*-
"""
动效系统测试
验证文字动效引擎功能
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

from core.text_animator import (
    TextAnimator, AnimationComposer,
    AnimationConfig, AnimationType, EasingType,
    PresetAnimations
)
from core.animation_config import get_animation_config, list_animation_styles


def test_basic_animations():
    """测试基础动效"""
    print("=" * 60)
    print("  动效引擎测试")
    print("=" * 60)

    output_dir = Path(__file__).parent / "output" / "animation_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 测试数据
    test_text = "Python异步编程完全指南"
    fps = 30

    animator = TextAnimator(width=1080, height=1920, fps=fps)

    results = {}

    # 测试1: 淡入
    print("\n[TEST 1] 淡入效果...")
    try:
        config = PresetAnimations.fade_in(duration=0.5)

        def draw_callback(draw, text, x, y, alpha, **kwargs):
            if alpha > 0:
                draw.text((x, y), text, fill=(0, 0, 0, alpha))

        frames = animator.animate(test_text, config, draw_callback)
        print(f"  [OK] 生成 {len(frames)} 帧")
        results["fade"] = len(frames)

        # 保存关键帧
        _save_sample_frame(frames, test_text, output_dir / "fade_sample.png")

    except Exception as e:
        print(f"  [FAIL] {e}")
        results["fade"] = f"ERROR: {e}"

    # 测试2: 滑动
    print("\n[TEST 2] 滑动效果...")
    try:
        config = PresetAnimations.slide_from_left(duration=0.6)

        frames = animator.animate(test_text, config, lambda d, t, x, y, a, **kw: None)
        print(f"  [OK] 生成 {len(frames)} 帧")
        results["slide"] = len(frames)

    except Exception as e:
        print(f"  [FAIL] {e}")
        results["slide"] = f"ERROR: {e}"

    # 测试3: 缩放
    print("\n[TEST 3] 缩放效果...")
    try:
        config = PresetAnimations.zoom_in(duration=0.5)

        frames = animator.animate(test_text, config, lambda d, t, x, y, a, **kw: None)
        print(f"  [OK] 生成 {len(frames)} 帧")
        results["zoom"] = len(frames)

    except Exception as e:
        print(f"  [FAIL] {e}")
        results["zoom"] = f"ERROR: {e}"

    # 测试4: 打字机
    print("\n[TEST 4] 打字机效果...")
    try:
        config = PresetAnimations.typewriter(duration=1.0)

        frames = animator.animate(test_text, config, lambda d, t, x, y, a, **kw: None)
        print(f"  [OK] 生成 {len(frames)} 帧")
        results["typewriter"] = len(frames)

    except Exception as e:
        print(f"  [FAIL] {e}")
        results["typewriter"] = f"ERROR: {e}"

    # 测试5: 闪烁
    print("\n[TEST 5] 闪烁效果...")
    try:
        config = PresetAnimations.blink(duration=0.5, repeat=3)

        frames = animator.animate(test_text, config, lambda d, t, x, y, a, **kw: None)
        print(f"  [OK] 生成 {len(frames)} 帧")
        results["blink"] = len(frames)

    except Exception as e:
        print(f"  [FAIL] {e}")
        results["blink"] = f"ERROR: {e}"

    # 汇总
    print("\n" + "=" * 60)
    print("  测试汇总")
    print("=" * 60)

    ok_count = sum(1 for v in results.values() if isinstance(v, int))
    print(f"\n通过: {ok_count}/5")

    for test, result in results.items():
        symbol = "[OK]" if isinstance(result, int) else "[FAIL]"
        print(f"  {symbol} {test}: {result}")

    return ok_count == 5


def test_animation_config():
    """测试动效配置系统"""
    print("\n" + "=" * 60)
    print("  动效配置测试")
    print("=" * 60)

    styles = list_animation_styles()
    print(f"\n支持的动效风格: {styles}\n")

    results = {}

    for style_id in styles:
        print(f"[{style_id.upper()}] 检查配置...")
        try:
            config = get_animation_config(style_id)

            if not config:
                print(f"  [WARN] 无配置")
                results[style_id] = "NO_CONFIG"
                continue

            # 检查必要元素
            elements = ["title", "subtitle", "bullets", "footer"]
            missing = []
            for elem in elements:
                if elem not in config:
                    missing.append(elem)

            if missing:
                print(f"  [WARN] 缺少元素: {missing}")
                results[style_id] = f"MISSING: {missing}"
            else:
                print(f"  [OK] 配置完整")
                results[style_id] = "OK"

        except Exception as e:
            print(f"  [FAIL] {e}")
            results[style_id] = f"ERROR: {e}"

    # 汇总
    print("\n" + "=" * 60)
    print("  配置测试汇总")
    print("=" * 60)

    ok_count = sum(1 for v in results.values() if v == "OK")
    print(f"\n配置完整: {ok_count}/{len(styles)}")

    return ok_count


def test_composer():
    """测试动效组合器"""
    print("\n" + "=" * 60)
    print("  动效组合器测试")
    print("=" * 60)

    try:
        composer = AnimationComposer(fps=30)

        # 添加多个动效
        composer.add(
            "标题1",
            PresetAnimations.fade_in(0.5),
            lambda d, t, x, y, a, **kw: None,
            start_frame=0
        )

        composer.add(
            "标题2",
            PresetAnimations.slide_from_left(0.4),
            lambda d, t, x, y, a, **kw: None,
            start_frame=15
        )

        frames = composer.render(1080, 1920)

        print(f"\n  [OK] 生成 {len(frames)} 帧")
        print("  组合器测试: 通过")
        return True

    except Exception as e:
        print(f"\n  [FAIL] {e}")
        print("  组合器测试: 失败")
        return False


def _save_sample_frame(frames, text, output_path):
    """保存示例帧"""
    if not frames:
        return

    try:
        # 取中间帧
        mid_idx = len(frames) // 2
        frame_data = frames[mid_idx]

        img = Image.new("RGB", (1080, 1920), "#FFFFFF")
        draw = ImageDraw.Draw(img)

        # 尝试加载字体
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 56)
        except:
            font = ImageFont.load_default()

        # 应用动效参数
        params = frame_data[1]
        alpha = params.get("alpha", 255)
        if alpha > 0:
            color = (0, 0, 0, min(255, alpha))
            draw.text((100, 500), text, fill=color[:3], font=font)

        img.save(output_path, quality=95)
    except Exception as e:
        print(f"    [WARN] 保存示例帧失败: {e}")


if __name__ == "__main__":
    success = True

    # 运行测试
    if not test_basic_animations():
        success = False

    if not test_animation_config():
        success = False

    if not test_composer():
        success = False

    sys.exit(0 if success else 1)
