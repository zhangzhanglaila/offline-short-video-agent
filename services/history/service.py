"""历史记录服务 - 管理视频生成历史"""
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GenerationRecord:
    """视频生成记录"""
    id: str
    input_text: str
    params: Dict[str, Any]
    output_path: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        d = asdict(self)
        d['status'] = self.status.value
        d['created_at'] = self.created_at
        d['updated_at'] = self.updated_at
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationRecord":
        """从字典创建"""
        status = TaskStatus(data.get("status", "pending"))
        return cls(
            id=data["id"],
            input_text=data["input_text"],
            params=data.get("params", {}),
            output_path=data.get("output_path"),
            status=status,
            error=data.get("error"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            duration=data.get("duration", 0.0),
            metadata=data.get("metadata", {}),
        )


class HistoryService:
    """历史记录服务

    基于 JSON 文件存储，支持:
    - 添加记录
    - 查询记录（分页、筛选）
    - 更新记录状态
    - 删除记录
    - 导出记录
    """

    def __init__(self, storage_dir: str = "data/history"):
        """初始化历史服务

        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.storage_dir / "index.json"
        self._records: Dict[str, GenerationRecord] = {}
        self._load_index()

    def _load_index(self):
        """加载索引文件"""
        if self._index_file.exists():
            try:
                with open(self._index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for record_id, record_data in data.items():
                    self._records[record_id] = GenerationRecord.from_dict(record_data)
            except Exception as e:
                print(f"[HistoryService] 加载索引失败: {e}")
                self._records = {}

    def _save_index(self):
        """保存索引文件"""
        try:
            data = {
                record_id: record.to_dict()
                for record_id, record in self._records.items()
            }
            with open(self._index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[HistoryService] 保存索引失败: {e}")

    def add_record(
        self,
        input_text: str,
        params: Dict[str, Any],
        record_id: Optional[str] = None,
    ) -> GenerationRecord:
        """添加新记录

        Args:
            input_text: 输入文本
            params: 生成参数
            record_id: 记录ID（可选，自动生成）

        Returns:
            创建的记录
        """
        import hashlib
        import uuid

        if record_id is None:
            # 生成唯一ID
            timestamp = int(time.time())
            unique = uuid.uuid4().hex[:8]
            record_id = f"task_{timestamp}_{unique}"

        record = GenerationRecord(
            id=record_id,
            input_text=input_text,
            params=params,
            status=TaskStatus.PENDING,
        )
        self._records[record_id] = record
        self._save_index()
        return record

    def get_record(self, record_id: str) -> Optional[GenerationRecord]:
        """获取记录

        Args:
            record_id: 记录ID

        Returns:
            记录，不存在返回None
        """
        return self._records.get(record_id)

    def update_record(
        self,
        record_id: str,
        status: Optional[TaskStatus] = None,
        output_path: Optional[str] = None,
        error: Optional[str] = None,
        duration: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[GenerationRecord]:
        """更新记录

        Args:
            record_id: 记录ID
            status: 新状态
            output_path: 输出路径
            error: 错误信息
            duration: 耗时
            metadata: 元数据

        Returns:
            更新后的记录，不存在返回None
        """
        record = self._records.get(record_id)
        if record is None:
            return None

        if status is not None:
            record.status = status
        if output_path is not None:
            record.output_path = output_path
        if error is not None:
            record.error = error
        if duration is not None:
            record.duration = duration
        if metadata is not None:
            record.metadata.update(metadata)

        record.updated_at = time.time()
        self._save_index()
        return record

    def delete_record(self, record_id: str) -> bool:
        """删除记录

        Args:
            record_id: 记录ID

        Returns:
            是否成功删除
        """
        if record_id in self._records:
            del self._records[record_id]
            self._save_index()
            return True
        return False

    def list_records(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> List[GenerationRecord]:
        """列出记录

        Args:
            status: 状态筛选
            limit: 返回数量限制
            offset: 偏移量
            sort_by: 排序字段
            order: 排序顺序 (asc/desc)

        Returns:
            记录列表
        """
        records = list(self._records.values())

        # 状态筛选
        if status is not None:
            records = [r for r in records if r.status == status]

        # 排序
        reverse = order == "desc"
        if sort_by == "created_at":
            records.sort(key=lambda r: r.created_at, reverse=reverse)
        elif sort_by == "updated_at":
            records.sort(key=lambda r: r.updated_at, reverse=reverse)
        elif sort_by == "duration":
            records.sort(key=lambda r: r.duration, reverse=reverse)

        # 分页
        return records[offset:offset + limit]

    def count_records(self, status: Optional[TaskStatus] = None) -> int:
        """统计记录数

        Args:
            status: 状态筛选

        Returns:
            记录数量
        """
        if status is None:
            return len(self._records)
        return sum(1 for r in self._records.values() if r.status == status)

    def export_csv(self, output_path: str) -> bool:
        """导出为CSV

        Args:
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            import csv

            records = self.list_records(limit=10000)  # 导出所有

            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ID", "输入文本", "状态", "输出路径",
                    "错误", "创建时间", "更新时间", "耗时(秒)"
                ])

                for r in records:
                    created = datetime.fromtimestamp(r.created_at).strftime("%Y-%m-%d %H:%M:%S")
                    updated = datetime.fromtimestamp(r.updated_at).strftime("%Y-%m-%d %H:%M:%S")
                    writer.writerow([
                        r.id,
                        r.input_text[:50] + "..." if len(r.input_text) > 50 else r.input_text,
                        r.status.value,
                        r.output_path or "",
                        r.error or "",
                        created,
                        updated,
                        r.duration,
                    ])
            return True
        except Exception as e:
            print(f"[HistoryService] 导出CSV失败: {e}")
            return False

    def clear_old_records(self, days: int = 30) -> int:
        """清理旧记录

        Args:
            days: 保留天数

        Returns:
            删除的记录数
        """
        cutoff_time = time.time() - (days * 24 * 3600)
        to_delete = [
            r_id for r_id, r in self._records.items()
            if r.created_at < cutoff_time
        ]

        for r_id in to_delete:
            del self._records[r_id]

        if to_delete:
            self._save_index()

        return len(to_delete)


# 全局单例
_history_service: Optional[HistoryService] = None


def get_history_service() -> HistoryService:
    """获取历史记录服务单例"""
    global _history_service
    if _history_service is None:
        _history_service = HistoryService()
    return _history_service
