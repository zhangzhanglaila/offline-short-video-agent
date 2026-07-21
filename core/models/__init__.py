"""数据模型包 - 定义系统中的数据结构。"""

from .message import (
    Message,
    create_task_message,
    create_result_message,
    create_error_message,
    create_heartbeat_message,
)
from .request import UserRequest
from .result import AgentResult, VideoResult
from .content import ContentStructure, Scene, SceneType
from .material import MaterialAsset, SceneMaterialMap

__all__ = [
    "Message",
    "create_task_message",
    "create_result_message",
    "create_error_message",
    "create_heartbeat_message",
    "UserRequest",
    "AgentResult",
    "VideoResult",
    "ContentStructure",
    "Scene",
    "SceneType",
    "MaterialAsset",
    "SceneMaterialMap",
]
