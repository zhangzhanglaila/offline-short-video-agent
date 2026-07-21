"""
消息数据模型 - Agent间通信的标准格式

定义了Agent通信中使用的消息结构，支持请求、响应、错误等多种消息类型。
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


@dataclass
class Message:
    """Agent间通信的标准消息格式。

    Attributes:
        msg_id: 唯一消息ID (自动生成)
        timestamp: ISO 8601格式的时间戳 (自动生成)
        sender: 发送方Agent ID
        receiver: 接收方Agent ID
        msg_type: 消息类型 (task/result/error/heartbeat)
        task_type: 任务类型 (analyze/fetch_material/compose_video等)
        priority: 优先级 (1=最高, 10=最低)
        timeout: 超时时间 (秒)
        payload: 消息载荷数据
        status: 消息状态 (pending/processing/success/failed)
        result: 执行结果 (成功时)
        error: 错误信息 (失败时)
    """

    # 基础字段
    sender: str
    receiver: str
    msg_type: str  # task, result, error, heartbeat

    # 可选字段
    msg_id: str = field(default_factory=lambda: f"msg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    task_type: Optional[str] = None
    priority: int = 1  # 1最高, 10最低
    timeout: int = 300  # 5分钟默认超时
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, processing, success, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。

        Returns:
            消息字典
        """
        return asdict(self)

    def to_json_compatible(self) -> Dict[str, Any]:
        """转换为JSON兼容的格式。

        Returns:
            JSON兼容的字典
        """
        return {
            "msg_id": self.msg_id,
            "timestamp": self.timestamp,
            "sender": self.sender,
            "receiver": self.receiver,
            "msg_type": self.msg_type,
            "task_type": self.task_type,
            "priority": self.priority,
            "timeout": self.timeout,
            "payload": self.payload,
            "status": self.status,
            "result": self.result,
            "error": self.error
        }

    def is_successful(self) -> bool:
        """判断消息是否表示成功。

        Returns:
            True如果状态为success
        """
        return self.status == "success"

    def is_failed(self) -> bool:
        """判断消息是否表示失败。

        Returns:
            True如果状态为failed或error
        """
        return self.status in ("failed", "error")

    def is_processing(self) -> bool:
        """判断消息是否正在处理中。

        Returns:
            True如果状态为processing
        """
        return self.status == "processing"

    def mark_processing(self) -> None:
        """标记消息为处理中状态。"""
        self.status = "processing"

    def mark_success(self, result: Optional[Dict[str, Any]] = None) -> None:
        """标记消息为成功。

        Args:
            result: 执行结果数据
        """
        self.status = "success"
        self.result = result

    def mark_failed(self, error: str) -> None:
        """标记消息为失败。

        Args:
            error: 错误信息
        """
        self.status = "failed"
        self.error = error

    def __repr__(self) -> str:
        return (
            f"Message(msg_id={self.msg_id}, from {self.sender} to {self.receiver}, "
            f"type={self.msg_type}, status={self.status})"
        )


def create_task_message(
    sender: str,
    receiver: str,
    task_type: str,
    payload: Dict[str, Any],
    priority: int = 1,
    timeout: int = 300
) -> Message:
    """创建任务消息的便捷函数。

    Args:
        sender: 发送方Agent ID
        receiver: 接收方Agent ID
        task_type: 任务类型
        payload: 任务载荷
        priority: 优先级
        timeout: 超时时间

    Returns:
        任务消息对象
    """
    return Message(
        sender=sender,
        receiver=receiver,
        msg_type="task",
        task_type=task_type,
        payload=payload,
        priority=priority,
        timeout=timeout,
        status="pending"
    )


def create_result_message(
    sender: str,
    receiver: str,
    original_msg_id: str,
    result: Dict[str, Any]
) -> Message:
    """创建结果消息的便捷函数。

    Args:
        sender: 发送方Agent ID
        receiver: 接收方Agent ID
        original_msg_id: 原始任务消息ID
        result: 执行结果

    Returns:
        结果消息对象
    """
    return Message(
        sender=sender,
        receiver=receiver,
        msg_type="result",
        msg_id=original_msg_id,  # 保持相同的消息ID用于追踪
        payload=result,
        status="success",
        result=result
    )


def create_error_message(
    sender: str,
    receiver: str,
    original_msg_id: str,
    error: str
) -> Message:
    """创建错误消息的便捷函数。

    Args:
        sender: 发送方Agent ID
        receiver: 接收方Agent ID
        original_msg_id: 原始任务消息ID
        error: 错误信息

    Returns:
        错误消息对象
    """
    return Message(
        sender=sender,
        receiver=receiver,
        msg_type="error",
        msg_id=original_msg_id,  # 保持相同的消息ID用于追踪
        status="failed",
        error=error
    )


def create_heartbeat_message(sender: str) -> Message:
    """创建心跳消息的便捷函数。

    Args:
        sender: 发送方Agent ID

    Returns:
        心跳消息对象
    """
    return Message(
        sender=sender,
        receiver="coordinator",
        msg_type="heartbeat",
        status="success"
    )
