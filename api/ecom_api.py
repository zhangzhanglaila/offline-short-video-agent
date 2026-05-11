# -*- coding: utf-8 -*-
"""
电商 API 路由 - 商品管理、带货视频生成、数据分析
"""
import sys
import os
import json
import re
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

router = APIRouter()


def _video_path_to_url(video_path: str) -> str:
    """将绝对文件路径转换为 /static/output/... URL。"""
    if not video_path:
        return ''
    normalized = video_path.replace('\\', '/')
    output_dir = str(config.OUTPUT_DIR).replace('\\', '/')
    if normalized.startswith(output_dir):
        relative = normalized[len(output_dir):].lstrip('/')
        return f'/static/output/{relative}'
    return normalized


def _split_sentences(text: str) -> list[str]:
    chunks = [s.strip() for s in re.split(r'(?<=[。！？!?])\s*|\n+', text or "") if s.strip()]
    return chunks


def _to_text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (list, tuple)):
        return " ".join([_to_text(x) for x in v if _to_text(x)]).strip()
    if isinstance(v, dict):
        return " ".join([_to_text(x) for x in v.values() if _to_text(x)]).strip()
    return str(v).strip()


def _normalize_script_result(script_result: dict) -> dict:
    normalized = dict(script_result or {})
    normalized["hook"] = _to_text(normalized.get("hook"))
    normalized["body"] = _to_text(normalized.get("body"))
    normalized["cta"] = _to_text(normalized.get("cta"))
    full_script = _to_text(normalized.get("full_script"))
    if not full_script:
        full_script = " ".join(
            part for part in (normalized["hook"], normalized["body"], normalized["cta"]) if part
        ).strip()
    normalized["full_script"] = full_script
    return normalized


def _extract_bullets(text: str, max_items: int = 4) -> list[str]:
    candidates = [s.strip("，。；;、 ") for s in re.split(r"[，。；;、\n]", text or "") if s.strip("，。；;、 ")]
    return candidates[:max_items] if candidates else [text.strip()[:24]] if text.strip() else []


def _normalize_storyboard(script_result: dict, duration: int) -> list[dict]:
    hook = _to_text(script_result.get("hook"))
    body = _to_text(script_result.get("body"))
    cta = _to_text(script_result.get("cta"))
    full_script = _to_text(script_result.get("full_script"))
    raw_storyboard = script_result.get("storyboard") or []
    if not isinstance(raw_storyboard, list):
        raw_storyboard = []

    scenes: list[dict] = []
    for idx, item in enumerate(raw_storyboard):
        if not isinstance(item, dict):
            continue
        subtitle = _to_text(item.get("subtitle") or item.get("字幕要点") or item.get("text"))
        if not subtitle:
            subtitle = _to_text(item.get("scene") or item.get("画面描述"))
        title = _to_text(item.get("title") or item.get("scene") or item.get("画面描述") or f"场景 {idx + 1}")
        bullets = [str(x).strip() for x in item.get("bullets", []) if str(x).strip()] if isinstance(item.get("bullets"), list) else _extract_bullets(subtitle)
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
        chunks = _split_sentences(full_script)
        scene_count = max(3, min(8, len(chunks) or 3))
        if not chunks:
            chunks = [hook, body, cta]
        chunks = [c for c in chunks if c and c.strip()]
        while len(chunks) < scene_count:
            chunks.append(chunks[-1] if chunks else "产品亮点介绍")
        chunks = chunks[:scene_count]

        ordered = []
        if hook:
            ordered.append(("Hook", hook))
        if body:
            for i, b in enumerate(_split_sentences(body), start=1):
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
                "bullets": _extract_bullets(text),
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
        s["bullets"] = s.get("bullets") or _extract_bullets(s.get("subtitle", ""))
    return scenes


def _ensure_storyboard_placeholders(video_id: int, storyboard: list[dict], script_content: str) -> list[dict]:
    """Generate comic-style placeholders for scenes without material_url."""
    scene_dir = config.OUTPUT_DIR / "storyboard" / f"video_{video_id}"
    scene_dir.mkdir(parents=True, exist_ok=True)
    generated = _generate_comic_placeholders(storyboard or [], script_content, scene_dir)
    idx = 0
    for i, scene in enumerate(storyboard):
        if scene.get("material_url"):
            continue
        if idx < len(generated):
            local_path = generated[idx]
            scene["material_url"] = _video_path_to_url(local_path)
            idx += 1
    return storyboard


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
            INSERT INTO ecom_videos (product_id, platform, style, script_content, storyboard, status, pipeline_step, prompt_snapshot, llm_model, duration, animation_style)
            VALUES (?, ?, ?, ?, ?, 'script_ready', 'script_ready', ?, ?, ?, ?)
        """, (
            product_id, platform, style,
            script_result.get('full_script', ''),
            json.dumps(normalized_storyboard, ensure_ascii=False),
            prompt,
            config.OPENAI_MODEL,
            duration,
            animation_style if animation_style in ('contain', 'side', 'comic_explain') else 'comic_explain',
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
    if animation_style in ("contain", "side"):
        try:
            conn = sqlite3.connect(get_db_path())
            conn.execute("UPDATE ecom_videos SET animation_style=? WHERE id=?", (animation_style, video_id))
            conn.commit()
            conn.close()
        except Exception:
            pass

    thread = threading.Thread(target=_run_render_pipeline, args=(video_id,), daemon=True)
    thread.start()

    return JSONResponse({'success': True, 'video_id': video_id})


def _generate_text_placeholders(storyboard, script_content, work_dir):
    """无素材时，为每个分镜生成纯色背景+文字的占位图。"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return []

    # 配色方案
    palettes = [
        ((251, 114, 153), (255, 255, 255)),  # 粉底白字
        ((35, 37, 41), (255, 255, 255)),      # 深底白字
        ((82, 196, 26), (255, 255, 255)),     # 绿底白字
        ((24, 144, 255), (255, 255, 255)),    # 蓝底白字
        ((250, 173, 20), (35, 37, 41)),       # 黄底深字
        ((114, 46, 209), (255, 255, 255)),    # 紫底白字
    ]

    # 加载字体
    font = None
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, 36)
            break
        except Exception:
            continue
    if font is None:
        try:
            font = ImageFont.load_default()
        except Exception:
            return []

    w, h = 1280, 720
    images = []
    scenes = storyboard if storyboard else [{'subtitle': s} for s in script_content.split('。') if s.strip()]

    for i, sb in enumerate(scenes):
        bg_color, text_color = palettes[i % len(palettes)]
        img = Image.new('RGB', (w, h), bg_color)
        draw = ImageDraw.Draw(img)

        # 文字内容
        text = sb.get('subtitle', '') or sb.get('text', '') or sb.get('scene', '') or script_content[:60]

        # 自动换行
        lines = []
        line = ''
        for ch in text:
            line += ch
            bbox = draw.textbbox((0, 0), line, font=font)
            if bbox[2] > w - 120:
                lines.append(line[:-1])
                line = ch
        if line:
            lines.append(line)

        # 居中绘制
        line_h = 50
        total_h = len(lines) * line_h
        y = (h - total_h) // 2
        for ln in lines[:6]:
            bbox = draw.textbbox((0, 0), ln, font=font)
            tw = bbox[2] - bbox[0]
            x = (w - tw) // 2
            draw.text((x, y), ln, fill=text_color, font=font)
            y += line_h

        # 场景编号
        num_text = f"{i + 1}/{len(scenes)}"
        draw.text((w - 100, 30), num_text, fill=(*text_color[:3], 150), font=font)

        out_path = str(work_dir / f"placeholder_{i}.png")
        img.save(out_path)
        images.append(out_path)

    return images


def _generate_comic_placeholders(storyboard, script_content, work_dir):
    """Render comic-style placeholder frames with title, bullets and subtitle."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return _generate_text_placeholders(storyboard, script_content, work_dir)

    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    font_title = None
    font_body = None
    for fp in ("C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"):
        try:
            font_title = ImageFont.truetype(fp, 48)
            font_body = ImageFont.truetype(fp, 34)
            break
        except Exception:
            continue
    if font_title is None or font_body is None:
        try:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
        except Exception:
            return _generate_text_placeholders(storyboard, script_content, work_dir)

    scenes = storyboard if storyboard else [{"title": f"场景 {i+1}", "subtitle": s, "bullets": _extract_bullets(s)} for i, s in enumerate(_split_sentences(script_content))]
    if not scenes:
        scenes = [{"title": "场景 1", "subtitle": "内容介绍", "bullets": ["内容介绍"]}]

    w, h = 1280, 720
    palettes = [
        ((250, 251, 252), (247, 227, 236), (251, 114, 153)),
        ((245, 246, 247), (233, 245, 236), (82, 196, 26)),
        ((250, 251, 252), (232, 242, 252), (24, 144, 255)),
    ]
    out = []
    for i, sb in enumerate(scenes):
        bg, panel, accent = palettes[i % len(palettes)]
        img = Image.new("RGB", (w, h), bg)
        draw = ImageDraw.Draw(img)
        title = str((sb.get("title") or f"场景 {i+1}")).strip()[:30]
        subtitle = str((sb.get("subtitle") or "")).strip()
        bullets = sb.get("bullets") if isinstance(sb.get("bullets"), list) else _extract_bullets(subtitle)
        bullets = [str(x).strip() for x in bullets if str(x).strip()][:4] or ["要点说明"]

        draw.rounded_rectangle([36, 30, w - 36, h - 30], radius=24, outline=accent, width=6, fill=bg)
        draw.rounded_rectangle([70, 64, w - 70, 184], radius=18, outline=accent, width=4, fill=(255, 255, 255))
        draw.text((96, 96), title, fill=(32, 35, 42), font=font_title)

        y = 220
        for b in bullets:
            draw.rounded_rectangle([86, y, w - 86, y + 96], radius=14, outline=(219, 225, 232), width=2, fill=panel)
            draw.text((112, y + 28), f"• {b[:34]}", fill=(43, 47, 55), font=font_body)
            y += 110

        if subtitle:
            draw.rounded_rectangle([86, h - 120, w - 86, h - 56], radius=12, outline=(219, 225, 232), width=2, fill=(255, 255, 255))
            draw.text((110, h - 102), subtitle[:46], fill=(95, 102, 112), font=font_body)

        draw.text((w - 180, 36), f"{i+1}/{len(scenes)}", fill=accent, font=font_body)
        p = work_dir / f"comic_scene_{i}.png"
        img.save(p)
        out.append(str(p))
    return out


def _generate_comic_explain_frames(storyboard, script_content, work_dir, materials=None):
    """Generate horizontal comic-explain frames (text first, media secondary)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return _generate_comic_placeholders(storyboard, script_content, work_dir)

    materials = materials or {}
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    title_font = None
    body_font = None
    for fp in ("C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"):
        try:
            title_font = ImageFont.truetype(fp, 48)
            body_font = ImageFont.truetype(fp, 32)
            break
        except Exception:
            continue
    if title_font is None or body_font is None:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    scenes = storyboard if storyboard else [{"title": "讲解", "subtitle": script_content[:80], "bullets": _extract_bullets(script_content)}]
    w, h = 1280, 720
    outputs = []
    for i, scene in enumerate(scenes):
        bg = Image.new("RGB", (w, h), (248, 250, 252))
        draw = ImageDraw.Draw(bg)

        def _fit_text(text: str, font, max_width: int, prefix: str = "") -> str:
            """Trim text by rendered width so long copy stays inside comic panels."""
            text = str(text or "").replace("\n", " ").strip()
            suffix = "..."
            if draw.textlength(prefix + text, font=font) <= max_width:
                return prefix + text
            available = max_width - draw.textlength(prefix + suffix, font=font)
            if available <= 0:
                return prefix + suffix
            lo, hi = 0, len(text)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if draw.textlength(text[:mid], font=font) <= available:
                    lo = mid
                else:
                    hi = mid - 1
            return prefix + text[:lo].rstrip() + suffix

        # comic background accents
        draw.rectangle([0, 0, w, 110], fill=(242, 245, 249))
        draw.rectangle([0, h - 70, w, h], fill=(245, 247, 250))
        draw.rounded_rectangle([24, 24, w - 24, h - 24], radius=20, outline=(251, 114, 153), width=4, fill=(250, 251, 252))

        # left explain panel
        lx0, ly0, lx1, ly1 = 46, 46, 860, 674
        draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=18, fill=(255, 255, 255), outline=(236, 220, 228), width=3)

        title = str(scene.get("title") or f"场景 {i+1}")[:28]
        subtitle = _fit_text(str(scene.get("subtitle") or "summary"), body_font, 700)
        bullets = scene.get("bullets") if isinstance(scene.get("bullets"), list) else _extract_bullets(subtitle)
        bullets = [_fit_text(x, body_font, 690).strip() for x in bullets]
        bullets = [str(x).strip() for x in bullets if str(x).strip()][:4] or ["要点讲解"]

        draw.rounded_rectangle([70, 72, 836, 154], radius=12, fill=(255, 244, 248), outline=(251, 114, 153), width=2)
        draw.text((92, 92), _fit_text(title, title_font, 720), fill=(34, 36, 42), font=title_font)

        y = 186
        for b in bullets:
            draw.rounded_rectangle([78, y, 832, y + 96], radius=12, fill=(247, 250, 253), outline=(220, 226, 233), width=2)
            draw.text((104, y + 28), f"• {b[:34]}", fill=(44, 48, 56), font=body_font)
            y += 108

        draw.rounded_rectangle([78, 620, 832, 664], radius=10, fill=(252, 252, 252), outline=(222, 226, 232), width=2)
        draw.text((98, 632), subtitle[:44] if subtitle else "辅助讲解", fill=(92, 99, 109), font=body_font)

        # right media panel (secondary)
        rx0, ry0, rx1, ry1 = 886, 96, 1238, 620
        draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=16, fill=(255, 255, 255), outline=(220, 226, 233), width=3)
        draw.text((922, 58), "素材辅助", fill=(117, 124, 136), font=body_font)

        media_img = None
        mp = materials.get(str(i))
        if mp and Path(mp).exists():
            try:
                media_img = Image.open(mp).convert("RGB")
            except Exception:
                media_img = None
        if media_img is None and scene.get("material_url"):
            p = str(scene.get("material_url"))
            if p.startswith("/static/output/"):
                local = config.OUTPUT_DIR / p.replace("/static/output/", "")
                if local.exists():
                    try:
                        media_img = Image.open(local).convert("RGB")
                    except Exception:
                        media_img = None
        if media_img is not None:
            media_img.thumbnail((rx1 - rx0 - 26, ry1 - ry0 - 26))
            px = rx0 + ((rx1 - rx0) - media_img.width) // 2
            py = ry0 + ((ry1 - ry0) - media_img.height) // 2
            bg.paste(media_img, (px, py))
            draw.rounded_rectangle([px - 4, py - 4, px + media_img.width + 4, py + media_img.height + 4], radius=8, outline=(251, 114, 153), width=2)
        else:
            draw.rounded_rectangle([rx0 + 24, ry0 + 24, rx1 - 24, ry1 - 24], radius=12, fill=(246, 248, 250), outline=(210, 218, 228), width=2)
            draw.text((rx0 + 72, (ry0 + ry1) // 2 - 16), "无素材", fill=(137, 146, 160), font=body_font)

        draw.text((w - 148, 28), f"{i+1}/{len(scenes)}", fill=(251, 114, 153), font=body_font)
        out = work_dir / f"explain_scene_{i}.png"
        bg.save(out)
        outputs.append(str(out))

    return outputs


def _run_render_pipeline(video_id: int):
    """后台线程: 动画 → 字幕 → 多轨道合成。"""
    import sqlite3
    import traceback
    from core.db_init import get_db_path

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
            conn.execute(f"UPDATE ecom_videos SET {','.join(sets)} WHERE id=?", params)
            conn.commit()
        finally:
            conn.close()

    try:
        # 读取 DB 数据
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ecom_videos WHERE id = ?", (video_id,))
        row = dict(cursor.fetchone())
        conn.close()

        script_content = row['script_content']
        storyboard_str = row['storyboard'] or '[]'
        tts_audio_path = row['tts_audio_path']
        materials_str = row['materials_json'] or '{}'
        duration = row['duration'] or 30
        animation_style = row.get('animation_style') or 'contain'

        storyboard = json.loads(storyboard_str)
        materials = json.loads(materials_str)

        work_dir = config.OUTPUT_DIR / "_work" / f"ecom_{video_id}"
        work_dir.mkdir(parents=True, exist_ok=True)

        # 准备素材: 优先用用户上传的，缺失的自动抓取
        from core.dual_mode_module import DualModeVideoGenerator
        from core.image_fetch_module import get_image_fetch_module
        from core.tts_module import TTSModule

        image_fetch = get_image_fetch_module()

        # 讲解风：优先生成漫画讲解帧（文字主导，素材次要）
        images = _generate_comic_explain_frames(storyboard, script_content, work_dir, materials=materials)
        if not images:
            # fallback
            images = _generate_comic_placeholders(storyboard, script_content, work_dir)
            if not images:
                _update(step='failed', status='failed', error_msg='无可用素材，请上传分镜素材')
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
            # 空分镜时，按图片数量均分时长
            seg_duration = duration / max(len(images), 1)
            for i in range(len(images)):
                segments.append({
                    'start': i * seg_duration,
                    'end': (i + 1) * seg_duration,
                    'text': '',
                    'image_index': i,
                })

        # Step: 动画视频
        _update(step='rendering')
        from core.animation_module import get_animation_module
        animation = get_animation_module()
        # 强制横屏生成
        animation.output_width = 1280
        animation.output_height = 720

        raw_video_path = str(work_dir / "raw_video.mp4")
        anim_ok = animation.create_animated_video_from_segments(
            images=images,
            segments=segments,
            output_path=raw_video_path,
            animation_style="ken_burns" if animation_style == "side" else "static",
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
        print(f"[EcomRender] video_id={video_id} done: {final_video_path}")

    except Exception as e:
        traceback.print_exc()
        _update(step='failed', status='failed', error_msg=str(e))
        print(f"[EcomRender] video_id={video_id} exception: {e}")


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
    })
