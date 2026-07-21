"""
主控Agent (Coordinator) - 编排整个视频生成流程。

职责：
- 接收用户需求
- 通过MessageBus下发任务给子Agent
- 汇总子Agent结果，校验质量
- 超时控制、重试、异常降级
- 组装最终VideoResult

通信模式：
- 子Agent各自运行serve-loop监听消息队列
- Coordinator下发任务 → 子Agent处理并回传 → Coordinator接收
- 全程通过MessageBus传递结构化JSON报文（而非直接调用）
"""

import time
import asyncio
from typing import Optional, Any, Tuple, List

from core.agents.base_agent import BaseAgent
from core.agents.message_bus import MessageBus
from core.models import (
    Message,
    UserRequest,
    ContentStructure,
    SceneMaterialMap,
    AgentResult,
    VideoResult,
    create_task_message,
)


# 各阶段的超时和重试配置
STAGE_CONFIG = {
    "analyze": {"timeout": 120, "retries": 1},
    "fetch_material": {"timeout": 180, "retries": 2},
    "compose_video": {"timeout": 300, "retries": 1},
}

# 子Agent的ID
CONTENT_AGENT_ID = "content_analysis"
MATERIAL_AGENT_ID = "material_fetch"
COMPOSE_AGENT_ID = "video_compose"


class CoordinatorAgent(BaseAgent):
    """主控Agent。

    编排内容分析→素材检索→视频合成的完整流程，
    通过MessageBus与子Agent通信。

    Attributes:
        bus: 消息总线
        content_agent: 内容分析Agent
        material_agent: 素材检索Agent
        compose_agent: 视频合成Agent
    """

    def __init__(
        self,
        agent_id: str = "coordinator",
        name: str = "CoordinatorAgent",
        bus: Optional[MessageBus] = None,
        content_agent: Any = None,
        material_agent: Any = None,
        compose_agent: Any = None,
    ):
        """初始化主控Agent。

        Args:
            agent_id: Agent ID
            name: Agent名称
            bus: 消息总线。None时新建。
            content_agent: 内容分析Agent。None时惰性创建默认。
            material_agent: 素材检索Agent。None时惰性创建默认。
            compose_agent: 视频合成Agent。None时惰性创建默认。
        """
        super().__init__(agent_id, name)
        self.bus = bus or MessageBus()
        self._content_agent = content_agent
        self._material_agent = material_agent
        self._compose_agent = compose_agent

    # ---------- 惰性加载子Agent ----------

    @property
    def content_agent(self):
        if self._content_agent is None:
            from core.agents.content_analysis_agent import ContentAnalysisAgent
            self._content_agent = ContentAnalysisAgent()
        return self._content_agent

    @property
    def material_agent(self):
        if self._material_agent is None:
            from core.agents.material_fetch_agent import MaterialFetchAgent
            self._material_agent = MaterialFetchAgent()
        return self._material_agent

    @property
    def compose_agent(self):
        if self._compose_agent is None:
            from core.agents.video_compose_agent import VideoComposeAgent
            self._compose_agent = VideoComposeAgent()
        return self._compose_agent

    # ---------- 主入口 ----------

    async def process_request(self, request: UserRequest) -> VideoResult:
        """处理用户需求，生成视频。

        Args:
            request: 用户需求

        Returns:
            视频生成结果
        """
        start_time = time.time()
        self.logger.info(f"开始处理请求: {request.request_id} - {request.user_input[:30]}")

        video_result = VideoResult(request_id=request.request_id, success=False)

        # 校验请求
        if not request.validate():
            video_result.error = "无效的用户请求"
            return video_result

        # 注册所有Agent到总线
        await self._register_agents()

        # 启动子Agent的serve-loop
        workers = await self._start_workers()

        try:
            # === 阶段1: 内容分析 ===
            content, content_result = await self._stage_content(request)
            video_result.add_stage_result("content_analysis", content_result)
            if content is None:
                video_result.error = "内容分析失败: " + (content_result.error or "未知")
                return video_result

            # === 阶段2: 素材检索 ===
            materials, material_result = await self._stage_material(content)
            video_result.add_stage_result("material_fetch", material_result)
            # 素材检索即使全占位符也能继续（不阻断）

            # === 阶段3: 视频合成 ===
            compose_data, compose_result = await self._stage_compose(content, materials)
            video_result.add_stage_result("video_compose", compose_result)
            if compose_data is None:
                video_result.error = "视频合成失败: " + (compose_result.error or "未知")
                return video_result

            # === 汇总 ===
            video_result.success = bool(compose_data.get("success"))
            video_result.video_path = compose_data.get("video_path")
            video_result.duration = int(compose_data.get("duration", 0))
            video_result.resolution = compose_data.get("resolution", "")
            video_result.quality_score = compose_data.get("quality_score", 0.0)
            if not video_result.success:
                video_result.error = "视频合成降级为图文模式"

            return video_result

        except Exception as e:
            self.logger.error(f"流程异常: {e}", exc_info=True)
            video_result.error = str(e)
            return video_result

        finally:
            video_result.total_time = round(time.time() - start_time, 2)
            # 停止serve-loop
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)
            self.logger.info(
                f"请求处理完成: {request.request_id}, "
                f"耗时{video_result.total_time}s, 成功={video_result.success}"
            )

    # ---------- 阶段实现 ----------

    async def _stage_content(
        self, request: UserRequest
    ) -> Tuple[Optional[ContentStructure], AgentResult]:
        """阶段1: 内容分析。

        Args:
            request: 用户请求

        Returns:
            (内容结构或None, 阶段结果)
        """
        self.logger.info("[阶段1] 内容分析...")
        task = create_task_message(
            sender=self.agent_id,
            receiver=CONTENT_AGENT_ID,
            task_type="analyze",
            payload=request.to_dict(),
        )
        reply = await self._dispatch("analyze", task)

        if reply is None or not reply.is_successful():
            err = reply.error if reply else "超时无响应"
            return None, AgentResult(False, CONTENT_AGENT_ID, "analyze", error=err)

        content = ContentStructure.from_dict(reply.result)
        return content, AgentResult(
            True, CONTENT_AGENT_ID, "analyze",
            data={"source": content.source, "scenes": content.scene_count},
        )

    async def _stage_material(
        self, content: ContentStructure
    ) -> Tuple[SceneMaterialMap, AgentResult]:
        """阶段2: 素材检索。

        Args:
            content: 内容结构

        Returns:
            (素材映射, 阶段结果)。失败时返回空映射（不阻断流程）。
        """
        self.logger.info("[阶段2] 素材检索...")
        task = create_task_message(
            sender=self.agent_id,
            receiver=MATERIAL_AGENT_ID,
            task_type="fetch_material",
            payload=content.to_dict(),
        )
        reply = await self._dispatch("fetch_material", task)

        if reply is None or not reply.is_successful():
            # 素材失败不阻断：用空映射，合成阶段会用渐变背景
            self.logger.warning("素材检索失败，使用空映射降级")
            return SceneMaterialMap(), AgentResult(
                False, MATERIAL_AGENT_ID, "fetch_material",
                error=(reply.error if reply else "超时"),
            )

        materials = SceneMaterialMap.from_dict(reply.result)
        return materials, AgentResult(
            True, MATERIAL_AGENT_ID, "fetch_material",
            data=materials.metadata,
        )

    async def _stage_compose(
        self, content: ContentStructure, materials: SceneMaterialMap
    ) -> Tuple[Optional[dict], AgentResult]:
        """阶段3: 视频合成。

        Args:
            content: 内容结构
            materials: 素材映射

        Returns:
            (合成结果字典或None, 阶段结果)
        """
        self.logger.info("[阶段3] 视频合成...")
        task = create_task_message(
            sender=self.agent_id,
            receiver=COMPOSE_AGENT_ID,
            task_type="compose_video",
            payload={
                "content": content.to_dict(),
                "materials": materials.to_dict(),
            },
        )
        reply = await self._dispatch("compose_video", task)

        if reply is None or not reply.is_successful():
            err = reply.error if reply else "超时无响应"
            return None, AgentResult(False, COMPOSE_AGENT_ID, "compose_video", error=err)

        data = reply.result
        return data, AgentResult(
            True, COMPOSE_AGENT_ID, "compose_video",
            data={"quality": data.get("quality_score"),
                  "degraded": data.get("degraded")},
        )

    # ---------- 通信：下发+重试 ----------

    async def _dispatch(self, stage: str, task: Message) -> Optional[Message]:
        """下发任务并等待响应，带超时和重试。

        Args:
            stage: 阶段名（决定超时/重试配置）
            task: 任务消息

        Returns:
            响应消息；全部重试失败返回None或最后一次失败响应
        """
        config = STAGE_CONFIG.get(stage, {"timeout": 120, "retries": 1})
        timeout = config["timeout"]
        max_retries = config["retries"]

        last_reply: Optional[Message] = None
        for attempt in range(max_retries + 1):
            if attempt > 0:
                self.logger.warning(f"[{stage}] 重试 {attempt}/{max_retries}")

            await self.bus.send(task)
            reply = await self.bus.receive(self.agent_id, timeout=timeout)

            if reply is not None:
                last_reply = reply
                if reply.is_successful():
                    return reply

        return last_reply

    # ---------- Agent运行时管理 ----------

    async def _register_agents(self) -> None:
        """注册所有Agent到消息总线。"""
        await self.bus.register_agent(self.agent_id)
        await self.bus.register_agent(CONTENT_AGENT_ID)
        await self.bus.register_agent(MATERIAL_AGENT_ID)
        await self.bus.register_agent(COMPOSE_AGENT_ID)

    async def _start_workers(self) -> List[asyncio.Task]:
        """为每个子Agent启动serve-loop。

        Returns:
            worker任务列表
        """
        return [
            asyncio.create_task(self._serve_loop(CONTENT_AGENT_ID, self.content_agent)),
            asyncio.create_task(self._serve_loop(MATERIAL_AGENT_ID, self.material_agent)),
            asyncio.create_task(self._serve_loop(COMPOSE_AGENT_ID, self.compose_agent)),
        ]

    async def _serve_loop(self, agent_id: str, agent: Any) -> None:
        """子Agent的服务循环：接收消息→执行→回传结果。

        Args:
            agent_id: Agent ID
            agent: Agent实例
        """
        while True:
            try:
                msg = await self.bus.receive(agent_id, timeout=None)
                if msg is None:
                    continue
                # 执行任务并回传
                reply = await agent.execute(msg)
                await self.bus.send(reply)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"[{agent_id}] serve-loop异常: {e}")

    # ---------- BaseAgent接口 ----------

    async def execute(self, message: Message) -> Message:
        """BaseAgent接口实现：从消息处理请求。

        Args:
            message: 包含UserRequest的消息

        Returns:
            包含VideoResult的结果消息
        """
        payload = message.payload or {}
        request = UserRequest(
            user_input=payload.get("user_input", ""),
            category=payload.get("category", ""),
            style=payload.get("style", ""),
            duration=int(payload.get("duration", 30)),
        )
        result = await self.process_request(request)
        return self.create_success_message(message, result.to_dict())

    async def handle_error(self, error: Exception, message: Message) -> Message:
        """处理错误。"""
        return self.create_error_message(message, str(error))
