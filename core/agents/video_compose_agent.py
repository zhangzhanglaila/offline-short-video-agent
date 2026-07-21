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
from core.compose.motion.ken_burns import make_ken_burns
from core.compose.motion.clip_spec import SceneClipSpec


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
        enable_motion: bool = True,
        enable_elements: bool = True,
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
        self.enable_motion = enable_motion
        self.enable_elements = enable_elements
        self._content_counter = 0

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

            # 3. 为每个场景构建片段规格(D1: 分层+运镜)
            work_dir = Path(output_path).parent / f".scenes_{Path(output_path).stem}"
            work_dir.mkdir(parents=True, exist_ok=True)

            scene_specs = []
            rendered_types = []  # 与scene_specs对齐的场景类型(供转场选择)
            rendered = 0
            self._content_counter = 0  # 每次生成重置内容场景计数(徽章序号)
            for idx, scene in enumerate(content.scenes):
                spec = self._build_scene_spec(scene, idx, material_map, renderer, work_dir)
                if spec is not None:
                    scene_specs.append(spec)
                    rendered_types.append(scene.scene_type)
                    rendered += 1
                else:
                    self.logger.warning(f"场景 {scene.scene_id} 渲染失败")

            if not scene_specs:
                raise RuntimeError("无任何场景成功渲染")

            # 4. 计算各边界转场(D4: 按场景类型智能选择，与已渲染场景对齐)
            from core.compose.motion.transitions import build_transitions
            transitions = build_transitions(rendered_types) if self.enable_motion else None

            # 5. FFmpeg合成
            composed = self.composer.compose(
                scenes=scene_specs,
                output_path=output_path,
                transition_duration=self.transition_duration,
                transitions=transitions,
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
            素材资产(MaterialAsset)；纯文字场景或无素材返回None
        """
        # 纯文字场景不需要素材
        if scene.is_text_only():
            return None

        assets = material_map.get(scene.scene_id)
        for asset in assets:
            # 优先用有本地文件的真实素材
            if not asset.is_placeholder and asset.local_path:
                if Path(asset.local_path).exists():
                    return asset
        return None

    # ---------- 场景片段构建(D1) ----------

    def _build_scene_spec(self, scene, idx, material_map, renderer, work_dir):
        """为场景构建片段规格(分层+运镜)。

        - 内容场景: 素材(或渐变)背景 + Ken Burns运镜 + 轻量字幕覆盖层
        - 标题/结尾卡: 静态文字卡，无运镜

        Args:
            scene: 场景
            idx: 场景索引(用于运镜变体)
            material_map: 素材映射
            renderer: 场景图渲染器
            work_dir: 工作目录

        Returns:
            SceneClipSpec，失败返回None
        """
        from core.compose.motion.animation_spec import (
            OverlayLayer, AnimationSpec,
            ANIM_FADE_IN, ANIM_SLIDE_UP, ANIM_NONE,
        )

        sid = scene.scene_id

        # 文字卡(标题/结尾): 纯色背景 + 标题文字层(淡入动画)
        if scene.is_text_only():
            if self.enable_motion:
                bg_path = str(work_dir / f"scene_{sid:03d}_solidbg.png")
                title_path = str(work_dir / f"scene_{sid:03d}_title.png")
                if (renderer.render_solid_bg(bg_path)
                        and renderer.render_title_overlay(
                            scene.text, title_path, scene.scene_type)):
                    anim = AnimationSpec(anim_type=ANIM_FADE_IN,
                                         start=0.1, duration=0.6)
                    return SceneClipSpec(
                        background_path=bg_path, duration=scene.duration,
                        overlays=[OverlayLayer(title_path, anim)],
                    )
            # 降级：静态整屏文字卡
            card_path = str(work_dir / f"scene_{sid:03d}_card.png")
            if not renderer.render_scene(
                scene_type=scene.scene_type, text=scene.text,
                output_path=card_path, material_path=None,
            ):
                return None
            return SceneClipSpec(background_path=card_path, duration=scene.duration)

        # 内容场景: 背景 + 运镜/视频 + 字幕覆盖层(上滑淡入)
        asset = self._pick_material(scene, material_map)
        is_video_bg = False
        if asset and getattr(asset, "media_type", "image") == "video":
            # D5: 视频背景(本身动态，不用Ken Burns)
            background_path = asset.local_path
            is_video_bg = True
        elif asset:
            background_path = asset.local_path  # 静图直接给运镜(内部cover-fit)
        else:
            background_path = str(work_dir / f"scene_{sid:03d}_bg.png")
            if not renderer.render_gradient_bg(background_path):
                return None

        kb = None
        if self.enable_motion and not is_video_bg:
            # 视频背景不叠加Ken Burns
            kb = make_ken_burns(idx, self.size, self.fps, scene.duration)

        overlays = []
        overlay_path = None
        if self.enable_motion:
            # D3: 多元素编排(序号徽章→关键词标签→字幕，错开出现)
            from core.compose.motion.scene_composer import build_content_overlays
            self._content_counter += 1
            overlays = build_content_overlays(
                scene, self._content_counter, renderer, work_dir,
                with_badge=self.enable_elements,
            )
        else:
            # 关闭动画: 静态字幕
            sub_path = str(work_dir / f"scene_{sid:03d}_sub.png")
            if renderer.render_subtitle_overlay(scene.text, sub_path):
                overlay_path = sub_path

        return SceneClipSpec(
            background_path=background_path,
            duration=scene.duration,
            ken_burns=kb,
            overlay_path=overlay_path,
            overlays=overlays,
            background_is_video=is_video_bg,
        )

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
