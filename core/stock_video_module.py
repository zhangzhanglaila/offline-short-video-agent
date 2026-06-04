# -*- coding: utf-8 -*-
"""
视频素材搜索下载模块 — Pexels / Pixabay 真实高清视频片段
参考 MoneyPrinterTurbo material.py 设计，适配本项目管线。
"""
import os
import re
import hashlib
import time
import random
import threading
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

import requests

import config


@dataclass
class VideoMaterial:
    """视频素材搜索结果"""
    url: str
    duration: float
    width: int = 0
    height: int = 0
    provider: str = ""
    keywords: str = ""


class StockVideoModule:
    """视频素材搜索下载模块"""

    PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
    PIXABAY_VIDEO_URL = "https://pixabay.com/api/videos/"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def __init__(self, orientation: str = "portrait"):
        self.orientation = orientation  # "portrait" or "landscape"
        self._session = requests.Session()
        self._session.headers.update(self.HEADERS)
        self._session.trust_env = False

        # 目标分辨率
        w, h = config.get_output_dimensions(orientation)
        self.target_width = w
        self.target_height = h

        # 下载缓存目录
        self.cache_dir = config.MATERIAL_DIR / "stock_videos"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # API key 轮转
        self._key_counter = 0
        self._key_lock = threading.Lock()

    # ────────────────────────────────────────────
    # Pexels Video API
    # ────────────────────────────────────────────

    def search_pexels(self, keywords: str, min_duration: int = 3,
                      per_page: int = 20) -> List[VideoMaterial]:
        """从 Pexels 搜索视频片段"""
        api_key = os.environ.get("PEXELS_API_KEY", "")
        if not api_key:
            return []

        try:
            params = {
                "query": keywords,
                "per_page": per_page,
                "orientation": self.orientation,
            }
            resp = self._session.get(
                self.PEXELS_VIDEO_URL,
                headers={"Authorization": api_key},
                params=params,
                timeout=(10, 30),
            )
            if resp.status_code == 429:
                print(f"[StockVideo] Pexels 请求频率限制")
                return []
            if resp.status_code != 200:
                print(f"[StockVideo] Pexels 请求失败: {resp.status_code}")
                return []

            data = resp.json()
            results = []
            for v in data.get("videos", []):
                duration = v.get("duration", 0)
                if duration < min_duration:
                    continue
                # 寻找匹配分辨率的视频文件
                best_url = self._pick_pexels_video_file(v.get("video_files", []))
                if best_url:
                    results.append(VideoMaterial(
                        url=best_url,
                        duration=duration,
                        provider="pexels",
                        keywords=keywords,
                    ))
            return results
        except Exception as e:
            print(f"[StockVideo] Pexels 搜索异常: {e}")
            return []

    def _pick_pexels_video_file(self, video_files: list) -> Optional[str]:
        """从 Pexels video_files 中选择最匹配目标分辨率的文件URL。
        优先精确匹配，其次最接近的分辨率。"""
        best_url = None
        best_diff = float("inf")
        for vf in video_files:
            w = int(vf.get("width", 0))
            h = int(vf.get("height", 0))
            if w == 0 or h == 0:
                continue
            # 精确匹配
            if w == self.target_width and h == self.target_height:
                return vf.get("link", "")
            # 接近匹配（宽高差最小）
            diff = abs(w - self.target_width) + abs(h - self.target_height)
            if diff < best_diff:
                best_diff = diff
                best_url = vf.get("link", "")
        # 如果没有接近的匹配，取第一个有效URL
        if not best_url and video_files:
            best_url = video_files[0].get("link", "")
        return best_url

    # ────────────────────────────────────────────
    # Pixabay Video API
    # ────────────────────────────────────────────

    def search_pixabay(self, keywords: str, min_duration: int = 3,
                       per_page: int = 50) -> List[VideoMaterial]:
        """从 Pixabay 搜索视频片段"""
        api_key = os.environ.get("PIXABAY_API_KEY", config.PIXABAY_API_KEY)
        if not api_key:
            return []

        try:
            params = {
                "q": keywords,
                "video_type": "all",
                "per_page": per_page,
                "key": api_key,
            }
            resp = self._session.get(
                self.PIXABAY_VIDEO_URL,
                params=params,
                timeout=(10, 30),
            )
            if resp.status_code != 200:
                print(f"[StockVideo] Pixabay 请求失败: {resp.status_code}")
                return []

            data = resp.json()
            results = []
            for hit in data.get("hits", []):
                duration = hit.get("duration", 0)
                if duration < min_duration:
                    continue
                # Pixabay 按质量分级: large > medium > small > tiny
                videos = hit.get("videos", {})
                best_url = self._pick_pixabay_video_file(videos)
                if best_url:
                    results.append(VideoMaterial(
                        url=best_url,
                        duration=duration,
                        provider="pixabay",
                        keywords=keywords,
                    ))
            return results
        except Exception as e:
            print(f"[StockVideo] Pixabay 搜索异常: {e}")
            return []

    def _pick_pixabay_video_file(self, videos: dict) -> Optional[str]:
        """从 Pixabay videos 字典中选择分辨率足够的文件。优先级: large > medium > small > tiny"""
        for tier in ("large", "medium", "small", "tiny"):
            vf = videos.get(tier, {})
            w = int(vf.get("width", 0))
            if w >= self.target_width:
                return vf.get("url", "")
        # fallback: 取第一个有效URL
        for tier in ("large", "medium", "small", "tiny"):
            vf = videos.get(tier, {})
            if vf.get("url"):
                return vf["url"]
        return None

    # ────────────────────────────────────────────
    # 下载 + 缓存
    # ────────────────────────────────────────────

    def download_video(self, url: str, save_dir: str = "") -> str:
        """下载单个视频，使用MD5缓存避免重复下载。返回本地路径。"""
        if not save_dir:
            save_dir = str(self.cache_dir)

        os.makedirs(save_dir, exist_ok=True)

        # MD5 缓存键（去掉 query string）
        url_clean = url.split("?")[0]
        url_hash = hashlib.md5(url_clean.encode()).hexdigest()[:12]
        filename = f"sv_{url_hash}.mp4"
        output_path = os.path.join(save_dir, filename)

        # 已缓存 → 直接返回
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path

        try:
            resp = self._session.get(url, timeout=(30, 120), stream=True)
            if resp.status_code != 200:
                print(f"[StockVideo] 下载失败 {resp.status_code}: {url[:80]}")
                return ""

            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 校验：文件非空且可被FFmpeg读取
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                if self._validate_video(output_path):
                    return output_path
                else:
                    self._safe_remove(output_path)
                    return ""
        except Exception as e:
            print(f"[StockVideo] 下载异常: {e}")
            self._safe_remove(output_path)

        return ""

    def _validate_video(self, path: str) -> bool:
        """用 FFmpeg probe 校验视频文件有效性"""
        try:
            import subprocess
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", path],
                capture_output=True, timeout=10,
            )
            if result.returncode != 0:
                return False
            import json
            # Windows 下用 bytes 解码避免 GBK 编码问题
            output = result.stdout.decode("utf-8", errors="replace") if isinstance(result.stdout, bytes) else result.stdout
            info = json.loads(output)
            duration = float(info.get("format", {}).get("duration", 0))
            return duration > 0
        except Exception:
            return False

    def _safe_remove(self, path: str):
        try:
            os.remove(path)
        except OSError:
            pass

    # ────────────────────────────────────────────
    # 按场景批量获取（核心接口）
    # ────────────────────────────────────────────

    def fetch_for_scenes(self, storyboard: list, audio_duration: float,
                         source: str = "") -> Dict[int, str]:
        """为每个场景搜索并下载视频素材。

        返回: {scene_index: local_video_path}
        无素材的场景不出现在字典中（调用方降级为漫画帧）。
        """
        source = source or config.STOCK_VIDEO_SOURCE
        min_dur = config.STOCK_VIDEO_MIN_DURATION
        max_clip = config.STOCK_VIDEO_MAX_CLIP_DURATION

        search_fn = self.search_pexels if source == "pexels" else self.search_pixabay

        scene_map: Dict[int, str] = {}
        total_downloaded_duration = 0.0
        target_duration = audio_duration * 1.1  # 多下 10% 余量

        for i, scene in enumerate(storyboard):
            if total_downloaded_duration >= target_duration:
                break

            # 提取场景关键词
            keywords = self._extract_scene_keywords(scene, i)
            if not keywords:
                continue

            print(f"[StockVideo] 场景 {i} 搜索: {keywords}")
            results = search_fn(keywords, min_duration=min_dur)

            # 尝试下载第一个有效结果
            for item in results[:3]:  # 最多尝试3个
                local_path = self.download_video(item.url)
                if local_path:
                    scene_map[i] = local_path
                    # 实际可用时长 = min(素材时长, max_clip)
                    clip_dur = min(item.duration, max_clip)
                    total_downloaded_duration += clip_dur
                    print(f"[StockVideo] 场景 {i} ✓ {item.provider} {item.duration:.0f}s → {local_path}")
                    break

            # 搜索间隔，避免频率限制
            time.sleep(random.uniform(0.3, 0.8))

        print(f"[StockVideo] 共获取 {len(scene_map)}/{len(storyboard)} 个场景视频素材, "
              f"累计 {total_downloaded_duration:.1f}s / 目标 {target_duration:.1f}s")
        return scene_map

    def _extract_scene_keywords(self, scene: dict, scene_index: int) -> str:
        """从场景数据提取英文搜索关键词。
        优先使用 scene 的 subtitle/title，转为英文搜索词。"""
        # 取场景标题和副标题
        title = str(scene.get("title") or "")
        subtitle = str(scene.get("subtitle") or "")
        text = f"{title} {subtitle}".strip()

        if not text:
            return ""

        # 提取中文关键词
        cn_keywords = re.findall(r'[一-鿿]+', text)
        if not cn_keywords:
            # 如果没有中文，直接用原文（可能是英文）
            return text[:50]

        # 常见中文→英文映射（技术/生活场景）
        cn_to_en = {
            "技术": "technology", "科技": "technology", "编程": "programming",
            "代码": "coding", "数据": "data", "网络": "network",
            "手机": "smartphone", "电脑": "computer", "办公": "office",
            "学习": "study", "教育": "education", "工作": "work",
            "健康": "health", "运动": "fitness", "美食": "food",
            "旅行": "travel", "自然": "nature", "城市": "city",
            "家庭": "family", "孩子": "children", "社交": "social",
            "金融": "finance", "投资": "investment", "股票": "stock",
            "AI": "artificial intelligence", "人工智能": "AI technology",
            "机器学习": "machine learning", "深度学习": "deep learning",
            "数据库": "database", "服务器": "server", "云计算": "cloud computing",
            "区块链": "blockchain", "加密": "cryptocurrency",
            "创业": "startup", "营销": "marketing", "品牌": "brand",
            "设计": "design", "创意": "creative", "艺术": "art",
            "音乐": "music", "电影": "movie", "游戏": "gaming",
            "购物": "shopping", "电商": "ecommerce", "直播": "livestream",
            "短视频": "short video", "社交媒体": "social media",
            "成功": "success", "效率": "productivity", "时间": "time management",
        }

        en_words = []
        for kw in cn_keywords:
            if kw in cn_to_en:
                en_words.append(cn_to_en[kw])
            elif len(kw) >= 2:
                # 尝试取部分映射
                for cn, en in cn_to_en.items():
                    if cn in kw or kw in cn:
                        en_words.append(en)
                        break

        if not en_words:
            # 兜底：用场景序号 + 通用词
            fallback_terms = [
                "business technology", "office workspace", "digital lifestyle",
                "modern city", "abstract background", "nature landscape",
            ]
            return fallback_terms[scene_index % len(fallback_terms)]

        return " ".join(en_words[:3])


# ==================== 便捷函数 ====================
_module_instance = None


def get_stock_video_module(orientation: str = "portrait") -> StockVideoModule:
    """获取视频素材模块单例"""
    global _module_instance
    if _module_instance is None or _module_instance.orientation != orientation:
        _module_instance = StockVideoModule(orientation=orientation)
    return _module_instance


def fetch_stock_videos_for_scenes(storyboard: list, audio_duration: float,
                                   orientation: str = "portrait",
                                   source: str = "") -> Dict[int, str]:
    """便捷函数：为场景列表获取视频素材"""
    return get_stock_video_module(orientation).fetch_for_scenes(
        storyboard, audio_duration, source
    )
