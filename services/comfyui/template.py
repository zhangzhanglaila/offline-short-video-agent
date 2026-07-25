"""工作流模板加载与 {{占位符}} 插值。"""
import copy
import json
import random
from pathlib import Path
from typing import Union

INT_FIELDS = {"width", "height", "steps", "seed"}
STR_FIELDS = {"prompt", "text", "negative_prompt"}


def load_template(path: Union[str, Path]) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"工作流模板不存在: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _escape_braces(value: str) -> str:
    """防止 prompt 内 {{ 触发二次插值。"""
    return value.replace("{{", "\\{").replace("}}", "\\}")


def _walk(node, replacements: dict, replacements_str: dict):
    """递归遍历 dict / list,做占位符替换。"""
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if isinstance(v, str) and v.startswith("{{") and v.endswith("}}"):
                key = v[2:-2].strip()
                if key in replacements:
                    node[k] = replacements[key]
                elif key in replacements_str:
                    node[k] = replacements_str[key]
                # 未知占位符:保留原样(由 client 层日志提示)
            else:
                _walk(v, replacements, replacements_str)
    elif isinstance(node, list):
        for item in node:
            _walk(item, replacements, replacements_str)


def render_template(
    workflow: dict,
    *,
    prompt: str,
    width: int,
    height: int,
    steps: int = 20,
    seed: int | None = None,
) -> dict:
    wf = copy.deepcopy(workflow)
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    int_repl = {"width": int(width), "height": int(height),
                "steps": int(steps), "seed": int(seed)}
    str_repl = {"prompt": _escape_braces(prompt)}
    _walk(wf, int_repl, str_repl)
    return wf
