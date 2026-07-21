# -*- coding: utf-8 -*-
"""
视频合成器
将动效帧序列合成为视频文件
"""
import subprocess
import threading
import queue
from typing import List, Dict, Optional, Callable
from pathlib import Path
import re


class VideoComposer:
    """视频合成器 - 使用FFmpeg将帧序列合成为视频"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """
        初始化视频合成器

        Args:
            ffmpeg_path: FFmpeg可执行文件路径
        """
        self.ffmpeg_path = ffmpeg_path
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg not found or not working")
        except Exception as e:
            print(f"[VideoComposer] FFmpeg check failed: {e}")
            print("[VideoComposer] Videos will be disabled")

    def compose_frames_to_video(
        self,
        frames_dir: str,
        output_path: str,
        fps: int = 30,
        codec: str = "libx264",
        bitrate: str = "2M",
        preset: str = "medium",
        audio_path: str = None,
        progress_callback: Callable[[float], None] = None
    ) -> bool:
        """
        将帧序列合成为视频

        Args:
            frames_dir: 帧序列目录
            output_path: 输出视频路径
            fps: 帧率
            codec: 视频编码器
            bitrate: 比特率
            preset: 编码预设 (ultrafast/fast/medium/slow)
            audio_path: 音频文件路径
            progress_callback: 进度回调函数

        Returns:
            成功返回True，失败返回False
        """
        frames_dir = Path(frames_dir)
        output_path = Path(output_path)

        if not frames_dir.exists():
            print(f"[VideoComposer] Frames directory not found: {frames_dir}")
            return False

        # 查找帧文件
        frame_files = sorted(frames_dir.glob("*.png"))
        if not frame_files:
            print(f"[VideoComposer] No frame files found in {frames_dir}")
            return False

        print(f"[VideoComposer] Found {len(frame_files)} frames")

        # 构建FFmpeg命令
        cmd = [
            self.ffmpeg_path,
            "-y",  # 覆盖输出文件
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%04d.png"),  # 输入模式
            "-c:v", codec,
            "-b:v", bitrate,
            "-preset", preset,
            "-pix_fmt", "yuv420p",  # 兼容性
        ]

        # 添加音频
        if audio_path and Path(audio_path).exists():
            cmd.extend(["-i", str(audio_path), "-c:a", "aac", "-shortest"])

        # 输出文件
        cmd.append(str(output_path))

        print(f"[VideoComposer] Running FFmpeg...")
        print(f"[VideoComposer] Command: {' '.join(cmd[:8])}...")

        try:
            # 运行FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            if result.returncode == 0:
                print(f"[VideoComposer] Video created: {output_path}")
                return True
            else:
                print(f"[VideoComposer] FFmpeg failed: {result.stderr}")
                return False

        except subprocess.CalledProcessError as e:
            print(f"[VideoComposer] FFmpeg error: {e.stderr}")
            return False
        except Exception as e:
            print(f"[VideoComposer] Composition failed: {e}")
            return False

    def create_video_from_scenes(
        self,
        scenes: List[Dict],
        output_path: str,
        fps: int = 30,
        transition_duration: float = 0.5,
        progress_callback: Callable[[float], None] = None
    ) -> bool:
        """
        从场景列表创建视频

        Args:
            scenes: 场景列表，每个场景包含图片路径和持续时间
            output_path: 输出视频路径
            fps: 帧率
            transition_duration: 转场持续时间
            progress_callback: 进度回调

        Returns:
            成功返回True
        """
        temp_dir = Path(output_path).parent / "temp_frames"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 为每个场景生成帧
            frame_idx = 0
            total_duration = sum(scene.get("duration", 3.0) for scene in scenes)

            for scene_idx, scene in enumerate(scenes):
                image_path = scene.get("image_path")
                duration = scene.get("duration", 3.0)
                scene_frames = int(duration * fps)

                if not image_path or not Path(image_path).exists():
                    print(f"[VideoComposer] Scene {scene_idx}: image not found")
                    continue

                # 复制图像作为帧
                for i in range(scene_frames):
                    src = Path(image_path)
                    dst = temp_dir / f"frame_{frame_idx:04d}.png"
                    # 可以在这里添加转场效果
                    import shutil
                    shutil.copy(src, dst)
                    frame_idx += 1

                # 进度回调
                if progress_callback:
                    progress = (scene_idx + 1) / len(scenes) * 0.8
                    progress_callback(progress)

            # 合成视频
            success = self.compose_frames_to_video(
                frames_dir=str(temp_dir),
                output_path=output_path,
                fps=fps,
                progress_callback=lambda p: progress_callback(0.8 + p * 0.2) if progress_callback else None
            )

            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            return success

        except Exception as e:
            print(f"[VideoComposer] Video creation failed: {e}")
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return False


class VideoGenerator:
    """视频生成器 - 完整的视频生成流程"""

    def __init__(self, style_id: str = "minimal", fps: int = 30):
        """
        初始化视频生成器

        Args:
            style_id: 视觉风格
            fps: 输出帧率
        """
        self.style_id = style_id
        self.fps = fps
        self.composer = VideoComposer()

    def generate_video(
        self,
        storyboard: List[Dict],
        output_path: str,
        enable_animations: bool = True,
        scene_duration: float = 3.0,
        progress_callback: Callable[[float], None] = None
    ) -> bool:
        """
        生成分镜视频

        Args:
            storyboard: 分镜列表
            output_path: 输出视频路径
            enable_animations: 是否启用动效
            scene_duration: 每个场景持续时间
            progress_callback: 进度回调

        Returns:
            成功返回True
        """
        output_path = Path(output_path)
        work_dir = output_path.parent / "generation_temp"
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 创建渲染器
            from core.style_renderers import create_renderer
            renderer = create_renderer(self.style_id)

            if not renderer:
                print(f"[VideoGenerator] Failed to create renderer")
                return False

            # 渲染场景
            scenes_data = []
            frames_dir = work_dir / "scenes"
            frames_dir.mkdir(parents=True, exist_ok=True)

            for i, scene in enumerate(storyboard):
                title = scene.get("title", f"Scene {i+1}")
                bullets = scene.get("bullets", [])
                subtitle = scene.get("subtitle", "")

                # 渲染场景
                scene_output = frames_dir / f"scene_{i:03d}.png"

                try:
                    renderer.render_frame(
                        title=title,
                        bullets=bullets,
                        output_path=str(scene_output),
                        subtitle=subtitle,
                        scene_index=i,
                        total_scenes=len(storyboard),
                        enable_animations=False  # 暂时禁用动效
                    )

                    scenes_data.append({
                        "image_path": str(scene_output),
                        "duration": scene_duration
                    })

                    if progress_callback:
                        progress = (i + 1) / len(storyboard) * 0.5
                        progress_callback(progress)

                except Exception as e:
                    print(f"[VideoGenerator] Failed to render scene {i}: {e}")

            # 合成视频
            if not scenes_data:
                print("[VideoGenerator] No scenes rendered")
                return False

            success = self.composer.create_video_from_scenes(
                scenes=scenes_data,
                output_path=output_path,
                fps=self.fps,
                progress_callback=lambda p: progress_callback(0.5 + p * 0.5) if progress_callback else None
            )

            # 清理
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)

            return success

        except Exception as e:
            print(f"[VideoGenerator] Video generation failed: {e}")
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)
            return False


# 便捷函数
def create_video_composer(ffmpeg_path: str = "ffmpeg") -> VideoComposer:
    """创建视频合成器"""
    return VideoComposer(ffmpeg_path)


def generate_video_from_storyboard(
    storyboard: List[Dict],
    output_path: str,
    style_id: str = "minimal",
    fps: int = 30,
    progress_callback: Callable[[float], None] = None
) -> bool:
    """从分镜生成视频的便捷函数"""
    generator = VideoGenerator(style_id, fps)
    return generator.generate_video(
        storyboard=storyboard,
        output_path=output_path,
        progress_callback=progress_callback
    )
