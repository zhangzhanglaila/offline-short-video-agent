# -*- coding: utf-8 -*-
"""电商适配器测试"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_product_to_topic_basic():
    from core.ecom_adapter import product_to_topic
    product = {
        'id': 1, 'name': '蓝牙耳机', 'category': '电子产品',
        'price': 29.99, 'currency': 'USD',
        'selling_points': ['降噪', '续航40小时'],
    }
    topic = product_to_topic(product, 'soft_sell')
    assert topic['category'] == '电子产品'
    assert '蓝牙耳机' in topic['title']
    assert topic['hook']
    assert '#蓝牙耳机' in topic['tags']
    assert topic['_product'] is product
    assert topic['_style'] == 'soft_sell'


def test_product_to_topic_different_styles():
    from core.ecom_adapter import product_to_topic
    product = {'id': 1, 'name': '手表', 'price': 99, 'selling_points': ['防水']}

    for style in ('hard_sell', 'soft_sell', 'unboxing', 'tutorial'):
        topic = product_to_topic(product, style)
        assert topic['_style'] == style
        assert topic['hook']


def test_product_to_topic_no_selling_points():
    from core.ecom_adapter import product_to_topic
    product = {'id': 1, 'name': '商品A', 'price': 10}
    topic = product_to_topic(product)
    assert topic['hook']
    assert '商品A' in topic['tags'][0]


def test_product_to_topic_selling_points_as_string():
    from core.ecom_adapter import product_to_topic
    product = {'id': 1, 'name': '商品B', 'price': 20, 'selling_points': '["卖点1","卖点2"]'}
    topic = product_to_topic(product)
    assert '#商品B' in topic['tags'][0]


def test_build_ecom_prompt():
    from core.ecom_adapter import build_ecom_prompt
    product = {
        'name': '耳机', 'price': 29.99, 'currency': 'USD',
        'description': '好耳机', 'selling_points': ['降噪', '续航'],
    }
    prompt = build_ecom_prompt(product, 'hard_sell', 'TikTok', 30)
    assert '耳机' in prompt
    assert '29.99' in prompt
    assert '降噪' in prompt
    assert '30秒' in prompt


def test_build_insight_prompt():
    from core.ecom_adapter import build_insight_prompt
    data = [
        {'video_id': 1, 'impressions': 1000, 'clicks': 30, 'ctr': 0.03, 'conversions': 5, 'completion_rate': 0.45},
    ]
    prompt = build_insight_prompt(data, '耳机')
    assert '耳机' in prompt
    assert '1000' in prompt


def test_platform_map():
    from core.ecom_adapter import PLATFORM_MAP
    assert PLATFORM_MAP['TikTok'] == '抖音'
    assert PLATFORM_MAP['Douyin'] == '抖音'
