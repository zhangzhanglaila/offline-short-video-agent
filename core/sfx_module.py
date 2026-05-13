# -*- coding: utf-8 -*-
"""
音效模块 — 纯 math 生成短促提示音（ding/whoosh/tick/emphasis）
零外部依赖，输出 16-bit PCM WAV，用 FFmpeg 混入最终音轨。
"""
import math
import struct
import wave
from pathlib import Path
from typing import List, Optional

SAMPLE_RATE = 44100
SAMPLE_WIDTH = 2  # 16-bit
MAX_AMP = 32767


def _make_wave(filename: str, samples: List[int], sr: int = SAMPLE_RATE):
    """写入 16-bit mono WAV 文件。"""
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(filename, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(sr)
        packed = b"".join(struct.pack("<h", max(-MAX_AMP, min(MAX_AMP, int(s)))) for s in samples)
        wf.writeframes(packed)
    return filename


def _envelope(t: float, duration: float, attack: float = 0.02, decay_start: float = 0.5) -> float:
    """ADSR 简易包络 — 淡入 → 保持 → 指数衰减。"""
    if t <= 0:
        return 0.0
    frac = t / duration
    if frac < attack:
        return frac / attack  # linear attack
    if frac < decay_start:
        return 1.0
    # exponential decay
    decay_frac = (frac - decay_start) / (1.0 - decay_start)
    return math.exp(-decay_frac * 4.0)


def generate_ding(output_path: str, freq: float = 880.0, duration: float = 0.15,
                  sr: int = SAMPLE_RATE) -> str:
    """清脆提示音「叮」— 正弦波 + 快速衰减。"""
    n = int(sr * duration)
    samples = []
    for i in range(n):
        t = i / sr
        env = _envelope(t, duration, attack=0.01, decay_start=0.15)
        # 轻微微颤
        vibrato = 1.0 + 0.003 * math.sin(2 * math.pi * 12 * t)
        val = MAX_AMP * 0.6 * env * math.sin(2 * math.pi * freq * vibrato * t)
        samples.append(val)
    return _make_wave(output_path, samples, sr)


def generate_emphasis_ding(output_path: str, duration: float = 0.25,
                           sr: int = SAMPLE_RATE) -> str:
    """双音强调提示音「叮-咚」— 大数字/图表完成时使用。"""
    n = int(sr * duration)
    samples = []
    f1, f2 = 1047.0, 1319.0  # C6 → E6 上行
    for i in range(n):
        t = i / sr
        env = _envelope(t, duration, attack=0.01, decay_start=0.35)
        # 前一半用 f1, 后一半渐变为 f2
        cross = min(1.0, t / (duration * 0.4))
        freq = f1 + (f2 - f1) * cross
        val = MAX_AMP * 0.55 * env * math.sin(2 * math.pi * freq * t)
        samples.append(val)
    return _make_wave(output_path, samples, sr)


def generate_whoosh(output_path: str, duration: float = 0.28,
                    sr: int = SAMPLE_RATE) -> str:
    """转场「唰」声 — 带通白噪声扫频。"""
    n = int(sr * duration)
    samples = []
    import random as _rand
    rng = _rand.Random(42)
    # 低频→高频扫频模拟风声
    for i in range(n):
        t = i / sr
        env = _envelope(t, duration, attack=0.02, decay_start=0.4)
        center_freq = 300 + 2000 * (t / duration)  # 低频扫到高频
        bw = 400 + 600 * (t / duration)
        # 简单谐振器：两个带通正弦叠加 + 噪声
        noise = (rng.random() - 0.5) * 2.0
        tone1 = math.sin(2 * math.pi * (center_freq - bw / 2) * t)
        tone2 = math.sin(2 * math.pi * (center_freq + bw / 2) * t)
        val = MAX_AMP * 0.25 * env * (noise * 0.6 + tone1 * 0.2 + tone2 * 0.2)
        samples.append(val)
    return _make_wave(output_path, samples, sr)


def generate_tick(output_path: str, duration: float = 0.04,
                  sr: int = SAMPLE_RATE) -> str:
    """极短点击音「咔」— 图表数据点动画用。"""
    n = int(sr * duration)
    samples = []
    for i in range(n):
        t = i / sr
        env = math.exp(-t * 80)  # 极快衰减
        val = MAX_AMP * 0.35 * env * math.sin(2 * math.pi * 1600 * t)
        samples.append(val)
    return _make_wave(output_path, samples, sr)


def generate_sfx_for_scenes(scenes: List[dict], output_dir: str) -> dict:
    """根据场景列表自动生成对应音效，返回 {start_time: wav_path} 映射。

    scenes: [{"start": 0.0, "emphasis": "big_number", ...}, ...]
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    sfx_map = {}

    for i, scene in enumerate(scenes):
        t = scene.get("start", 0)
        emphasis = scene.get("emphasis", "")

        if emphasis == "big_number":
            fp = str(out / f"sfx_emphasis_{i:03d}.wav")
            generate_emphasis_ding(fp)
            sfx_map[t] = fp
        elif emphasis in ("chart_done",):
            fp = str(out / f"sfx_ding_{i:03d}.wav")
            generate_ding(fp)
            sfx_map[t] = fp

        # 转场音效（片段间）
        if i < len(scenes) - 1:
            # 在场景切换前0.05s放 whoosh
            end_t = scene.get("end", t + 3)
            fp = str(out / f"sfx_whoosh_{i:03d}.wav")
            generate_whoosh(fp)
            sfx_map[max(0, end_t - 0.15)] = fp

    return sfx_map


def mix_sfx_to_video(video_path: str, tts_audio_path: str,
                     sfx_map: dict, bgm_path: str = None,
                     output_path: str = None) -> str:
    """将音效混入视频音频轨道。

    使用 FFmpeg amix 将 TTS + SFX + BGM 混合。
    sfx_map: {start_time_seconds: sfx_wav_path}
    """
    if output_path is None:
        output_path = str(Path(video_path).parent / "mixed_output.mp4")

    # 构建 FFmpeg 命令：多路音频输入 + adelay + amix
    inputs = ["-i", video_path]
    audio_inputs = []
    filter_parts = []

    # 视频原音轨
    audio_labels = ["[0:a]"]

    # TTS
    if tts_audio_path and Path(tts_audio_path).exists():
        inputs.extend(["-i", tts_audio_path])
        idx = len(audio_labels)
        audio_labels.append(f"[{idx}:a]")

    # BGM
    if bgm_path and Path(bgm_path).exists():
        inputs.extend(["-i", bgm_path])
        bgm_idx = len(audio_labels)
        audio_labels.append(f"[{bgm_idx}:a]")

    # SFX — 每个音效在指定时间偏移处混入
    sfx_inputs_start = len(audio_labels)
    sfx_parts = []
    for i, (start_time, sfx_path) in enumerate(sorted(sfx_map.items())):
        if Path(sfx_path).exists():
            inputs.extend(["-i", sfx_path])
            sidx = sfx_inputs_start + i
            delay_ms = int(start_time * 1000)
            sfx_parts.append(f"[{sidx}:a]adelay={delay_ms}|{delay_ms}[sfx{i}]")

    # 混合
    if sfx_parts:
        filter_parts.extend(sfx_parts)

    # amix: 将所有音轨混合
    mix_inputs = "".join(audio_labels)
    filter_parts.append(f"{mix_inputs}{''.join(f'[sfx{i}]' for i in range(len(sfx_parts)))}amix=inputs={len(audio_labels) + len(sfx_parts)}:duration=first:dropout_transition=2[aout]")
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]

    from core.utils.ffmpeg_runner import run_ffmpeg_safe
    if run_ffmpeg_safe(cmd):
        return output_path
    return video_path  # fallback: 返回原视频
