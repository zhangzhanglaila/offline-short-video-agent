# -*- coding: utf-8 -*-
"""
主题适配器 - 将用户输入的主题/描述转换为现有 pipeline 的 topic 字典格式。

替代电商专属的 product_to_topic：通用生成流程不再依赖商品，
用户直接输入主题文本 + 分类，即可产出脚本管道所需的 topic 结构。

设计要点：
- 输出结构与 core.ecom_adapter.product_to_topic 兼容（下游 generate_script 只读
  title / category / hook / id / tags 这几个字段）。
- 纯函数，无副作用，便于单元测试。
"""
from typing import List, Optional


# 与 CLI (generate_video.py) 保持一致的分类
CATEGORIES = ["教育讲解", "短视频", "纪录片", "商业宣传"]

# 平台中文名映射（generate_script 需要中文平台名）
PLATFORM_MAP = {
    "抖音": "抖音",
    "TikTok": "抖音",
    "小红书": "小红书",
    "视频号": "视频号",
    "B站": "视频号",
    "YouTube": "抖音",
}


def topic_to_dict(
    topic: str,
    category: str = "短视频",
    style: str = "爆款",
    tags: Optional[List[str]] = None,
) -> dict:
    """将用户主题转换为脚本管道所需的 topic 字典。

    Args:
        topic: 用户输入的主题/视频描述
        category: 分类（教育讲解/短视频/纪录片/商业宣传）
        style: 脚本风格（爆款/温和/专业）
        tags: 可选标签列表

    Returns:
        与 product_to_topic 结构兼容的 topic 字典
    """
    clean_topic = (topic or "").strip()
    cat = category if category in CATEGORIES else "短视频"

    return {
        "id": "topic_user",
        "category": cat,
        "sub_category": style,
        "title": clean_topic,
        "hook": "",  # 留空，让 generate_script 自行生成开头
        "tags": tags or [],
        "duration": "30-45秒",
        "heat_score": 0,
        "transform_rate": 0.0,
        "likes": 0,
        "platform": "内置",
        "source_url": "",
        "is_bookmarked": 0,
        "_style": style,
    }
