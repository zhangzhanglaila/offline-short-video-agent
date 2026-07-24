"""
测试历史记录服务
"""
import json
import time
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from services.history import HistoryService, GenerationRecord, TaskStatus


def test_history_service():
    """测试历史记录服务基础功能"""
    print("\n" + "=" * 60)
    print("[历史记录服务测试]")
    print("=" * 60)

    # 使用临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        service = HistoryService(storage_dir=temp_dir)

        # 测试1: 添加记录
        print("\n[测试1] 添加记录")
        record = service.add_record(
            input_text="讲解什么是区块链",
            params={"style": "tech", "duration": 15},
        )
        print(f"  记录ID: {record.id}")
        print(f"  输入: {record.input_text}")
        print(f"  状态: {record.status.value}")
        assert record.id is not None
        assert record.status == TaskStatus.PENDING

        # 测试2: 获取记录
        print("\n[测试2] 获取记录")
        fetched = service.get_record(record.id)
        assert fetched is not None
        assert fetched.input_text == "讲解什么是区块链"

        # 测试3: 更新记录
        print("\n[测试3] 更新记录")
        updated = service.update_record(
            record.id,
            status=TaskStatus.SUCCEEDED,
            output_path="output/video.mp4",
            duration=45.5,
        )
        assert updated.status == TaskStatus.SUCCEEDED
        assert updated.output_path == "output/video.mp4"
        assert updated.duration == 45.5
        print(f"  状态: {updated.status.value}")
        print(f"  输出: {updated.output_path}")

        # 测试4: 添加多条记录
        print("\n[测试4] 添加多条记录")
        for i in range(5):
            service.add_record(
                input_text=f"测试视频 {i}",
                params={"style": "default"},
            )
        print(f"  总记录数: {service.count_records()}")

        # 测试5: 列出记录
        print("\n[测试5] 列出记录")
        records = service.list_records(limit=3)
        print(f"  返回记录数: {len(records)}")
        assert len(records) == 3

        # 测试6: 筛选记录
        print("\n[测试6] 筛选记录")
        succeeded_count = service.count_records(TaskStatus.SUCCEEDED)
        print(f"  成功记录数: {succeeded_count}")
        assert succeeded_count == 1

        # 测试7: 删除记录
        print("\n[测试7] 删除记录")
        delete_success = service.delete_record(record.id)
        assert delete_success
        assert service.get_record(record.id) is None
        print(f"  删除成功")

        # 测试8: 导出CSV
        print("\n[测试8] 导出CSV")
        csv_path = Path(temp_dir) / "export.csv"
        export_success = service.export_csv(str(csv_path))
        assert export_success
        assert csv_path.exists()
        print(f"  导出路径: {csv_path}")

        print("\n[完成] 所有测试通过")
        return True

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_record_serialization():
    """测试记录序列化"""
    print("\n" + "=" * 60)
    print("[记录序列化测试]")
    print("=" * 60)

    # 创建记录
    record = GenerationRecord(
        id="test_001",
        input_text="测试输入",
        params={"key": "value"},
        status=TaskStatus.PROCESSING,
    )

    # 转字典
    d = record.to_dict()
    print(f"\n[序列化]")
    print(f"  ID: {d['id']}")
    print(f"  状态: {d['status']}")
    assert d["status"] == "processing"

    # 从字典恢复
    restored = GenerationRecord.from_dict(d)
    assert restored.id == "test_001"
    assert restored.input_text == "测试输入"
    assert restored.status == TaskStatus.PROCESSING

    print(f"\n[反序列化]")
    print(f"  ID: {restored.id}")
    print(f"  状态: {restored.status.value}")

    print("\n[完成] 序列化测试通过")
    return True


def test_statistics():
    """测试统计功能"""
    print("\n" + "=" * 60)
    print("[统计功能测试]")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()
    try:
        service = HistoryService(storage_dir=temp_dir)

        # 添加不同状态的记录
        for i in range(3):
            r = service.add_record(f"成功任务 {i}", {})
            service.update_record(r.id, status=TaskStatus.SUCCEEDED)

        for i in range(2):
            r = service.add_record(f"失败任务 {i}", {})
            service.update_record(r.id, status=TaskStatus.FAILED)

        r = service.add_record("处理中任务", {})
        service.update_record(r.id, status=TaskStatus.PROCESSING)

        # 统计
        total = service.count_records()
        succeeded = service.count_records(TaskStatus.SUCCEEDED)
        failed = service.count_records(TaskStatus.FAILED)
        processing = service.count_records(TaskStatus.PROCESSING)

        print(f"\n[统计结果]")
        print(f"  总记录: {total}")
        print(f"  成功: {succeeded}")
        print(f"  失败: {failed}")
        print(f"  处理中: {processing}")

        assert total == 6
        assert succeeded == 3
        assert failed == 2
        assert processing == 1

        print("\n[完成] 统计测试通过")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """运行所有测试"""
    import sys
    import io
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    try:
        test_history_service()
        test_record_serialization()
        test_statistics()

        print("\n" + "=" * 60)
        print("[测试结果]")
        print("=" * 60)
        print(f"  基础功能: [通过]")
        print(f"  序列化: [通过]")
        print(f"  统计功能: [通过]")
        print(f"\n[完成] 所有测试通过")

    except Exception as e:
        print(f"\n[异常] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
