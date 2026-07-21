"""
背景音乐选择 - 从素材库挑选BGM。

从 assets/bgm/ 目录选取背景音乐。当前为简单选取(首个可用)，
后续可扩展为按分类/情绪匹配。
"""

from pathlib import Path
from typing import Optional, List


# BGM素材目录
_BGM_DIRS = ["assets/bgm", "assets/bgm/crawled"]


def find_bgm(category: Optional[str] = None) -> Optional[str]:
    """查找一个可用的背景音乐文件。

    Args:
        category: 视频分类(预留，当前未按分类区分)

    Returns:
        BGM文件路径，无则None
    """
    candidates = list_bgm()
    if not candidates:
        return None
    # 当前简单返回首个(确定性)。后续可按category/情绪选择。
    return candidates[0]


def list_bgm() -> List[str]:
    """列出所有可用BGM文件。

    Returns:
        BGM路径列表(去重排序)
    """
    found = set()
    for d in _BGM_DIRS:
        base = Path(d)
        if base.exists():
            for ext in ("*.mp3", "*.wav", "*.m4a", "*.aac"):
                for p in base.rglob(ext):
                    found.add(str(p))
    return sorted(found)
