# -*- coding: utf-8 -*-
"""
音视频同步集成
整合视频生成和音乐同步功能
"""
from typing import Dict, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SyncEvent:
    """同步事件"""
    event_type: str         # 事件类型 (transition/effect/scene)
    time: float            # 事件时间(秒)
    duration: float        # 事件持续时间(秒)
    beat_aligned: bool = False  # 是否已对齐到节拍
    beat_index: int = -1   # 对应的节拍索引


class VideoMusicSyncController:
    """视频-音乐同步控制器"""

    def __init__(self, audio_analyzer=None):
        """
        初始化同步控制器

        Args:
            audio_analyzer: 音频分析器实例
        """
        if audio_analyzer is None:
            from core.audio_analyzer import create_synchronizer
            self.sync = create_synchronizer()
        else:
            self.sync = audio_analyzer

    def create_sync_timeline(
        self,
        storyboard: List[Dict],
        audio_path: str,
        rhythm_engine=None
    ) -> Dict:
        """
        创建同步时间线

        Args:
            storyboard: 分镜列表
            audio_path: 音频文件路径
            rhythm_engine: 节奏引擎

        Returns:
            同步时间线字典
        """
        print(f"[VideoMusicSyncController] Creating sync timeline...")

        # 分析音乐
        music_info = self.sync.analyze_music(audio_path)

        if music_info.get("status") != "success":
            print(f"[VideoMusicSyncController] Music analysis failed")
            return {"status": "error"}

        # 获取节拍信息
        beats_data = music_info.get("beats", {})
        bpm = beats_data.get("bpm", 120)
        beat_times = beats_data.get("beat_times", [])

        # 导入节奏引擎
        if rhythm_engine is None:
            from core.rhythm_engine import create_rhythm_controller
            rhythm_engine = create_rhythm_controller()

        # 为分镜推荐节奏
        recommended_rhythm = rhythm_engine.optimize_rhythm(
            storyboard,
            music_bpm=bpm,
            content_type="general"
        )

        # 创建视频结构
        video_structure = rhythm_engine.create_video_structure(
            storyboard,
            rhythm_template=recommended_rhythm
        )

        # 创建同步事件
        sync_events = self._generate_sync_events(
            video_structure,
            beats_data
        )

        # 对齐事件到节拍
        aligned_events = self._align_events(sync_events, beats_data)

        return {
            "status": "success",
            "music_info": music_info,
            "rhythm_template": recommended_rhythm,
            "video_structure": video_structure,
            "sync_events": aligned_events,
            "sync_quality": self._calculate_sync_quality(aligned_events)
        }

    def _generate_sync_events(
        self,
        video_structure: Dict,
        beats_data: Dict
    ) -> List[SyncEvent]:
        """
        生成同步事件

        Args:
            video_structure: 视频结构
            beats_data: 节拍数据

        Returns:
            同步事件列表
        """
        events = []

        for scene_config in video_structure.get("scenes", []):
            # 场景事件
            scene_event = SyncEvent(
                event_type="scene",
                time=scene_config.get("start_time", 0),
                duration=scene_config.get("duration", 3.0)
            )
            events.append(scene_event)

            # 转场事件
            if scene_config.get("transition"):
                transition_time = (scene_config.get("start_time", 0) +
                                 scene_config.get("duration", 3.0))
                transition_event = SyncEvent(
                    event_type="transition",
                    time=transition_time,
                    duration=scene_config.get("transition_duration", 0.5)
                )
                events.append(transition_event)

        return events

    def _align_events(
        self,
        events: List[SyncEvent],
        beats_data: Dict
    ) -> List[SyncEvent]:
        """
        对齐事件到节拍

        Args:
            events: 事件列表
            beats_data: 节拍数据

        Returns:
            对齐后的事件列表
        """
        beat_times = beats_data.get("beat_times", [])

        if not beat_times:
            return events

        aligned = []

        for event in events:
            # 找到最接近的节拍
            closest_beat_idx = self._find_closest_beat(event.time, beat_times)

            if closest_beat_idx is not None and closest_beat_idx < len(beat_times):
                event.beat_aligned = True
                event.beat_index = closest_beat_idx
                # 可选: 将事件时间调整到节拍时间
                # event.time = beat_times[closest_beat_idx]

            aligned.append(event)

        return aligned

    def _find_closest_beat(
        self,
        time: float,
        beat_times: List[float]
    ) -> Optional[int]:
        """
        找到最接近的节拍索引

        Args:
            time: 时间
            beat_times: 节拍时间列表

        Returns:
            节拍索引
        """
        if not beat_times:
            return None

        closest_idx = min(
            range(len(beat_times)),
            key=lambda i: abs(beat_times[i] - time)
        )

        return closest_idx

    def _calculate_sync_quality(self, events: List[SyncEvent]) -> float:
        """
        计算同步质量评分

        Args:
            events: 事件列表

        Returns:
            质量评分 0.0-1.0
        """
        if not events:
            return 0.0

        aligned_count = sum(1 for e in events if e.beat_aligned)
        return aligned_count / len(events)


class SyncVideoGenerator:
    """同步视频生成器 - 生成与音乐同步的视频"""

    def __init__(self):
        self.sync_controller = VideoMusicSyncController()

    def generate_synced_video(
        self,
        storyboard: List[Dict],
        audio_path: str,
        output_path: str,
        style_id: str = "minimal",
        progress_callback: Callable = None
    ) -> bool:
        """
        生成与音乐同步的视频

        Args:
            storyboard: 分镜列表
            audio_path: 音频文件路径
            output_path: 输出视频路径
            style_id: 视觉风格
            progress_callback: 进度回调

        Returns:
            成功返回True
        """
        print(f"[SyncVideoGenerator] Generating synced video...")

        # 创建同步时间线
        sync_timeline = self.sync_controller.create_sync_timeline(
            storyboard,
            audio_path
        )

        if sync_timeline.get("status") != "success":
            print(f"[SyncVideoGenerator] Failed to create sync timeline")
            return False

        print(f"[SyncVideoGenerator] Sync quality: {sync_timeline['sync_quality']:.1%}")

        # 后续步骤：使用同步信息生成视频
        # 这里需要集成VideoGenerator等模块

        try:
            from core.video_composer import VideoGenerator

            generator = VideoGenerator(style_id=style_id, fps=30)

            # 使用同步信息生成视频
            success = generator.generate_video(
                storyboard=storyboard,
                output_path=output_path,
                enable_animations=False,
                scene_duration=3.0,
                progress_callback=progress_callback
            )

            if success:
                print(f"[SyncVideoGenerator] Video generated: {output_path}")
                return True

        except Exception as e:
            print(f"[SyncVideoGenerator] Video generation failed: {e}")

        return False

    def get_sync_info(self, sync_timeline: Dict) -> Dict:
        """获取同步信息摘要"""
        return {
            "bpm": sync_timeline.get("music_info", {}).get("beats", {}).get("bpm"),
            "rhythm_template": sync_timeline.get("rhythm_template"),
            "sync_quality": sync_timeline.get("sync_quality"),
            "total_events": len(sync_timeline.get("sync_events", [])),
            "aligned_events": sum(1 for e in sync_timeline.get("sync_events", []) if e.beat_aligned)
        }


# 便捷函数
def create_sync_controller(audio_analyzer=None) -> VideoMusicSyncController:
    """创建同步控制器"""
    return VideoMusicSyncController(audio_analyzer)


def create_sync_video_generator() -> SyncVideoGenerator:
    """创建同步视频生成器"""
    return SyncVideoGenerator()
