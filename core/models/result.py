"""
结果数据模型 - 定义Agent执行结果的标准格式。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class AgentResult:
    """Agent执行结果的标准格式。

    Attributes:
        success: 执行是否成功
        data: 执行数据 (成功时)
        error: 错误信息 (失败时)
        agent_id: 执行该任务的Agent ID
        task_type: 任务类型
        duration: 执行耗时 (秒)
        metadata: 额外元数据
    """

    success: bool
    agent_id: str
    task_type: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。

        Returns:
            结果字典
        """
        return {
            "success": self.success,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "data": self.data,
            "error": self.error,
            "duration": self.duration,
            "metadata": self.metadata
        }

    @property
    def is_success(self) -> bool:
        """判断是否成功。"""
        return self.success

    @property
    def is_failed(self) -> bool:
        """判断是否失败。"""
        return not self.success


@dataclass
class VideoResult:
    """最终的视频生成结果。

    Attributes:
        request_id: 原始请求ID
        success: 生成是否成功
        video_path: 生成的视频文件路径 (成功时)
        duration: 生成的视频时长 (秒)
        resolution: 视频分辨率
        quality_score: 质量评分 (0-1)
        error: 错误信息 (失败时)
        total_time: 总耗时 (秒)
        stages: 各阶段执行结果
    """

    request_id: str
    success: bool
    video_path: Optional[str] = None
    duration: Optional[int] = None
    resolution: str = "1920x1080"
    quality_score: float = 0.0
    error: Optional[str] = None
    total_time: float = 0.0
    stages: Dict[str, AgentResult] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。

        Returns:
            结果字典
        """
        return {
            "request_id": self.request_id,
            "success": self.success,
            "video_path": self.video_path,
            "duration": self.duration,
            "resolution": self.resolution,
            "quality_score": self.quality_score,
            "error": self.error,
            "total_time": self.total_time,
            "stages": {k: v.to_dict() for k, v in self.stages.items()}
        }

    def add_stage_result(self, stage_name: str, result: AgentResult) -> None:
        """添加阶段执行结果。

        Args:
            stage_name: 阶段名称
            result: 阶段执行结果
        """
        self.stages[stage_name] = result

    def get_summary(self) -> str:
        """获取结果摘要。

        Returns:
            结果摘要文本
        """
        if self.success:
            return (
                f"✅ 视频生成成功\n"
                f"   路径: {self.video_path}\n"
                f"   时长: {self.duration}秒\n"
                f"   质量: {self.quality_score:.2f}/1.0\n"
                f"   耗时: {self.total_time:.2f}秒"
            )
        else:
            return (
                f"❌ 视频生成失败\n"
                f"   错误: {self.error}"
            )
