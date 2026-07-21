# -*- coding: utf-8 -*-
"""
视频合成测试
验证视频合成功能
"""
import sys
import os
from pathlib import Path

# UTF-8输出
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("[ERROR] PIL not available")
    sys.exit(1)

from core.video_composer import VideoComposer, VideoGenerator, generate_video_from_storyboard


def create_test_frames():
    """创建测试帧"""
    print("=" * 60)
    print("  创建测试帧")
    print("=" * 60)

    output_dir = Path(__file__).parent / "output" / "video_tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    frames_dir = output_dir / "test_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # 创建30帧测试图像
    fps = 30
    duration = 3.0
    total_frames = int(fps * duration)

    print(f"\n生成 {total_frames} 帧测试图像...")

    try:
        # 尝试加载字体
        try:
            title_font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 80)
            body_font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 40)
        except:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()

        for i in range(total_frames):
            img = Image.new("RGB", (1080, 1920), "#1A1A2E")
            draw = ImageDraw.Draw(img)

            # 绘制帧编号
            frame_text = f"Frame {i+1}/{total_frames}"
            draw.text((540, 960), frame_text, fill="#FFD700",
                     font=title_font, anchor="mm")

            # 绘制说明
            desc_text = "Video Composition Test"
            draw.text((540, 1060), desc_text, fill="#FFFFFF",
                     font=body_font, anchor="mm")

            # 保存帧
            frame_path = frames_dir / f"frame_{i:04d}.png"
            img.save(frame_path, quality=95)

        print(f"  [OK] 生成 {total_frames} 帧到 {frames_dir}")
        return frames_dir

    except Exception as e:
        print(f"  [FAIL] {e}")
        return None


def test_video_composition():
    """测试视频合成"""
    print("\n" + "=" * 60)
    print("  视频合成测试")
    print("=" * 60)

    # 创建测试帧
    frames_dir = create_test_frames()
    if not frames_dir:
        print("\n[FAIL] 无法创建测试帧")
        return False

    output_dir = Path(__file__).parent / "output" / "video_tests"
    output_path = output_dir / "test_video.mp4"

    print(f"\n合成视频到: {output_path}")

    try:
        # 创建合成器
        composer = VideoComposer()

        # 合成视频
        success = composer.compose_frames_to_video(
            frames_dir=str(frames_dir),
            output_path=str(output_path),
            fps=30,
            codec="libx264",
            bitrate="2M",
            preset="medium"
        )

        if success:
            # 检查输出文件
            if output_path.exists():
                size = output_path.stat().st_size / (1024 * 1024)  # MB
                print(f"\n[OK] 视频创建成功: {output_path} ({size:.2f} MB)")
                return True
            else:
                print(f"\n[FAIL] 输出文件不存在")
                return False
        else:
            print(f"\n[FAIL] 视频合成失败")
            return False

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_video_generator():
    """测试视频生成器"""
    print("\n" + "=" * 60)
    print("  视频生成器测试")
    print("=" * 60)

    # 创建测试分镜
    storyboard = [
        {
            "title": "Python异步编程",
            "subtitle": "高性能并发编程指南",
            "bullets": [
                "async/await 语法糖",
                "事件循环原理",
                "协程并发模型"
            ]
        },
        {
            "title": "实战应用",
            "subtitle": "真实场景案例分析",
            "bullets": [
                "异步爬虫实现",
                "API请求优化",
                "数据库操作"
            ]
        },
        {
            "title": "性能对比",
            "subtitle": "不同方案性能测试",
            "bullets": [
                "协程 vs 多线程",
                "内存占用分析",
                "响应时间对比"
            ]
        }
    ]

    output_dir = Path(__file__).parent / "output" / "video_tests"
    output_path = output_dir / "generated_video.mp4"

    print(f"\n生成分镜视频: {len(storyboard)} 个场景")
    print(f"输出路径: {output_path}")

    try:
        # 创建视频生成器
        generator = VideoGenerator(style_id="minimal", fps=30)

        # 生成视频
        success = generator.generate_video(
            storyboard=storyboard,
            output_path=str(output_path),
            enable_animations=False,
            scene_duration=3.0,
            progress_callback=lambda p: print(f"  进度: {p*100:.0f}%")
        )

        if success and output_path.exists():
            size = output_path.stat().st_size / (1024 * 1024)  # MB
            print(f"\n[OK] 视频生成成功: {output_path} ({size:.2f} MB)")
            return True
        else:
            print(f"\n[FAIL] 视频生成失败")
            return False

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("视频合成系统测试")
    print("=" * 60)

    # 测试1: 基础视频合成
    test1_pass = test_video_composition()

    # 测试2: 视频生成器
    test2_pass = test_video_generator()

    # 汇总
    print("\n" + "=" * 60)
    print("  测试汇总")
    print("=" * 60)

    results = [
        ("视频合成", test1_pass),
        ("视频生成器", test2_pass)
    ]

    for test_name, passed in results:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {test_name}")

    ok_count = sum(1 for _, passed in results if passed)
    print(f"\n通过: {ok_count}/{len(results)}")

    sys.exit(0 if ok_count == len(results) else 1)
