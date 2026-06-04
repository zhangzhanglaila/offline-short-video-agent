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


def extract_bullets(text: str, max_items: int = 8) -> list[str]:
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
        # 按段落分组，每个场景包含2-3句话，内容更丰富
        ordered = []
        if hook:
            ordered.append(("Hook", hook))
        if body:
            body_sents = split_sentences(body)
            if body_sents:
                # 将body句子按每2-3句分组
                group_size = 2 if len(body_sents) <= 5 else 3
                groups = []
                for gi in range(0, len(body_sents), group_size):
                    groups.append("。".join(body_sents[gi:gi+group_size]))
                for i, g in enumerate(groups, start=1):
                    ordered.append((f"亮点 {i}", g))
        if cta:
            ordered.append(("CTA", cta))
        if not ordered:
            # fallback: 从full_script分段
            chunks = split_sentences(full_script)
            if not chunks:
                chunks = [hook or "精彩内容", body or "详细介绍", cta or "关注点赞"]
            group_size = max(1, len(chunks) // 3)
            for i in range(0, len(chunks), max(1, group_size)):
                segment = "。".join(chunks[i:i+group_size])
                ordered.append((f"场景 {len(ordered)+1}", segment))

        if len(ordered) < 3:
            ordered.extend((f"场景 {len(ordered)+i+1}", c) for i, c in enumerate([body or "详细内容介绍"][: 3 - len(ordered)]))

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


def generate_chart_materials(script_result: dict, work_dir: Path, visual_style: str,
                              video_width: int = 1080, video_height: int = 1920) -> dict:
    """从 script_result 的 chart_data 生成图表 PNG，返回 {scene_index: file_path} 字典。"""
    chart_data = script_result.get("chart_data", [])
    if not isinstance(chart_data, list):
        chart_data = []
    diagram_layout = script_result.get("diagram_layout", "")

    materials = {}
    chart_dir = Path(work_dir) / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)

    chart_w = min(340, video_width // 3)
    chart_h = min(700, video_height * 2 // 5)

    # 处理 chart_data 条目（跳过 big_number / vs_compare — 它们在漫画帧层渲染）
    CHART_RENDER_TYPES = {"bar", "bar_chart", "column", "pie", "pie_chart", "line", "line_chart", "flowchart", "diagram", "architecture"}
    for chart_spec in chart_data:
        if not isinstance(chart_spec, dict):
            continue
        ct = chart_spec.get("chart_type", "bar")
        if ct not in CHART_RENDER_TYPES:
            continue  # big_number / vs_compare 在漫画帧渲染器层处理
        scene_idx = chart_spec.get("scene_index", 0)
        output_path = str(chart_dir / f"chart_{scene_idx:03d}.png")
        try:
            from core.chart_renderer import render_chart
            render_chart(chart_spec, output_path, visual_style, width=chart_w, height=chart_h)
            materials[str(scene_idx)] = output_path
        except Exception as e:
            print(f"[Chart] 图表渲染失败 scene={scene_idx}: {e}")

    # 处理旧 diagram_layout（无 flowchart 时）
    has_flowchart = any(
        isinstance(c, dict) and c.get("chart_type") in ("flowchart", "diagram")
        for c in chart_data
    )
    if diagram_layout and not has_flowchart:
        dsl_output = str(chart_dir / "diagram_000.png")
        try:
            from core.chart_renderer import parse_diagram_dsl, render_chart
            layout = parse_diagram_dsl(diagram_layout, target_w=chart_w, target_h=chart_h)
            if layout:
                render_chart({"chart_type": "flowchart", "title": ""}, dsl_output, visual_style,
                            width=chart_w, height=chart_h, _override_layout=layout)
                materials["0"] = dsl_output
        except Exception as e:
            print(f"[Chart] diagram_layout 渲染失败: {e}")

    return materials


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

        # ═══ 自动图表生成（含动态图表动画） ═══
        chart_data_raw = json.loads(row.get("chart_data") or "[]") if isinstance(row.get("chart_data"), str) else (row.get("chart_data") or [])
        if not isinstance(chart_data_raw, list):
            chart_data_raw = []
        chart_script = {"chart_data": chart_data_raw,
                        "diagram_layout": row.get("diagram_layout") or ""}

        # 静态图表 PNG（进度=1.0）→ 用于素材字典
        chart_materials = generate_chart_materials(chart_script, work_dir, visual_style, video_width, video_height)
        for k, v in chart_materials.items():
            if k not in materials or not materials[k]:
                materials[k] = v

        # 动态图表动画帧（进度=0→1 的多帧序列）
        ANIM_FRAMES = 12
        chart_anim_frames = {}  # {scene_index: [frame_png_paths]}
        if chart_data_raw:
            anim_dir = work_dir / "charts" / "anim"
            anim_dir.mkdir(parents=True, exist_ok=True)
            chart_w = min(340, video_width // 3)
            chart_h = min(700, video_height * 2 // 5)
            for cspec in chart_data_raw:
                if not isinstance(cspec, dict):
                    continue
                ct = cspec.get("chart_type", "bar")
                if ct not in ("bar", "bar_chart", "column", "pie", "pie_chart", "line", "line_chart", "flowchart", "diagram", "architecture"):
                    continue  # big_number / vs_compare 不需要图表帧
                si = cspec.get("scene_index", 0)
                scene_anim_dir = anim_dir / f"scene_{si:03d}"
                scene_anim_dir.mkdir(parents=True, exist_ok=True)
                try:
                    from core.chart_renderer import render_chart_frames
                    paths = render_chart_frames(cspec, str(scene_anim_dir), visual_style, chart_w, chart_h, ANIM_FRAMES)
                    chart_anim_frames[str(si)] = paths
                except Exception as e:
                    print(f"[Chart] 动画帧生成失败 scene={si}: {e}")

        # ═══ 漫画风讲解帧（含动态图表多帧支持） ═══
        from core.manga_frame_renderer import MangaFrameRenderer
        renderer = MangaFrameRenderer(width=video_width, height=video_height, visual_style=visual_style)

        # 合并 storyboard 场景的 visual_data（从 chart_data 中提取 big_number / vs_compare 数据）
        for cspec in chart_data_raw:
            if not isinstance(cspec, dict):
                continue
            si = cspec.get("scene_index", 0)
            ct = cspec.get("chart_type", "")
            if si < len(storyboard):
                sb = storyboard[si]
                if ct in ("big_number",):
                    sb["visual_element"] = "big_number"
                    sb["visual_data"] = {"value": cspec.get("value", ""), "label": cspec.get("title", ""),
                                          "trend": cspec.get("trend", ""), "subtitle": cspec.get("subtitle", "")}
                elif ct in ("vs_compare", "vs", "compare"):
                    sb["visual_element"] = "vs_compare"
                    sb["visual_data"] = {"left": cspec.get("left", {}), "right": cspec.get("right", {}), "vs_text": cspec.get("vs_text", "VS")}

        images = []
        chart_frame_counts = {}  # {scene_index: frame_count} for segment subdivision
        total_scenes = len(storyboard) if storyboard else 1

        # ═══ 真实视频素材获取（Pexels/Pixabay） ═══
        scene_video_map = {}  # {scene_index: local_video_path}
        if storyboard and config.STOCK_VIDEO_SOURCE in ("pexels", "pixabay"):
            try:
                from core.stock_video_module import fetch_stock_videos_for_scenes
                _update(step='fetching_materials')
                scene_video_map = fetch_stock_videos_for_scenes(
                    storyboard=storyboard,
                    audio_duration=duration,
                    orientation=orientation,
                )
            except Exception as e:
                print(f"[StockVideo] 视频素材获取失败（降级为漫画帧）: {e}")
                scene_video_map = {}

        if storyboard:
            for i, scene in enumerate(storyboard):
                title = str(scene.get("title") or f"场景 {i+1}")[:36]
                subtitle = str(scene.get("subtitle") or "")
                bullets = scene.get("bullets") if isinstance(scene.get("bullets"), list) else []
                if not bullets:
                    import re as _re
                    bullets = [s.strip() for s in _re.split(r'(?<=[。！？!?])\s*|\n+', subtitle or script_content) if s.strip()][:8]
                bullets = [str(x).strip() for x in bullets if str(x).strip()] or ["要点讲解"]
                bullets = bullets[:8]
                sfx = str(scene.get("sfx") or "")
                ve = str(scene.get("visual_element") or "")
                vd = scene.get("visual_data") if isinstance(scene.get("visual_data"), dict) else {}

                anim_frames = chart_anim_frames.get(str(i)) or []
                if anim_frames:
                    # 动态图表：每个 chart frame 生成独立的漫画帧 + 要点逐条弹出
                    chart_frame_counts[i] = len(anim_frames)
                    n_anim = len(anim_frames)
                    n_bullets = len(bullets)
                    for fi, chart_fp in enumerate(anim_frames):
                        # 要点逐条弹出：从第2条开始，逐帧增加
                        if n_bullets > 2 and n_anim > 1:
                            vis = min(n_bullets, 2 + int((n_bullets - 2) * fi / max(n_anim - 1, 1)))
                        else:
                            vis = 0  # 0 = 全部显示
                        out = work_dir / f"manga_scene_{i:03d}_f{fi:03d}.png"
                        renderer.render_frame(
                            title=title, bullets=bullets, output_path=str(out),
                            subtitle=subtitle[:200], media_path=chart_fp,
                            scene_index=i, total_scenes=total_scenes, sfx_text=sfx,
                            visual_element=ve, visual_data=vd,
                            visible_bullets=vis,
                        )
                        images.append(str(out))
                else:
                    mp = materials.get(str(i)) or scene.get("material_url")
                    out = work_dir / f"manga_scene_{i:03d}.png"
                    renderer.render_frame(
                        title=title, bullets=bullets, output_path=str(out),
                        subtitle=subtitle[:200], media_path=mp,
                        scene_index=i, total_scenes=total_scenes, sfx_text=sfx,
                        visual_element=ve, visual_data=vd,
                    )
                    images.append(str(out))
                    chart_frame_counts[i] = 1
        else:
            # fallback: 从 script_content 分句生成场景
            import re as _re
            chunks = [s.strip() for s in _re.split(r'(?<=[。！？!?])\s*|\n+', script_content) if s.strip()]
            total_scenes = max(3, min(8, len(chunks) or 3))
            for i in range(total_scenes):
                sub = chunks[i] if i < len(chunks) else "内容要点"
                out = work_dir / f"manga_scene_{i:03d}.png"
                renderer.render_frame(
                    title=f"场景 {i+1}", bullets=[sub], output_path=str(out),
                    subtitle=sub[:200], scene_index=i, total_scenes=total_scenes,
                )
                images.append(str(out))
                chart_frame_counts[i] = 1

        if not images:
            _update(step='failed', status='failed', error_msg='漫画帧生成失败，请检查素材')
            return

        # ═══ 智能节奏控制 + segments 生成 ═══
        # 场景节奏权重：前2个场景(钩子)短快，图表场景长，CTA结尾长
        segments = []
        image_offset = 0
        if storyboard:
            n_scenes = len(storyboard)
            # 计算每个场景的节奏权重
            weights = []
            for i, sb in enumerate(storyboard):
                ve = str(sb.get("visual_element") or "")
                has_chart = bool(chart_anim_frames.get(str(i)))
                if i < 2 and not has_chart:
                    weights.append(0.7)   # 钩子：快节奏
                elif has_chart or ve in ("big_number", "vs_compare"):
                    weights.append(1.35)  # 数据/图表：慢，给观众消化时间
                elif i >= n_scenes - 1:
                    weights.append(1.2)   # CTA结尾：略慢
                else:
                    weights.append(1.0)
            weight_sum = sum(weights)
            time_base = 0.0
            for i, sb in enumerate(storyboard):
                scene_dur = duration * weights[i] / weight_sum
                n_frames = chart_frame_counts.get(i, 1)
                sub_dur = scene_dur / n_frames
                ve = str(sb.get("visual_element") or "")
                has_chart = bool(chart_anim_frames.get(str(i)))
                # 确定强调效果
                if ve == "big_number":
                    emphasis = "big_number"
                elif has_chart and i > 0:
                    emphasis = "chart_done"
                elif i == 0:
                    emphasis = "hook"
                elif i >= n_scenes - 1:
                    emphasis = "cta"
                else:
                    emphasis = None

                for fi in range(n_frames):
                    seg = {
                        'start': time_base + fi * sub_dur,
                        'end': time_base + (fi + 1) * sub_dur,
                        'text': sb.get('subtitle', sb.get('text', '')),
                        'image_index': image_offset + fi,
                        'emphasis': emphasis if fi == n_frames - 1 else None,
                        'media_type': 'image',
                        'video_path': '',
                    }
                    # 有真实视频素材的场景（仅非图表帧场景使用视频）
                    if i in scene_video_map and not has_chart and fi == 0:
                        seg['media_type'] = 'video'
                        seg['video_path'] = scene_video_map[i]
                    segments.append(seg)
                time_base += scene_dur
                image_offset += n_frames
        else:
            for i in range(len(images)):
                seg_dur = duration / max(len(images), 1)
                segments.append({
                    'start': i * seg_dur,
                    'end': (i + 1) * seg_dur,
                    'text': '',
                    'image_index': i,
                    'emphasis': 'hook' if i == 0 else ('cta' if i == len(images) - 1 else None),
                })

        # Step: 动画视频（xfade 转场 + 强调动效 + 电影调色）
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
            transition="fadegrays",
            film_look=True,
        )
        if not anim_ok:
            _update(step='failed', status='failed', error_msg='动画视频生成失败')
            return

        # Step: 字幕 (漫画帧已自带文字排版，跳过 drawtext 烧录避免双层字)
        if animation_style == "manga_frame":
            srt_path = None
        else:
            from core.subtitle_module import get_subtitle_module
            subtitle_mod = get_subtitle_module()
            srt_path = str(work_dir / "subtitle.srt")
            subtitle_mod.generate_srt(segments, srt_path)

        # Step: 多轨道合成 (TTS + BGM)
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

        # Step: 音效混合 (ding/whoosh/emphasis 混入音轨)
        try:
            from core.sfx_module import generate_sfx_for_scenes, mix_sfx_to_video
            sfx_map = generate_sfx_for_scenes(segments, str(work_dir / "sfx"))
            if sfx_map:
                sfx_output = str(work_dir / "sfx_mixed.mp4")
                mixed = mix_sfx_to_video(final_video_path, tts_audio_path, sfx_map, bgm_path, sfx_output)
                if mixed != final_video_path and Path(mixed).exists():
                    # 替换为含音效的版本
                    import shutil as _shutil
                    _shutil.move(mixed, final_video_path)
        except Exception as e:
            print(f"[SFX] 音效混合失败（非致命）: {e}")

        _update(step='done', status='done', video_path=final_video_path)
        print(f"[Render] {table_name} video_id={video_id} done: {final_video_path}")

    except Exception as e:
        traceback.print_exc()
        _update(step='failed', status='failed', error_msg=str(e))
        print(f"[Render] {table_name} video_id={video_id} exception: {e}")
