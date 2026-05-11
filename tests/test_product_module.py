# -*- coding: utf-8 -*-
"""商品模块测试"""
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


def test_create_and_get_product():
    from core.product_module import create_product, get_product
    pid = create_product({
        'name': '蓝牙耳机', 'category': '电子产品', 'price': 29.99,
        'selling_points': ['降噪', '续航40小时'], 'platform': 'TikTok Shop',
    })
    assert pid > 0
    p = get_product(pid)
    assert p['name'] == '蓝牙耳机'
    assert p['price'] == 29.99
    assert p['selling_points'] == ['降噪', '续航40小时']


def test_list_products_filter():
    from core.product_module import create_product, list_products
    create_product({'name': '耳机', 'category': '电子'})
    create_product({'name': '包包', 'category': '时尚'})
    create_product({'name': '手机壳', 'category': '电子'})

    result = list_products(category='电子')
    assert result['total'] == 2
    assert all(p['category'] == '电子' for p in result['items'])


def test_list_products_search():
    from core.product_module import create_product, list_products
    create_product({'name': '无线蓝牙耳机', 'description': '高品质音频'})
    create_product({'name': '运动手表'})

    result = list_products(search='蓝牙')
    assert result['total'] == 1
    assert result['items'][0]['name'] == '无线蓝牙耳机'


def test_update_product():
    from core.product_module import create_product, update_product, get_product
    pid = create_product({'name': '旧名称', 'price': 10})
    update_product(pid, {'name': '新名称', 'price': 20})
    p = get_product(pid)
    assert p['name'] == '新名称'
    assert p['price'] == 20


def test_delete_product():
    from core.product_module import create_product, delete_product, get_product
    pid = create_product({'name': '待删除'})
    assert delete_product(pid) is True
    assert get_product(pid) == {}


def test_delete_nonexistent():
    from core.product_module import delete_product
    assert delete_product(99999) is False


def test_list_pagination():
    from core.product_module import create_product, list_products
    for i in range(25):
        create_product({'name': f'商品{i}'})

    page1 = list_products(page=1, page_size=10)
    assert len(page1['items']) == 10
    assert page1['total'] == 25

    page3 = list_products(page=3, page_size=10)
    assert len(page3['items']) == 5


def test_get_categories():
    from core.product_module import create_product, get_product_categories
    create_product({'name': 'A', 'category': '电子'})
    create_product({'name': 'B', 'category': '时尚'})
    create_product({'name': 'C', 'category': '电子'})

    cats = get_product_categories()
    assert set(cats) == {'电子', '时尚'}


def test_get_stats():
    from core.product_module import create_product, get_product_stats
    create_product({'name': 'A', 'category': '电子'})
    create_product({'name': 'B', 'category': '时尚', 'status': 'inactive'})

    stats = get_product_stats()
    assert stats['total'] == 2
    assert stats['active'] == 1
    assert stats['categories'] == 2
