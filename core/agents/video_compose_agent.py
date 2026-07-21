"""
视频合成Agent - 将内容结构和素材合成为最终视频。

职责：
- 消费内容分析Agent的ContentStructure和素材检索Agent的SceneMaterialMap
- 为每个场景渲染画面图（标题卡/内容场景/结尾卡）
- 内容场景实现"素材背景 + 底部字幕条"的配合展示
- FFmpeg合成为视频（含转场）

设计特点：
- 复用styles配色配置
- 场景图渲染始终可用（PIL），FFmpeg合成可降级
- 依赖注入renderer/composer，便于测试
"""

import time
from pathlib import Path
from typing import Optional, Any, Tuple, List

from core.agents.base_agent import BaseAgent
from core.models import (
    Message,
    ContentStructure,
    Scene,
    SceneMaterialMap,
)
from core.compose.scene_image_renderer import SceneImageRenderer
from core.compose.ffmpeg_composer import FFmpegComposer


DEFAULT_SIZE = (1080, 1920)
DEFAULT_FPS = 30
DEFAULT_TRANSITION = 0.4
DEFAULT_OUTPUT_DIR = "output/agent_videos"


class VideoComposeAgent(BaseAgent):
    """视频合成Agent。

    将内容结构+素材合成为最终视频文件。

    Attributes:
        size: 输出分辨率
        fps: 帧率
        transition_duration: 转场时长
        output_dir: 默认输出目录
    """

    def __init__(
        self,
        agent_id: str = "video_compose",
        name: str = "VideoComposeAgent",
        size: Tuple[int, int] = DEFAULT_SIZE,
        fps: int = DEFAULT_FPS,
        transition_duration: float = DEFAULT_TRANSITION,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        composer: Any = None,
    ):
        """初始化视频合成Agent。

        Args:
            agent_id: Agent ID
            name: Agent名称
            size: 输出分辨率 (宽, 高)
            fps: 帧率
            transition_duration: 转场时长
            output_dir: 默认输出目录
            composer: 可选的FFmpeg合成器（可注入用于测试）
        """
        super().__init__(agent_id, name)
        self.size = size
        self.fps = fps
        self.transition_duration = transition_duration
        self.output_dir = output_dir
        self._composer = composer

    @property
    def composer(self) -> FFmpegComposer:
        """惰性加载FFmpeg合成器。"""
        if self._composer is None:
            self._composer = FFmpegComposer(size=self.size, fps=self.fps)
        return self._composer

    # ---------- 主执行入口 ----------

    async def execute(self, message: Message) -> Message:
        """执行视频合成任务。

        Args:
            message: 包含content和materials的任务消息

        Returns:
            包含视频路径和统计的结果消息
        """
        start_time = time.time()
        self.log_task_start(message)
        self.set_status("processing")

        try:
            # 1. 解析输入
            content, material_map, output_path = self._parse_input(message)

            # 2. 加载风格
            style = self._load_style(content.style)
            renderer = SceneImageRenderer(style=style, size=self.size)

            # 3. 渲染每个场景为画面图
            work_dir = Path(output_path).parent / f".scenes_{Path(output_path).stem}"
            work_dir.mkdir(parents=True, exist_ok=True)

            scene_images: List[Tuple[str, float]] = []
            rendered = 0
            for scene in content.scenes:
                img_path = str(work_dir / f"scene_{scene.scene_id:03d}.png")
                material_path = self._pick_material(scene, material_map)
                ok = renderer.render_scene(
                    scene_type=scene.scene_type,
                    text=scene.text,
                    output_path=img_path,
                    material_path=material_path,
                )
                if ok:
                    scene_images.append((img_path, scene.duration))
                    rendered += 1
                else:
                    self.logger.warning(f"场景 {scene.scene_id} 渲染失败")

            if not scene_images:
                raise RuntimeError("无任何场景成功渲染")

            # 4. FFmpeg合成
            composed = self.composer.compose(
                scenes=scene_images,
                output_path=output_path,
                transition_duration=self.transition_duration,
            )

            duration = time.time() - start_time

            # 5. 构建结果
            if composed:
                result = self._build_result(
                    content, material_map, output_path, rendered, success=True
                )
                self.set_status("idle")
                result_msg = self.create_success_message(message, result)
                self.log_task_end(result_msg, duration)
                self.logger.info(
                    f"✅ 视频合成成功: {output_path} "
                    f"({rendered}场景, {content.computed_duration:.1f}s)"
                )
                return result_msg
            else:
                # FFmpeg失败：降级为图文模式（保留场景图）
                self.logger.warning("FFmpeg合成失败，降级为图文模式")
                result = self._build_result(
                    content, material_map, output_path, rendered,
                    success=False, degraded=True, scenes_dir=str(work_dir),
                )
                self.set_status("idle")
                return self.create_success_message(message, result)

        except Exception as e:
            self.logger.error(f"视频合成失败: {e}", exc_info=True)
            return await self.handle_error(e, message)

    async def handle_error(self, error: Exception, message: Message) -> Message:
        """处理错误。"""
        self.set_status("error")
        return self.create_error_message(message, str(error))

    # ---------- 输入解析 ----------

    def _parse_input(
        self, message: Message
    ) -> Tuple[ContentStructure, SceneMaterialMap, str]:
        """解析任务输入。

        Args:
            message: 任务消息

        Returns:
            (内容结构, 素材映射, 输出路径)
        """
        payload = message.payload or {}

        content_data = payload.get("content")
        if not content_data:
            raise ValueError("缺少content字段")
        content = ContentStructure.from_dict(content_data)

        if not content.scenes:
            raise ValueError("内容结构无场景")

        material_data = payload.get("materials")
        if material_data:
            material_map = SceneMaterialMap.from_dict(material_data)
        else:
            material_map = SceneMaterialMap()

        output_path = payload.get("output_path") or self._default_output_path(content)

        return content, material_map, output_path

    def _default_output_path(self, content: ContentStructure) -> str:
        """生成默认输出路径。

        Args:
            content: 内容结构

        Returns:
            输出路径
        """
        # 用标题的安全化字符串作为文件名
        safe_title = "".join(
            c for c in content.title if c.isalnum() or c in " -_"
        ).strip().replace(" ", "_")[:30] or "video"
        return str(Path(self.output_dir) / f"{safe_title}.mp4")

    # ---------- 素材选择 ----------

    def _pick_material(
        self, scene: Scene, material_map: SceneMaterialMap
    ) -> Optional[str]:
        """为场景选择素材图路径。

        Args:
            scene: 场景
            material_map: 素材映射

        Returns:
            素材本地路径；纯文字场景或无素材返回None
        """
        # 纯文字场景不需要素材
        if scene.is_text_only():
            return None

        assets = material_map.get(scene.scene_id)
        for asset in assets:
            # 优先用有本地文件的真实素材
            if not asset.is_placeholder and asset.local_path:
                if Path(asset.local_path).exists():
                    return asset.local_path
        return None

    # ---------- 风格加载 ----------

    def _load_style(self, style_id: str) -> Optional[dict]:
        """加载风格配置。

        Args:
            style_id: 风格ID

        Returns:
            风格配置字典，失败返回None（渲染器用默认）
        """
        try:
            from styles import get_style
            return get_style(style_id)
        except Exception as e:
            self.logger.debug(f"加载风格 {style_id} 失败: {e}")
            return None

    # ---------- 结果构建 ----------

    def _build_result(
        self,
        content: ContentStructure,
        material_map: SceneMaterialMap,
        output_path: str,
        rendered: int,
        success: bool,
        degraded: bool = False,
        scenes_dir: Optional[str] = None,
    ) -> dict:
        """构建结果字典。

        Args:
            content: 内容结构
            material_map: 素材映射
            output_path: 视频输出路径
            rendered: 成功渲染的场景数
            success: 视频是否合成成功
            degraded: 是否降级为图文模式
            scenes_dir: 降级时的场景图目录

        Returns:
            结果字典
        """
        content_scenes = len(content.get_content_scenes())
        match_rate = material_map.match_rate(content_scenes) if content_scenes else 1.0

        # 质量评分: 素材匹配率(0.6) + 渲染完整度(0.4)
        render_rate = rendered / content.scene_count if content.scene_count else 0
        quality = round(0.6 * match_rate + 0.4 * render_rate, 3)

        return {
            "success": success,
            "degraded": degraded,
            "video_path": output_path if success else None,
            "scenes_dir": scenes_dir,
            "duration": round(content.computed_duration, 1),
            "resolution": f"{self.size[0]}x{self.size[1]}",
            "scenes_rendered": rendered,
            "scene_count": content.scene_count,
            "source": content.source,
            "material_match_rate": round(match_rate, 3),
            "quality_score": quality,
        }
