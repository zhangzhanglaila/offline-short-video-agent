"""
MessageBus - 异步消息总线。

负责Agent间的异步通信，支持消息发送、接收、超时控制等功能。
"""

import asyncio
import logging
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime

from core.models import Message


class MessageBus:
    """异步消息总线。

    负责管理Agent间的通信，使用消息队列和回调机制实现解耦通信。

    Attributes:
        inbox: 消息队列字典 {agent_id: 消息队列}
        subscribers: 订阅者字典 {agent_id: 回调函数列表}
        message_log: 消息日志（可选）
    """

    def __init__(self, enable_logging: bool = True):
        """初始化MessageBus。

        Args:
            enable_logging: 是否启用消息日志
        """
        self.inbox: Dict[str, asyncio.Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_log: List[Message] = []
        self.enable_logging = enable_logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("MessageBus initialized")

    async def register_agent(self, agent_id: str) -> None:
        """注册一个Agent。

        Args:
            agent_id: Agent的ID
        """
        if agent_id not in self.inbox:
            self.inbox[agent_id] = asyncio.Queue()
            self.subscribers[agent_id] = []
            self.logger.info(f"Registered agent: {agent_id}")

    async def unregister_agent(self, agent_id: str) -> None:
        """注销一个Agent。

        Args:
            agent_id: Agent的ID
        """
        if agent_id in self.inbox:
            del self.inbox[agent_id]
            del self.subscribers[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")

    async def send(self, message: Message) -> None:
        """发送消息。

        Args:
            message: 要发送的消息
        """
        receiver = message.receiver

        # 验证接收者存在
        if receiver not in self.inbox:
            error_msg = f"Receiver '{receiver}' not found"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # 添加到接收者的队列
        await self.inbox[receiver].put(message)

        # 记录消息
        if self.enable_logging:
            self._log_message(message)

        self.logger.debug(
            f"Message sent: {message.msg_id} from {message.sender} to {receiver}"
        )

        # 触发订阅回调
        await self._trigger_subscribers(receiver, message)

    async def receive(
        self,
        agent_id: str,
        timeout: Optional[float] = None
    ) -> Optional[Message]:
        """接收消息（阻塞）。

        Args:
            agent_id: Agent的ID
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            接收到的消息，超时时返回None
        """
        if agent_id not in self.inbox:
            self.logger.warning(f"Agent '{agent_id}' not registered")
            return None

        try:
            message = await asyncio.wait_for(
                self.inbox[agent_id].get(),
                timeout=timeout
            )
            self.logger.debug(
                f"Message received by {agent_id}: {message.msg_id}"
            )
            return message
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for message for {agent_id}")
            return None

    async def subscribe(
        self,
        agent_id: str,
        callback: Callable[[Message], Any]
    ) -> None:
        """订阅某个Agent的消息。

        Args:
            agent_id: 要订阅的Agent ID
            callback: 消息到达时的回调函数
        """
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []

        self.subscribers[agent_id].append(callback)
        self.logger.info(f"Subscriber registered for {agent_id}")

    async def unsubscribe(
        self,
        agent_id: str,
        callback: Callable[[Message], Any]
    ) -> None:
        """取消订阅。

        Args:
            agent_id: Agent ID
            callback: 要移除的回调函数
        """
        if agent_id in self.subscribers and callback in self.subscribers[agent_id]:
            self.subscribers[agent_id].remove(callback)
            self.logger.info(f"Subscriber unregistered for {agent_id}")

    async def broadcast(self, message: Message) -> None:
        """广播消息给多个Agent。

        Args:
            message: 要广播的消息
        """
        for agent_id in self.inbox.keys():
            if agent_id != message.sender:
                msg_copy = Message(
                    sender=message.sender,
                    receiver=agent_id,
                    msg_type=message.msg_type,
                    task_type=message.task_type,
                    payload=message.payload,
                    priority=message.priority,
                    timeout=message.timeout
                )
                await self.send(msg_copy)
        self.logger.debug(f"Broadcast message: {message.msg_id}")

    async def wait_for_response(
        self,
        message_id: str,
        agent_id: str,
        timeout: float = 30.0
    ) -> Optional[Message]:
        """等待特定消息的响应。

        Args:
            message_id: 原始消息ID
            agent_id: 要等待响应的Agent ID
            timeout: 超时时间（秒）

        Returns:
            响应消息，超时时返回None
        """
        start_time = datetime.now()
        deadline = start_time.timestamp() + timeout

        while True:
            message = await self.receive(agent_id, timeout=1.0)
            if message and message.msg_id == message_id:
                return message

            if datetime.now().timestamp() > deadline:
                self.logger.warning(
                    f"Timeout waiting for response to message {message_id}"
                )
                return None

    def get_queue_size(self, agent_id: str) -> int:
        """获取Agent的消息队列大小。

        Args:
            agent_id: Agent ID

        Returns:
            队列中的消息数
        """
        if agent_id in self.inbox:
            return self.inbox[agent_id].qsize()
        return 0

    def get_message_log(
        self,
        agent_id: Optional[str] = None,
        msg_type: Optional[str] = None
    ) -> List[Message]:
        """获取消息日志（可用于调试）。

        Args:
            agent_id: 过滤特定Agent的消息
            msg_type: 过滤特定类型的消息

        Returns:
            过滤后的消息列表
        """
        logs = self.message_log

        if agent_id:
            logs = [m for m in logs if m.sender == agent_id or m.receiver == agent_id]

        if msg_type:
            logs = [m for m in logs if m.msg_type == msg_type]

        return logs

    def clear_logs(self) -> None:
        """清除消息日志。"""
        self.message_log.clear()
        self.logger.info("Message log cleared")

    def get_stats(self) -> Dict[str, Any]:
        """获取消息总线的统计信息。

        Returns:
            统计信息字典
        """
        return {
            "registered_agents": list(self.inbox.keys()),
            "agent_count": len(self.inbox),
            "queue_sizes": {
                agent_id: self.get_queue_size(agent_id)
                for agent_id in self.inbox.keys()
            },
            "total_messages": len(self.message_log),
            "messages_by_type": self._count_messages_by_type(),
        }

    def _count_messages_by_type(self) -> Dict[str, int]:
        """统计各类型的消息数量。

        Returns:
            消息类型统计字典
        """
        counts: Dict[str, int] = {}
        for msg in self.message_log:
            counts[msg.msg_type] = counts.get(msg.msg_type, 0) + 1
        return counts

    def _log_message(self, message: Message) -> None:
        """记录消息。

        Args:
            message: 要记录的消息
        """
        self.message_log.append(message)

    async def _trigger_subscribers(
        self,
        agent_id: str,
        message: Message
    ) -> None:
        """触发订阅回调。

        Args:
            agent_id: Agent ID
            message: 消息对象
        """
        if agent_id in self.subscribers:
            for callback in self.subscribers[agent_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    self.logger.error(f"Error in subscriber callback: {e}")

    def __repr__(self) -> str:
        return (
            f"MessageBus("
            f"agents={len(self.inbox)}, "
            f"messages={len(self.message_log)}"
            f")"
        )


# 全局消息总线实例
_message_bus: Optional[MessageBus] = None


def get_message_bus(enable_logging: bool = True) -> MessageBus:
    """获取全局MessageBus实例。

    Args:
        enable_logging: 是否启用消息日志

    Returns:
        全局MessageBus实例
    """
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus(enable_logging=enable_logging)
    return _message_bus


def reset_message_bus() -> None:
    """重置全局MessageBus（主要用于测试）。"""
    global _message_bus
    _message_bus = None
