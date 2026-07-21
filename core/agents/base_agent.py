"""
BaseAgent抽象类 - 所有Agent的基类。

定义了Agent的基本接口和生命周期，所有具体的Agent都必须继承此类。
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

from core.models import Message, AgentResult


def get_logger(name: str) -> logging.Logger:
    """获取或创建logger。

    Args:
        name: Logger名称

    Returns:
        Logger实例
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class BaseAgent(ABC):
    """Agent的抽象基类。

    所有具体的Agent（如ContentAnalysisAgent、MaterialFetchAgent等）都必须
    继承此类并实现execute和handle_error方法。

    Attributes:
        agent_id: Agent的唯一标识
        name: Agent的名称
        logger: Agent的日志对象
        status: Agent的当前状态 (idle/processing/error)
    """

    def __init__(self, agent_id: str, name: str):
        """初始化Agent。

        Args:
            agent_id: Agent的唯一标识
            name: Agent的名称
        """
        self.agent_id = agent_id
        self.name = name
        self.logger = get_logger(name)
        self.status = "idle"
        self.logger.info(f"Agent initialized: {name} ({agent_id})")

    @abstractmethod
    async def execute(self, message: Message) -> Message:
        """执行任务的抽象方法。

        子类必须实现此方法以处理具体的任务逻辑。

        Args:
            message: 包含任务信息的消息对象

        Returns:
            执行结果消息
        """
        pass

    @abstractmethod
    async def handle_error(self, error: Exception, message: Message) -> Message:
        """处理错误的抽象方法。

        子类应该实现此方法来处理执行过程中的异常。

        Args:
            error: 发生的异常
            message: 原始的消息对象

        Returns:
            错误消息
        """
        pass

    async def validate_input(self, message: Message) -> bool:
        """验证输入消息的有效性。

        可在子类中覆盖以实现自定义验证逻辑。

        Args:
            message: 要验证的消息

        Returns:
            True如果消息有效
        """
        if not message:
            self.logger.warning("Received None message")
            return False

        if not message.sender:
            self.logger.warning("Message has no sender")
            return False

        if not message.payload:
            self.logger.warning("Message has empty payload")
            return False

        return True

    def set_status(self, status: str) -> None:
        """设置Agent的状态。

        Args:
            status: 新状态 (idle/processing/error)
        """
        self.status = status
        self.logger.debug(f"Agent status changed to: {status}")

    def format_result(
        self,
        data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> AgentResult:
        """格式化执行结果。

        Args:
            data: 执行数据
            success: 是否成功
            error: 错误信息
            task_type: 任务类型

        Returns:
            格式化的结果对象
        """
        return AgentResult(
            success=success,
            agent_id=self.agent_id,
            task_type=task_type or "unknown",
            data=data,
            error=error
        )

    def create_error_message(
        self,
        original_message: Message,
        error_text: str
    ) -> Message:
        """创建错误消息。

        Args:
            original_message: 原始消息
            error_text: 错误信息文本

        Returns:
            错误消息对象
        """
        msg = Message(
            sender=self.agent_id,
            receiver=original_message.sender,
            msg_type="error",
            msg_id=original_message.msg_id,
            status="failed",
            error=error_text
        )
        self.logger.error(f"Error occurred: {error_text}")
        return msg

    def create_success_message(
        self,
        original_message: Message,
        result_data: Dict[str, Any]
    ) -> Message:
        """创建成功响应消息。

        Args:
            original_message: 原始消息
            result_data: 结果数据

        Returns:
            成功消息对象
        """
        msg = Message(
            sender=self.agent_id,
            receiver=original_message.sender,
            msg_type="result",
            msg_id=original_message.msg_id,
            status="success",
            result=result_data
        )
        self.logger.info(f"Task completed successfully")
        return msg

    def log_task_start(self, message: Message) -> None:
        """记录任务开始。

        Args:
            message: 任务消息
        """
        self.logger.info(
            f"Starting task: {message.task_type}, "
            f"msg_id: {message.msg_id}, "
            f"priority: {message.priority}"
        )

    def log_task_end(self, message: Message, duration: float) -> None:
        """记录任务结束。

        Args:
            message: 任务消息
            duration: 任务耗时（秒）
        """
        self.logger.info(
            f"Completed task: {message.task_type}, "
            f"duration: {duration:.2f}s, "
            f"status: {message.status}"
        )

    def __str__(self) -> str:
        return f"{self.name}({self.agent_id})"

    def __repr__(self) -> str:
        return f"BaseAgent(id={self.agent_id}, name={self.name}, status={self.status})"
