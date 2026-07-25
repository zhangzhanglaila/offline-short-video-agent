"""轻量 yaml 配置加载器。环境变量覆盖顶层键。"""
import os
from pathlib import Path
from typing import Union

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # 仅在调用方传入真实 yaml 时才需要


def load_config(path: Union[str, Path] = "config.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        cfg: dict = {}
    else:
        if yaml is None:
            raise RuntimeError("需要 PyYAML;pip install pyyaml")
        cfg = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    # 环境变量覆盖(顶层键,大写形式)
    for key in list(cfg.keys()):
        env_key = key.upper()
        if env_key in os.environ:
            cfg[key] = os.environ[env_key]

    return cfg
