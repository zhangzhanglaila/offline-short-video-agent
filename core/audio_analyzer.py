# -*- coding: utf-8 -*-
"""
音频分析系统
分析音乐的BPM、节拍和音频特性
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AudioFeatures:
    """音频特性"""
    duration: float          # 时长(秒)
    sample_rate: int        # 采样率
    channels: int           # 声道数
    bitrate: int            # 比特率
    format: str             # 文件格式


@dataclass
class BeatInfo:
    """节拍信息"""
    bpm: float              # BPM
    beat_times: List[float] # 节拍时间列表(秒)
    confidence: float       # 置信度(0.0-1.0)
    time_signature: str     # 拍号 (e.g., "4/4")


class AudioAnalyzer:
    """音频分析器 - 分析音乐特性"""

    def __init__(self):
        self.has_librosa = self._check_librosa()
        self.has_soundfile = self._check_soundfile()

    def _check_librosa(self) -> bool:
        """检查librosa是否可用"""
        try:
            import librosa
            return True
        except ImportError:
            return False

    def _check_soundfile(self) -> bool:
        """检查soundfile是否可用"""
        try:
            import soundfile
            return True
        except ImportError:
            return False

    def get_audio_features(self, audio_path: str) -> Optional[AudioFeatures]:
        """
        获取音频特性

        Args:
            audio_path: 音频文件路径

        Returns:
            AudioFeatures 对象
        """
        if not Path(audio_path).exists():
            print(f"[AudioAnalyzer] File not found: {audio_path}")
            return None

        try:
            # 尝试使用librosa
            if self.has_librosa:
                import librosa

                y, sr = librosa.load(audio_path, sr=None)
                duration = librosa.get_duration(y=y, sr=sr)

                return AudioFeatures(
                    duration=duration,
                    sample_rate=sr,
                    channels=1,  # librosa默认转换为单声道
                    bitrate=0,   # librosa不提供比特率
                    format=Path(audio_path).suffix.lower()
                )

            # 尝试使用soundfile
            elif self.has_soundfile:
                import soundfile as sf

                data, sr = sf.read(audio_path, dtype='float32')

                return AudioFeatures(
                    duration=len(data) / sr,
                    sample_rate=sr,
                    channels=data.ndim if data.ndim > 1 else 1,
                    bitrate=0,
                    format=Path(audio_path).suffix.lower()
                )

            else:
                # 使用ffprobe获取基本信息
                import subprocess
                import json

                result = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json",
                     "-show_format", "-show_streams", audio_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    fmt = data.get("format", {})
                    duration = float(fmt.get("duration", 0))

                    # 获取第一个音频流
                    streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
                    if streams:
                        stream = streams[0]
                        return AudioFeatures(
                            duration=duration,
                            sample_rate=int(stream.get("sample_rate", 44100)),
                            channels=int(stream.get("channels", 2)),
                            bitrate=int(stream.get("bit_rate", 128000)),
                            format=Path(audio_path).suffix.lower()
                        )

                return AudioFeatures(
                    duration=duration,
                    sample_rate=44100,
                    channels=2,
                    bitrate=128000,
                    format=Path(audio_path).suffix.lower()
                )

        except Exception as e:
            print(f"[AudioAnalyzer] Failed to analyze audio: {e}")
            return None

    def estimate_bpm(self, audio_path: str) -> Optional[float]:
        """
        估算BPM

        Args:
            audio_path: 音频文件路径

        Returns:
            BPM值
        """
        if not self.has_librosa:
            print("[AudioAnalyzer] librosa not available, using estimation")
            return self._estimate_bpm_heuristic(audio_path)

        try:
            import librosa
            import numpy as np

            y, sr = librosa.load(audio_path, sr=None)

            # 提取节拍
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            bpm = librosa.beat.tempo(onset_strength=onset_env, sr=sr)

            # 返回第一个BPM值或平均值
            if isinstance(bpm, np.ndarray):
                return float(np.mean(bpm))
            else:
                return float(bpm)

        except Exception as e:
            print(f"[AudioAnalyzer] BPM estimation failed: {e}")
            return self._estimate_bpm_heuristic(audio_path)

    def _estimate_bpm_heuristic(self, audio_path: str) -> float:
        """
        启发式BPM估算 (当librosa不可用时)

        基于文件大小和时长的粗略估计
        """
        try:
            features = self.get_audio_features(audio_path)
            if not features:
                return 120.0  # 默认BPM

            # 粗略估计: 基于音频时长
            # 较短的音频通常节奏较快
            if features.duration < 60:
                return 140.0  # 快速音乐
            elif features.duration < 180:
                return 120.0  # 中等节奏
            else:
                return 100.0  # 缓慢音乐

        except Exception:
            return 120.0


class BeatExtractor:
    """节拍提取器 - 从音频提取节拍信息"""

    def __init__(self):
        self.has_librosa = self._check_librosa()

    def _check_librosa(self) -> bool:
        """检查librosa是否可用"""
        try:
            import librosa
            return True
        except ImportError:
            return False

    def extract_beats(
        self,
        audio_path: str,
        expected_bpm: Optional[float] = None
    ) -> Optional[BeatInfo]:
        """
        提取节拍信息

        Args:
            audio_path: 音频文件路径
            expected_bpm: 期望的BPM (可选)

        Returns:
            BeatInfo 对象
        """
        if not self.has_librosa:
            print("[BeatExtractor] librosa not available, generating synthetic beats")
            return self._generate_synthetic_beats(audio_path, expected_bpm)

        try:
            import librosa
            import numpy as np

            y, sr = librosa.load(audio_path, sr=None)

            # 提取节拍
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            bpm = librosa.beat.tempo(onset_strength=onset_env, sr=sr)

            if isinstance(bpm, np.ndarray):
                bpm_value = float(np.mean(bpm))
                confidence = float(np.std(bpm) / (np.mean(bpm) + 1e-6))
            else:
                bpm_value = float(bpm)
                confidence = 0.8

            # 获取节拍帧
            frames = librosa.beat.beat_track(onset_strength=onset_env, sr=sr, bpm=bpm_value)[1]
            beat_times = librosa.frames_to_time(frames, sr=sr).tolist()

            return BeatInfo(
                bpm=bpm_value,
                beat_times=beat_times,
                confidence=min(1.0, confidence),
                time_signature="4/4"  # 默认4/4拍
            )

        except Exception as e:
            print(f"[BeatExtractor] Beat extraction failed: {e}")
            return self._generate_synthetic_beats(audio_path, expected_bpm)

    def _generate_synthetic_beats(
        self,
        audio_path: str,
        expected_bpm: Optional[float] = None
    ) -> Optional[BeatInfo]:
        """
        生成合成节拍 (当librosa不可用时)

        Args:
            audio_path: 音频文件路径
            expected_bpm: 期望的BPM

        Returns:
            BeatInfo 对象 (合成)
        """
        try:
            analyzer = AudioAnalyzer()
            features = analyzer.get_audio_features(audio_path)

            if not features:
                return None

            # 使用期望BPM或估算BPM
            bpm = expected_bpm or analyzer.estimate_bpm(audio_path) or 120.0

            # 生成节拍时间列表
            beat_interval = 60.0 / bpm  # 节拍间隔(秒)
            beat_times = []

            current_time = 0.0
            while current_time < features.duration:
                beat_times.append(current_time)
                current_time += beat_interval

            return BeatInfo(
                bpm=bpm,
                beat_times=beat_times,
                confidence=0.6,  # 较低的置信度表示合成节拍
                time_signature="4/4"
            )

        except Exception as e:
            print(f"[BeatExtractor] Synthetic beat generation failed: {e}")
            return None


class AudioMusicSynchronizer:
    """音乐同步器 - 同步视频与音乐"""

    def __init__(self):
        self.analyzer = AudioAnalyzer()
        self.extractor = BeatExtractor()

    def analyze_music(self, audio_path: str) -> Dict:
        """
        完整的音乐分析

        Args:
            audio_path: 音频文件路径

        Returns:
            分析结果字典
        """
        print(f"[AudioMusicSynchronizer] Analyzing: {audio_path}")

        features = self.analyzer.get_audio_features(audio_path)
        if not features:
            return {"status": "error", "message": "Failed to get audio features"}

        bpm = self.analyzer.estimate_bpm(audio_path)
        beats = self.extractor.extract_beats(audio_path, bpm)

        if not beats:
            return {"status": "error", "message": "Failed to extract beats"}

        return {
            "status": "success",
            "features": {
                "duration": features.duration,
                "sample_rate": features.sample_rate,
                "channels": features.channels,
                "format": features.format
            },
            "beats": {
                "bpm": beats.bpm,
                "beat_count": len(beats.beat_times),
                "confidence": beats.confidence,
                "time_signature": beats.time_signature,
                "beat_times": beats.beat_times[:10]  # 返回前10个节拍
            }
        }

    def get_beat_at_time(
        self,
        beats: BeatInfo,
        time_seconds: float
    ) -> Optional[Tuple[int, float]]:
        """
        获取指定时间的节拍

        Args:
            beats: 节拍信息
            time_seconds: 时间(秒)

        Returns:
            (beat_index, beat_time) 或 None
        """
        if not beats or not beats.beat_times:
            return None

        for i, beat_time in enumerate(beats.beat_times):
            if abs(beat_time - time_seconds) < 0.05:  # 50毫秒容差
                return (i, beat_time)

        # 找到最接近的节拍
        closest_idx = min(
            range(len(beats.beat_times)),
            key=lambda i: abs(beats.beat_times[i] - time_seconds)
        )

        return (closest_idx, beats.beat_times[closest_idx])

    def align_events_to_beats(
        self,
        events: List[Dict],
        beats: BeatInfo
    ) -> List[Dict]:
        """
        将事件对齐到节拍

        Args:
            events: 事件列表 (每个包含 'time' 字段)
            beats: 节拍信息

        Returns:
            对齐后的事件列表
        """
        aligned = []

        for event in events:
            event_time = event.get("time", 0)
            beat_info = self.get_beat_at_time(beats, event_time)

            if beat_info:
                beat_idx, beat_time = beat_info
                aligned_event = event.copy()
                aligned_event["aligned_time"] = beat_time
                aligned_event["beat_index"] = beat_idx
                aligned_event["time_offset"] = abs(beat_time - event_time)
                aligned.append(aligned_event)

        return aligned


# 便捷函数
def create_audio_analyzer() -> AudioAnalyzer:
    """创建音频分析器"""
    return AudioAnalyzer()


def create_beat_extractor() -> BeatExtractor:
    """创建节拍提取器"""
    return BeatExtractor()


def create_synchronizer() -> AudioMusicSynchronizer:
    """创建音乐同步器"""
    return AudioMusicSynchronizer()
