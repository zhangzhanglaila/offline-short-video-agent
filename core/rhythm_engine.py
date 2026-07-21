# -*- coding: utf-8 -*-
"""
节奏模板系统
定义不同风格的视频节奏和转场策略
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class RhythmType(Enum):
    """节奏类型"""
    SLOW = "slow"              # 缓慢节奏
    MEDIUM = "medium"          # 中等节奏
    FAST = "fast"              # 快速节奏
    DYNAMIC = "dynamic"        # 动态节奏


@dataclass
class RhythmTemplate:
    """节奏模板"""
    name: str
    type: RhythmType
    scene_duration: float       # 单场景显示时长(秒)
    transition_duration: float  # 转场时长(秒)
    transition_style: str       # 转场风格
    music_match: bool = True    # 是否匹配音乐节拍


class RhythmEngine:
    """节奏引擎 - 管理视频节奏"""

    def __init__(self):
        self.templates: Dict[str, RhythmTemplate] = {}
        self._load_presets()

    def _load_presets(self):
        """加载预设节奏模板"""
        # 缓慢节奏 - 适合冥想、美食、风景
        self.templates["slow"] = RhythmTemplate(
            name="缓慢节奏",
            type=RhythmType.SLOW,
            scene_duration=5.0,         # 每个场景显示5秒
            transition_duration=1.0,    # 转场1秒
            transition_style="fade",
            music_match=True
        )

        # 中等节奏 - 适合教程、讲解、故事
        self.templates["medium"] = RhythmTemplate(
            name="中等节奏",
            type=RhythmType.MEDIUM,
            scene_duration=3.0,         # 每个场景显示3秒
            transition_duration=0.6,    # 转场0.6秒
            transition_style="slide_left",
            music_match=True
        )

        # 快速节奏 - 适合音乐、短视频、快节奏内容
        self.templates["fast"] = RhythmTemplate(
            name="快速节奏",
            type=RhythmType.FAST,
            scene_duration=1.5,         # 每个场景显示1.5秒
            transition_duration=0.3,    # 转场0.3秒
            transition_style="wipe_left",
            music_match=True
        )

        # 动态节奏 - 适合混合内容
        self.templates["dynamic"] = RhythmTemplate(
            name="动态节奏",
            type=RhythmType.DYNAMIC,
            scene_duration=3.5,
            transition_duration=0.5,
            transition_style="zoom_in",
            music_match=True
        )

    def get_template(self, name: str) -> Optional[RhythmTemplate]:
        """获取节奏模板"""
        return self.templates.get(name)

    def list_templates(self) -> List[str]:
        """列出所有节奏模板"""
        return list(self.templates.keys())

    def calculate_duration(
        self,
        num_scenes: int,
        template_name: str = "medium"
    ) -> float:
        """
        计算视频总时长

        Args:
            num_scenes: 场景数
            template_name: 节奏模板名

        Returns:
            视频时长(秒)
        """
        template = self.get_template(template_name)

        if not template:
            return 0.0

        # 总时长 = 场景时长 * 场景数 + 转场时长 * (场景数 - 1)
        total = (template.scene_duration * num_scenes +
                 template.transition_duration * (num_scenes - 1))

        return total

    def get_scene_timing(
        self,
        num_scenes: int,
        template_name: str = "medium"
    ) -> List[Dict]:
        """
        获取每个场景的时间安排

        Args:
            num_scenes: 场景数
            template_name: 节奏模板名

        Returns:
            [{start: float, duration: float, transition: str}, ...]
        """
        template = self.get_template(template_name)

        if not template:
            return []

        timings = []
        current_time = 0.0

        for i in range(num_scenes):
            # 场景时间
            timings.append({
                "scene_index": i,
                "start": current_time,
                "duration": template.scene_duration,
                "transition": template.transition_style if i < num_scenes - 1 else None,
                "transition_duration": template.transition_duration if i < num_scenes - 1 else 0.0
            })

            # 更新当前时间
            current_time += template.scene_duration
            if i < num_scenes - 1:
                current_time += template.transition_duration

        return timings


class RhythmAnalyzer:
    """节奏分析器 - 分析内容并推荐节奏"""

    def __init__(self):
        self.engine = RhythmEngine()

    def analyze_content(
        self,
        title: str,
        content_type: str = "general"
    ) -> str:
        """
        分析内容并推荐节奏

        Args:
            title: 内容标题
            content_type: 内容类型

        Returns:
            推荐的节奏模板名
        """
        # 基于内容类型推荐节奏
        content_type = content_type.lower()

        # 快速内容
        fast_keywords = ["音乐", "舞蹈", "vlog", "快速", "搞笑", "综艺"]
        if any(kw in title for kw in fast_keywords) or content_type in ["music", "dance", "vlog"]:
            return "fast"

        # 缓慢内容
        slow_keywords = ["冥想", "美食", "风景", "旅游", "放松", "自然"]
        if any(kw in title for kw in slow_keywords) or content_type in ["meditation", "food", "travel"]:
            return "slow"

        # 教程/讲解
        tutorial_keywords = ["教程", "讲解", "指南", "学习", "培训"]
        if any(kw in title for kw in tutorial_keywords) or content_type in ["tutorial", "education"]:
            return "medium"

        # 默认中等节奏
        return "medium"

    def adapt_to_music(
        self,
        music_bpm: int,
        template_name: str = "medium"
    ) -> str:
        """
        根据音乐BPM自适应节奏

        Args:
            music_bpm: 音乐BPM
            template_name: 基础模板

        Returns:
            自适应后的模板名
        """
        # 根据BPM选择节奏
        if music_bpm < 80:
            return "slow"
        elif music_bpm < 120:
            return "medium"
        elif music_bpm < 160:
            return "fast"
        else:
            return "fast"  # 极快节奏


class VideoRhythmController:
    """视频节奏控制器 - 整合节奏和转场"""

    def __init__(self):
        self.engine = RhythmEngine()
        self.analyzer = RhythmAnalyzer()

    def create_video_structure(
        self,
        storyboard: List[Dict],
        rhythm_template: str = "medium",
        transitions: Dict[int, str] = None
    ) -> Dict:
        """
        创建视频结构

        Args:
            storyboard: 分镜列表
            rhythm_template: 节奏模板
            transitions: 自定义转场映射 {scene_idx: transition_name}

        Returns:
            完整的视频结构定义
        """
        transitions = transitions or {}
        num_scenes = len(storyboard)

        # 获取节奏模板
        template = self.engine.get_template(rhythm_template)

        if not template:
            template = self.engine.get_template("medium")

        # 计算时间安排
        timings = self.engine.get_scene_timing(num_scenes, rhythm_template)

        # 构建视频结构
        video_structure = {
            "rhythm_template": rhythm_template,
            "total_duration": self.engine.calculate_duration(num_scenes, rhythm_template),
            "scenes": []
        }

        for i, timing in enumerate(timings):
            scene_config = {
                "scene_index": i,
                "scene_data": storyboard[i],
                "start_time": timing["start"],
                "duration": timing["duration"],
                "transition": transitions.get(i, timing["transition"]),
                "transition_duration": timing["transition_duration"]
            }
            video_structure["scenes"].append(scene_config)

        return video_structure

    def optimize_rhythm(
        self,
        storyboard: List[Dict],
        music_bpm: int = None,
        content_type: str = "general"
    ) -> str:
        """
        优化节奏选择

        Args:
            storyboard: 分镜列表
            music_bpm: 音乐BPM
            content_type: 内容类型

        Returns:
            优化后的节奏模板名
        """
        # 获取第一个场景的标题用于分析
        title = storyboard[0].get("title", "") if storyboard else ""

        # 先根据内容分析
        recommended = self.analyzer.analyze_content(title, content_type)

        # 如果有音乐，根据BPM调整
        if music_bpm:
            recommended = self.analyzer.adapt_to_music(music_bpm, recommended)

        return recommended

    def get_video_info(self, video_structure: Dict) -> Dict:
        """获取视频信息"""
        return {
            "rhythm_template": video_structure["rhythm_template"],
            "total_duration": video_structure["total_duration"],
            "num_scenes": len(video_structure["scenes"]),
            "scene_duration": video_structure["scenes"][0]["duration"] if video_structure["scenes"] else 0,
            "transition_style": video_structure["scenes"][0]["transition"] if video_structure["scenes"] else None
        }


# 便捷函数
def create_rhythm_engine() -> RhythmEngine:
    """创建节奏引擎"""
    return RhythmEngine()


def create_rhythm_controller() -> VideoRhythmController:
    """创建节奏控制器"""
    return VideoRhythmController()
