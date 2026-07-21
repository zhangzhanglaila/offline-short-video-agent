"""
内容分析Agent的提示词模板。

集中管理内容分析所用的LLM提示词，便于迭代优化。
"""

from typing import Dict


# 各分类的内容风格指引，帮助LLM生成符合分类特点的内容
CATEGORY_GUIDELINES: Dict[str, str] = {
    "教育讲解": (
        "逻辑清晰、由浅入深。开头点明主题，中间分点讲解核心概念，"
        "结尾总结要点。语言准确、易懂，适合科普。"
    ),
    "短视频": (
        "节奏明快、抓人眼球。开头制造悬念或抛出金句，中间快速推进，"
        "结尾留下记忆点或号召互动。语言口语化、有感染力。"
    ),
    "纪录片": (
        "叙事性强、有画面感。开头营造氛围，中间娓娓道来，"
        "结尾升华主题。语言富有质感、沉稳。"
    ),
    "商业宣传": (
        "突出卖点、有说服力。开头直击痛点或亮出品牌，中间展示价值，"
        "结尾促成行动。语言简洁有力、有号召性。"
    ),
}


# 场景类型说明
SCENE_TYPE_GUIDE = (
    "场景类型说明：\n"
    "- title_card: 标题卡，整屏文字，用于开头点题或章节过渡，不需要素材\n"
    "- content: 内容场景，画面为素材+下方字幕，是讲解主体\n"
    "- conclusion: 结尾卡，整屏文字，用于总结或号召，不需要素材"
)


SYSTEM_PROMPT = (
    "你是一位专业的短视频编导，擅长把用户的需求拆解为结构化的视频分镜。"
    "你只输出严格的JSON，不输出任何解释性文字。"
)


def build_analysis_prompt(
    user_input: str,
    category: str,
    style: str,
    duration: int,
    suggested_scene_count: int,
) -> str:
    """构建内容分析的完整提示词。

    Args:
        user_input: 用户需求文本
        category: 视频分类
        style: 视频风格
        duration: 目标时长（秒）
        suggested_scene_count: 建议的场景数

    Returns:
        完整的提示词字符串
    """
    guideline = CATEGORY_GUIDELINES.get(category, "内容清晰、结构合理。")

    return f"""请为以下需求设计一个短视频分镜脚本。

【用户需求】
{user_input}

【视频参数】
- 分类: {category}
- 风格: {style}
- 目标总时长: {duration}秒
- 建议场景数: {suggested_scene_count}个（可微调）

【分类风格要求】
{guideline}

{SCENE_TYPE_GUIDE}

【设计要求】
1. 第一个场景应为 title_card（标题卡）
2. 最后一个场景应为 conclusion（结尾卡）
3. 中间为 content（内容场景），是讲解主体
4. 每个 content 场景必须提供2-4个用于检索配图的英文或中文关键词
5. 所有场景的 duration 之和应接近 {duration} 秒
6. title_card 和 conclusion 各约3秒，其余时长分配给 content 场景
7. 文字精炼，每个场景文字不超过30字

【输出格式】
严格输出如下JSON（不要输出markdown代码块标记，不要输出任何额外文字）：
{{
  "title": "视频标题",
  "scenes": [
    {{
      "scene_id": 1,
      "scene_type": "title_card",
      "text": "标题文字",
      "duration": 3,
      "keywords": []
    }},
    {{
      "scene_id": 2,
      "scene_type": "content",
      "text": "讲解文字",
      "duration": 8,
      "keywords": ["关键词1", "关键词2"]
    }},
    {{
      "scene_id": 3,
      "scene_type": "conclusion",
      "text": "结尾文字",
      "duration": 3,
      "keywords": []
    }}
  ]
}}"""
