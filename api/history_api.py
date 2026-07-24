"""历史记录 API 路由"""
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.history import HistoryService, TaskStatus, get_history_service

router = APIRouter(prefix="/api/history", tags=["history"])


def get_service() -> HistoryService:
    """获取历史服务"""
    return get_history_service()


@router.get("/")
async def list_history(
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    sort_by: str = Query("created_at", description="排序字段"),
    order: str = Query("desc", description="排序顺序"),
):
    """获取历史记录列表"""
    service = get_service()

    # 解析状态
    task_status = None
    if status:
        try:
            task_status = TaskStatus(status)
        except ValueError:
            pass

    records = service.list_records(
        status=task_status,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
    )

    total = service.count_records(status=task_status)

    return JSONResponse({
        "total": total,
        "items": [r.to_dict() for r in records],
        "limit": limit,
        "offset": offset,
    })


@router.get("/{record_id}")
async def get_history(record_id: str):
    """获取单条历史记录"""
    service = get_service()
    record = service.get_record(record_id)

    if record is None:
        raise HTTPException(status_code=404, detail="记录不存在")

    return JSONResponse(record.to_dict())


@router.delete("/{record_id}")
async def delete_history(record_id: str):
    """删除历史记录"""
    service = get_service()
    success = service.delete_record(record_id)

    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")

    return JSONResponse({"success": True})


@router.post("/{record_id}/regenerate")
async def regenerate_history(record_id: str):
    """重新生成视频"""
    service = get_service()
    record = service.get_record(record_id)

    if record is None:
        raise HTTPException(status_code=404, detail="记录不存在")

    # TODO: 触发重新生成任务
    # 这里需要调用 CoordinatorAgent 重新执行
    return JSONResponse({
        "success": True,
        "message": "重新生成任务已创建",
        "task_id": record_id,
    })


@router.get("/export/csv")
async def export_history_csv():
    """导出历史记录为CSV"""
    service = get_service()

    output_path = "data/history_export.csv"
    success = service.export_csv(output_path)

    if not success:
        raise HTTPException(status_code=500, detail="导出失败")

    return FileResponse(
        output_path,
        media_type="text/csv",
        filename=f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    )


@router.get("/stats/summary")
async def get_history_stats():
    """获取历史记录统计"""
    service = get_service()

    total = service.count_records()
    succeeded = service.count_records(TaskStatus.SUCCEEDED)
    failed = service.count_records(TaskStatus.FAILED)
    processing = service.count_records(TaskStatus.PROCESSING)

    return JSONResponse({
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "processing": processing,
        "success_rate": round(succeeded / total * 100, 1) if total > 0 else 0,
    })
