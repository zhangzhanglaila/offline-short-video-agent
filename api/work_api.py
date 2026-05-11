# -*- coding: utf-8 -*-
"""
作品API路由
"""
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

router = APIRouter()

THUMBNAILS_DIR = config.THUMBNAILS_DIR


def _generate_thumbnail(video_path: Path) -> str | None:
    """Generate a thumbnail for a video, return URL path or None."""
    thumb_name = video_path.stem + '_thumb.jpg'
    thumb_path = THUMBNAILS_DIR / thumb_name
    if thumb_path.exists():
        return f'/static/thumbnails/{thumb_name}'
    # Try at 1s, then 0s (for very short videos)
    for ts in ['00:00:01', '00:00:00']:
        try:
            cmd = [
                'ffmpeg', '-y', '-i', str(video_path),
                '-ss', ts, '-vframes', '1',
                '-vf', 'scale=320:180',
                '-q:v', '2',
                str(thumb_path)
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode == 0 and thumb_path.exists():
                return f'/static/thumbnails/{thumb_name}'
        except Exception:
            continue
    return None


def _video_to_http_url(video_path: Path) -> str:
    """Convert absolute video path to HTTP URL via /static/output mount."""
    try:
        rel = video_path.relative_to(config.OUTPUT_DIR)
        return f'/static/output/{rel.as_posix()}'
    except ValueError:
        return f'/static/output/{video_path.name}'


@router.get("/api/works")
async def api_works():
    """获取已生成作品（含封面和可播放URL）"""
    try:
        works = []
        output_dir = Path(config.OUTPUT_DIR)
        seen = set()  # deduplicate by resolved path

        if output_dir.exists():
            # Scan platform dirs (抖音/, 小红书/, B站/, etc.)
            for platform_dir in output_dir.iterdir():
                if not platform_dir.is_dir() or platform_dir.name.startswith('_'):
                    continue
                for video_file in platform_dir.rglob('*.mp4'):
                    real = video_file.resolve()
                    if real in seen:
                        continue
                    seen.add(real)
                    works.append(_build_work_entry(video_file, platform_dir.name))

            # Scan _work/ temp dir for videos not yet exported
            work_dir = output_dir / '_work'
            if work_dir.exists():
                for video_file in work_dir.rglob('*.mp4'):
                    real = video_file.resolve()
                    if real in seen:
                        continue
                    seen.add(real)
                    works.append(_build_work_entry(video_file, '未分类'))

        works.sort(key=lambda x: x['date'], reverse=True)
        return JSONResponse({'works': works})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


def _build_work_entry(video_file: Path, platform: str) -> dict:
    """Build a single work entry dict with thumbnail and playable URL."""
    info_file = video_file.with_suffix('.txt')
    title = video_file.stem
    if info_file.exists():
        try:
            content = info_file.read_text(encoding='utf-8')
            for line in content.split('\n'):
                if line.startswith('【标题】'):
                    title = line.replace('【标题】', '').strip()
                    break
        except Exception:
            pass

    thumb_url = _generate_thumbnail(video_file)
    video_url = _video_to_http_url(video_file)

    return {
        'name': video_file.name,
        'path': str(video_file),
        'platform': platform,
        'title': title,
        'date': datetime.fromtimestamp(video_file.stat().st_mtime).strftime('%Y-%m-%d'),
        'thumb_url': thumb_url,
        'video_url': video_url,
    }
