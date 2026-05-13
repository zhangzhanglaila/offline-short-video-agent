# -*- coding: utf-8 -*-
"""
素材智能剪辑 API 路由 (原双模式生成)
Mode A 已迁移至 topic_pipeline_api.py
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


def get_generator():
    from core.dual_mode_module import get_dual_mode_generator
    return get_dual_mode_generator()


@router.post("/api/generate/mode-b")
async def api_generate_mode_b(request: Request):
    """
    素材智能剪辑

    请求体:
    {
        "material_paths": ["path/to/img1.jpg", "path/to/img2.png"],
        "platform": "抖音",
        "transition": "fade",
        "add_bgm": true,
        "add_subtitles": true,
        "use_whisper": false,
        "duration_per_image": 4
    }
    """
    try:
        data = await request.json()

        material_paths = data.get("material_paths", [])
        platform = data.get("platform", "抖音")
        transition = data.get("transition", "fade")
        add_bgm = data.get("add_bgm", True)
        add_subtitles = data.get("add_subtitles", True)
        use_whisper = data.get("use_whisper", False)
        duration_per_image = data.get("duration_per_image", 4)

        if not material_paths:
            return JSONResponse({
                "success": False,
                "error": "素材路径不能为空"
            }, status_code=400)

        generator = get_generator()

        result = generator.generate_mode_b(
            material_paths=material_paths,
            platform=platform,
            transition=transition,
            add_bgm=add_bgm,
            add_subtitles=add_subtitles,
            use_whisper=use_whisper,
            duration_per_image=duration_per_image,
        )

        return JSONResponse(result)

    except Exception as e:
        import traceback
        return JSONResponse({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }, status_code=500)
