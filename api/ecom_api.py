# -*- coding: utf-8 -*-
"""
电商 API 路由 - 商品管理、带货视频生成、数据分析
"""
import sys
import os
import json
from pathlib import Path

from fastapi import APIRouter, Query, UploadFile, File
from fastapi.responses import JSONResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.product_module import (
    create_product, get_product, list_products, update_product, delete_product,
    get_product_categories, get_product_stats,
)
from core.ecom_adapter import product_to_topic, build_ecom_prompt, ECOM_STYLES, PLATFORM_MAP
from core.pipeline_helpers import (
    video_path_to_url as _video_path_to_url,
    split_sentences as _split_sentences,
    to_text as _to_text,
    normalize_script_result as _normalize_script_result,
    extract_bullets as _extract_bullets,
    normalize_storyboard as _normalize_storyboard,
    ensure_storyboard_placeholders as _ensure_storyboard_placeholders,
    generate_manga_frames as _generate_manga_frames,
    run_render_pipeline as _run_render_pipeline_shared,
)

router = APIRouter()


def _run_render_pipeline(video_id: int):
    """后台线程: 动画 → 字幕 → 多轨道合成。"""
    _run_render_pipeline_shared(video_id, table_name="ecom_videos")


# ==================== 商品 CRUD ====================

@router.post("/api/ecom/products")
async def api_create_product(data: dict):
    """创建商品。"""
    try:
        if not data.get('name'):
            return JSONResponse({'error': '商品名称不能为空'}, status_code=400)
        product_id = create_product(data)
        return JSONResponse({'id': product_id, 'success': True})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.get("/api/ecom/products")
async def api_list_products(
    search: str = Query('', description='搜索关键词'),
    category: str = Query('', description='分类筛选'),
    platform: str = Query('', description='平台筛选'),
    status: str = Query('', description='状态筛选'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """商品列表。"""
    try:
        result = list_products(
            search=search, category=category, platform=platform,
            status=status, page=page, page_size=page_size,
        )
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.get("/api/ecom/products/categories")
async def api_product_categories():
    """获取所有商品分类。"""
    try:
        categories = get_product_categories()
        return JSONResponse({'categories': categories})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.get("/api/ecom/products/stats")
async def api_product_stats():
    """商品统计概览。"""
    try:
        stats = get_product_stats()
        return JSONResponse(stats)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.get("/api/ecom/products/{product_id}")
async def api_get_product(product_id: int):
    """获取单个商品详情。"""
    try:
        product = get_product(product_id)
        if not product:
            return JSONResponse({'error': '商品不存在'}, status_code=404)
        return JSONResponse(product)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.put("/api/ecom/products/{product_id}")
async def api_update_product(product_id: int, data: dict):
    """更新商品。"""
    try:
        success = update_product(product_id, data)
        if not success:
            return JSONResponse({'error': '商品不存在或无更新字段'}, status_code=404)
        return JSONResponse({'success': True})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.delete("/api/ecom/products/{product_id}")
async def api_delete_product(product_id: int):
    """删除商品。"""
    try:
        success = delete_product(product_id)
        if not success:
            return JSONResponse({'error': '商品不存在'}, status_code=404)
        return JSONResponse({'success': True})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


# ==================== 分步可控管线 ====================

@router.post("/api/ecom/generate")
async def api_ecom_generate(data: dict):
    """
    Step 1: 生成脚本（不启动视频管线）。
    入参: {product_id, style, platform, duration}
    返回: {success, video_id, script}
    """
    from core.db_init import get_db_path
    import sqlite3

    product_id = data.get('product_id')
    if not product_id:
        return JSONResponse({'error': '请选择商品'}, status_code=400)

    product = get_product(product_id)
    if not product:
        return JSONResponse({'error': '商品不存在'}, status_code=404)

    selling_points = product.get('selling_points', [])
    if isinstance(selling_points, str):
        try:
            selling_points = json.loads(selling_points)
        except json.JSONDecodeError:
            selling_points = []
    if not selling_points or len(selling_points) == 0:
        return JSONResponse({'error': '该商品缺少核心卖点，请先编辑商品补充卖点信息'}, status_code=400)

    style = data.get('style', 'soft_sell')
    animation_style = data.get('animation_style', 'comic_explain')
    platform = data.get('platform', 'TikTok')
    duration = data.get('duration', 30)
    orientation = data.get('orientation', 'portrait')
    visual_style = data.get('visual_style', 'manga')
    video_width, video_height = config.get_output_dimensions(orientation)

    prompt = build_ecom_prompt(product, style, platform, duration)
    topic = product_to_topic(product, style)

    try:
        from core.script_module import generate_script
        script_result = generate_script(topic, PLATFORM_MAP.get(platform, '抖音'), duration)
    except Exception as e:
        return JSONResponse({'error': f'脚本生成失败: {str(e)}'}, status_code=500)

    if 'error' in script_result:
        return JSONResponse({'error': f'LLM 生成失败: {script_result["error"]}'}, status_code=500)

    script_result = _normalize_script_result(script_result)

    if not script_result.get('full_script'):
        return JSONResponse({'error': 'LLM 返回空内容，请检查 API Key 是否有效或稍后重试'}, status_code=500)

    normalized_storyboard = _normalize_storyboard(script_result, int(duration))
    conn = sqlite3.connect(get_db_path())
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN")
        cursor.execute("""
            INSERT INTO ecom_videos (product_id, platform, style, script_content, storyboard, status, pipeline_step, prompt_snapshot, llm_model, duration, animation_style, orientation, video_width, video_height, visual_style)
            VALUES (?, ?, ?, ?, ?, 'script_ready', 'script_ready', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_id, platform, style,
            script_result.get('full_script', ''),
            json.dumps(normalized_storyboard, ensure_ascii=False),
            prompt,
            config.OPENAI_MODEL,
            duration,
            animation_style if animation_style in ('contain', 'side', 'comic_explain') else 'comic_explain',
            orientation,
            video_width,
            video_height,
            visual_style if visual_style in config.VISUAL_STYLES else 'manga',
        ))
        video_id = cursor.lastrowid
        normalized_storyboard = _ensure_storyboard_placeholders(video_id, normalized_storyboard, script_result.get('full_script', ''))
        cursor.execute("UPDATE ecom_videos SET storyboard=? WHERE id=?", (json.dumps(normalized_storyboard, ensure_ascii=False), video_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return JSONResponse({'error': f'数据库写入失败: {str(e)}'}, status_code=500)
    finally:
        conn.close()

    return JSONResponse({
        'success': True,
        'video_id': video_id,
        'script': {**script_result, 'storyboard': normalized_storyboard},
    })


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


# ==================== 视频列表 ====================

@router.get("/api/ecom/videos")
async def api_ecom_videos(
    product_id: int = Query(None, description='按商品筛选'),
    status: str = Query('', description='状态筛选'),
    platform: str = Query('', description='平台筛选'),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """电商视频列表。"""
    try:
        from core.db_init import get_db_path
        import sqlite3
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions = []
        params = []
        if product_id:
            conditions.append("v.product_id = ?")
            params.append(product_id)
        if status:
            conditions.append("v.status = ?")
            params.append(status)
        if platform:
            conditions.append("v.platform = ?")
            params.append(platform)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ''

        cursor.execute(f"SELECT COUNT(*) FROM ecom_videos v {where}", params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * page_size
        cursor.execute(f"""
            SELECT v.*, p.name as product_name, p.price as product_price, p.images as product_images
            FROM ecom_videos v
            LEFT JOIN products p ON v.product_id = p.id
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
            if d.get('product_images') and isinstance(d['product_images'], str):
                try:
                    d['product_images'] = json.loads(d['product_images'])
                except json.JSONDecodeError:
                    d['product_images'] = []
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
        cursor.execute("""
            SELECT v.*, p.name as product_name, p.price as product_price
            FROM ecom_videos v
            LEFT JOIN products p ON v.product_id = p.id
            WHERE v.id = ?
        """, (video_id,))
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

        # 收集所有文件路径
        cursor.execute("SELECT video_path, thumbnail_path FROM ecom_videos")
        rows = cursor.fetchall()

        # 删除数据库记录
        cursor.execute("DELETE FROM ecom_videos")
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        # 删除文件系统文件
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

        # 先查询文件路径
        cursor.execute("SELECT video_path, thumbnail_path FROM ecom_videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return JSONResponse({'error': '视频不存在'}, status_code=404)

        video_path = row['video_path'] or ''
        thumb_path = row['thumbnail_path'] or ''

        # 删除数据库记录
        cursor.execute("DELETE FROM ecom_videos WHERE id = ?", (video_id,))
        conn.commit()
        conn.close()

        # 删除文件系统文件
        for fpath in (video_path, thumb_path):
            if fpath and Path(fpath).exists():
                try:
                    Path(fpath).unlink()
                except OSError:
                    pass

        return JSONResponse({'success': True})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


# ==================== 分析数据 ====================

@router.get("/api/ecom/analytics")
async def api_ecom_analytics(
    video_id: int = Query(None, description='按视频筛选'),
    product_id: int = Query(None, description='按商品筛选'),
):
    """获取分析数据。"""
    try:
        from core.db_init import get_db_path
        import sqlite3
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions = []
        params = []
        if video_id:
            conditions.append("a.video_id = ?")
            params.append(video_id)
        if product_id:
            conditions.append("v.product_id = ?")
            params.append(product_id)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ''

        cursor.execute(f"""
            SELECT a.*, v.product_id, v.style, v.platform as video_platform
            FROM ecom_analytics a
            LEFT JOIN ecom_videos v ON a.video_id = v.id
            {where}
            ORDER BY a.recorded_at DESC
        """, params)

        items = [dict(row) for row in cursor.fetchall()]

        # 聚合指标
        total_impressions = sum(i.get('impressions', 0) for i in items)
        total_clicks = sum(i.get('clicks', 0) for i in items)
        total_conversions = sum(i.get('conversions', 0) for i in items)
        total_revenue = sum(i.get('revenue', 0) for i in items)
        avg_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
        avg_completion = sum(i.get('completion_rate', 0) for i in items) / len(items) if items else 0

        conn.close()
        return JSONResponse({
            'items': items,
            'aggregated': {
                'impressions': total_impressions,
                'clicks': total_clicks,
                'conversions': total_conversions,
                'revenue': total_revenue,
                'ctr': avg_ctr,
                'completion_rate': avg_completion,
                'video_count': len(items),
            }
        })
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.post("/api/ecom/analytics")
async def api_create_analytics(data: dict):
    """录入分析数据。"""
    try:
        video_id = data.get('video_id')
        if not video_id:
            return JSONResponse({'error': 'video_id 必填'}, status_code=400)

        from core.db_init import get_db_path
        import sqlite3
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ecom_analytics (video_id, platform, impressions, clicks, ctr, conversions, conversion_rate, revenue, avg_watch_time, completion_rate, engagement_rate, notes, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_id,
            data.get('platform', ''),
            data.get('impressions', 0),
            data.get('clicks', 0),
            data.get('ctr', 0.0),
            data.get('conversions', 0),
            data.get('conversion_rate', 0.0),
            data.get('revenue', 0.0),
            data.get('avg_watch_time', 0.0),
            data.get('completion_rate', 0.0),
            data.get('engagement_rate', 0.0),
            data.get('notes', ''),
            data.get('recorded_at', ''),
        ))
        analytics_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return JSONResponse({'id': analytics_id, 'success': True})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@router.get("/api/ecom/analytics/insights")
async def api_ecom_insights(product_id: int = Query(None)):
    """AI 洞察 - 基于分析数据给出优化建议。"""
    try:
        from core.db_init import get_db_path
        import sqlite3
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if product_id:
            cursor.execute("""
                SELECT a.* FROM ecom_analytics a
                JOIN ecom_videos v ON a.video_id = v.id
                WHERE v.product_id = ?
                ORDER BY a.recorded_at DESC LIMIT 20
            """, (product_id,))
        else:
            cursor.execute("SELECT * FROM ecom_analytics ORDER BY recorded_at DESC LIMIT 20")

        items = [dict(row) for row in cursor.fetchall()]

        product_name = ''
        if product_id:
            cursor.execute("SELECT name FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            if row:
                product_name = row[0]

        conn.close()

        if not items:
            return JSONResponse({'insights': '暂无分析数据，请先录入视频表现数据。'})

        # 调用 LLM 生成洞察
        from core.ecom_adapter import build_insight_prompt
        prompt = build_insight_prompt(items, product_name)

        from config import get_cloud_llm_config
        cfg = get_cloud_llm_config()

        if not cfg.get('api_key'):
            # 无 LLM 时返回规则洞察
            insights = _rule_based_insights(items)
            return JSONResponse({'insights': insights, 'source': 'rule'})

        try:
            import requests as req
            resp = req.post(
                f'{cfg["api_base"]}/chat/completions',
                headers={'Authorization': f'Bearer {cfg["api_key"]}', 'Content-Type': 'application/json'},
                json={'model': cfg['model'], 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 1024, 'temperature': 0.7},
                timeout=30,
                proxies={'http': None, 'https': None},
            )
            result = resp.json()
            content = result['choices'][0]['message']['content']
            return JSONResponse({'insights': content, 'source': 'llm'})
        except Exception as e:
            insights = _rule_based_insights(items)
            return JSONResponse({'insights': insights, 'source': 'rule', 'llm_error': str(e)})

    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


def _rule_based_insights(items: list) -> str:
    """无 LLM 时的规则洞察。"""
    avg_ctr = sum(i.get('ctr', 0) for i in items) / len(items) if items else 0
    avg_completion = sum(i.get('completion_rate', 0) for i in items) / len(items) if items else 0

    tips = []
    if avg_ctr < 0.03:
        tips.append("【问题】CTR 偏低\n【优化方案】优化视频封面和开头3秒hook，使用更有冲击力的文案")
    if avg_completion < 0.4:
        tips.append("【问题】完播率偏低\n【优化方案】缩短视频时长，加快节奏，在前5秒抛出核心卖点")
    if not tips:
        tips.append("【表现良好】各项指标正常，建议持续产出并A/B测试不同风格")

    return '\n\n'.join(tips)


# ==================== 元数据 ====================

@router.get("/api/ecom/meta")
async def api_ecom_meta():
    """返回电商模块的元数据（风格列表、平台映射等）。"""
    return JSONResponse({
        'styles': ECOM_STYLES,
        'platforms': list(PLATFORM_MAP.keys()),
        'visual_styles': {k: {"name_cn": v["name_cn"], "paper_color": v["paper_color"], "accent_red": v["accent_red"], "text_c": v["text_c"]} for k, v in config.VISUAL_STYLES.items()},
    })
