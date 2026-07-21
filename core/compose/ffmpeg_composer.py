"""
FFmpeg合成器 - 将场景图序列合成为视频。

流程：
1. 每张场景图 → 持续指定时长的视频片段
2. 片段拼接（支持交叉淡入转场，失败回退硬切）
3. 可选混入背景音频
"""

import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple, Optional


class FFmpegComposer:
    """FFmpeg视频合成器。

    Attributes:
        ffmpeg_path: FFmpeg可执行文件路径
        size: 输出分辨率 (宽, 高)
        fps: 帧率
        available: FFmpeg是否可用
    """

    def __init__(
        self,
        ffmpeg_path: str = "ffmpeg",
        size: Tuple[int, int] = (1080, 1920),
        fps: int = 30,
    ):
        """初始化合成器。

        Args:
            ffmpeg_path: FFmpeg路径
            size: 输出分辨率
            fps: 帧率
        """
        self.ffmpeg_path = ffmpeg_path
        self.size = size
        self.fps = fps
        self.available = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        """检查FFmpeg是否可用。

        Returns:
            True如果可用
        """
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True, text=True,
                encoding="utf-8", errors="ignore", timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    # ---------- 主合成入口 ----------

    def compose(
        self,
        scenes: list,
        output_path: str,
        transition_duration: float = 0.0,
        audio_path: Optional[str] = None,
        transitions: Optional[List[str]] = None,
        bgm_path: Optional[str] = None,
        bgm_volume: float = 0.3,
    ) -> bool:
        """将场景序列合成为视频。

        Args:
            scenes: 场景列表，元素可为：
                - (图片路径, 时长秒) 元组：静态片段(向后兼容)
                - SceneClipSpec：支持运镜和覆盖层
            output_path: 输出视频路径
            transition_duration: 转场时长（0为硬切）
            audio_path: 可选背景音频路径(直接混入，不循环)
            transitions: 各边界的xfade转场名称列表(长度=场景数-1)。
                         None时全部用fade。(D4)
            bgm_path: 可选背景音乐路径(循环+降音量+尾部淡出)。(D6)
            bgm_volume: BGM音量(0-1)

        Returns:
            True如果合成成功
        """
        if not self.available:
            return False
        if not scenes:
            return False

        # 归一化为SceneClipSpec
        specs = [self._normalize_spec(s) for s in scenes]

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        work_dir = output_path.parent / f".compose_tmp_{output_path.stem}"
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. 每个场景渲染为片段
            clips: List[Tuple[str, float]] = []
            for i, spec in enumerate(specs):
                clip_path = str(work_dir / f"clip_{i:03d}.mp4")
                ok = self._render_scene_clip(spec, clip_path)
                # 运镜/覆盖失败 → 降级为静态片段
                if not ok and (spec.has_motion or spec.has_overlay):
                    ok = self._render_clip(
                        spec.background_path, spec.duration, clip_path
                    )
                if ok:
                    clips.append((clip_path, spec.duration))

            if not clips:
                return False

            # 2. 拼接
            silent_video = str(work_dir / "silent.mp4")
            use_xfade = transition_duration > 0 and len(clips) >= 2
            ok = False
            if use_xfade:
                ok = self._concat_with_xfade(
                    clips, silent_video, transition_duration, transitions,
                )
            if not ok:
                # 回退硬切
                ok = self._concat_hard_cut(clips, silent_video)
            if not ok:
                return False

            # 3. 音频（优先BGM循环混音，其次直接混音，否则无声）
            if bgm_path and Path(bgm_path).exists():
                ok = self._add_bgm(silent_video, bgm_path, str(output_path),
                                    bgm_volume)
                if not ok:
                    shutil.copy(silent_video, output_path)
            elif audio_path and Path(audio_path).exists():
                ok = self._mux_audio(silent_video, audio_path, str(output_path))
                if not ok:
                    shutil.copy(silent_video, output_path)
            else:
                shutil.copy(silent_video, output_path)

            return output_path.exists()

        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    # ---------- 片段渲染 ----------

    def _normalize_spec(self, item):
        """将场景项归一化为SceneClipSpec。

        Args:
            item: (path, duration)元组 或 SceneClipSpec

        Returns:
            SceneClipSpec
        """
        from core.compose.motion.clip_spec import SceneClipSpec
        if isinstance(item, SceneClipSpec):
            return item
        # 元组 (path, duration)
        path, duration = item
        return SceneClipSpec(background_path=path, duration=duration)

    def _render_scene_clip(self, spec, output: str) -> bool:
        """按规格渲染场景片段(支持运镜+多动画覆盖层)。

        Args:
            spec: SceneClipSpec
            output: 输出路径

        Returns:
            True如果成功
        """
        if not Path(spec.background_path).exists():
            return False

        from core.compose.motion.text_animations import build_overlay_filter
        from core.compose.motion.animation_spec import AnimationSpec, ANIM_NONE

        w, h = self.size

        # 收集覆盖层：优先动画列表overlays，否则回退静态overlay_path
        layers = []
        for lyr in spec.overlays:
            if lyr.image_path and Path(lyr.image_path).exists():
                layers.append(lyr)
        if not layers and spec.overlay_path and Path(spec.overlay_path).exists():
            from core.compose.motion.animation_spec import OverlayLayer
            layers.append(OverlayLayer(
                image_path=spec.overlay_path,
                animation=AnimationSpec(anim_type=ANIM_NONE),
            ))

        # 背景滤镜与输入方式
        if spec.background_is_video:
            # D5: 视频背景 → loop + cover-fit (无zoompan，视频本身在动)
            bg_filter = (
                f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                f"crop={w}:{h},fps={self.fps},setsar=1"
            )
            # -stream_loop -1 循环视频以填满场景时长
            cmd = [self.ffmpeg_path, "-y", "-stream_loop", "-1",
                   "-t", f"{spec.duration:.3f}", "-i", spec.background_path]
        else:
            # 静图背景：运镜 或 静态cover-fit
            if spec.has_motion:
                bg_filter = spec.ken_burns.build_filter()
            else:
                bg_filter = (
                    f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                    f"crop={w}:{h},fps={self.fps}"
                )
            cmd = [self.ffmpeg_path, "-y", "-loop", "1",
                   "-t", f"{spec.duration:.3f}", "-i", spec.background_path]

        if layers:
            # 背景 + 多覆盖层链式合成
            for lyr in layers:
                cmd.extend(["-loop", "1", "-t", f"{spec.duration:.3f}",
                            "-i", lyr.image_path])

            parts = [f"[0:v]{bg_filter}[bg]"]
            prev = "bg"
            for i, lyr in enumerate(layers):
                input_idx = i + 1
                out_label = f"ov{i}" if i < len(layers) - 1 else "vout"
                parts.append(build_overlay_filter(
                    input_idx, prev, out_label, lyr.animation, self.size,
                ))
                prev = out_label
            # 末尾统一format
            filter_complex = ";".join(parts) + ";[vout]format=yuv420p[out]"

            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "[out]",
            ])
        else:
            cmd.extend(["-vf", f"{bg_filter},format=yuv420p"])

        cmd.extend([
            "-t", f"{spec.duration:.3f}",
            "-c:v", "libx264", "-preset", "medium",
            "-pix_fmt", "yuv420p", output,
        ])
        return self._run(cmd)

    def _render_clip(self, image_path: str, duration: float, output: str) -> bool:
        """将单张图渲染为指定时长的视频片段。

        Args:
            image_path: 图片路径
            duration: 时长（秒）
            output: 输出片段路径

        Returns:
            True如果成功
        """
        if not Path(image_path).exists():
            return False

        w, h = self.size
        vf = (
            f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},fps={self.fps},format=yuv420p"
        )
        cmd = [
            self.ffmpeg_path, "-y",
            "-loop", "1",
            "-t", f"{duration:.3f}",
            "-i", image_path,
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "medium",
            "-pix_fmt", "yuv420p",
            output,
        ]
        return self._run(cmd)

    # ---------- 拼接：硬切 ----------

    def _concat_hard_cut(self, clips: List[Tuple[str, float]], output: str) -> bool:
        """使用concat demuxer硬切拼接。

        Args:
            clips: [(片段路径, 时长), ...]
            output: 输出路径

        Returns:
            True如果成功
        """
        list_file = Path(output).parent / "concat_list.txt"
        try:
            with open(list_file, "w", encoding="utf-8") as f:
                for clip_path, _ in clips:
                    abs_path = str(Path(clip_path).resolve()).replace("\\", "/")
                    f.write(f"file '{abs_path}'\n")

            cmd = [
                self.ffmpeg_path, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c:v", "libx264",
                "-preset", "medium",
                "-pix_fmt", "yuv420p",
                output,
            ]
            return self._run(cmd)
        finally:
            list_file.unlink(missing_ok=True)

    # ---------- 拼接：交叉淡入 ----------

    def _concat_with_xfade(
        self, clips: List[Tuple[str, float]], output: str, transition: float,
        transitions: Optional[List[str]] = None,
    ) -> bool:
        """使用xfade拼接，支持每边界不同转场类型。

        Args:
            clips: [(片段路径, 时长), ...]
            output: 输出路径
            transition: 转场时长
            transitions: 各边界转场名称列表(长度=片段数-1)。None时全用fade。

        Returns:
            True如果成功（任何片段过短则失败，交由回退处理）
        """
        # 任何片段短于转场时长则放弃xfade
        if any(d <= transition for _, d in clips):
            return False

        inputs: List[str] = []
        for clip_path, _ in clips:
            inputs.extend(["-i", clip_path])

        # 构建xfade滤镜链(每边界可用不同转场)
        filters: List[str] = []
        prev_label = "0:v"
        cumulative = 0.0
        for i in range(1, len(clips)):
            prev_duration = clips[i - 1][1]
            cumulative += prev_duration
            offset = cumulative - transition * i
            out_label = f"v{i}" if i < len(clips) - 1 else "vout"
            # 选择该边界的转场类型
            if transitions and (i - 1) < len(transitions):
                trans = transitions[i - 1]
            else:
                trans = "fade"
            filters.append(
                f"[{prev_label}][{i}:v]"
                f"xfade=transition={trans}:duration={transition:.3f}:"
                f"offset={offset:.3f}[{out_label}]"
            )
            prev_label = out_label

        filter_complex = ";".join(filters)
        cmd = [
            self.ffmpeg_path, "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-pix_fmt", "yuv420p",
            output,
        ]
        return self._run(cmd)

    # ---------- 音频 ----------

    def _mux_audio(self, video_path: str, audio_path: str, output: str) -> bool:
        """将音频混入视频（视频时长为准）。

        Args:
            video_path: 无声视频路径
            audio_path: 音频路径
            output: 输出路径

        Returns:
            True如果成功
        """
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output,
        ]
        return self._run(cmd)

    def _add_bgm(
        self, video_path: str, bgm_path: str, output: str, volume: float = 0.3,
    ) -> bool:
        """将背景音乐循环混入视频(降音量+尾部淡出)。

        Args:
            video_path: 无声视频路径
            bgm_path: 背景音乐路径
            output: 输出路径
            volume: BGM音量(0-1)

        Returns:
            True如果成功
        """
        dur = self.probe_duration(video_path)
        if not dur or dur <= 0:
            return False

        # 尾部2秒淡出(时长足够时)
        fade_start = max(0.0, dur - 2.0)
        afilter = f"volume={volume:.2f},afade=t=out:st={fade_start:.2f}:d=2"

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", video_path,
            "-stream_loop", "-1", "-i", bgm_path,  # 循环BGM
            "-filter_complex", f"[1:a]{afilter}[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac",
            "-t", f"{dur:.3f}",  # 视频时长为准
            output,
        ]
        return self._run(cmd)

    # ---------- 工具 ----------

    def _run(self, cmd: List[str], timeout: int = 300) -> bool:
        """运行FFmpeg命令。

        Args:
            cmd: 命令列表
            timeout: 超时（秒）

        Returns:
            True如果返回码为0且未超时
        """
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding="utf-8", errors="ignore", timeout=timeout,
            )
            return result.returncode == 0
        except Exception:
            return False

    def probe_duration(self, video_path: str) -> Optional[float]:
        """探测视频时长（用于验证）。

        Args:
            video_path: 视频路径

        Returns:
            时长（秒），失败返回None
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_path,
                ],
                capture_output=True, text=True,
                encoding="utf-8", errors="ignore", timeout=10,
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
        return None
