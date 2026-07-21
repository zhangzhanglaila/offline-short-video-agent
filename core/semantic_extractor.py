# -*- coding: utf-8 -*-
"""
素材语义提取与分析系统
从脚本中提取关键词和主题，用于素材匹配
"""
import re
from typing import List, Dict, Tuple, Set, Optional
from collections import Counter
from dataclasses import dataclass


@dataclass
class SemanticKeywords:
    """语义关键词"""
    primary: List[str]      # 主要关键词
    secondary: List[str]    # 次要关键词
    entities: List[str]     # 实体词
    emotions: List[str]     # 情感词
    topics: List[str]       # 主题词


class SemanticExtractor:
    """语义提取器 - 从文本中提取关键词和主题"""

    def __init__(self):
        # 中文停用词
        self.stopwords = self._load_stopwords()

        # 关键词权重
        self.keyword_weights = {
            "title": 3.0,      # 标题权重最高
            "subtitle": 2.0,   # 副标题次之
            "bullets": 1.5,    # 要点
            "description": 1.0 # 描述
        }

        # 主题词库
        self.topic_keywords = {
            "technology": ["科技", "技术", "代码", "编程", "算法", "数据", "AI", "机器学习", "深度学习"],
            "education": ["教育", "学习", "教学", "培训", "课程", "知识", "教科书", "学生"],
            "lifestyle": ["生活", "日常", "家居", "美食", "旅游", "运动", "健康", "美容"],
            "business": ["商业", "企业", "营销", "销售", "管理", "战略", "金融", "投资"],
            "entertainment": ["娱乐", "电影", "音乐", "综艺", "游戏", "明星", "搞笑", "幽默"],
            "nature": ["自然", "风景", "动物", "植物", "天气", "环境", "生态", "森林"],
            "health": ["健康", "医学", "健身", "营养", "心理", "疾病", "治疗", "医生"],
            "travel": ["旅游", "旅行", "景点", "城市", "探险", "攻略", "度假", "国家"]
        }

        # 情感词库
        self.emotion_keywords = {
            "positive": ["好", "美", "棒", "优秀", "成功", "开心", "高兴", "满意", "完美"],
            "negative": ["差", "丑", "糟糕", "失败", "伤心", "难过", "沮丧", "糟"],
            "neutral": ["中等", "普通", "一般", "标准", "基本", "简单", "复杂"],
            "action": ["快", "动态", "激烈", "冲击", "爆炸", "运动", "跳跃", "奔跑"]
        }

    def _load_stopwords(self) -> Set[str]:
        """加载停用词"""
        stopwords = {
            "的", "了", "是", "在", "有", "和", "人", "这", "中", "大",
            "为", "上", "个", "国", "我", "以", "要", "他", "时", "来",
            "用", "们", "生", "到", "作", "地", "于", "出", "就", "分",
            "对", "成", "会", "可", "主", "发", "年", "动", "同", "工",
            "也", "能", "下", "过", "民", "前", "面", "所", "自", "第",
            "与", "进", "着", "没", "有", "最", "立", "资", "英", "法",
            "获", "经", "认", "家", "高", "长", "外", "都", "历", "夫",
            "新", "5", "2", "1", "3", "4", "6", "7", "8", "9", "0"
        }
        return stopwords

    def extract_keywords(
        self,
        text: str,
        text_type: str = "description",
        max_keywords: int = 10
    ) -> List[Tuple[str, float]]:
        """
        提取关键词

        Args:
            text: 输入文本
            text_type: 文本类型 (title/subtitle/bullets/description)
            max_keywords: 最多返回关键词数

        Returns:
            [(keyword, score), ...] 按得分排序
        """
        if not text:
            return []

        # 分词 (简单的中英文分词)
        words = self._tokenize(text)

        # 过滤停用词
        words = [w for w in words if w not in self.stopwords and len(w) > 1]

        # 计算词频
        word_freq = Counter(words)

        # 加权评分
        weight = self.keyword_weights.get(text_type, 1.0)
        scored_words = [
            (word, freq * weight)
            for word, freq in word_freq.most_common()
        ]

        return scored_words[:max_keywords]

    def extract_entities(self, text: str) -> List[str]:
        """提取实体词 (名词)"""
        # 简化实体提取 - 使用长词和大写词
        words = self._tokenize(text)
        entities = [
            w for w in words
            if len(w) >= 2 and (w[0].isupper() or self._is_chinese_noun(w))
        ]
        return list(set(entities))

    def extract_emotions(self, text: str) -> List[str]:
        """提取情感词"""
        emotions = []
        for emotion_type, keywords in self.emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    emotions.append(keyword)
        return list(set(emotions))

    def extract_topics(self, text: str) -> List[str]:
        """提取主题"""
        topics = []
        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    topics.append(topic)
                    break  # 一个主题只计算一次
        return topics

    def extract_all_semantics(
        self,
        title: str = "",
        subtitle: str = "",
        bullets: List[str] = None,
        description: str = ""
    ) -> SemanticKeywords:
        """
        完整语义提取

        Args:
            title: 标题
            subtitle: 副标题
            bullets: 要点列表
            description: 描述

        Returns:
            SemanticKeywords 对象
        """
        bullets = bullets or []

        # 提取关键词
        all_keywords = []

        if title:
            all_keywords.extend(self.extract_keywords(title, "title", 5))
        if subtitle:
            all_keywords.extend(self.extract_keywords(subtitle, "subtitle", 3))
        for bullet in bullets:
            all_keywords.extend(self.extract_keywords(bullet, "bullets", 2))
        if description:
            all_keywords.extend(self.extract_keywords(description, "description", 5))

        # 按得分排序
        all_keywords.sort(key=lambda x: x[1], reverse=True)
        primary = [w[0] for w in all_keywords[:5]]
        secondary = [w[0] for w in all_keywords[5:10]]

        # 提取其他语义
        full_text = f"{title} {subtitle} {' '.join(bullets)} {description}"
        entities = self.extract_entities(full_text)
        emotions = self.extract_emotions(full_text)
        topics = self.extract_topics(full_text)

        return SemanticKeywords(
            primary=primary,
            secondary=secondary,
            entities=entities,
            emotions=emotions,
            topics=topics
        )

    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 分离中英文
        tokens = []
        current = ""

        for char in text:
            if self._is_chinese(char):
                if current:
                    tokens.extend(current.split())
                    current = ""
                tokens.append(char)
            elif char.isalnum():
                current += char
            else:
                if current:
                    tokens.extend(current.split())
                    current = ""

        if current:
            tokens.extend(current.split())

        return [t.lower() for t in tokens if t]

    def _is_chinese(self, char: str) -> bool:
        """检查是否为中文字符"""
        code = ord(char)
        return 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF

    def _is_chinese_noun(self, word: str) -> bool:
        """简单的中文名词判断"""
        # 假设连续的中文字符是名词
        return all(self._is_chinese(c) for c in word)


class MaterialMatcher:
    """素材匹配器 - 计算脚本与素材的相关性"""

    def __init__(self, extractor: SemanticExtractor = None):
        self.extractor = extractor or SemanticExtractor()

    def match_score(
        self,
        script_keywords: SemanticKeywords,
        material_keywords: SemanticKeywords
    ) -> float:
        """
        计算匹配得分

        Args:
            script_keywords: 脚本语义
            material_keywords: 素材语义

        Returns:
            匹配得分 (0.0-1.0)
        """
        if not script_keywords.primary or not material_keywords.primary:
            return 0.0

        # 主关键词匹配权重: 0.5
        primary_match = self._calculate_overlap(
            script_keywords.primary,
            material_keywords.primary
        )
        score = primary_match * 0.5

        # 次关键词匹配权重: 0.2
        if script_keywords.secondary or material_keywords.secondary:
            secondary_match = self._calculate_overlap(
                script_keywords.secondary,
                material_keywords.secondary
            )
            score += secondary_match * 0.2

        # 实体匹配权重: 0.15
        if script_keywords.entities or material_keywords.entities:
            entity_match = self._calculate_overlap(
                script_keywords.entities,
                material_keywords.entities
            )
            score += entity_match * 0.15

        # 主题匹配权重: 0.15
        if script_keywords.topics or material_keywords.topics:
            topic_match = self._calculate_overlap(
                script_keywords.topics,
                material_keywords.topics
            )
            score += topic_match * 0.15

        return min(1.0, score)

    def rank_materials(
        self,
        script_keywords: SemanticKeywords,
        materials_list: List[Dict],
        top_k: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        为素材排序

        Args:
            script_keywords: 脚本语义
            materials_list: 素材列表，每个素材包含keywords字段
            top_k: 返回前K个最匹配的素材

        Returns:
            [(material, score), ...] 按得分排序
        """
        scored = []

        for material in materials_list:
            if "keywords" not in material:
                continue

            score = self.match_score(script_keywords, material["keywords"])
            scored.append((material, score))

        # 按得分排序
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def _calculate_overlap(self, list1: List[str], list2: List[str]) -> float:
        """计算两个列表的重叠度"""
        if not list1 or not list2:
            return 0.0

        set1 = set(list1)
        set2 = set(list2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0


# 便捷函数
def create_semantic_extractor() -> SemanticExtractor:
    """创建语义提取器"""
    return SemanticExtractor()


def extract_script_semantics(
    title: str = "",
    subtitle: str = "",
    bullets: List[str] = None,
    description: str = ""
) -> SemanticKeywords:
    """提取脚本语义的便捷函数"""
    extractor = SemanticExtractor()
    return extractor.extract_all_semantics(title, subtitle, bullets, description)
