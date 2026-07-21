"""
Ken Burns运镜 - 生成FFmpeg zoompan滤镜参数。

将静态背景图变为缓慢缩放/平移的运动画面，消除"静态PPT"感。
运镜方向随场景索引变化，避免每个场景雷同。

技术要点：
- 先将素材cover-fit到2倍目标尺寸，给zoompan足够像素避免画质损失
- zoompan用 on(输出帧号) 驱动，线性缩放/平移，表达式平滑无抖动
- s=输出尺寸，d=总帧数
"""

from dataclasses import dataclass
from typing import Tuple


# 运镜变体：(缩放起点, 缩放终点, X漂移比例, Y漂移比例)
# 缩放>1为放大；漂移比例是"占可用余量的比例"(-1~1)，
# 实际像素在build时按 iw*(1-1/zoom) 的可平移余量换算，避免越界被钳制。
_VARIANTS = [
    ("zoom_in_center", 1.0, 1.20, 0.0, 0.0),    # 推近(居中)
    ("zoom_out_center", 1.20, 1.0, 0.0, 0.0),   # 拉远(居中)
    ("zoom_in_right", 1.10, 1.22, 0.9, 0.0),    # 推近+右移
    ("zoom_in_left", 1.10, 1.22, -0.9, 0.0),    # 推近+左移
    ("zoom_in_up", 1.10, 1.22, 0.0, -0.9),      # 推近+上移
    ("zoom_in_down", 1.10, 1.22, 0.0, 0.9),     # 推近+下移
    ("pan_right", 1.18, 1.18, 0.9, 0.0),        # 恒定缩放+平移
    ("pan_left", 1.18, 1.18, -0.9, 0.0),        # 恒定缩放+平移
]


@dataclass
class KenBurnsSpec:
    """Ken Burns运镜规格。

    Attributes:
        name: 变体名称
        z_start: 缩放起点
        z_end: 缩放终点
        drift_x: X方向漂移比例(-1~1，占可平移余量的比例)
        drift_y: Y方向漂移比例(-1~1)
        size: 输出尺寸 (宽, 高)
        fps: 帧率
        duration: 时长(秒)
    """

    name: str
    z_start: float
    z_end: float
    drift_x: float
    drift_y: float
    size: Tuple[int, int]
    fps: int
    duration: float

    @property
    def total_frames(self) -> int:
        """总帧数。"""
        return max(1, int(round(self.duration * self.fps)))

    def build_filter(self) -> str:
        """构建FFmpeg滤镜链字符串(-vf值)。

        Returns:
            滤镜链，输入单张图，输出运动视频流
        """
        w, h = self.size
        # 2倍画布，给zoompan缩放/平移留出像素余量，避免放大失真
        w2, h2 = w * 2, h * 2
        d = self.total_frames
        fps = self.fps

        # 进度 p = on/(d-1)，0→1
        denom = max(1, d - 1)
        p = f"(on/{denom})"

        # 缩放表达式：从z_start线性到z_end
        if abs(self.z_end - self.z_start) < 1e-6:
            z_expr = f"{self.z_start:.4f}"
        else:
            z_expr = f"{self.z_start:.4f}+({self.z_end - self.z_start:.4f})*{p}"

        # 裁剪窗口左上角：居中 + 漂移
        # 可平移余量 = iw-iw/zoom (完整半幅)；漂移比例×半余量，
        # 保证 x 在 [0, iw-iw/zoom] 内不被钳制
        # x = 居中 + drift_ratio * (余量/2) * (2p-1)
        x_expr = (
            f"(iw-iw/zoom)/2+({self.drift_x})*(iw-iw/zoom)/2*(2*{p}-1)"
        )
        y_expr = (
            f"(ih-ih/zoom)/2+({self.drift_y})*(ih-ih/zoom)/2*(2*{p}-1)"
        )

        # 先cover-fit到2倍画布，再zoompan
        # 不含format，便于与overlay组合；format由合成器在末尾统一追加
        return (
            f"scale={w2}:{h2}:force_original_aspect_ratio=increase,"
            f"crop={w2}:{h2},"
            f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={d}:s={w}x{h}:fps={fps}"
        )


def make_ken_burns(
    scene_index: int,
    size: Tuple[int, int],
    fps: int,
    duration: float,
) -> KenBurnsSpec:
    """根据场景索引生成运镜规格(变体轮换)。

    Args:
        scene_index: 场景索引(用于选择变体，避免雷同)
        size: 输出尺寸
        fps: 帧率
        duration: 时长(秒)

    Returns:
        Ken Burns运镜规格
    """
    name, z0, z1, dx, dy = _VARIANTS[scene_index % len(_VARIANTS)]
    return KenBurnsSpec(
        name=name,
        z_start=z0,
        z_end=z1,
        drift_x=dx,
        drift_y=dy,
        size=size,
        fps=fps,
        duration=duration,
    )
