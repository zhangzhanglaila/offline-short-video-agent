# -*- coding: utf-8 -*-
"""
动画生成模块 - 基于FFmpeg动态效果
支持：漫画转场(xfade)、Ken Burns缩放、强调冲击效果、电影级调色
"""
import math
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from config import OUTPUT_WIDTH, OUTPUT_HEIGHT, OUTPUT_FPS, OUTPUT_CRF
from core.utils.ffmpeg_runner import run_ffmpeg_safe


class AnimationModule:
    """动画生成模块 - FFmpeg动态效果"""

    MANGA_TRANSITIONS = {
        "fade": "fade",
        "fadegrays": "fadegrays",       # 灰阶淡入淡出 — 漫画纸质感
        "wipeleft": "wipeleft",          # 左向右擦除 — 翻页感
        "wiperight": "wiperight",        # 右向左擦除
        "slidedown": "slidedown",        # 下滑 — 分镜格切分感
        "pixelize": "pixelize",          # 像素化 — 网点纸过渡
        "circleclose": "circleclose",    # 圆形收缩 — 聚焦强调
        "smoothleft": "smoothleft",      # 平滑左滑
        "rectcrop": "rectcrop",          # 矩形裁剪展开
    }

    EMPHASIS_MODES = {
        # (zoom_start, zoom_peak, peak_time, settle_time, shake_px)
        "big_number": (1.0, 1.14, 0.25, 0.55, 0),
        "chart_done": (1.0, 1.06, 0.2, 0.45, 4),
        "cta": (1.0, 1.10, 1.5, 3.0, 0),
        "hook": (1.0, 1.08, 0.2, 0.5, 0),
    }

    def __init__(self):
        self.output_width = OUTPUT_WIDTH
        self.output_height = OUTPUT_HEIGHT
        self.output_fps = OUTPUT_FPS
        self.output_crf = OUTPUT_CRF

    # ═══════════════════════════════════════════════════════════════
    # 漫画帧片段生成（支持强调动效）
    # ═══════════════════════════════════════════════════════════════

    def create_manga_frame_clip(self, image_path: str, output_path: str,
                                 duration: float = 3.0, emphasis: str = None) -> bool:
        """漫画帧转视频片段，可选强调动效 (big_number/chart_done/cta/hook)。"""
        if not Path(image_path).exists():
            return False

        W, H = self.output_width, self.output_height
        total_frames = int(duration * self.output_fps)

        emphasis_mode = self.EMPHASIS_MODES.get(emphasis) if emphasis else None

        if emphasis_mode:
            z_start, z_peak, t_peak, t_settle, shake = emphasis_mode
            # zoom表达式: 0→t_peak 放大到z_peak, t_peak→t_settle 回到1.0, 之后保持1.0
            # 注意: FFmpeg zoompan 使用 'time' 而非 't' 作为时间变量
            rate_up = (z_peak - z_start) / max(t_peak, 0.01)
            rate_down = (1.0 - z_peak) / max(t_settle - t_peak, 0.01)
            # 避免 FFmpeg 表达式中的 *- (multiply-by-negative) 语法错误:
            # 负斜率用减法表示: A+(t-s)*(neg) → A-(t-s)*abs(neg)
            if rate_down >= 0:
                mid_expr = f"{z_peak}+(time-{t_peak})*{rate_down:.4f}"
            else:
                mid_expr = f"{z_peak}-(time-{t_peak})*{-rate_down:.4f}"
            z_expr = (
                f"if(lt(time,{t_peak}),{z_start}+time*{rate_up:.4f},"
                f"if(lt(time,{t_settle}),{mid_expr},1))"
            )
            if shake:
                shake_freq = 30
                shake_amp = shake
                shake_decay = shake_amp / max(t_settle, 0.01)
                px_expr = f"iw/2-(iw/zoom/2)+if(lt(time,{t_settle}),sin(time*{shake_freq})*({shake_amp}-time*{shake_decay:.2f}),0)"
                py_expr = f"ih/2-(ih/zoom/2)+if(lt(time,{t_settle}),cos(time*{shake_freq}*1.3)*({shake_amp}-time*{shake_decay:.2f})*0.5,0)"
            else:
                px_expr = "iw/2-(iw/zoom/2)"
                py_expr = "ih/2-(ih/zoom/2)"

            filter_complex = (
                f"zoompan=z='{z_expr}':"
                f"x='{px_expr}':y='{py_expr}':"
                f"d={total_frames}:s={W}x{H}:fps={self.output_fps}"
            )
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-framerate", str(self.output_fps),
                "-i", image_path,
                "-t", str(duration),
                "-filter_complex", filter_complex,
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", str(self.output_crf),
                output_path
            ]
        else:
            # 无强调动效时也需要统一缩放至输出分辨率，否则 xfade 合并会因尺寸不一致而失败
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-framerate", str(self.output_fps),
                "-i", image_path,
                "-t", str(duration),
                "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", str(self.output_crf),
                "-pix_fmt", "yuv420p",
                output_path
            ]

        return self._run_ffmpeg(cmd)

    # ═══════════════════════════════════════════════════════════════
    # 场景序列 → 带转场的完整视频（xfade 核心）
    # ═══════════════════════════════════════════════════════════════

    def create_animated_video_from_segments(self, images: List[str],
                                            segments: List[Dict],
                                            output_path: str,
                                            animation_style: str = "manga_frame",
                                            transition: str = "fadegrays",
                                            film_look: bool = True) -> bool:
        """根据时间轴创建动画视频，使用 xfade 转场 + 可选电影调色。

        参数:
            images: 图片路径列表
            segments: 时间轴 [{start, end, text, image_index, emphasis}]
            output_path: 输出视频路径
            animation_style: manga_frame/contain/ken_burns/pan_zoom/static
            transition: xfade 转场名 (见 MANGA_TRANSITIONS)
            film_look: 是否添加暗角+胶片颗粒+暖色调

        返回: 是否成功
        """
        if not images or not segments:
            return False

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        temp_dir = Path(output_path).parent / "temp_animation"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # ── 1. 每个片段生成独立视频 ──
        video_clips = []
        for i, seg in enumerate(segments):
            start = seg.get("start", 0)
            end = seg.get("end", 3)
            duration = end - start
            emphasis = seg.get("emphasis")
            media_type = seg.get("media_type", "image")
            video_src = seg.get("video_path", "")

            clip_path = str(temp_dir / f"clip_{i:03d}.mp4")

            if media_type == "video" and video_src and Path(video_src).exists():
                # 视频素材：裁剪 + 缩放到目标分辨率
                self._prepare_video_clip(video_src, clip_path, duration)
            else:
                # 图片素材：现有逻辑
                image_idx = seg.get("image_index", i % len(images))
                if image_idx >= len(images):
                    image_idx = i % len(images)
                image_path = images[image_idx]

                if animation_style == "manga_frame":
                    self.create_manga_frame_clip(image_path, clip_path, duration=duration, emphasis=emphasis)
                elif animation_style == "contain":
                    self._create_contain_clip(image_path, clip_path, duration=duration)
                elif animation_style == "ken_burns":
                    zoom_in = random.choice([True, False])
                    self.create_ken_burns_clip(
                        image_path, clip_path, duration=duration,
                        zoom_in=zoom_in,
                        zoom_range=(1.0, random.uniform(1.2, 1.5))
                    )
                elif animation_style == "pan_zoom":
                    effects = ["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"]
                    self.create_pan_zoom_clip(image_path, clip_path, duration=duration, effect=random.choice(effects))
                else:
                    self._create_simple_clip(image_path, clip_path, duration=duration)

            if Path(clip_path).exists() and Path(clip_path).stat().st_size > 0:
                video_clips.append((clip_path, duration, start))
            else:
                print(f"[Animation] WARNING: clip_{i:03d}.mp4 生成失败或为空 (media_type={media_type})")

        if not video_clips:
            print(f"[Animation] ERROR: 所有视频片段生成失败，共 {len(segments)} 个片段")
            return False

        video_clips.sort(key=lambda x: x[2])

        # ── 2. xfade 合并（带转场效果）──
        trans = self.MANGA_TRANSITIONS.get(transition, "fadegrays")
        trans_dur = 0.28  # 转场时长

        if len(video_clips) == 1:
            # 单片段直接拷贝
            cmd = [
                "ffmpeg", "-y",
                "-i", video_clips[0][0],
                "-c:v", "libx264", "-preset", "fast",
                "-crf", str(self.output_crf),
                "-pix_fmt", "yuv420p",
                output_path
            ]
            success = self._run_ffmpeg(cmd)
        else:
            success = self._xfade_merge(video_clips, output_path, trans, trans_dur)

        if not success:
            return False

        # ── 3. 电影级调色（如果启用）──
        if film_look:
            graded_path = str(Path(output_path).parent / "graded_temp.mp4")
            if self._apply_film_look(output_path, graded_path):
                import shutil
                shutil.move(graded_path, output_path)

        # ── 4. 清理临时文件 ──
        for clip_path, _, _ in video_clips:
            try:
                Path(clip_path).unlink()
            except FileNotFoundError:
                pass
        try:
            temp_dir.rmdir()
        except FileNotFoundError:
            pass

        return success

    def _xfade_merge(self, clips: List[tuple], output_path: str, transition: str, trans_dur: float) -> bool:
        """使用 FFmpeg xfade 滤镜合并多个片段到单一输出。"""
        inputs = []
        for clip_path, _, _ in clips:
            inputs.extend(["-i", clip_path])

        # 构建 xfade filter chain
        # offset 必须 < 输入最后一帧 PTS（= (frames-1)/fps），否则 ffmpeg 静默丢帧
        # 用 xfade_out 追踪每个 xfade 的实际输出时长（= offset + 下一段时长），
        # 而不是简单的片段时长累加（累加值会逐渐偏离实际输出时长）
        XFADE_MARGIN = trans_dur + 0.01
        filter_parts = []
        xfade_out_dur = 0.0  # 上一级 xfade 输出的时长（首个 xfade 的输入是 clip_0）
        prev_label = "[0:v]"

        for i in range(len(clips) - 1):
            if i == 0:
                offset = max(0.0, clips[0][1] - trans_dur - XFADE_MARGIN)
            else:
                offset = max(0.0, xfade_out_dur - trans_dur - XFADE_MARGIN)
            xfade_out_dur = offset + clips[i + 1][1]
            next_input = f"[{i + 1}:v]"
            out_label = f"[v{i}]"
            filter_parts.append(
                f"{prev_label}{next_input}"
                f"xfade=transition={transition}:duration={trans_dur}:offset={offset:.2f}"
                f"{out_label}"
            )
            prev_label = out_label

        filter_complex = ";".join(filter_parts)
        # xfade 输出需映射到最后一段的标签
        last_label = f"[v{len(clips) - 2}]"

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", last_label,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(self.output_crf),
            "-pix_fmt", "yuv420p",
            output_path
        ]
        return self._run_ffmpeg(cmd)

    # ═══════════════════════════════════════════════════════════════
    # 电影级调色（暗角 + 暖色 + 胶片颗粒）
    # ═══════════════════════════════════════════════════════════════

    def _apply_film_look(self, input_path: str, output_path: str) -> bool:
        """对视频应用电影调色：暗角、微暖色、胶片颗粒。"""
        W, H = self.output_width, self.output_height
        # vignette: 用 geq 实现暗角，边缘亮度降低 8-12%
        # eq: 微提饱和+对比度
        # noise: 极细胶片颗粒
        filter_complex = (
            f"geq=r='r(X,Y)*min(1,1.12-0.22*(pow((X-{W/2})/({W/2}),2)+pow((Y-{H/2})/({H/2}),2)))':"
            f"g='g(X,Y)*min(1,1.12-0.22*(pow((X-{W/2})/({W/2}),2)+pow((Y-{H/2})/({H/2}),2)))':"
            f"b='b(X,Y)*min(1,1.12-0.22*(pow((X-{W/2})/({W/2}),2)+pow((Y-{H/2})/({H/2}),2)))'"
            f",eq=saturation=1.08:contrast=1.04:brightness=0.01"
            f",noise=alls=3:allf=t:all_seed=42"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-filter_complex", filter_complex,
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", str(self.output_crf),
            output_path
        ]
        return self._run_ffmpeg(cmd)

    # ═══════════════════════════════════════════════════════════════
    # 原有方法（保留兼容）
    # ═══════════════════════════════════════════════════════════════

    def create_ken_burns_clip(self, image_path: str, output_path: str,
                               duration: float = 3.0,
                               zoom_in: bool = True,
                               zoom_range: Tuple[float, float] = (1.0, 1.15),
                               pan_x: float = 0.0,
                               pan_y: float = 0.0) -> bool:
        if not Path(image_path).exists():
            return False
        zoom_start, zoom_end = zoom_range
        if not zoom_in:
            zoom_start, zoom_end = zoom_end, zoom_start
        W, H = self.output_width, self.output_height
        total_frames = int(duration * self.output_fps)
        zoom_delta = (zoom_end - zoom_start) / total_frames
        filter_complex = (
            f"[0:v]split=2[fg][bg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},boxblur=15:8[bgblur];"
            f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"zoompan=z='min(zoom+{zoom_delta:.6f},{zoom_end})':"
            f"x='iw/2-(iw/zoom/2)+{int(pan_x*40)}':"
            f"y='ih/2-(ih/zoom/2)+{int(pan_y*40)}':"
            f"d={total_frames}:s={W}x{H}:fps={self.output_fps}[fgzoom];"
            f"[bgblur][fgzoom]overlay=(W-w)/2:(H-h)/2"
        )
        cmd = [
            "ffmpeg", "-y", "-loop", "1",
            "-framerate", str(self.output_fps),
            "-i", image_path,
            "-filter_complex", filter_complex,
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-preset", "fast",
            "-crf", str(self.output_crf),
            "-t", str(duration),
            output_path
        ]
        return self._run_ffmpeg(cmd)

    def create_pan_zoom_clip(self, image_path: str, output_path: str,
                              duration: float = 3.0, effect: str = "zoom_in",
                              placement: str = "right") -> bool:
        if not Path(image_path).exists():
            return False
        W, H = self.output_width, self.output_height
        total_frames = int(duration * self.output_fps)
        zoom_effects = {"zoom_in": ("1.0", "1.3"), "zoom_out": ("1.3", "1.0"), "static": ("1.0", "1.0")}
        zoom_start, zoom_end = zoom_effects.get(effect, ("1.0", "1.0"))
        zoom_delta = (float(zoom_end) - float(zoom_start)) / total_frames
        filter_complex = (
            f"[0:v]split=2[fg][bg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},boxblur=15:8[bgblur];"
            f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"zoompan=z='min(zoom+{zoom_delta:.6f},{zoom_end})':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={W}x{H}:fps={self.output_fps}[fgzoom];"
            f"[bgblur][fgzoom]overlay=(W-w)/2:(H-h)/2"
        )
        cmd = [
            "ffmpeg", "-y", "-loop", "1",
            "-framerate", str(self.output_fps),
            "-i", image_path,
            "-filter_complex", filter_complex,
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "fast",
            "-crf", str(self.output_crf),
            output_path
        ]
        return self._run_ffmpeg(cmd)

    def _create_contain_clip(self, image_path: str, output_path: str, duration: float) -> bool:
        if not Path(image_path).exists():
            return False
        filter_complex = (
            f"[0:v]split=2[fgsrc][bgsrc];"
            f"[bgsrc]scale={self.output_width}:{self.output_height}:force_original_aspect_ratio=increase,"
            f"crop={self.output_width}:{self.output_height},boxblur=20:10[bg];"
            f"[fgsrc]scale={self.output_width}:{self.output_height}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )
        cmd = [
            "ffmpeg", "-y", "-loop", "1",
            "-framerate", str(self.output_fps),
            "-i", image_path,
            "-t", str(duration),
            "-filter_complex", filter_complex,
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-preset", "fast",
            "-crf", str(self.output_crf),
            output_path
        ]
        return self._run_ffmpeg(cmd)

    def _create_simple_clip(self, image_path: str, output_path: str, duration: float,
                            placement: str = "right") -> bool:
        W, H = self.output_width, self.output_height
        filter_complex = (
            f"[0:v]split=2[fg][bg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},boxblur=12:6[bgblur];"
            f"[fg]scale={W}:{H}:force_original_aspect_ratio=decrease[fgscaled];"
            f"[bgblur][fgscaled]overlay=(W-w)/2:(H-h)/2"
        )
        cmd = [
            "ffmpeg", "-y", "-loop", "1",
            "-i", image_path,
            "-t", str(duration),
            "-filter_complex", filter_complex,
            "-pix_fmt", "yuv420p",
            "-r", str(self.output_fps),
            "-c:v", "libx264", "-preset", "fast",
            "-crf", str(self.output_crf),
            output_path
        ]
        return self._run_ffmpeg(cmd)

    def _prepare_video_clip(self, source_video: str, output_path: str,
                            duration: float) -> bool:
        """将真实视频素材裁剪+缩放到统一格式，与图片片段兼容用于 xfade 合并。

        处理逻辑:
        1. 从源视频中随机选取起始点（避免总是取开头）
        2. 截取指定时长
        3. scale+crop 到输出分辨率（保持比例，居中裁剪）
        4. 统一编码参数（libx264, crf, yuv420p）
        """
        W, H = self.output_width, self.output_height

        # 获取源视频时长，用于随机起始点
        offset = 0.0
        try:
            import subprocess, json
            probe = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", source_video],
                capture_output=True, timeout=5,
            )
            if probe.returncode == 0:
                probe_out = probe.stdout.decode("utf-8", errors="replace") if isinstance(probe.stdout, bytes) else probe.stdout
                src_duration = float(json.loads(probe_out).get("format", {}).get("duration", 0))
                # 随机起始点，确保有足够时长可截取
                max_offset = max(0, src_duration - duration - 0.5)
                if max_offset > 0:
                    offset = random.uniform(0, max_offset)
        except Exception:
            pass

        # scale+crop 统一分辨率，-ss/-t 截取片段
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},setsar=1,fps={self.output_fps}"
        )
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{offset:.2f}",
            "-i", source_video,
            "-t", str(duration),
            "-vf", vf,
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264", "-preset", "fast",
            "-crf", str(self.output_crf),
            "-an",  # 去掉音频（最终用TTS+BGM）
            output_path
        ]
        return self._run_ffmpeg(cmd)

    def _run_ffmpeg(self, cmd: List[str]) -> bool:
        return run_ffmpeg_safe(cmd)


# ==================== 便捷函数 ====================
_anim_instance = None


def get_animation_module() -> AnimationModule:
    global _anim_instance
    if _anim_instance is None:
        _anim_instance = AnimationModule()
    return _anim_instance
