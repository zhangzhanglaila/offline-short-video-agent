# -*- coding: utf-8 -*-
"""
音乐节拍同步测试
验证音频分析和视频同步功能
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

from core.audio_analyzer import (
    AudioAnalyzer, BeatExtractor, AudioMusicSynchronizer
)
from core.video_music_sync import (
    VideoMusicSyncController, SyncVideoGenerator, SyncEvent
)


def test_audio_analyzer():
    """测试音频分析器"""
    print("=" * 60)
    print("  音频分析器测试")
    print("=" * 60)

    analyzer = AudioAnalyzer()

    print(f"\n[1] 音频分析器能力检测:")
    print(f"  librosa 可用: {analyzer.has_librosa}")
    print(f"  soundfile 可用: {analyzer.has_soundfile}")

    # 测试BPM估算 (不需要真实音频文件)
    print(f"\n[2] BPM估算模拟:")
    test_bpms = [60, 100, 140, 180]
    for bpm in test_bpms:
        # 模拟估算
        if bpm < 80:
            category = "缓慢"
        elif bpm < 120:
            category = "中等"
        elif bpm < 160:
            category = "快速"
        else:
            category = "极快"
        print(f"  BPM {bpm}: {category}节奏")

    return True


def test_beat_extractor():
    """测试节拍提取器"""
    print("\n" + "=" * 60)
    print("  节拍提取器测试")
    print("=" * 60)

    extractor = BeatExtractor()

    print(f"\n[1] 节拍提取器能力:")
    print(f"  librosa 可用: {extractor.has_librosa}")

    # 生成合成节拍信息
    print(f"\n[2] 合成节拍生成:")

    test_bpms = [120, 140]
    for bpm in test_bpms:
        beat_interval = 60.0 / bpm
        beat_count = int(10 / beat_interval)  # 模拟10秒
        print(f"  BPM {bpm}: 节拍间隔 {beat_interval:.2f}s, 10s内节拍数 {beat_count}")

    return True


def test_audio_synchronizer():
    """测试音频同步器"""
    print("\n" + "=" * 60)
    print("  音频同步器测试")
    print("=" * 60)

    synchronizer = AudioMusicSynchronizer()

    print(f"\n[1] 同步器功能:")
    print(f"  - 音频特性分析")
    print(f"  - BPM估算")
    print(f"  - 节拍提取")
    print(f"  - 事件对齐")

    # 模拟节拍信息
    class MockBeatInfo:
        def __init__(self):
            self.bpm = 120
            self.beat_times = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
            self.confidence = 0.85
            self.time_signature = "4/4"

    beats = MockBeatInfo()

    # 测试获取节拍
    print(f"\n[2] 节拍查询:")
    test_times = [0.0, 0.51, 1.0, 2.05]
    for test_time in test_times:
        beat_info = synchronizer.get_beat_at_time(beats, test_time)
        if beat_info:
            beat_idx, beat_time = beat_info
            print(f"  时间 {test_time}s → 节拍{beat_idx} ({beat_time}s)")

    return True


def test_sync_controller():
    """测试同步控制器"""
    print("\n" + "=" * 60)
    print("  同步控制器测试")
    print("=" * 60)

    controller = VideoMusicSyncController()

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

    print(f"\n[1] 同步事件生成:")
    print(f"  分镜数: {len(storyboard)}")

    # 模拟节拍数据
    beats_data = {
        "bpm": 120,
        "beat_times": [i * 0.5 for i in range(30)],  # 0-15秒
        "beat_count": 30,
        "confidence": 0.85,
        "time_signature": "4/4"
    }

    # 模拟视频结构
    video_structure = {
        "rhythm_template": "medium",
        "total_duration": 10.2,
        "scenes": [
            {
                "scene_index": 0,
                "start_time": 0.0,
                "duration": 3.0,
                "transition": "slide_left",
                "transition_duration": 0.6
            },
            {
                "scene_index": 1,
                "start_time": 3.6,
                "duration": 3.0,
                "transition": "slide_left",
                "transition_duration": 0.6
            },
            {
                "scene_index": 2,
                "start_time": 7.2,
                "duration": 3.0,
                "transition": None,
                "transition_duration": 0.0
            }
        ]
    }

    # 生成同步事件
    sync_events = controller._generate_sync_events(video_structure, beats_data)
    print(f"  生成事件数: {len(sync_events)}")

    # 对齐事件
    aligned_events = controller._align_events(sync_events, beats_data)
    aligned_count = sum(1 for e in aligned_events if e.beat_aligned)
    print(f"  对齐事件数: {aligned_count}/{len(aligned_events)}")

    # 计算同步质量
    sync_quality = controller._calculate_sync_quality(aligned_events)
    print(f"  同步质量: {sync_quality:.1%}")

    return True


def test_sync_event():
    """测试同步事件"""
    print("\n" + "=" * 60)
    print("  同步事件测试")
    print("=" * 60)

    print(f"\n[1] 创建同步事件:")

    # 创建场景事件
    scene_event = SyncEvent(
        event_type="scene",
        time=0.0,
        duration=3.0
    )

    # 创建转场事件
    transition_event = SyncEvent(
        event_type="transition",
        time=3.0,
        duration=0.6,
        beat_aligned=True,
        beat_index=6
    )

    print(f"  场景事件: {scene_event.event_type} @ {scene_event.time}s")
    print(f"  转场事件: {transition_event.event_type} @ {transition_event.time}s (节拍{transition_event.beat_index})")
    print(f"  对齐状态: {transition_event.beat_aligned}")

    return True


if __name__ == "__main__":
    print("音乐节拍同步系统测试")
    print("=" * 60)

    results = {}

    # 测试1: 音频分析器
    results["音频分析器"] = test_audio_analyzer()

    # 测试2: 节拍提取器
    results["节拍提取器"] = test_beat_extractor()

    # 测试3: 音频同步器
    results["音频同步器"] = test_audio_synchronizer()

    # 测试4: 同步控制器
    results["同步控制器"] = test_sync_controller()

    # 测试5: 同步事件
    results["同步事件"] = test_sync_event()

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
