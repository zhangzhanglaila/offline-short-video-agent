# -*- coding: utf-8 -*-
"""
转场效果和节奏系统测试
验证完整的视频节奏控制功能
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

from core.transition_effects import (
    TransitionType, TransitionDirection, TransitionConfig,
    TransitionLibrary, create_preset_library
)
from core.rhythm_engine import (
    RhythmType, RhythmTemplate, RhythmEngine,
    RhythmAnalyzer, VideoRhythmController
)


def test_transition_library():
    """测试转场效果库"""
    print("=" * 60)
    print("  转场效果库测试")
    print("=" * 60)

    # 创建预设库
    lib = create_preset_library()

    print(f"\n[1] 可用转场效果:")
    transitions = lib.list_transitions()
    print(f"  总数: {len(transitions)}")

    for trans in transitions:
        config = lib.get_transition(trans)
        print(f"    - {trans}: {config.type.value} ({config.duration}s)")

    # 检查特定转场
    print(f"\n[2] 转场配置检查:")
    fade_config = lib.get_transition("fade")
    if fade_config:
        print(f"  [OK] Fade: 类型={fade_config.type.value}, 时长={fade_config.duration}s")

    slide_config = lib.get_transition("slide_left")
    if slide_config:
        print(f"  [OK] Slide Left: 方向={slide_config.direction.value}, 时长={slide_config.duration}s")

    return len(transitions) >= 10


def test_rhythm_engine():
    """测试节奏引擎"""
    print("\n" + "=" * 60)
    print("  节奏引擎测试")
    print("=" * 60)

    engine = RhythmEngine()

    print(f"\n[1] 可用节奏模板:")
    templates = engine.list_templates()
    print(f"  总数: {len(templates)}")

    for template_name in templates:
        template = engine.get_template(template_name)
        print(f"    - {template.name}")
        print(f"      场景时长: {template.scene_duration}s")
        print(f"      转场时长: {template.transition_duration}s")
        print(f"      转场风格: {template.transition_style}")

    # 计算视频时长
    print(f"\n[2] 视频时长计算:")
    num_scenes = 5
    for template_name in ["slow", "medium", "fast"]:
        duration = engine.calculate_duration(num_scenes, template_name)
        print(f"  {template_name}: {num_scenes}个场景 = {duration:.1f}秒")

    # 获取场景时间安排
    print(f"\n[3] 场景时间安排 (medium节奏, 3个场景):")
    timings = engine.get_scene_timing(3, "medium")
    for timing in timings:
        print(f"  场景{timing['scene_index']}: {timing['start']:.1f}s - {timing['start']+timing['duration']:.1f}s")
        if timing["transition"]:
            print(f"    转场: {timing['transition']} ({timing['transition_duration']:.1f}s)")

    return len(templates) >= 4


def test_rhythm_analyzer():
    """测试节奏分析器"""
    print("\n" + "=" * 60)
    print("  节奏分析器测试")
    print("=" * 60)

    analyzer = RhythmAnalyzer()

    # 测试内容分析
    print(f"\n[1] 内容节奏推荐:")

    test_cases = [
        ("欢快的音乐舞蹈视频", "music"),
        ("美食烹饪教程", "food"),
        ("编程教学讲解", "tutorial"),
        ("自然风景旅游", "travel"),
        ("综艺搞笑合集", "comedy")
    ]

    for title, content_type in test_cases:
        recommended = analyzer.analyze_content(title, content_type)
        print(f"  '{title}' → {recommended}节奏")

    # 测试音乐自适应
    print(f"\n[2] 音乐BPM自适应:")

    bpm_tests = [60, 100, 140, 180]
    for bpm in bpm_tests:
        rhythm = analyzer.adapt_to_music(bpm)
        print(f"  BPM {bpm} → {rhythm}节奏")

    return True


def test_rhythm_controller():
    """测试节奏控制器"""
    print("\n" + "=" * 60)
    print("  节奏控制器测试")
    print("=" * 60)

    controller = VideoRhythmController()

    # 创建测试分镜
    storyboard = [
        {
            "title": "场景1",
            "subtitle": "开场",
            "bullets": ["介绍"]
        },
        {
            "title": "场景2",
            "subtitle": "内容",
            "bullets": ["讲解"]
        },
        {
            "title": "场景3",
            "subtitle": "结尾",
            "bullets": ["总结"]
        }
    ]

    # 测试视频结构创建
    print(f"\n[1] 创建视频结构 (medium节奏):")

    structure = controller.create_video_structure(storyboard, "medium")
    info = controller.get_video_info(structure)

    print(f"  节奏模板: {info['rhythm_template']}")
    print(f"  总时长: {info['total_duration']:.1f}秒")
    print(f"  场景数: {info['num_scenes']}")
    print(f"  单场景时长: {info['scene_duration']}秒")
    print(f"  转场风格: {info['transition_style']}")

    # 测试节奏优化
    print(f"\n[2] 节奏优化:")

    # 基于音乐BPM
    optimized = controller.optimize_rhythm(
        storyboard,
        music_bpm=140,
        content_type="general"
    )
    print(f"  BPM 140 → {optimized}节奏")

    # 基于内容类型
    title_storyboard = storyboard.copy()
    title_storyboard[0]["title"] = "音乐舞蹈教学"
    optimized = controller.optimize_rhythm(title_storyboard, content_type="music")
    print(f"  音乐内容 → {optimized}节奏")

    return True


def test_custom_transitions():
    """测试自定义转场"""
    print("\n" + "=" * 60)
    print("  自定义转场测试")
    print("=" * 60)

    lib = create_preset_library()

    # 创建自定义转场
    from core.transition_effects import TransitionConfig, TransitionType, TransitionDirection

    custom = TransitionConfig(
        type=TransitionType.SLIDE,
        duration=0.8,
        direction=TransitionDirection.RIGHT,
        easing="ease_in_out",
        intensity=1.0
    )

    lib.add_transition("custom_slide_right", custom)

    print(f"\n[1] 添加自定义转场:")
    print(f"  转场名: custom_slide_right")
    print(f"  类型: {custom.type.value}")
    print(f"  方向: {custom.direction.value}")
    print(f"  时长: {custom.duration}s")

    # 验证添加成功
    retrieved = lib.get_transition("custom_slide_right")
    if retrieved:
        print(f"\n[OK] 自定义转场成功添加")
        return True
    else:
        print(f"\n[FAIL] 自定义转场添加失败")
        return False


if __name__ == "__main__":
    print("转场效果与节奏系统测试")
    print("=" * 60)

    results = {}

    # 测试1: 转场效果库
    results["转场效果库"] = test_transition_library()

    # 测试2: 节奏引擎
    results["节奏引擎"] = test_rhythm_engine()

    # 测试3: 节奏分析器
    results["节奏分析器"] = test_rhythm_analyzer()

    # 测试4: 节奏控制器
    results["节奏控制器"] = test_rhythm_controller()

    # 测试5: 自定义转场
    results["自定义转场"] = test_custom_transitions()

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
