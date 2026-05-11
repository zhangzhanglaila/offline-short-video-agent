# -*- coding: utf-8 -*-
"""
商品管理模块 - 电商短视频系统
商品的 CRUD 操作、URL 爬取
"""
import json
import sqlite3
from typing import Optional


def _get_conn():
    from core.db_init import get_db_path
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row) -> dict:
    if row is None:
        return {}
    d = dict(row)
    for key in ('selling_points', 'images'):
        if d.get(key) and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except json.JSONDecodeError:
                d[key] = []
    return d


def create_product(data: dict) -> int:
    """创建商品，返回商品 ID。"""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, category, price, currency, description, selling_points, images, source_url, platform, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('name', ''),
        data.get('category', ''),
        data.get('price', 0.0),
        data.get('currency', 'USD'),
        data.get('description', ''),
        json.dumps(data.get('selling_points', []), ensure_ascii=False),
        json.dumps(data.get('images', []), ensure_ascii=False),
        data.get('source_url', ''),
        data.get('platform', ''),
        data.get('status', 'active'),
    ))
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id


def get_product(product_id: int) -> dict:
    """获取单个商品。"""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_dict(row)


def list_products(
    search: str = '',
    category: str = '',
    platform: str = '',
    status: str = '',
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """商品列表，支持搜索/筛选/分页。返回 {items, total, page, page_size}。"""
    conn = _get_conn()
    cursor = conn.cursor()

    conditions = []
    params = []

    if search:
        conditions.append("(name LIKE ? OR description LIKE ?)")
        params.extend([f'%{search}%', f'%{search}%'])
    if category:
        conditions.append("category = ?")
        params.append(category)
    if platform:
        conditions.append("platform = ?")
        params.append(platform)
    if status:
        conditions.append("status = ?")
        params.append(status)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ''

    cursor.execute(f"SELECT COUNT(*) FROM products {where}", params)
    total = cursor.fetchone()[0]

    offset = (page - 1) * page_size
    cursor.execute(
        f"SELECT * FROM products {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [page_size, offset]
    )
    items = [_row_to_dict(row) for row in cursor.fetchall()]

    conn.close()
    return {'items': items, 'total': total, 'page': page, 'page_size': page_size}


def update_product(product_id: int, data: dict) -> bool:
    """更新商品字段。返回是否成功。"""
    allowed = {'name', 'category', 'price', 'currency', 'description', 'selling_points', 'images', 'source_url', 'platform', 'status'}
    fields = {k: v for k, v in data.items() if k in allowed}
    if not fields:
        return False

    for key in ('selling_points', 'images'):
        if key in fields and isinstance(fields[key], list):
            fields[key] = json.dumps(fields[key], ensure_ascii=False)

    set_clause = ', '.join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [product_id]

    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE products SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def delete_product(product_id: int) -> bool:
    """删除商品。返回是否成功。"""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_product_categories() -> list[str]:
    """获取所有商品分类。"""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_product_stats() -> dict:
    """商品统计概览。"""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM products WHERE status = 'active'")
    active = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT category) FROM products WHERE category IS NOT NULL AND category != ''")
    categories = cursor.fetchone()[0]
    conn.close()
    return {'total': total, 'active': active, 'categories': categories}
