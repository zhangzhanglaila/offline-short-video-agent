# -*- coding: utf-8 -*-
"""
漫画帧 + 线条插画 混合风格

左侧：漫画帧（网点纸、气泡框、速度线、文字要点）
右侧：线条插画（机器人、大脑、齿轮等，strokeDashoffset 动画）
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, '.')

import config
config.OUTPUT_WIDTH = 1920
config.OUTPUT_HEIGHT = 1080

from core.manga_frame_renderer import MangaFrameRenderer
from core.lineart_renderer import (
    _draw_illustration, _draw_stroke, _smooth, _path_length, _cut_path,
    _ease_out_cubic, _clamp, _get_font, COLORS, WEIGHT_SCALE,
)
from core.svg_lineart_library import get_illustration, Weight, Stroke


def render_manga_lineart_frame(
    title: str,
    subtitle: str,
    bullets: list,
    lineart_keyword: str,
    canvas_w: int = 1920,
    canvas_h: int = 1080,
    manga_progress: float = 1.0,
    lineart_progress: float = 1.0,
):
    """
    渲染一帧：左侧漫画帧 + 右侧线条插画

    布局：
    ┌────────────────────────────────────────┐
    │ ┌──────────────────┐ ┌──────────────┐ │
    │ │  漫画帧           │ │  线条插画    │ │
    │ │  网点纸背景       │ │  机器人/大脑 │ │
    │ │  气泡框文字       │ │  /齿轮等    │ │
    │ │  速度线装饰       │ │  stroke动画 │ │
    │ │  要点列表         │ │             │ │
    │ └──────────────────┘ └──────────────┘ │
    │ [进度条]                               │
    └────────────────────────────────────────┘
    """
    from PIL import Image, ImageDraw

    # 1. 生成漫画帧（左侧 60%）
    manga_w = int(canvas_w * 0.55)
    renderer = MangaFrameRenderer(width=manga_w, height=canvas_h)

    manga_frame_path = "output/temp_manga_frame.png"
    renderer.render_frame(
        title=title,
        subtitle=subtitle,
        bullets=bullets,
        output_path=manga_frame_path,
        scene_index=0,
        total_scenes=1,
    )

    # 2. 创建完整画布
    img = Image.new("RGB", (canvas_w, canvas_h), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # 3. 粘贴漫画帧到左侧
    manga_img = Image.open(manga_frame_path)
    img.paste(manga_img, (0, 0))

    # 4. 在右侧绘制线条插画
    art = get_illustration(lineart_keyword)
    art_x = canvas_w * 0.60
    art_y = canvas_h * 0.15
    art_scale = 4.0

    # 绘制插画（带动画）
    from core.lineart_renderer import _draw_illustration
    _draw_illustration(draw, art, art_x, art_y, art_scale, lineart_progress)

    # 5. 添加右侧装饰框
    border_x = int(canvas_w * 0.57)
    draw.rectangle(
        [border_x, 60, canvas_w - 40, canvas_h - 100],
        outline=COLORS["line"],
        width=2,
    )

    # 6. 进度条
    if manga_progress > 0:
        bar_y = canvas_h - 60
        bar_w = canvas_w - 100
        filled = int(bar_w * manga_progress)
        draw.rectangle([50, bar_y, 50 + bar_w, bar_y + 8], fill=(220, 220, 220))
        draw.rectangle([50, bar_y, 50 + filled, bar_y + 8], fill=COLORS["accent"])

    return img


def generate_manga_lineart_video():
    """生成漫画帧+线条插画混合视频"""

    print("=" * 60)
    print("   漫画帧 + 线条插画 混合风格")
    print("=" * 60)

    # 深入讲解 Redis
    scenes = [
        {
            "title": "什么是Redis？",
            "subtitle": "开源内存数据结构存储系统",
            "bullets": ["高性能键值数据库", "数据存储在内存中", "支持多种数据结构", "广泛用于缓存场景"],
            "keyword": "database",
        },
        {
            "title": "为什么这么快？",
            "subtitle": "内存存储 + 单线程模型",
            "bullets": ["内存读写速度是磁盘10万倍", "单线程避免锁竞争", "IO多路复用处理并发", "高效数据结构设计"],
            "keyword": "brain",
        },
        {
            "title": "5种核心数据结构",
            "subtitle": "String / Hash / List / Set / ZSet",
            "bullets": ["String：最基础的类型", "Hash：适合存储对象", "List：有序队列", "Set：无序集合", "ZSet：有序集合+分数"],
            "keyword": "gear",
        },
        {
            "title": "缓存流程",
            "subtitle": "App → Redis → Database",
            "bullets": ["App发起请求", "先查Redis缓存", "命中直接返回", "未命中查数据库", "结果写回缓存"],
            "keyword": "laptop",
        },
        {
            "title": "缓存命中 vs 未命中",
            "subtitle": "命中<1ms，未命中>100ms",
            "bullets": ["命中：直接从内存读取", "未命中：查询数据库", "命中率越高性能越好", "合理设置过期时间"],
            "keyword": "check_mark",
        },
        {
            "title": "缓存穿透",
            "subtitle": "查询不存在的数据",
            "bullets": ["请求直达数据库", "数据库压力暴增", "解决方案：布隆过滤器", "解决方案：缓存空值"],
            "keyword": "magnifying_glass",
        },
        {
            "title": "缓存雪崩",
            "subtitle": "大量缓存同时过期",
            "bullets": ["缓存集体失效", "请求全部打到数据库", "解决方案：随机过期时间", "解决方案：多级缓存"],
            "keyword": "database",
        },
        {
            "title": "持久化方案",
            "subtitle": "RDB快照 + AOF日志",
            "bullets": ["RDB：定时全量快照", "AOF：记录每个写命令", "RDB恢复快但可能丢数据", "AOF数据安全但文件大"],
            "keyword": "gear",
        },
        {
            "title": "应用场景",
            "subtitle": "不只是缓存",
            "bullets": ["会话缓存（Session）", "消息队列（List）", "排行榜（ZSet）", "分布式锁（SETNX）", "计数器（INCR）"],
            "keyword": "chat_bubble",
        },
        {
            "title": "总结",
            "subtitle": "后端开发必备技能",
            "bullets": ["掌握Redis核心概念", "理解缓存三大问题", "熟悉数据结构选型", "了解持久化方案"],
            "keyword": "brain",
        },
    ]

    # 生成视频
    import shutil
    import subprocess

    output_path = "output/manga_lineart_redis.mp4"
    temp_dir = Path("output/_manga_lineart_frames")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    fps = 25
    draw_dur = 4.0
    hold_dur = 2.5
    frame_idx = 0

    print(f"\n  场景数: {len(scenes)}")
    print(f"  画布: 1920x1080")
    print(f"  风格: 漫画帧(左) + 线条插画(右)\n")

    for si, scene in enumerate(scenes):
        # 绘制阶段
        draw_frames = int(draw_dur * fps)
        for f in range(draw_frames):
            progress = f / draw_frames
            img = render_manga_lineart_frame(
                title=scene["title"],
                subtitle=scene["subtitle"],
                bullets=scene["bullets"],
                lineart_keyword=scene["keyword"],
                manga_progress=progress,
                lineart_progress=progress,
            )
            img.save(str(temp_dir / f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

        # 停留阶段
        hold_frames = int(hold_dur * fps)
        last_img = render_manga_lineart_frame(
            title=scene["title"],
            subtitle=scene["subtitle"],
            bullets=scene["bullets"],
            lineart_keyword=scene["keyword"],
            manga_progress=1.0,
            lineart_progress=1.0,
        )
        for f in range(hold_frames):
            last_img.save(str(temp_dir / f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

        print(f"  场景 {si+1}/{len(scenes)}: {scene['title']}")

    # FFmpeg 编码
    print(f"\n  编码中 ({frame_idx} 帧)...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(temp_dir / "frame_%05d.png"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, timeout=600)

    # 清理
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    if Path("output/temp_manga_frame.png").exists():
        os.remove("output/temp_manga_frame.png")

    # 视频信息
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", output_path],
        capture_output=True, text=True
    )
    import json
    info = json.loads(probe.stdout)
    duration = float(info["format"]["duration"])
    size_mb = int(info["format"]["size"]) / 1024 / 1024

    print(f"\n{'='*60}")
    print(f"   生成完成！")
    print(f"{'='*60}")
    print(f"  输出: {output_path}")
    print(f"  时长: {duration:.1f}秒")
    print(f"  大小: {size_mb:.1f}MB")
    print(f"  场景: {len(scenes)}")

    return output_path


if __name__ == "__main__":
    import os
    generate_manga_lineart_video()
