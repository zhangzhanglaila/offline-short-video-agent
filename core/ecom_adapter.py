# -*- coding: utf-8 -*-
"""
电商适配器 - 商品数据 → 现有视频管线
将商品信息转换为 topic/script 格式，复用 script_module + dual_mode_module + FFmpeg 管线
"""
import json
from typing import Optional

ECOM_STYLES = {
    "hard_sell": "强促销风格：限时优惠+价格锚点+紧迫感CTA",
    "soft_sell": "软种草风格：场景代入+使用体验+自然推荐",
    "unboxing": "开箱风格：拆箱惊喜+细节展示+真实感受",
    "tutorial": "教程风格：痛点引入+解决方案+产品展示",
}

PLATFORM_MAP = {
    "TikTok": "抖音",
    "Douyin": "抖音",
    "Shopee Video": "小红书",
    "YouTube Shorts": "B站",
}


def product_to_topic(product: dict, style: str = "soft_sell") -> dict:
    """将商品数据转换为现有 pipeline 的 topic 格式。"""
    name = product.get('name', '')
    category = product.get('category', '电商带货')
    selling_points = product.get('selling_points', [])
    if isinstance(selling_points, str):
        try:
            selling_points = json.loads(selling_points)
        except json.JSONDecodeError:
            selling_points = [selling_points]

    price = product.get('price', 0)
    currency = product.get('currency', 'USD')
    description = product.get('description', '')

    sp_text = '、'.join(selling_points[:5]) if selling_points else name
    hook = _build_hook(name, price, currency, style, sp_text)

    tags = [f"#{name}", f"#{category}"]
    if selling_points:
        tags.extend([f"#{sp}" for sp in selling_points[:3]])
    tags.append(f"#{ECOM_STYLES.get(style, style).split('：')[0]}")

    return {
        "id": f"ecom_{product.get('id', 0)}",
        "category": category,
        "sub_category": style,
        "title": f"{name} 带货视频",
        "hook": hook,
        "tags": tags,
        "duration": "30-45秒",
        "heat_score": 85,
        "transform_rate": 0.8,
        "likes": 0,
        "platform": "内置",
        "source_url": product.get('source_url', ''),
        "is_bookmarked": 0,
        "_product": product,
        "_style": style,
    }


def build_ecom_prompt(product: dict, style: str, platform: str, duration: int = 30) -> str:
    """构建电商专用 prompt。"""
    name = product.get('name', '')
    price = product.get('price', 0)
    currency = product.get('currency', 'USD')
    description = product.get('description', '')
    selling_points = product.get('selling_points', [])
    if isinstance(selling_points, str):
        try:
            selling_points = json.loads(selling_points)
        except json.JSONDecodeError:
            selling_points = [selling_points]

    style_desc = ECOM_STYLES.get(style, style)
    sp_lines = '\n'.join(f"  - {sp}" for sp in selling_points[:8]) if selling_points else f"  - {name}"

    return f"""你是一位顶级电商带货短视频文案专家。请为以下商品生成一段{duration}秒的带货口播脚本。

【商品信息】
- 商品名称: {name}
- 价格: {currency} {price}
- 商品描述: {description}
- 核心卖点:
{sp_lines}

【风格要求】
{style_desc}

【平台】
{platform}

【脚本要求】
1. 黄金3秒开头：用{style.split('_')[0] == 'hard' and '紧迫感/限时优惠' or '痛点/场景'}抓住观众
2. 中间部分：逐个展示核心卖点，每个卖点配一个使用场景或效果描述
3. 结尾CTA：引导点击购买、关注账号
4. 口播风格：口语化、有感染力、节奏紧凑
5. 总字数控制在{duration * 3}字以内

【输出格式 - JSON】
{{
  "hook": "黄金3秒开头文案",
  "body": "主体内容（卖点展示）",
  "cta": "行动号召",
  "full_script": "完整口播文案",
  "storyboard": [
    {{"time": "0-3秒", "scene": "画面描述", "subtitle": "字幕", "duration": 3}},
    {{"time": "3-8秒", "scene": "画面描述", "subtitle": "字幕", "duration": 5}}
  ]
}}

直接输出JSON，不要有其他文字:"""


def build_insight_prompt(analytics_data: list, product_name: str = '') -> str:
    """构建数据分析洞察 prompt。"""
    data_lines = []
    for item in analytics_data[:10]:
        data_lines.append(
            f"- 视频#{item.get('video_id', '?')}: 展示{item.get('impressions', 0)}, "
            f"点击{item.get('clicks', 0)}, CTR{item.get('ctr', 0):.1%}, "
            f"转化{item.get('conversions', 0)}, 完播率{item.get('completion_rate', 0):.0%}"
        )
    data_text = '\n'.join(data_lines) if data_lines else '暂无数据'

    return f"""你是一位电商短视频数据分析师。请根据以下数据给出优化建议。

【商品】{product_name or '未知商品'}

【视频表现数据】
{data_text}

请从以下维度分析并给出3-5条可执行的优化建议：
1. 标题/开头hook优化
2. 视频节奏/时长调整
3. 卖点展示顺序
4. CTA话术优化
5. 发布时间/平台策略

输出格式：直接给出建议，每条建议包含【问题】和【优化方案】。"""


def _build_hook(name: str, price: float, currency: str, style: str, selling_points: str) -> str:
    """根据风格构建 hook。"""
    if style == "hard_sell":
        return f"最后{currency}{price}！{name}限时特惠，错过再等一年！"
    elif style == "unboxing":
        return f"花{currency}{price}买的{name}到了！拆开看看值不值？"
    elif style == "tutorial":
        return f"还在为XX烦恼？{name}一步到位解决！"
    else:  # soft_sell
        return f"用了{name}之后，再也回不去了。{selling_points}真的太香了。"
