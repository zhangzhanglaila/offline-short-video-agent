# -*- coding: utf-8 -*-
"""
素材智能剪辑模块 (原双模式生成器)
Mode A 已迁移至 topic_pipeline_api.py + pipeline_helpers.py
Mode B 素材智能剪辑：用户上传素材→仅剪辑拼接→转场→字幕烧录→多轨道合成
"""
import os
import re
import json
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import config
from core.tts_module import get_tts_module
from core.subtitle_module import get_subtitle_module
from core.video_module import get_video_module
from core.animation_module import get_animation_module
from core.timeline_sync_module import get_timeline_module

# 日志回调 - 实时推送进度到前端
_dual_log_callback = None

def set_dual_log_callback(callback):
    global _dual_log_callback
    _dual_log_callback = callback

def _log(msg: str, level: str = 'info'):
    if _dual_log_callback:
        try:
            _dual_log_callback(msg, level)
        except Exception:
            pass


def _parse_srt(srt_path: str) -> list:
    """解析SRT字幕文件，返回 [(start_sec, end_sec, text), ...]"""
    segments = []
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        pattern = r'(\d+)\s*\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n(.*?)(?=\n\n|\n\d+\s*\n|\Z)'
        for m in re.finditer(pattern, content, re.DOTALL):
            start = _srt_time_to_sec(m.group(2))
            end = _srt_time_to_sec(m.group(3))
            text = m.group(4).strip().replace('\n', ' ')
            if text:
                segments.append((start, end, text))
    except Exception as e:
        _log(f"SRT解析失败: {e}", 'warn')
    return segments


def _srt_time_to_sec(t: str) -> float:
    """SRT时间码转秒数: HH:MM:SS,mmm -> float"""
    h, m, rest = t.split(':')
    s, ms = rest.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def multitrack_composite(
    video_path: str,
    audio_path: str,
    subtitle_path: str,
    bgm_path: str,
    output_path: str
) -> bool:
    """多轨道合成（模块级函数，供 ecom 管线等外部调用）"""
    subtitled_video = Path(output_path).parent / "video_with_subs.mp4"

    if subtitle_path and Path(subtitle_path).exists():
        segments = _parse_srt(subtitle_path)
        if segments:
            drawtext_filters = []
            total = len(segments)
            for i, (start, end, text) in enumerate(segments):
                escaped = text.replace("'", "\\'").replace(":", "\\:").replace("\\", "\\\\")
                is_title = (i == 0 and len(text) < 30) or (i == 0 and total > 2)
                if is_title:
                    dt = (
                        f"drawtext=text='{escaped}'"
                        f":fontfile=C\\\\:/Windows/Fonts/msyh.ttc"
                        f":fontsize=56"
                        f":fontcolor=#1a1a2e"
                        f":borderw=3"
                        f":bordercolor=#1a1a2e"
                        f":box=1"
                        f":boxcolor=white@0.92"
                        f":boxborderw=20"
                        f":x=80"
                        f":y=280"
                        f":enable='between(t,{start:.3f},{end:.3f})'"
                    )
                else:
                    dt = (
                        f"drawtext=text='{escaped}'"
                        f":fontfile=C\\\\:/Windows/Fonts/msyh.ttc"
                        f":fontsize=40"
                        f":fontcolor=#232529"
                        f":borderw=1"
                        f":bordercolor=#232529"
                        f":box=1"
                        f":boxcolor=white@0.85"
                        f":boxborderw=16"
                        f":line_spacing=12"
                        f":x=80"
                        f":y=400"
                        f":enable='between(t,{start:.3f},{end:.3f})'"
                    )
                drawtext_filters.append(dt)

            vf = ",".join(drawtext_filters)
            cmd_sub = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", vf,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", str(config.OUTPUT_CRF),
                "-an",
                str(subtitled_video)
            ]

            try:
                result = subprocess.run(cmd_sub, capture_output=True, text=True, timeout=600)
                if result.returncode != 0 or not subtitled_video.exists():
                    _log(f"字幕烧录失败，跳过字幕继续合成: {result.stderr[:300]}", 'warn')
                    subtitled_video = Path(video_path)
                else:
                    _log("字幕烧录完成（drawtext）", 'info')
            except Exception as e:
                _log(f"字幕烧录异常，跳过字幕继续合成: {e}", 'warn')
                subtitled_video = Path(video_path)
        else:
            _log("SRT文件为空或解析失败，跳过字幕", 'warn')
            subtitled_video = Path(video_path)
    else:
        subtitled_video = Path(video_path)

    input_video = str(subtitled_video)
    cmd_audio = ["ffmpeg", "-y", "-i", input_video, "-i", audio_path]

    input_idx = 2
    if bgm_path and Path(bgm_path).exists():
        cmd_audio.append("-i")
        cmd_audio.append(bgm_path)
        bgm_idx = input_idx
        input_idx += 1
    else:
        bgm_idx = None

    if bgm_idx:
        audio_filter = (
            f"[1:a]volume=1.0[narration];"
            f"[{bgm_idx}:a]volume={config.BGM_VOLUME}[bgmtrack];"
            f"[narration][bgmtrack]amix=inputs=2:duration=first[aout]"
        )
    else:
        audio_filter = "[1:a]volume=1.0[aout]"

    cmd_audio.extend([
        "-filter_complex", audio_filter,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy" if input_video == str(subtitled_video) else "libx264",
        "-preset", "fast",
        "-crf", str(config.OUTPUT_CRF),
        "-c:a", "aac",
        "-b:a", config.OUTPUT_AUDIO_BITRATE,
        "-shortest",
        output_path
    ])

    try:
        result = subprocess.run(cmd_audio, capture_output=True, text=True, timeout=600)
        return result.returncode == 0 and Path(output_path).exists()
    except Exception:
        return False


class DualModeVideoGenerator:
    """素材智能剪辑生成器 — Mode A 已迁移至 topic_pipeline_api.py"""

    MODE_CLIP = "mode_b"

    def __init__(self):
        self.tts = get_tts_module()
        self.subtitle = get_subtitle_module()
        self.video = get_video_module()
        self.animation = get_animation_module()
        self.timeline = get_timeline_module()

    def generate_mode_b(
        self,
        material_paths: List[str],
        platform: str = "抖音",
        transition: str = "fade",
        add_bgm: bool = True,
        add_subtitles: bool = True,
        use_whisper: bool = False,
        duration_per_image: int = 4,
    ) -> Dict:
        """
        素材智能剪辑

        参数:
            material_paths: 用户上传的素材路径（图片/视频/音频）
            platform: 目标平台
            transition: 转场效果
            add_bgm: 是否添加BGM
            add_subtitles: 是否添加字幕
            use_whisper: 是否用Whisper识别字幕
            duration_per_image: 每张图片持续秒数

        返回:
            生成结果字典
        """
        result = {
            "mode": self.MODE_CLIP,
            "success": False,
            "steps": [],
            "materials": material_paths,
            "video": None,
            "final_video": None,
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = config.OUTPUT_DIR / "_work" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        # 分离素材类型
        images = []
        videos = []
        audio = None

        for p in material_paths:
            path = Path(p)
            if not path.exists():
                continue
            ext = path.suffix.lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                images.append(str(path))
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                videos.append(str(path))
            elif ext in ['.mp3', '.wav', '.aac', '.m4a']:
                audio = str(path)

        print(f"[Mode B] 素材: {len(images)} 图片, {len(videos)} 视频, 音频: {bool(audio)}")

        # Step 1: 素材拼接
        print("[Mode B] Step 1: 素材拼接...")

        if videos:
            raw_video_path = str(output_dir / "raw_video.mp4")
            concat_success = self._concat_videos(videos, raw_video_path)
            if not concat_success:
                result["error"] = "视频拼接失败"
                return result
            result["steps"].append({"step": "concat_videos", "status": "success"})
        elif images:
            raw_video_path = str(output_dir / "raw_video.mp4")
            video_success = self.video.create_video_from_images(
                images=images,
                output_path=raw_video_path,
                duration_per_image=duration_per_image,
                transition=transition
            )
            if not video_success:
                result["error"] = "图片转视频失败"
                return result
            result["steps"].append({"step": "images_to_video", "status": "success"})
        else:
            result["error"] = "没有有效素材"
            return result

        result["video"] = raw_video_path
        print(f"  素材拼接完成: {raw_video_path}")

        # Step 2: 添加音频
        final_video_path = raw_video_path

        if audio:
            print("[Mode B] Step 2: 添加音频...")
            final_video_path = str(output_dir / "with_audio.mp4")
            audio_success = self._add_narration(raw_video_path, audio, final_video_path)
            if audio_success:
                result["steps"].append({"step": "add_audio", "status": "success"})
            else:
                final_video_path = raw_video_path

        # Step 3: 添加BGM
        if add_bgm and not audio:
            print("[Mode B] Step 3: 添加BGM...")
            available_bgm = self.video.get_available_bgm()
            if available_bgm:
                bgm_path = available_bgm[0]
                temp_path = str(output_dir / "with_bgm.mp4")
                bgm_success = self.video.add_bgm(final_video_path, temp_path, bgm_path)
                if bgm_success:
                    final_video_path = temp_path
                    result["steps"].append({"step": "add_bgm", "status": "success"})

        # Step 4: 字幕处理
        if add_subtitles:
            print("[Mode B] Step 4: 字幕处理...")

            video_duration = self.video._get_media_duration(final_video_path)
            srt_path = str(output_dir / "subtitle.srt")

            if audio and use_whisper:
                whisper_segments = self.timeline.transcribe_audio(audio)
                if whisper_segments:
                    self.subtitle.generate_srt(whisper_segments, srt_path)
                else:
                    self.subtitle.generate_srt_from_script(" ", video_duration, srt_path)
            elif audio:
                from core.script_module import ScriptModule
                script = ScriptModule().generate_script(
                    {"title": "素材剪辑"}, platform, int(video_duration)
                )
                sentences = self._split_sentences(script.get("full_script", ""))
                segments = []
                per_duration = video_duration / max(len(sentences), 1)
                for i, s in enumerate(sentences):
                    segments.append({
                        "start": i * per_duration,
                        "end": (i + 1) * per_duration,
                        "text": s
                    })
                self.subtitle.generate_srt(segments, srt_path)
            else:
                self.subtitle.generate_srt_from_script(" ", video_duration, srt_path)

            # 烧录字幕
            subtitled_path = str(output_dir / "subtitled.mp4")
            burn_success = self.subtitle.burn_subtitles(final_video_path, srt_path, subtitled_path)
            if burn_success:
                final_video_path = subtitled_path
                result["steps"].append({"step": "burn_subtitles", "status": "success"})

        result["final_video"] = final_video_path
        result["success"] = True
        result["steps"].append({"step": "complete", "status": "success"})
        print(f"[Mode B] 完成: {final_video_path}")

        return result

    def _generate_topic_from_keyword(self, keyword: str, category: str = None) -> Optional[Dict]:
        """用LLM根据关键词直接生成选题"""
        import requests
        try:
            import importlib
            import config as _cfg
            importlib.reload(_cfg)
            from config import get_cloud_llm_config
            cfg = get_cloud_llm_config()
            if not cfg["api_key"]:
                _log("❌ API Key 未配置，请先在 API 配置中填写密钥", 'error')
                return None

            _log(f"📡 LLM 配置: {cfg['api_base']} | 模型: {cfg['model']}", 'info')

            cat_hint = f"赛道：{category}，" if category else ""

            prompt = f"""你是一个短视频选题专家。请根据用户输入的关键词生成一个爆款短视频选题。

关键词：{keyword}
{cat_hint}要求：
1. 标题要吸引人、有悬念或痛点
2. 符合短视频平台传播规律
3. 输出JSON格式：
{{"title": "标题", "hook": "3秒钩子", "category": "分类", "tags": ["标签1", "标签2"]}}

只输出JSON，不要其他文字："""

            response = requests.post(
                f'{cfg["api_base"]}/chat/completions',
                headers={
                    'Authorization': f'Bearer {cfg["api_key"]}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': cfg["model"],
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 2048,
                    'temperature': 0.8
                },
                timeout=30,
                proxies={'http': None, 'https': None}
            )

            if response.status_code != 200:
                _log(f"❌ LLM API 返回错误: HTTP {response.status_code} — {response.text[:200]}", 'error')
                return None

            result = response.json()
            if 'choices' not in result or not result['choices']:
                _log(f"❌ LLM API 返回异常: {str(result)[:200]}", 'error')
                return None

            content = result['choices'][0]['message']['content']
            _log(f"✅ LLM 返回: {content[:100]}...", 'info')

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                topic = json.loads(json_match.group())
                topic['id'] = 0
                return topic
            else:
                _log(f"⚠️ LLM 返回内容无法解析为JSON: {content[:100]}", 'warn')
        except requests.exceptions.ConnectionError as e:
            _log(f"❌ LLM 连接失败: {e}。请检查接口地址是否正确", 'error')
        except requests.exceptions.Timeout:
            _log("❌ LLM 请求超时 (30s)，请检查网络或换一个接口", 'error')
        except Exception as e:
            _log(f"❌ LLM 调用异常: {type(e).__name__}: {e}", 'error')
        return None

    def _split_sentences(self, text: str) -> List[str]:
        """分句（按标点）"""
        if not text:
            return []
        pattern = r'[。！？.!?；;]'
        parts = re.split(pattern, text)
        return [p.strip() for p in parts if p.strip() and len(p.strip()) >= 3]

    def _concat_videos(self, video_paths: List[str], output_path: str) -> bool:
        """拼接视频"""
        list_file = Path(output_path).parent / "concat_list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for vp in video_paths:
                f.write(f"file '{Path(vp).absolute().as_posix()}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(config.OUTPUT_CRF),
            "-pix_fmt", "yuv420p",
            output_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace', timeout=600)
            return result.returncode == 0 and Path(output_path).exists()
        except Exception:
            return False
        finally:
            try:
                list_file.unlink()
            except FileNotFoundError:
                pass

    def _add_narration(self, video_path: str, audio_path: str, output_path: str) -> bool:
        """添加配音"""
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", "[0:a]volume=0.5[a0];[1:a]volume=1.0[a1];[a0][a1]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", config.OUTPUT_AUDIO_BITRATE,
            "-shortest",
            output_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace', timeout=600)
            return result.returncode == 0 and Path(output_path).exists()
        except Exception:
            return False


# ==================== 便捷函数 ====================
_module_instance = None


def get_dual_mode_generator() -> DualModeVideoGenerator:
    """获取生成器单例"""
    global _module_instance
    if _module_instance is None:
        _module_instance = DualModeVideoGenerator()
        if _dual_log_callback:
            _module_instance._log = _dual_log_callback
    return _module_instance


def generate_mode_b(material_paths: List[str], **kwargs) -> Dict:
    """快速素材剪辑生成"""
    return get_dual_mode_generator().generate_mode_b(material_paths, **kwargs)
