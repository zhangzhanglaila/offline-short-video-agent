# -*- coding: utf-8 -*-
"""
配置文件 - Offline-ShortVideo-Agent
所有路径和参数配置集中管理
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件（override=True 确保 .env 值始终覆盖系统环境变量）
load_dotenv(override=True)

PROJECT_ROOT = Path(__file__).parent.absolute()

DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = PROJECT_ROOT / "output"
BGM_DIR = ASSETS_DIR / "bgm"
MATERIAL_DIR = ASSETS_DIR / "素材池_待剪辑"
THUMBNAILS_DIR = ASSETS_DIR / "thumbnails"

OUTPUT_DY = OUTPUT_DIR / "抖音"
OUTPUT_XHS = OUTPUT_DIR / "小红书"
OUTPUT_BILIBILI = OUTPUT_DIR / "B站"
OUTPUT_TECH = OUTPUT_DIR / "技术存档"  # tech_lecture、流程图动画

TOPICS_DB = DATA_DIR / "topics.db"

# ========== 本地Ollama配置 ==========
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-14b"  # 支持原生Function Calling
OLLAMA_TIMEOUT = 120

# ========== 云端API配置（可选） ==========
# 若本地Ollama不可用，将自动使用云端API
# 支持：OpenAI、通义千问(qwen)、DeepSeek、GLM-4 等OpenAI格式API
# 优先从环境变量读取，不存在则用默认值
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_API_BASE = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
OPENAI_MODEL = os.environ.get('OPENAI_API_MODEL', 'gpt-4o')

# DeepSeek 专用配置（可选覆盖）
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_BASE = os.environ.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')


def get_cloud_llm_config() -> dict:
    """获取云端LLM配置（优先DeepSeek，其次通用OpenAI）。

    所有需要调用云端大模型的模块统一使用此函数，
    禁止在各自模块内直接读取环境变量。
    """
    return {
        "api_key": DEEPSEEK_API_KEY or OPENAI_API_KEY,
        "api_base": DEEPSEEK_API_BASE if DEEPSEEK_API_KEY else OPENAI_API_BASE,
        "model": DEEPSEEK_MODEL if DEEPSEEK_API_KEY else OPENAI_MODEL,
    }

# RAG 知识增强引擎配置
RAG_CONFIG = {
    "enabled": True,                     # 是否启用RAG（可在选题生成入口控制）
    "embedding_model": "nomic-embed-text",  # nomic-embed-text(137M,快) / bge-m3(567M,中英好)
    "chunk_size": 480,                   # 切块字符数
    "chunk_overlap": 120,                # 重叠字符数
    "top_k_retrieve": 5,                 # 检索返回的片段数
    "max_context_tokens": 800,           # 注入prompt的上下文最大token数
    "search_num_results": 5,             # 搜索引擎返回数
}

# Agent企业级配置
AGENT_CONFIG = {
    "max_retries": 3,              # 最大重试次数
    "retry_backoff": 2,            # 指数退避因子
    "stream_output": True,          # 启用流式输出
    "enable_mcp": True,            # 启用MCP协议
    "enable_multi_user": False,    # 默认关闭多用户
    "log_to_ui": True,             # 日志推送到前端
    "persist_memory": True,         # 记忆持久化
}

WHISPER_MODEL = "base"
WHISPER_LANGUAGE = "zh"

OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
DEFAULT_ORIENTATION = "portrait"

def get_output_dimensions(orientation: str = "portrait") -> tuple:
    """返回 (width, height) 基于方向。portrait=1080×1920, landscape=1920×1080。"""
    if orientation == "landscape":
        return 1920, 1080
    return 1080, 1920
OUTPUT_FPS = 30
OUTPUT_CRF = 23
OUTPUT_AUDIO_BITRATE = "192k"
OUTPUT_VIDEO_BITRATE = "2M"

# 漫画风格配置（竖屏讲解视频）
MANGA_STYLE_CONFIG = {
    "paper_color": "#FFF8F0",       # 漫画纸底色（米黄）
    "panel_gap": 14,                # 分镜格间距
    "border_width": 5,              # 格边框宽度
    "halftone_dot_size": 3,         # 网点大小
    "halftone_spacing": 6,          # 网点间距
    "speedline_count": 28,          # 速度线默认数量
    "text_color_primary": "#1A1A2E",
    "accent_red": "#E04040",
    "accent_blue": "#3060C0",
}

PLATFORM_CONFIGS = {
    "抖音": {
        "max_duration": 60,
        "min_duration": 15,
        "aspect_ratio": "9:16",
        "output_dir": OUTPUT_DY,
        "title_max_len": 40,
        "desc_max_len": 200,
        "hashtags_max": 20,
    },
    "小红书": {
        "max_duration": 300,
        "min_duration": 10,
        "aspect_ratio": "9:16",
        "output_dir": OUTPUT_XHS,
        "title_max_len": 20,
        "desc_max_len": 1000,
        "hashtags_max": 15,
    },
    "B站": {
        "max_duration": 600,
        "min_duration": 30,
        "aspect_ratio": "16:9",
        "output_dir": OUTPUT_BILIBILI,
        "title_max_len": 60,
        "desc_max_len": 500,
        "hashtags_max": 10,
    },
}

CATEGORIES = {
    "知识付费": ["干货分享", "技能教学", "职场晋升", "创业故事", "学习技巧", "知识变现"],
    "美食探店": ["各地美食", "网红餐厅", "家常菜谱", "小吃推荐", "快手料理", "减脂餐"],
    "生活方式": ["日常VLOG", "极简生活", "穿搭美妆", "健身打卡", "家居收纳", "自律生活"],
    "情感心理": ["情感故事", "心理分析", "两性关系", "自我成长", "人际交往", "情绪管理"],
    "科技数码": ["产品测评", "APP推荐", "科技前沿", "使用技巧", "效率工具", "AI应用"],
    "娱乐搞笑": ["搞笑段子", "萌宠动物", "热点吐槽", "影视解说", "明星娱乐", "游戏解说"],
}

TRENDING_TAGS = [
    "#爆款", "#必看", "#干货分享", "#建议收藏", "#涨知识",
    "#揭秘", "#干货", "#好物推荐", "#宝藏", "#治愈",
    "#人间真实", "#破防了", "#绝绝子", "#神仙打架", "#YYDS",
]

# ═══════════════════════════════════════════════════════════════
# 视频视觉风格预设 — 控制 MangaFrameRenderer 的全部视觉元素
# ═══════════════════════════════════════════════════════════════
VISUAL_STYLES = {
    "manga": {
        "name_cn": "日式漫画",
        "paper_color": "#FFF8F0",
        "panel_bg": "#FFFBF5",
        "bubble_bg": "#FFFFFF",
        "text_c": "#1A1A2E",
        "accent_red": "#E04040",
        "accent_blue": "#3060C0",
        "border_color": "#1A1A2E",
        "border_width": 5,
        "deco_color": "#1A1A2E",
        "tag_text": "MANGA EXPLAIN",
        "tag_secondary": "MANGA",
        "placeholder_text": "素材参考",
        "default_subtitle": "详细讲解 · 建议收藏反复观看",
        "tags_bottom": ["收藏", "点赞", "转发"],
        "enable_halftone": True,
        "enable_speed_lines": True,
        "enable_crosshatch": True,
        "enable_bg_speckles": True,
        "enable_inner_border": True,
        "enable_decorative_lines": True,
        "enable_progress_dots": True,
        "enable_numbered_circles": True,
        "enable_bottom_tags": True,
        "halftone_dot_size": 2,
        "halftone_spacing": 8,
        "halftone_angle": 45,
        "halftone_opacity": 0.04,
        "speckle_count": 80,
        "speedline_count": 28,
        "crosshatch_spacing": 22,
        "crosshatch_angle": 30,
        "crosshatch_opacity": 7,
        "panel_gap": 14,
        "card_radius": 10,
        "card_border_color": (180, 180, 190, 100),
        "card_border_width": 1,
        "text_secondary": (80, 80, 90, 255),
        "text_muted": (150, 150, 160, 255),
        "progress_inactive": (200, 200, 210, 255),
        "media_panel_bg": (248, 246, 242, 255),
        "title_color_override": None,
        "body_color_override": None,
        "bg_grid": False,
        "bg_grid_color": None,
        "bg_grid_spacing": 0,
        "bg_grid_opacity": 0,
    },
    "minimal": {
        "name_cn": "极简清新",
        "paper_color": "#FFFFFF",
        "panel_bg": "#FAFAFA",
        "bubble_bg": "#FFFFFF",
        "text_c": "#1A1A2E",
        "accent_red": "#4A90D9",
        "accent_blue": "#4A90D9",
        "border_color": "#D0D5DD",
        "border_width": 2,
        "deco_color": "#D0D5DD",
        "tag_text": "",
        "tag_secondary": "",
        "placeholder_text": "图片参考",
        "default_subtitle": "详细讲解",
        "tags_bottom": [],
        "enable_halftone": False,
        "enable_speed_lines": False,
        "enable_crosshatch": False,
        "enable_bg_speckles": False,
        "enable_inner_border": False,
        "enable_decorative_lines": False,
        "enable_progress_dots": False,
        "enable_numbered_circles": False,
        "enable_bottom_tags": False,
        "halftone_dot_size": 2,
        "halftone_spacing": 8,
        "halftone_angle": 45,
        "halftone_opacity": 0,
        "speckle_count": 0,
        "speedline_count": 0,
        "crosshatch_spacing": 0,
        "crosshatch_angle": 0,
        "crosshatch_opacity": 0,
        "panel_gap": 14,
        "card_radius": 8,
        "card_border_color": (208, 213, 221, 80),
        "card_border_width": 1,
        "text_secondary": (100, 100, 110, 255),
        "text_muted": (160, 160, 170, 255),
        "progress_inactive": (220, 220, 225, 255),
        "media_panel_bg": (248, 248, 250, 255),
        "title_color_override": None,
        "body_color_override": None,
        "bg_grid": False,
        "bg_grid_color": None,
        "bg_grid_spacing": 0,
        "bg_grid_opacity": 0,
    },
    "neon": {
        "name_cn": "赛博霓虹",
        "paper_color": "#0A0A1A",
        "panel_bg": "#111128",
        "bubble_bg": "#161630",
        "text_c": "#E0E0F0",
        "accent_red": "#00FFC8",
        "accent_blue": "#00FFC8",
        "border_color": "#00FFC8",
        "border_width": 3,
        "deco_color": "#00FFC8",
        "tag_text": "",
        "tag_secondary": "",
        "placeholder_text": "CYBER REF",
        "default_subtitle": "详细解析",
        "tags_bottom": [],
        "enable_halftone": False,
        "enable_speed_lines": False,
        "enable_crosshatch": False,
        "enable_bg_speckles": False,
        "enable_inner_border": True,
        "enable_decorative_lines": True,
        "enable_progress_dots": True,
        "enable_numbered_circles": True,
        "enable_bottom_tags": False,
        "halftone_dot_size": 2,
        "halftone_spacing": 8,
        "halftone_angle": 45,
        "halftone_opacity": 0,
        "speckle_count": 0,
        "speedline_count": 0,
        "crosshatch_spacing": 0,
        "crosshatch_angle": 0,
        "crosshatch_opacity": 0,
        "panel_gap": 14,
        "card_radius": 4,
        "card_border_color": (0, 255, 200, 120),
        "card_border_width": 1,
        "text_secondary": (140, 140, 180, 255),
        "text_muted": (100, 100, 140, 255),
        "progress_inactive": (40, 40, 80, 255),
        "media_panel_bg": (18, 18, 50, 255),
        "title_color_override": "#00FFC8",
        "body_color_override": "#E0E0F0",
        "bg_grid": True,
        "bg_grid_color": (0, 255, 200, 12),
        "bg_grid_spacing": 40,
        "bg_grid_opacity": 0.08,
    },
    "magazine": {
        "name_cn": "时尚杂志",
        "paper_color": "#FDFBF7",
        "panel_bg": "#F9F6F0",
        "bubble_bg": "#FDFBF7",
        "text_c": "#2C2C2C",
        "accent_red": "#B8860B",
        "accent_blue": "#B8860B",
        "border_color": "#C4A882",
        "border_width": 3,
        "deco_color": "#C4A882",
        "tag_text": "VOGUE",
        "tag_secondary": "",
        "placeholder_text": "商品展示",
        "default_subtitle": "精致生活 · 品味优选",
        "tags_bottom": ["精选", "好物"],
        "enable_halftone": False,
        "enable_speed_lines": False,
        "enable_crosshatch": False,
        "enable_bg_speckles": True,
        "enable_inner_border": True,
        "enable_decorative_lines": True,
        "enable_progress_dots": True,
        "enable_numbered_circles": True,
        "enable_bottom_tags": True,
        "halftone_dot_size": 0,
        "halftone_spacing": 0,
        "halftone_angle": 0,
        "halftone_opacity": 0,
        "speckle_count": 30,
        "speedline_count": 0,
        "crosshatch_spacing": 0,
        "crosshatch_angle": 0,
        "crosshatch_opacity": 0,
        "panel_gap": 16,
        "card_radius": 2,
        "card_border_color": (196, 168, 130, 80),
        "card_border_width": 1,
        "text_secondary": (100, 90, 80, 255),
        "text_muted": (160, 150, 140, 255),
        "progress_inactive": (210, 205, 195, 255),
        "media_panel_bg": (248, 244, 236, 255),
        "title_color_override": None,
        "body_color_override": None,
        "bg_grid": False,
        "bg_grid_color": None,
        "bg_grid_spacing": 0,
        "bg_grid_opacity": 0,
    },
    "vibrant": {
        "name_cn": "活力撞色",
        "paper_color": "#FFF5F5",
        "panel_bg": "#FFFFFF",
        "bubble_bg": "#FFFFFF",
        "text_c": "#1A1A2E",
        "accent_red": "#FF4757",
        "accent_blue": "#3742FA",
        "border_color": "#FF4757",
        "border_width": 4,
        "deco_color": "#FF4757",
        "tag_text": "HOT",
        "tag_secondary": "",
        "placeholder_text": "爆款素材",
        "default_subtitle": "必入好物 · 不容错过",
        "tags_bottom": ["必买", "推荐", "超值"],
        "enable_halftone": False,
        "enable_speed_lines": True,
        "enable_crosshatch": False,
        "enable_bg_speckles": False,
        "enable_inner_border": True,
        "enable_decorative_lines": True,
        "enable_progress_dots": True,
        "enable_numbered_circles": True,
        "enable_bottom_tags": True,
        "halftone_dot_size": 0,
        "halftone_spacing": 0,
        "halftone_angle": 0,
        "halftone_opacity": 0,
        "speckle_count": 0,
        "speedline_count": 20,
        "crosshatch_spacing": 0,
        "crosshatch_angle": 0,
        "crosshatch_opacity": 0,
        "panel_gap": 14,
        "card_radius": 12,
        "card_border_color": (255, 71, 87, 100),
        "card_border_width": 2,
        "text_secondary": (80, 80, 90, 255),
        "text_muted": (150, 150, 160, 255),
        "progress_inactive": (220, 220, 225, 255),
        "media_panel_bg": (255, 245, 245, 255),
        "title_color_override": None,
        "body_color_override": None,
        "bg_grid": False,
        "bg_grid_color": None,
        "bg_grid_spacing": 0,
        "bg_grid_opacity": 0,
    },
}

DEFAULT_VISUAL_STYLE = "manga"


def get_visual_style_config(style_name: str) -> dict:
    """返回指定名称的视觉风格预设，无效名称退回 manga。"""
    return VISUAL_STYLES.get(style_name, VISUAL_STYLES[DEFAULT_VISUAL_STYLE])


# ═══════════════════════════════════════════════════════════════
# 视频素材源配置 — Pexels / Pixabay 真实视频素材
# ═══════════════════════════════════════════════════════════════
STOCK_VIDEO_SOURCE = os.environ.get("STOCK_VIDEO_SOURCE", "pexels")  # pexels / pixabay / local
STOCK_VIDEO_MIN_DURATION = 3       # 搜索时最短片段秒数
STOCK_VIDEO_MAX_CLIP_DURATION = 5  # 每个片段最长秒数（超出则截取）
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")

ECOM_CONFIG = {
    "default_style": "soft_sell",
    "default_platform": "TikTok",
    "default_duration": 30,
    "max_products_per_page": 50,
}

BGM_VOLUME = 0.3
BG_MUTE_DURATION = 2

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

DB_TOPICS_TABLE = "topics"
DB_SCRIPTS_TABLE = "scripts"
DB_ANALYTICS_TABLE = "analytics"

CACHE_CONFIG = {
    "enabled": True,
    "maxsize": 2000,
    "preload_count": 500,
}

CRAWLER_CONFIG = {
    "enabled": True,
    "offline_mode_after_crawl": True,
    "headless": True,
    "request_delay": (1, 3),
    "max_topics_per_platform": 500,
}

LIBRARY_EXPAND_CONFIG = {
    "target_count": 1000,
    "synthetic_ratio": 0.8,
}


def ensure_dirs():
    """确保所有必要目录存在"""
    for dir_path in [DATA_DIR, ASSETS_DIR, OUTPUT_DIR, BGM_DIR, MATERIAL_DIR, THUMBNAILS_DIR,
                     OUTPUT_DY, OUTPUT_XHS, OUTPUT_BILIBILI, OUTPUT_TECH]:
        dir_path.mkdir(parents=True, exist_ok=True)
