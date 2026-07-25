# -*- coding: utf-8 -*-
"""
视频管线 API 路由 - 通用的分步可控视频管线（脚本编辑 / TTS / 素材 / 渲染 / 列表）。

历史沿革：本模块原为电商带货专属，现已去除商品/分析逻辑，
成为主题驱动统一流程（见 api/topic_video_api.py 的 /api/generate）的下游管线。
路由前缀保留 /api/ecom/videos 以兼容现有前端与主应用注册。
"""
import sys
import os
import json
from pathlib import Path

from fastapi import APIRouter, Query, UploadFile, File
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.pipeline_helpers import (
    video_path_to_url as _video_path_to_url,
    to_text as _to_text,
    normalize_storyboard as _normalize_storyboard,
    ensure_storyboard_placeholders as _ensure_storyboard_placeholders,
    run_render_pipeline as _run_render_pipeline_shared,
)

router = APIRouter()


def _run_render_pipeline(video_id: int):
    """后台线程: 动画 → 字幕 → 多轨道合成。"""
    _run_render_pipeline_shared(video_id, table_name="ecom_videos")


# ==================== 分步可控管线 ====================

@router.put("/api/ecom/videos/{video_id}/script")
async def api_update_script(video_id: int, data: dict):
    """Step 2: 保存用户编辑后的脚本。"""
    from core.db_init import get_db_path
    import sqlite3

    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT pipeline_step FROM ecom_videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse({'error': '视频不存在'}, status_code=404)
        if row['pipeline_step'] not in ('script_ready', 'script_edited'):
            return JSONResponse({'error': f'当前状态不允许编辑脚本: {row["pipeline_step"]}'}, status_code=400)

        script_content = _to_text(data.get("full_script", ""))
        normalized_storyboard = _normalize_storyboard(
            {"full_script": script_content, "storyboard": data.get("storyboard", [])},
            30,
        )
        normalized_storyboard = _ensure_storyboard_placeholders(video_id, normalized_storyboard, script_content)
        cursor.execute("""
            UPDATE ecom_videos SET script_content=?, storyboard=?, pipeline_step='script_edited' WHERE id=?
        """, (
            script_content,
            json.dumps(normalized_storyboard, ensure_ascii=False),
            video_id,
        ))
        conn.commit()
        return JSONResponse({'success': True})
    except Exception as e:
        conn.rollback()
        return JSONResponse({'error': str(e)}, status_code=500)
    finally:
        conn.close()


@router.post("/api/ecom/videos/{video_id}/tts")
async def api_generate_tts(video_id: int, data: dict = None):
    """Step 3: 基于已保存脚本生成 TTS 配音。"""
    from core.db_init import get_db_path
    import sqlite3

    if data is None:
        data = {}

    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT pipeline_step, script_content, duration FROM ecom_videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse({'error': '视频不存在'}, status_code=404)
        if row['pipeline_step'] not in ('script_ready', 'script_edited'):
            return JSONResponse({'error': f'当前状态不允许生成 TTS: {row["pipeline_step"]}'}, status_code=400)

        script_content = row['script_content']
        duration = row['duration'] or 30
    except Exception as e:
        conn.close()
        return JSONResponse({'error': str(e)}, status_code=500)

    voice = data.get('voice', 'zh-CN-XiaoxiaoNeural')
    output_dir = config.OUTPUT_DIR / "ecom"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / f"tts_{video_id}.wav")

    scene_audio_urls = []
    try:
        from core.tts_module import generate_tts_from_script, TTSModule
        cursor = conn.cursor()
        cursor.execute("SELECT storyboard FROM ecom_videos WHERE id = ?", (video_id,))
        sb_row = cursor.fetchone()
        try:
            storyboard = json.loads(sb_row["storyboard"]) if (sb_row and sb_row["storyboard"]) else []
        except Exception:
            storyboard = []
        scene_segments = [{"text": (s.get("subtitle") or s.get("title") or "").strip()} for s in storyboard if (s.get("subtitle") or s.get("title"))]
        if scene_segments:
            scene_dir = output_dir / f"tts_{video_id}_scenes"
            tts = TTSModule(voice)
            ok, scene_files = tts.generate_from_segments(scene_segments, str(scene_dir), voice=voice)
            if ok:
                scene_audio_urls = [f'/api/tts/audio/{Path(p).name}' for p in scene_files]
        success, audio_path = generate_tts_from_script(script_content, output_path, duration, voice)
    except Exception as e:
        return JSONResponse({'error': f'TTS 生成失败: {str(e)}'}, status_code=500)

    if not success or not audio_path:
        return JSONResponse({'error': 'TTS 生成失败，请检查 TTS 配置'}, status_code=500)

    try:
        audio_duration = TTSModule.get_audio_duration(audio_path)
    except Exception:
        audio_duration = 0

    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ecom_videos SET tts_audio_path=?, pipeline_step='tts_ready', status='tts_ready' WHERE id=?
        """, (audio_path, video_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return JSONResponse({'error': f'数据库更新失败: {str(e)}'}, status_code=500)
    finally:
        conn.close()

    audio_filename = Path(audio_path).name
    return JSONResponse({
        'success': True,
        'audio_url': f'/api/tts/audio/{audio_filename}',
        'audio_path': audio_path,
        'duration': audio_duration,
        'scene_audio_urls': scene_audio_urls,
    })


@router.post("/api/ecom/videos/{video_id}/materials")
async def api_upload_material(
    video_id: int,
    scene_index: int = Query(0, description='分镜索引'),
    file: UploadFile = File(...),
):
    """Step 3.5: 上传分镜素材（multipart/form-data）。"""
    from core.db_init import get_db_path
    import sqlite3

    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT pipeline_step, materials_json FROM ecom_videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse({'error': '视频不存在'}, status_code=404)
        if row['pipeline_step'] not in ('script_ready', 'script_edited', 'tts_ready'):
            return JSONResponse({'error': f'当前状态不允许上传素材: {row["pipeline_step"]}'}, status_code=400)
    except Exception as e:
        conn.close()
        return JSONResponse({'error': str(e)}, status_code=500)

    # 保存文件
    save_dir = config.OUTPUT_DIR / "ecom" / f"video_{video_id}"
    save_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"scene_{scene_index}_{file.filename}"
    save_path = save_dir / safe_name

    contents = await file.read()
    save_path.write_bytes(contents)

    # 更新 materials_json
    try:
        materials = {}
        if row['materials_json']:
            try:
                materials = json.loads(row['materials_json'])
            except json.JSONDecodeError:
                pass
        materials[str(scene_index)] = str(save_path)

        cursor = conn.cursor()
        cursor.execute("UPDATE ecom_videos SET materials_json=? WHERE id=?",
                       (json.dumps(materials, ensure_ascii=False), video_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return JSONResponse({'error': f'数据库更新失败: {str(e)}'}, status_code=500)
    finally:
        conn.close()

    return JSONResponse({
        'success': True,
        'path': str(save_path),
        'scene_index': scene_index,
        'url': _video_path_to_url(str(save_path)),
    })


@router.post("/api/ecom/videos/{video_id}/render")
async def api_render_video(video_id: int, data: dict = None):
    """Step 4: 启动视频渲染管线（后台线程）。"""
    import threading
    from core.db_init import get_db_path
    import sqlite3

    if data is None:
        data = {}

    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT pipeline_step FROM ecom_videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse({'error': '视频不存在'}, status_code=404)
        if row['pipeline_step'] != 'tts_ready':
            return JSONResponse({'error': f'当前状态不允许渲染: {row["pipeline_step"]}'}, status_code=400)

        cursor.execute("UPDATE ecom_videos SET pipeline_step='rendering', status='generating' WHERE id=?", (video_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return JSONResponse({'error': str(e)}, status_code=500)
    finally:
        conn.close()

    animation_style = (data or {}).get("animation_style")
    orientation = (data or {}).get("orientation")
    visual_style = (data or {}).get("visual_style")
    if animation_style in ("contain", "side") or orientation in ("portrait", "landscape") or visual_style in config.VISUAL_STYLES:
        try:
            conn = sqlite3.connect(get_db_path())
            params = []
            sets = []
            if animation_style in ("contain", "side"):
                sets.append("animation_style=?")
                params.append(animation_style)
            if visual_style in config.VISUAL_STYLES:
                sets.append("visual_style=?")
                params.append(visual_style)
            if orientation in ("portrait", "landscape"):
                w, h = config.get_output_dimensions(orientation)
                sets.append("orientation=?")
                params.append(orientation)
                sets.append("video_width=?")
                params.append(w)
                sets.append("video_height=?")
                params.append(h)
            params.append(video_id)
            conn.execute(f"UPDATE ecom_videos SET {', '.join(sets)} WHERE id=?", params)
            conn.commit()
            conn.close()
        except Exception:
            pass

    thread = threading.Thread(target=_run_render_pipeline, args=(video_id,), daemon=True)
    thread.start()

    return JSONResponse({'success': True, 'video_id': video_id})


@router.post("/api/ecom/videos/{video_id}/retry-render")
async def api_ecom_retry_render(video_id: int, data: dict = None):
    """Step 4 重试: 从失败状态回退到 tts_ready 后重新触发渲染，保留脚本和配音。"""
    import threading
    from core.db_init import get_db_path
    import sqlite3

    if data is None:
        data = {}

    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT pipeline_step, tts_audio_path FROM ecom_videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse({'error': '视频不存在'}, status_code=404)
        if row['pipeline_step'] != 'failed':
            return JSONResponse({'error': f'当前状态不允许重试: {row["pipeline_step"]}'}, status_code=400)
        if not row['tts_audio_path']:
            return JSONResponse({'error': '配音文件丢失，请重新生成脚本和配音'}, status_code=400)

        cursor.execute("UPDATE ecom_videos SET pipeline_step='rendering', status='generating', notes='' WHERE id=?", (video_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return JSONResponse({'error': str(e)}, status_code=500)
    finally:
        conn.close()

    thread = threading.Thread(target=_run_render_pipeline, args=(video_id,), daemon=True)
    thread.start()

    return JSONResponse({'success': True, 'video_id': video_id})


@router.get("/api/ecom/videos/{video_id}/status")
async def api_ecom_video_status(video_id: int):
    """状态轮询端点（含 pipeline_step）。"""
    try:
        from core.db_init import get_db_path
        import sqlite3
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT status, video_path, notes, pipeline_step, tts_audio_path FROM ecom_videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return JSONResponse({'error': '视频不存在'}, status_code=404)

        d = dict(row)
        resp = {
            'status': d['status'],
            'pipeline_step': d.get('pipeline_step') or d['status'],
        }
        if d.get('video_path'):
            resp['video_url'] = _video_path_to_url(d['video_path'])
            resp['video_path'] = d['video_path']
        if d.get('tts_audio_path'):
            resp['audio_url'] = f'/api/tts/audio/{Path(d["tts_audio_path"]).name}'
        if d.get('notes') and d['status'] == 'failed':
            resp['error'] = d['notes']
        return JSONResponse(resp)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


# ==================== 视频列表 / 历史 ====================

@router.get("/api/ecom/videos")
async def api_ecom_videos(
    status: str = Query('', description='状态筛选'),
    category: str = Query('', description='分类筛选'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """视频历史列表。"""
    try:
        from core.db_init import get_db_path
        import sqlite3
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions = []
        params = []
        if status:
            conditions.append("v.status = ?")
            params.append(status)
        if category:
            conditions.append("v.category = ?")
            params.append(category)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ''

        cursor.execute(f"SELECT COUNT(*) FROM ecom_videos v {where}", params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * page_size
        cursor.execute(f"""
            SELECT v.*
            FROM ecom_videos v
            {where}
            ORDER BY v.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [page_size, offset])

        items = []
        for row in cursor.fetchall():
            d = dict(row)
            if d.get('storyboard') and isinstance(d['storyboard'], str):
                try:
                    d['storyboard'] = json.loads(d['storyboard'])
                except json.JSONDecodeError:
                    d['storyboard'] = []
            d['video_url'] = _video_path_to_url(d.get('video_path', ''))
            items.append(d)

        conn.close()
        return JSONResponse({'items': items, 'total': total, 'page': page, 'page_size': page_size})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.get("/api/ecom/videos/{video_id}")
async def api_ecom_video_detail(video_id: int):
    """视频详情。"""
    try:
        from core.db_init import get_db_path
        import sqlite3
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT v.* FROM ecom_videos v WHERE v.id = ?", (video_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return JSONResponse({'error': '视频不存在'}, status_code=404)

        d = dict(row)
        for key in ('storyboard',):
            if d.get(key) and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except json.JSONDecodeError:
                    d[key] = []
        d['video_url'] = _video_path_to_url(d.get('video_path', ''))
        return JSONResponse(d)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.delete("/api/ecom/videos/all")
async def api_delete_all_videos():
    """删除全部视频（数据库记录 + 文件系统文件）。"""
    try:
        from core.db_init import get_db_path
        import sqlite3
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT video_path, thumbnail_path FROM ecom_videos")
        rows = cursor.fetchall()

        cursor.execute("DELETE FROM ecom_videos")
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        for row in rows:
            for fpath in (row['video_path'] or '', row['thumbnail_path'] or ''):
                if fpath and Path(fpath).exists():
                    try:
                        Path(fpath).unlink()
                    except OSError:
                        pass

        return JSONResponse({'success': True, 'deleted_count': deleted_count})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.delete("/api/ecom/videos/{video_id}")
async def api_delete_video(video_id: int):
    """删除单个视频（数据库记录 + 文件系统文件）。"""
    try:
        from core.db_init import get_db_path
        import sqlite3
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT video_path, thumbnail_path FROM ecom_videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return JSONResponse({'error': '视频不存在'}, status_code=404)

        video_path = row['video_path'] or ''
        thumb_path = row['thumbnail_path'] or ''

        cursor.execute("DELETE FROM ecom_videos WHERE id = ?", (video_id,))
        conn.commit()
        conn.close()

        for fpath in (video_path, thumb_path):
            if fpath and Path(fpath).exists():
                try:
                    Path(fpath).unlink()
                except OSError:
                    pass

        return JSONResponse({'success': True})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)
