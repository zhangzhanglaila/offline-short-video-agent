"""
内容分析Agent - 将用户需求转化为结构化的视频内容。

职责：
- 理解用户需求
- 生成视频标题和大纲
- 划分场景（标题卡/内容/结尾）
- 为每个场景编写文字和提取关键词

设计特点：
- LLM优先：使用DualModeLLMClient（Ollama本地 + 云端自动切换）
- 规则降级：LLM不可用时，基于规则和语义提取生成有效的内容结构
- 依赖注入：可注入自定义LLM客户端，便于测试
"""

import re
import time
from typing import List, Optional, Dict, Any

from core.agents.base_agent import BaseAgent
from core.models import Message, UserRequest, ContentStructure, Scene, SceneType
from core.prompts.content_analysis_prompts import (
    build_analysis_prompt,
    SYSTEM_PROMPT,
)


# 标题卡和结尾卡的固定时长（秒）
CARD_DURATION = 3.0
# 单个内容场景的理想时长（秒），用于估算场景数
IDEAL_CONTENT_SCENE_DURATION = 7.0
# 内容场景的最少/最多数量约束
MIN_CONTENT_SCENES = 1
MAX_CONTENT_SCENES = 8


class ContentAnalysisAgent(BaseAgent):
    """内容分析Agent。

    将用户的视频生成需求分析为结构化的内容（ContentStructure）。

    Attributes:
        llm_client: LLM客户端（可注入，默认使用全局双模式客户端）
        semantic_extractor: 语义提取器（用于降级路径的关键词提取）
    """

    def __init__(
        self,
        agent_id: str = "content_analysis",
        name: str = "ContentAnalysisAgent",
        llm_client: Any = None,
    ):
        """初始化内容分析Agent。

        Args:
            agent_id: Agent ID
            name: Agent名称
            llm_client: 可选的LLM客户端。None时惰性加载全局客户端。
                        传入False可强制禁用LLM（仅用规则降级，便于测试）。
        """
        super().__init__(agent_id, name)
        self._llm_client = llm_client
        self._llm_disabled = llm_client is False
        self._semantic_extractor = None

    # ---------- 惰性加载依赖 ----------

    @property
    def llm_client(self):
        """惰性加载LLM客户端。"""
        if self._llm_disabled:
            return None
        if self._llm_client is None:
            try:
                from agent.llm.ollama_client import get_llm_client
                self._llm_client = get_llm_client()
            except Exception as e:
                self.logger.warning(f"无法加载LLM客户端: {e}")
                self._llm_disabled = True
                return None
        return self._llm_client

    @property
    def semantic_extractor(self):
        """惰性加载语义提取器。"""
        if self._semantic_extractor is None:
            from core.semantic_extractor import SemanticExtractor
            self._semantic_extractor = SemanticExtractor()
        return self._semantic_extractor

    # ---------- 主执行入口 ----------

    async def execute(self, message: Message) -> Message:
        """执行内容分析任务。

        Args:
            message: 包含UserRequest的任务消息

        Returns:
            包含ContentStructure的结果消息
        """
        start_time = time.time()
        self.log_task_start(message)
        self.set_status("processing")

        try:
            # 1. 解析并验证请求
            request = self._parse_request(message)
            if not request.validate():
                raise ValueError(f"无效的用户请求: {request.to_dict()}")

            # 2. 分析内容（LLM优先，失败降级）
            content = await self._analyze(request)

            # 3. 验证输出
            is_valid, err = content.validate()
            if not is_valid:
                # LLM输出无效时降级到规则路径
                self.logger.warning(f"内容结构验证失败({content.source}): {err}，降级到规则路径")
                content = self._analyze_by_rules(request)
                is_valid, err = content.validate()
                if not is_valid:
                    raise ValueError(f"内容结构验证失败: {err}")

            # 4. 返回结果
            duration = time.time() - start_time
            self.set_status("idle")
            result_msg = self.create_success_message(message, content.to_dict())
            self.log_task_end(result_msg, duration)
            self.logger.info(f"\n{content.get_summary()}")
            return result_msg

        except Exception as e:
            self.logger.error(f"内容分析失败: {e}", exc_info=True)
            return await self.handle_error(e, message)

    async def handle_error(self, error: Exception, message: Message) -> Message:
        """处理错误。

        Args:
            error: 发生的异常
            message: 原始消息

        Returns:
            错误消息
        """
        self.set_status("error")
        return self.create_error_message(message, str(error))

    # ---------- 请求解析 ----------

    def _parse_request(self, message: Message) -> UserRequest:
        """从消息中解析用户请求。

        Args:
            message: 任务消息

        Returns:
            UserRequest对象
        """
        payload = message.payload or {}
        return UserRequest(
            user_input=payload.get("user_input", ""),
            category=payload.get("category", ""),
            style=payload.get("style", ""),
            duration=int(payload.get("duration", 30)),
            request_id=payload.get("request_id", f"req_{message.msg_id}"),
        )

    # ---------- 分析（LLM优先） ----------

    async def _analyze(self, request: UserRequest) -> ContentStructure:
        """分析内容，LLM优先，不可用时降级。

        Args:
            request: 用户请求

        Returns:
            内容结构
        """
        client = self.llm_client
        if client is None:
            self.logger.info("LLM不可用，使用规则路径生成内容")
            return self._analyze_by_rules(request)

        # 检查LLM实际可用性
        try:
            available = client.local.check_available() or client.cloud.check_available()
        except Exception:
            available = False

        if not available:
            self.logger.info("LLM服务未就绪，使用规则路径生成内容")
            return self._analyze_by_rules(request)

        try:
            return self._analyze_by_llm(request, client)
        except Exception as e:
            self.logger.warning(f"LLM分析失败: {e}，降级到规则路径")
            return self._analyze_by_rules(request)

    def _analyze_by_llm(self, request: UserRequest, client) -> ContentStructure:
        """使用LLM分析内容。

        Args:
            request: 用户请求
            client: LLM客户端

        Returns:
            内容结构
        """
        scene_count = self._estimate_scene_count(request.duration)
        prompt = build_analysis_prompt(
            user_input=request.user_input,
            category=request.category,
            style=request.style,
            duration=request.duration,
            suggested_scene_count=scene_count,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        response = client.chat(messages, temperature=0.7)

        # 提取JSON
        data = self._extract_json(response)
        if not data:
            raise ValueError("LLM响应中未找到有效JSON")

        # 补全字段并构建内容结构
        data["category"] = request.category
        data["style"] = request.style
        data["total_duration"] = request.duration
        data["source"] = "llm"

        content = ContentStructure.from_dict(data)

        # 确保每个内容场景都有关键词（LLM有时会遗漏）
        for scene in content.scenes:
            if scene.scene_type == SceneType.CONTENT.value and not scene.keywords:
                scene.keywords = self._extract_keywords(scene.text)

        return content

    # ---------- 分析（规则降级） ----------

    def _analyze_by_rules(self, request: UserRequest) -> ContentStructure:
        """使用规则生成内容结构（LLM降级路径）。

        将用户输入按句子切分，分配为内容场景，
        自动生成标题卡和结尾卡，并用语义提取器补充关键词。

        Args:
            request: 用户请求

        Returns:
            内容结构
        """
        segments = self._split_sentences(request.user_input)

        # 根据时长确定内容场景数量
        target_content_scenes = self._estimate_scene_count(request.duration) - 2
        target_content_scenes = max(MIN_CONTENT_SCENES, target_content_scenes)

        # 将句子分组为目标数量的场景
        content_segments = self._group_segments(segments, target_content_scenes)

        # 计算时长分配
        content_duration = max(
            request.duration - 2 * CARD_DURATION,
            len(content_segments) * 2.0,
        )
        per_scene = content_duration / len(content_segments)

        scenes: List[Scene] = []

        # 1. 标题卡
        title = self._generate_title(request)
        scenes.append(Scene(
            scene_id=1,
            scene_type=SceneType.TITLE_CARD.value,
            text=title,
            duration=CARD_DURATION,
            keywords=[],
        ))

        # 2. 内容场景
        for i, segment in enumerate(content_segments):
            scenes.append(Scene(
                scene_id=i + 2,
                scene_type=SceneType.CONTENT.value,
                text=segment[:30],
                duration=round(per_scene, 1),
                keywords=self._extract_keywords(segment),
                narration=segment,
            ))

        # 3. 结尾卡
        scenes.append(Scene(
            scene_id=len(scenes) + 1,
            scene_type=SceneType.CONCLUSION.value,
            text=self._generate_conclusion(request),
            duration=CARD_DURATION,
            keywords=[],
        ))

        return ContentStructure(
            title=title,
            category=request.category,
            style=request.style,
            total_duration=request.duration,
            scenes=scenes,
            source="fallback",
            metadata={"segments": len(segments)},
        )

    # ---------- 辅助方法 ----------

    def _estimate_scene_count(self, duration: int) -> int:
        """根据时长估算总场景数（含标题卡和结尾卡）。

        Args:
            duration: 目标时长（秒）

        Returns:
            估算的场景数
        """
        content_scenes = round(duration / IDEAL_CONTENT_SCENE_DURATION)
        content_scenes = max(MIN_CONTENT_SCENES, min(MAX_CONTENT_SCENES, content_scenes))
        return content_scenes + 2  # 加上标题卡和结尾卡

    def _split_sentences(self, text: str) -> List[str]:
        """将文本切分为句子。

        Args:
            text: 输入文本

        Returns:
            句子列表（已去除空白）
        """
        # 按中英文标点切分
        parts = re.split(r'[。！？；\.\!\?;\n]+', text)
        sentences = [p.strip() for p in parts if p.strip()]
        # 若无法切分（单句无标点），按逗号切分
        if len(sentences) <= 1:
            parts = re.split(r'[，,、]+', text)
            sentences = [p.strip() for p in parts if p.strip()]
        # 仍然只有一句，直接返回原文
        if not sentences:
            sentences = [text.strip()] if text.strip() else ["视频内容"]
        return sentences

    def _group_segments(self, segments: List[str], target_count: int) -> List[str]:
        """将句子列表分组为目标数量的段落。

        Args:
            segments: 句子列表
            target_count: 目标段落数

        Returns:
            分组后的段落列表
        """
        if not segments:
            return ["视频内容"]

        target_count = max(1, min(target_count, len(segments)))

        # 均匀分组
        groups: List[str] = []
        chunk_size = len(segments) / target_count
        for i in range(target_count):
            start = int(i * chunk_size)
            end = int((i + 1) * chunk_size) if i < target_count - 1 else len(segments)
            chunk = segments[start:end]
            groups.append("，".join(chunk) if chunk else segments[min(start, len(segments) - 1)])

        return groups

    def _extract_keywords(self, text: str, top_k: int = 3) -> List[str]:
        """从文本中提取关键词。

        Args:
            text: 输入文本
            top_k: 返回的关键词数量

        Returns:
            关键词列表
        """
        try:
            keywords = self.semantic_extractor.extract_keywords(text)
            # extract_keywords返回 [(词, 权重), ...]
            result = [kw for kw, _ in keywords[:top_k]]
            if result:
                return result
        except Exception as e:
            self.logger.debug(f"关键词提取失败: {e}")

        # 降级：取文本前几个字符作为兜底
        cleaned = re.sub(r'[^\w一-鿿]', '', text)
        return [cleaned[:6]] if cleaned else []

    def _generate_title(self, request: UserRequest) -> str:
        """生成视频标题（规则路径）。

        Args:
            request: 用户请求

        Returns:
            标题文本
        """
        text = request.user_input.strip()
        # 取第一句作为标题基础
        first = self._split_sentences(text)[0]
        # 限制长度
        if len(first) > 20:
            first = first[:20]
        return first

    def _generate_conclusion(self, request: UserRequest) -> str:
        """生成结尾文字（规则路径，按分类定制）。

        Args:
            request: 用户请求

        Returns:
            结尾文本
        """
        conclusions = {
            "教育讲解": "以上就是本期内容\n感谢观看",
            "短视频": "点赞关注\n下期更精彩",
            "纪录片": "故事仍在继续",
            "商业宣传": "立即了解更多",
        }
        return conclusions.get(request.category, "感谢观看")

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从LLM响应中提取JSON对象。

        Args:
            text: LLM响应文本

        Returns:
            解析出的字典，失败返回None
        """
        import json

        # 优先使用客户端的提取方法
        client = self._llm_client
        if client and hasattr(client, "extract_json_from_response"):
            try:
                result = client.extract_json_from_response(text)
                if result:
                    return result
            except Exception:
                pass

        # 兜底：正则提取第一个JSON对象
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
