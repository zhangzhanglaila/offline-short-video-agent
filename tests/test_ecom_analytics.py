# -*- coding: utf-8 -*-
"""电商分析模块测试"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """使用临时数据库。"""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr('core.db_init.get_db_path', lambda: str(db_path))
    from core.db_init import init_topics_db
    conn = init_topics_db()
    conn.close()
    yield
    if db_path.exists():
        db_path.unlink()


def _seed_data():
    """插入测试数据。"""
    from core.db_init import get_db_path
    import sqlite3
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("INSERT INTO products (name) VALUES ('测试商品')")
    pid = c.lastrowid
    c.execute("INSERT INTO ecom_videos (product_id, platform, style, status) VALUES (?, 'TikTok', 'soft_sell', 'done')", (pid,))
    vid = c.lastrowid
    c.execute("""INSERT INTO ecom_analytics (video_id, platform, impressions, clicks, ctr, conversions, revenue, completion_rate, recorded_at)
                 VALUES (?, 'TikTok', 1000, 50, 0.05, 10, 299.9, 0.45, '2025-01-01')""", (vid,))
    c.execute("""INSERT INTO ecom_analytics (video_id, platform, impressions, clicks, ctr, conversions, revenue, completion_rate, recorded_at)
                 VALUES (?, 'TikTok', 2000, 80, 0.04, 15, 450.0, 0.50, '2025-01-02')""", (vid,))
    conn.commit()
    conn.close()
    return pid, vid


def test_get_aggregated():
    from core.ecom_analytics_module import get_aggregated
    pid, vid = _seed_data()
    agg = get_aggregated()
    assert agg['impressions'] == 3000
    assert agg['clicks'] == 130
    assert agg['conversions'] == 25
    assert abs(agg['revenue'] - 749.9) < 0.01


def test_get_aggregated_filtered():
    from core.ecom_analytics_module import get_aggregated
    pid, vid = _seed_data()
    agg = get_aggregated({'product_id': pid})
    assert agg['impressions'] == 3000


def test_get_trends():
    from core.ecom_analytics_module import get_trends
    _, vid = _seed_data()
    trends = get_trends(vid, days=30)
    assert len(trends) == 2
    assert trends[0]['impressions'] == 2000  # DESC order


def test_compare_videos():
    from core.ecom_analytics_module import compare_videos
    _, vid = _seed_data()
    result = compare_videos([vid])
    assert vid in result
    assert result[vid]['impressions'] == 2000  # MAX


def test_compare_empty():
    from core.ecom_analytics_module import compare_videos
    assert compare_videos([]) == {}


def test_generate_insights_no_data():
    from core.ecom_analytics_module import generate_insights
    result = generate_insights()
    assert '暂无' in result


def test_generate_insights_with_data():
    from core.ecom_analytics_module import generate_insights
    _seed_data()
    result = generate_insights()
    assert isinstance(result, str)
    assert len(result) > 0
