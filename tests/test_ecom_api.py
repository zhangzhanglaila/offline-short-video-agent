# -*- coding: utf-8 -*-
"""电商 API 集成测试"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


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


@pytest.fixture
def client():
    from main_fastapi import create_app
    app = create_app()
    return TestClient(app)


def test_create_product_api(client):
    resp = client.post('/api/ecom/products', json={'name': '耳机', 'category': '电子', 'price': 29.99})
    assert resp.status_code == 200
    data = resp.json()
    assert data['success'] is True
    assert data['id'] > 0


def test_create_product_empty_name(client):
    resp = client.post('/api/ecom/products', json={'name': ''})
    assert resp.status_code == 400


def test_list_products_api(client):
    client.post('/api/ecom/products', json={'name': 'A'})
    client.post('/api/ecom/products', json={'name': 'B'})
    resp = client.get('/api/ecom/products')
    assert resp.status_code == 200
    data = resp.json()
    assert data['total'] == 2
    assert len(data['items']) == 2


def test_get_product_api(client):
    r = client.post('/api/ecom/products', json={'name': '测试商品', 'price': 10})
    pid = r.json()['id']
    resp = client.get(f'/api/ecom/products/{pid}')
    assert resp.status_code == 200
    assert resp.json()['name'] == '测试商品'


def test_get_product_not_found(client):
    resp = client.get('/api/ecom/products/99999')
    assert resp.status_code == 404


def test_update_product_api(client):
    r = client.post('/api/ecom/products', json={'name': '旧名'})
    pid = r.json()['id']
    resp = client.put(f'/api/ecom/products/{pid}', json={'name': '新名'})
    assert resp.status_code == 200
    assert resp.json()['success'] is True
    p = client.get(f'/api/ecom/products/{pid}').json()
    assert p['name'] == '新名'


def test_delete_product_api(client):
    r = client.post('/api/ecom/products', json={'name': '待删'})
    pid = r.json()['id']
    resp = client.delete(f'/api/ecom/products/{pid}')
    assert resp.status_code == 200
    assert resp.json()['success'] is True


def test_product_categories_api(client):
    client.post('/api/ecom/products', json={'name': 'A', 'category': '电子'})
    client.post('/api/ecom/products', json={'name': 'B', 'category': '时尚'})
    resp = client.get('/api/ecom/products/categories')
    assert resp.status_code == 200
    assert set(resp.json()['categories']) == {'电子', '时尚'}


def test_product_stats_api(client):
    client.post('/api/ecom/products', json={'name': 'A'})
    resp = client.get('/api/ecom/products/stats')
    assert resp.status_code == 200
    assert resp.json()['total'] == 1


def test_ecom_meta_api(client):
    resp = client.get('/api/ecom/meta')
    assert resp.status_code == 200
    data = resp.json()
    assert 'styles' in data
    assert 'platforms' in data
    assert 'TikTok' in data['platforms']


def test_generate_requires_product(client):
    resp = client.post('/api/ecom/generate', json={'style': 'soft_sell', 'platform': 'TikTok', 'duration': 30})
    assert resp.status_code == 400


def test_normalize_script_result_accepts_nested_values():
    from api.ecom_api import _normalize_script_result, _normalize_storyboard

    script = _normalize_script_result({
        "hook": ["Hook", {"extra": "start"}],
        "body": ["Point A", {"point": "Point B"}],
        "cta": {"text": "Buy now"},
        "full_script": ["Hook", "Point A", {"point": "Point B"}, "Buy now"],
    })

    assert script["body"] == "Point A Point B"
    assert script["full_script"] == "Hook Point A Point B Buy now"

    storyboard = _normalize_storyboard(script, 30)
    assert storyboard
    assert all(isinstance(scene["subtitle"], str) for scene in storyboard)


def test_ecom_videos_empty(client):
    resp = client.get('/api/ecom/videos')
    assert resp.status_code == 200
    assert resp.json()['total'] == 0


def test_ecom_analytics_empty(client):
    resp = client.get('/api/ecom/analytics')
    assert resp.status_code == 200
    assert resp.json()['items'] == []


def test_create_analytics_requires_video_id(client):
    resp = client.post('/api/ecom/analytics', json={'impressions': 100})
    assert resp.status_code == 400


def test_insights_no_data(client):
    resp = client.get('/api/ecom/analytics/insights')
    assert resp.status_code == 200
    assert '暂无' in resp.json()['insights']
