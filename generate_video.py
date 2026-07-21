#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
短视频生成 - 命令行入口。

用法：
    # 命令行参数模式
    python generate_video.py --input "讲解什么是机器学习" --category 教育讲解 --style tech --duration 30

    # 交互式模式（不带参数直接运行）
    python generate_video.py

支持的分类: 教育讲解 / 短视频 / 纪录片 / 商业宣传
支持的风格: minimal / vibrant / cinematic / tech / manga
"""

import sys
import asyncio
import argparse

# 确保UTF-8输出（Windows终端兼容）
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 加载环境变量（.env中的API密钥）
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass


CATEGORIES = ["教育讲解", "短视频", "纪录片", "商业宣传"]
STYLES = ["minimal", "vibrant", "cinematic", "tech", "manga"]
STYLE_NAMES = {
    "minimal": "极简清新",
    "vibrant": "活力时尚",
    "cinematic": "电影质感",
    "tech": "科技霓虹",
    "manga": "日式漫画",
}


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="AI短视频自动生成 - 输入需求，自动生成配素材和字幕的视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", "-i", type=str, help="视频内容需求描述")
    parser.add_argument("--category", "-c", type=str, choices=CATEGORIES,
                        default="教育讲解", help="视频分类")
    parser.add_argument("--style", "-s", type=str, choices=STYLES,
                        default="minimal", help="视觉风格")
    parser.add_argument("--duration", "-d", type=int, default=30,
                        help="目标时长(秒), 5-300")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="输出视频路径(可选)")
    parser.add_argument("--vertical", action="store_true", default=True,
                        help="竖屏1080x1920(默认)")
    parser.add_argument("--horizontal", action="store_true",
                        help="横屏1920x1080")
    return parser.parse_args()


def interactive_input() -> dict:
    """交互式收集用户输入。"""
    print("=" * 56)
    print("  🎬 AI短视频自动生成")
    print("=" * 56)

    # 需求
    user_input = ""
    while not user_input.strip():
        user_input = input("\n请描述视频内容 (例: 讲解什么是机器学习):\n> ").strip()

    # 分类
    print("\n选择分类:")
    for i, cat in enumerate(CATEGORIES, 1):
        print(f"  {i}. {cat}")
    cat_idx = _choose("分类", len(CATEGORIES), default=1)
    category = CATEGORIES[cat_idx - 1]

    # 风格
    print("\n选择风格:")
    for i, st in enumerate(STYLES, 1):
        print(f"  {i}. {st} ({STYLE_NAMES[st]})")
    st_idx = _choose("风格", len(STYLES), default=1)
    style = STYLES[st_idx - 1]

    # 时长
    dur_raw = input("\n目标时长(秒, 默认30): ").strip()
    try:
        duration = int(dur_raw) if dur_raw else 30
    except ValueError:
        duration = 30
    duration = max(5, min(300, duration))

    return {
        "user_input": user_input,
        "category": category,
        "style": style,
        "duration": duration,
    }


def _choose(name: str, count: int, default: int = 1) -> int:
    """让用户选择编号。"""
    raw = input(f"{name}编号 (默认{default}): ").strip()
    try:
        idx = int(raw) if raw else default
        if 1 <= idx <= count:
            return idx
    except ValueError:
        pass
    return default


async def run(params: dict, output_path: str = None, size=(1080, 1920)) -> int:
    """执行视频生成。

    Args:
        params: 用户参数
        output_path: 输出路径
        size: 分辨率

    Returns:
        退出码 (0成功)
    """
    from core.agents.coordinator_agent import CoordinatorAgent
    from core.agents.video_compose_agent import VideoComposeAgent
    from core.agents.message_bus import MessageBus
    from core.models import UserRequest

    request = UserRequest(
        user_input=params["user_input"],
        category=params["category"],
        style=params["style"],
        duration=params["duration"],
    )

    if not request.validate():
        print("\n❌ 输入参数无效，请检查分类/风格/时长")
        return 1

    print("\n" + "=" * 56)
    print(f"  需求: {request.user_input}")
    print(f"  分类: {request.category} | 风格: {request.style} "
          f"({STYLE_NAMES.get(request.style, '')})")
    print(f"  时长: {request.duration}秒 | 分辨率: {size[0]}x{size[1]}")
    print("=" * 56)
    print("\n⏳ 生成中... (内容分析 → 素材检索 → 视频合成)\n")

    # 构建主控Agent
    compose_agent = VideoComposeAgent(size=size)
    coordinator = CoordinatorAgent(
        bus=MessageBus(),
        compose_agent=compose_agent,
        output_path=output_path,
    )

    result = await coordinator.process_request(request)

    # 展示结果
    print("\n" + "=" * 56)
    print(result.get_summary())
    print("=" * 56)

    if result.stages:
        print("\n各阶段:")
        for name, stage in result.stages.items():
            status = "✅" if stage.success else "⚠️"
            print(f"  {status} {name}: {stage.data or stage.error}")

    return 0 if result.success else 2


def main() -> int:
    """主入口。"""
    args = parse_args()

    if args.input:
        params = {
            "user_input": args.input,
            "category": args.category,
            "style": args.style,
            "duration": max(5, min(300, args.duration)),
        }
    else:
        params = interactive_input()

    size = (1920, 1080) if args.horizontal else (1080, 1920)

    try:
        return asyncio.run(run(params, args.output, size))
    except KeyboardInterrupt:
        print("\n\n已取消")
        return 130
    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
