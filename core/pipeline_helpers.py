# -*- coding: utf-8 -*-
"""
共享流水线辅助函数 — 从 api/ecom_api.py 提取，供 ecom + topic 双路径复用。
"""
import re
import json
import sqlite3
import traceback
from pathlib import Path

import config
from core.db_init import get_db_path


def video_path_to_url(video_path: str) -> str:
    """将绝对文件路径转换为 /static/output/... URL。"""
    if not video_path:
        return ''
    normalized = video_path.replace('\\', '/')
    output_dir = str(config.OUTPUT_DIR).replace('\\', '/')
    if normalized.startswith(output_dir):
        relative = normalized[len(output_dir):].lstrip('/')
        return f'/static/output/{relative}'
    return normalized


def split_sentences(text: str) -> list[str]:
    chunks = [s.strip() for s in re.split(r'(?<=[。！？!?])\s*|\n+', text or "") if s.strip()]
    return chunks


def to_text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (list, tuple)):
        return " ".join([to_text(x) for x in v if to_text(x)]).strip()
    if isinstance(v, dict):
        return " ".join([to_text(x) for x in v.values() if to_text(x)]).strip()
    return str(v).strip()


def normalize_script_result(script_result: dict) -> dict:
    normalized = dict(script_result or {})
    normalized["hook"] = to_text(normalized.get("hook"))
    normalized["body"] = to_text(normalized.get("body"))
    normalized["cta"] = to_text(normalized.get("cta"))
    full_script = to_text(normalized.get("full_script"))
    if not full_script:
        full_script = " ".join(
            part for part in (normalized["hook"], normalized["body"], normalized["cta"]) if part
        ).strip()
    normalized["full_script"] = full_script
    return normalized


def extract_bullets(text: str, max_items: int = 6) -> list[str]:
    parts = re.split(r'(?<=[。！？!?])\s*|\n+', text or "")
    candidates = [s.strip() for s in parts if s.strip()]
    if candidates:
        return candidates[:max_items]
    if text and text.strip():
        return [text.strip()]
    return []


def normalize_storyboard(script_result: dict, duration: int) -> list[dict]:
    hook = to_text(script_result.get("hook"))
    body = to_text(script_result.get("body"))
    cta = to_text(script_result.get("cta"))
    full_script = to_text(script_result.get("full_script"))
    raw_storyboard = script_result.get("storyboard") or []
    if not isinstance(raw_storyboard, list):
        raw_storyboard = []

    scenes: list[dict] = []
    for idx, item in enumerate(raw_storyboard):
        if not isinstance(item, dict):
            continue
        subtitle = to_text(item.get("subtitle") or item.get("字幕要点") or item.get("text"))
        if not subtitle:
            subtitle = to_text(item.get("scene") or item.get("画面描述"))
        title = to_text(item.get("title") or item.get("scene") or item.get("画面描述") or f"场景 {idx + 1}")
        bullets = [str(x).strip() for x in item.get("bullets", []) if str(x).strip()] if isinstance(item.get("bullets"), list) else extract_bullets(subtitle)
        scenes.append({
            "time": item.get("time") or item.get("时间点") or "",
            "title": title,
            "bullets": bullets,
            "subtitle": subtitle,
            "duration": int(item.get("duration") or item.get("时长") or 0),
            "material_url": item.get("material_url"),
            "style": item.get("style") or "comic",
        })

    if not scenes:
        chunks = split_sentences(full_script)
        scene_count = max(3, min(8, len(chunks) or 3))
        if not chunks:
            chunks = [hook, body, cta]
        chunks = [c for c in chunks if c and c.strip()]
        while len(chunks) < scene_count:
            chunks.append(chunks[-1] if chunks else "内容亮点介绍")
        chunks = chunks[:scene_count]

        ordered = []
        if hook:
            ordered.append(("Hook", hook))
        if body:
            for i, b in enumerate(split_sentences(body), start=1):
                ordered.append((f"亮点 {i}", b))
        if cta:
            ordered.append(("CTA", cta))
        if not ordered:
            ordered = [(f"场景 {i+1}", t) for i, t in enumerate(chunks)]

        if len(ordered) < 3:
            ordered.extend((f"场景 {len(ordered)+i+1}", c) for i, c in enumerate(chunks[: 3 - len(ordered)]))

        base = max(2, int(duration / max(len(ordered), 1)))
        for i, (title, text) in enumerate(ordered[:8]):
            scenes.append({
                "time": f"{i * base}-{(i + 1) * base}s",
                "title": title,
                "bullets": extract_bullets(text),
                "subtitle": text,
                "duration": base,
                "material_url": "",
                "style": "comic",
            })

    total = sum(max(1, int(s.get("duration") or 0)) for s in scenes) or duration
    scale = duration / total if total > 0 else 1
    acc = 0
    for s in scenes:
        d = max(1, int(round(max(1, int(s.get("duration") or 1)) * scale)))
        s["duration"] = d
        s["time"] = f"{acc}-{acc + d}s"
        acc += d
        s["style"] = s.get("style") or "comic"
        s["bullets"] = s.get("bullets") or extract_bullets(s.get("subtitle", ""))
    return scenes


def generate_manga_frames(storyboard, script_content, work_dir, materials=None, width=1080, height=1920, visual_style="manga"):
    """漫画风讲解帧 — 文字为主，网点纸+气泡框+速度线+分镜格。支持横竖屏与多种视觉风格。"""
    from core.manga_frame_renderer import MangaFrameRenderer

    materials = materials or {}
    renderer = MangaFrameRenderer(width=width, height=height, visual_style=visual_style)
    return renderer.render_storyboard(
        storyboard=storyboard,
        script_content=script_content,
        work_dir=str(work_dir),
        materials=materials,
    )


def ensure_storyboard_placeholders(video_id: int, storyboard: list[dict], script_content: str, table_name: str = "ecom_videos") -> list[dict]:
    """Generate manga-style placeholders for scenes without material_url."""
    scene_dir = config.OUTPUT_DIR / "storyboard" / f"video_{video_id}"
    scene_dir.mkdir(parents=True, exist_ok=True)
    generated = generate_manga_frames(storyboard or [], script_content, scene_dir)
    idx = 0
    for i, scene in enumerate(storyboard):
        if scene.get("material_url"):
            continue
        if idx < len(generated):
            local_path = generated[idx]
            scene["material_url"] = video_path_to_url(local_path)
            idx += 1
    return storyboard


def run_render_pipeline(video_id: int, table_name: str = "ecom_videos"):
    """后台线程: 动画 → 字幕 → 多轨道合成。table_name 用于 ecom_videos 或 topic_videos。"""
    def _update(step=None, status=None, video_path=None, error_msg=None):
        conn = sqlite3.connect(get_db_path())
        try:
            sets, params = [], []
            if step:
                sets.append("pipeline_step=?")
                params.append(step)
            if status:
                sets.append("status=?")
                params.append(status)
            if video_path:
                sets.append("video_path=?")
                params.append(video_path)
            if error_msg:
                sets.append("notes=?")
                params.append(error_msg)
            params.append(video_id)
            conn.execute(f"UPDATE {table_name} SET {','.join(sets)} WHERE id=?", params)
            conn.commit()
        finally:
            conn.close()

    try:
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (video_id,))
        row = dict(cursor.fetchone())
        conn.close()

        script_content = row['script_content']
        storyboard_str = row['storyboard'] or '[]'
        tts_audio_path = row['tts_audio_path']
        materials_str = row['materials_json'] or '{}'
        duration = row['duration'] or 30
        animation_style = row.get('animation_style') or 'manga_frame'
        orientation = row.get('orientation') or 'portrait'
        visual_style = row.get('visual_style') or 'manga'
        video_width = row.get('video_width') or 1080
        video_height = row.get('video_height') or 1920

        storyboard = json.loads(storyboard_str)
        materials = json.loads(materials_str)

        work_dir = config.OUTPUT_DIR / "_work" / f"{'topic' if 'topic' in table_name else 'ecom'}_{video_id}"
        work_dir.mkdir(parents=True, exist_ok=True)

        # 漫画风讲解帧（文字主导，素材次要）
        images = generate_manga_frames(storyboard, script_content, work_dir, materials=materials,
                                        width=video_width, height=video_height, visual_style=visual_style)
        if not images:
            _update(step='failed', status='failed', error_msg='漫画帧生成失败，请检查素材')
            return

        # 生成 timeline segments
        segments = []
        if storyboard:
            seg_duration = duration / len(storyboard)
            for i, sb in enumerate(storyboard):
                segments.append({
                    'start': i * seg_duration,
                    'end': (i + 1) * seg_duration,
                    'text': sb.get('subtitle', sb.get('text', '')),
                    'image_index': i % len(images),
                })
        else:
            seg_duration = duration / max(len(images), 1)
            for i in range(len(images)):
                segments.append({
                    'start': i * seg_duration,
                    'end': (i + 1) * seg_duration,
                    'text': '',
                    'image_index': i,
                })

        # Step: 动画视频（横竖屏自适应）
        _update(step='rendering')
        from core.animation_module import get_animation_module
        animation = get_animation_module()
        animation.output_width = video_width
        animation.output_height = video_height

        raw_video_path = str(work_dir / "raw_video.mp4")
        anim_ok = animation.create_animated_video_from_segments(
            images=images,
            segments=segments,
            output_path=raw_video_path,
            animation_style="manga_frame",
            transition="fade",
        )
        if not anim_ok:
            _update(step='failed', status='failed', error_msg='动画视频生成失败')
            return

        # Step: 字幕
        from core.subtitle_module import get_subtitle_module
        subtitle_mod = get_subtitle_module()
        srt_path = str(work_dir / "subtitle.srt")
        subtitle_mod.generate_srt(segments, srt_path)

        # Step: 多轨道合成
        from core.dual_mode_module import multitrack_composite
        final_video_path = str(work_dir / "final_video.mp4")

        bgm_path = None
        available_bgm = config.ASSETS_DIR / "bgm"
        if available_bgm.exists():
            bgm_files = list(available_bgm.glob("*.mp3")) + list(available_bgm.glob("*.wav"))
            if bgm_files:
                bgm_path = str(bgm_files[0])

        composite_ok = multitrack_composite(
            video_path=raw_video_path,
            audio_path=tts_audio_path,
            subtitle_path=srt_path,
            bgm_path=bgm_path,
            output_path=final_video_path,
        )
        if not composite_ok:
            _update(step='failed', status='failed', error_msg='多轨道合成失败')
            return

        _update(step='done', status='done', video_path=final_video_path)
        print(f"[Render] {table_name} video_id={video_id} done: {final_video_path}")

    except Exception as e:
        traceback.print_exc()
        _update(step='failed', status='failed', error_msg=str(e))
        print(f"[Render] {table_name} video_id={video_id} exception: {e}")
