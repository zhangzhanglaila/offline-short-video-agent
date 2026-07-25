# E5 ComfyUI 集成 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把本地 ComfyUI 作为 AI 生图/生视频的首选 provider,通过 `ComfyUIClient` + 两个 generator 适配类接入 `MaterialFetchAgent`,沿用现有 E2/E3 lazy 降级机制,云端 API 保留为可手动切换选项。

**Architecture:** 原生 `requests` HTTP 客户端 → `ComfyUIClient`(submit/wait/download/test_connection) → `ComfyUIImageGenerator` / `ComfyUIVideoGenerator` 实现项目既有抽象基类 → `MaterialFetchAgent` 读 `config.yaml` 选 provider;工作流模板从 `workflows/image/*.json` 加载,占位符 `{{prompt}} {{width}} {{height}} {{steps}} {{seed}}` 插值。

**Tech Stack:** Python 3.10+、FastAPI、`requests`、`pytest`、`pytest-asyncio`、`unittest.mock`(无新外部依赖)。

**Spec:** `docs/superpowers/specs/2026-08-02-e5-comfyui-integration-design.md`

---

## Global Constraints

- **Python 版本**:3.10+(项目统一)
- **测试运行**:`pytest tests/ -q`(项目已有约定)
- **异步测试**:`@pytest.mark.asyncio`(已在用)
- **HTTP 客户端**:仅用 `requests`(已在 `requirements.txt`)
- **Mock 库**:`unittest.mock` + `monkeypatch`,**不引入** `requests-mock`/`pytest-mock`
- **Provider 枚举扩展**:`AIProvider.COMFYUI = "comfyui"`、`VideoProvider.COMFYUI = "comfyui"`,不动现有值
- **降级链路**:复用 `MaterialFetchAgent._ai_generator` 的 lazy-属性 try/except 模式,不动 agent 主流程
- **TTS 模块**:`core/tts_module.py` 完全不动
- **git 提交**:每任务一次 commit,Co-Authored-By 标 Claude
- **devlog**:每周结束时更新 `devlog/daily/YYYY-MM-DD.md`(本计划跨 4 周,每周一汇总)
- **错误日志**:用 `logging.getLogger(__name__)`,降级路径用 `logger.warning(...)`
- **路径**:相对项目根,Windows 兼容(`/` 分隔符,Python 会处理)

---

## 文件结构(实施前确认)

```
新增:
  services/comfyui/__init__.py
  services/comfyui/client.py
  services/comfyui/errors.py
  services/comfyui/template.py
  services/ai_image/comfyui_generator.py
  services/ai_video/comfyui_generator.py
  services/config.py                    (轻量 yaml 读取助手)
  workflows/image/flux_dev.json
  workflows/video/wan22_t2v.json
  workflows/video/wan22_i2v.json
  tests/test_comfyui_client.py
  tests/test_comfyui_template.py
  tests/test_comfyui_image_generator.py
  tests/test_comfyui_video_generator.py
  tests/test_comfyui_integration.py     (mark.integration)
  tests/test_config_loader.py

修改:
  services/ai_image/base.py             (+ AIProvider.COMFYUI)
  services/ai_video/base.py             (+ VideoProvider.COMFYUI)
  services/ai_image/__init__.py         (导出 ComfyUIImageGenerator)
  services/ai_video/__init__.py         (导出 ComfyUIVideoGenerator)
  core/agents/material_fetch_agent.py   (lazy 属性读 config 选 provider)
  config.yaml                            (+ ai/comfyui 键)
  docs/27-E5-comfyui.md                  (更新状态)
  CLAUDE.md                              (E5 状态 ✅ + 概述)
  workflows/README.md                    (补 workflows/image 与 workflows/video 现状)

不动:
  core/tts_module.py                     (TTS 明确排除)
  api/, services/history/, services/template/
```

---

## Task 1: 配置加载器(让后续任务能读 config)

**为什么先做**:MaterialFetchAgent 改造(Task 7)和 generator 工厂都需要读 config。如果先写 generator,会反复改 import 顺序。

**Files:**
- Create: `services/config.py`
- Test: `tests/test_config_loader.py`

**Interfaces:**
- Consumes: (nothing — first task)
- Produces:
  ```python
  def load_config(path: str | Path = "config.yaml") -> dict
  ```
  返回字典;若文件不存在返回 `{}`;以 `os.environ` 覆盖同名顶层键(便于 CI 覆盖)。

- [ ] **Step 1: 写失败测试**

`tests/test_config_loader.py`:
```python
import os
from pathlib import Path
from services.config import load_config


def test_load_config_returns_empty_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_config("nonexistent.yaml") == {}


def test_load_config_reads_yaml(tmp_path, monkeypatch):
    cfg_file = tmp_path / "c.yaml"
    cfg_file.write_text("ai:\n  image_provider: comfyui\n")
    monkeypatch.chdir(tmp_path)
    cfg = load_config("c.yaml")
    assert cfg["ai"]["image_provider"] == "comfyui"


def test_load_config_env_override(tmp_path, monkeypatch):
    cfg_file = tmp_path / "c.yaml"
    cfg_file.write_text("ai_image_provider: comfyui\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AI_IMAGE_PROVIDER", "bailian")
    cfg = load_config("c.yaml")
    assert cfg["ai_image_provider"] == "bailian"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_config_loader.py -v`
Expected: `ModuleNotFoundError: No module named 'services.config'`

- [ ] **Step 3: 实现最小代码**

`services/__init__.py`(如不存在,空文件)。

`services/config.py`:
```python
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_config_loader.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add services/__init__.py services/config.py tests/test_config_loader.py
git commit -m "feat(config): add lightweight yaml loader with env override"
```

---

## Task 2: 自定义异常类

**Files:**
- Create: `services/comfyui/__init__.py`
- Create: `services/comfyui/errors.py`
- Test: 在 `tests/test_comfyui_client.py` 里覆盖(后面 Task 3 一并验证)

**Interfaces:**
- Produces:
  ```python
  class ComfyUIError(Exception): ...
  class ComfyUIConnectionError(ComfyUIError): ...
  class ComfyUIExecutionError(ComfyUIError): ...
  class ComfyUITimeoutError(ComfyUIError): ...
  ```

- [ ] **Step 1: 写最小异常模块**

`services/comfyui/__init__.py`:
```python
"""ComfyUI 服务:本地 ComfyUI HTTP 客户端 + 工作流模板加载。"""
from .client import ComfyUIClient, WorkflowOutput
from .errors import (
    ComfyUIError,
    ComfyUIConnectionError,
    ComfyUIExecutionError,
    ComfyUITimeoutError,
)
from .template import load_template, render_template

__all__ = [
    "ComfyUIClient", "WorkflowOutput",
    "ComfyUIError", "ComfyUIConnectionError",
    "ComfyUIExecutionError", "ComfyUITimeoutError",
    "load_template", "render_template",
]
```

`services/comfyui/errors.py`:
```python
"""ComfyUI 相关异常。"""


class ComfyUIError(Exception):
    """ComfyUI 调用失败的基类。"""


class ComfyUIConnectionError(ComfyUIError):
    """服务不可达 / 连接拒绝。"""


class ComfyUIExecutionError(ComfyUIError):
    """工作流执行报错或无 outputs。"""


class ComfyUITimeoutError(ComfyUIError):
    """轮询超过 timeout_sec。"""
```

- [ ] **Step 2: smoke 导入**

Run:
```bash
python -c "from services.comfyui import ComfyUIClient, ComfyUIConnectionError; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add services/comfyui/__init__.py services/comfyui/errors.py
git commit -m "feat(comfyui): add error classes and package init"
```

---

## Task 3: 工作流模板加载与插值

**Files:**
- Create: `services/comfyui/template.py`
- Test: `tests/test_comfyui_template.py`

**Interfaces:**
- Produces:
  ```python
  def load_template(path: str | Path) -> dict
  def render_template(workflow: dict, *, prompt: str, width: int, height: int,
                     steps: int = 20, seed: int | None = None) -> dict
  ```
  - `load_template` 读 JSON 文件;不存在抛 `FileNotFoundError`
  - `render_template` 深拷贝 workflow,把 `{{xxx}}` 占位符替换;`seed=None` 时用 `random.randint(0, 2**31 - 1)`

- [ ] **Step 1: 写失败测试**

`tests/test_comfyui_template.py`:
```python
import pytest
from pathlib import Path
from services.comfyui.template import load_template, render_template


def test_load_template_reads_json(tmp_path):
    f = tmp_path / "wf.json"
    f.write_text('{"nodes":[{"id":1,"inputs":{"text":"{{prompt}}"}}]}')
    wf = load_template(f)
    assert wf["nodes"][0]["inputs"]["text"] == "{{prompt}}"


def test_load_template_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_template(tmp_path / "missing.json")


def test_render_template_replaces_string():
    wf = {"nodes": [{"id": 1, "inputs": {"text": "{{prompt}}"}}]}
    out = render_template(wf, prompt="a cat", width=1024, height=1024)
    assert out["nodes"][0]["inputs"]["text"] == "a cat"


def test_render_template_replaces_int_fields():
    wf = {"nodes": [{"id": 1, "inputs": {"width": "{{width}}", "height": "{{height}}", "steps": "{{steps}}", "seed": "{{seed}}"}}]}
    out = render_template(wf, prompt="x", width=512, height=768, steps=30, seed=42)
    n = out["nodes"][0]["inputs"]
    assert n["width"] == 512
    assert n["height"] == 768
    assert n["steps"] == 30
    assert n["seed"] == 42


def test_render_template_escapes_prompt_braces():
    """防止 prompt 里出现 {{ 触发二次插值。"""
    wf = {"nodes": [{"id": 1, "inputs": {"text": "{{prompt}}"}}]}
    out = render_template(wf, prompt="hello {{evil}} world", width=64, height=64)
    assert out["nodes"][0]["inputs"]["text"] == "hello \\{evil\\} world"


def test_render_template_seed_random_if_none():
    wf = {"nodes": [{"id": 1, "inputs": {"seed": "{{seed}}"}}]}
    a = render_template(wf, prompt="x", width=64, height=64)
    b = render_template(wf, prompt="x", width=64, height=64)
    assert isinstance(a["nodes"][0]["inputs"]["seed"], int)
    assert a["nodes"][0]["inputs"]["seed"] != b["nodes"][0]["inputs"]["seed"]
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_comfyui_template.py -v`
Expected: `ModuleNotFoundError: No module named 'services.comfyui.template'`

- [ ] **Step 3: 实现**

`services/comfyui/template.py`:
```python
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_comfyui_template.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add services/comfyui/template.py tests/test_comfyui_template.py
git commit -m "feat(comfyui): workflow template loader with placeholder interpolation"
```

---

## Task 4: ComfyUIClient — 连接检测与提交

**Files:**
- Create: `services/comfyui/client.py`(部分)
- Test: `tests/test_comfyui_client.py`

**Interfaces:**
- Produces(本任务只到 `submit`,`wait_for_completion` / `download_outputs` 在 Task 5):
  ```python
  @dataclass
  class WorkflowOutput:
      filename: str
      subfolder: str
      type: str

  class ComfyUIClient:
      def __init__(self, base_url="http://127.0.0.1:8188",
                   poll_interval_sec=2.0, timeout_sec=600.0, session=None): ...
      def test_connection(self) -> bool: ...
      def submit(self, workflow: dict) -> str: ...   # returns prompt_id
  ```

- [ ] **Step 1: 写失败测试**

`tests/test_comfyui_client.py`:
```python
import pytest
import requests
from unittest.mock import MagicMock
from services.comfyui import ComfyUIClient, ComfyUIConnectionError


def _mock_session(json_responses):
    """json_responses: list of (method, url_substr, status, body)"""
    sess = MagicMock(spec=requests.Session)
    def fake_request(method, url, json=None, timeout=None, params=None):
        for m, u, s, b in json_responses:
            if m == method and u in url:
                resp = MagicMock()
                resp.status_code = s
                resp.json.return_value = b
                resp.raise_for_status = MagicMock()
                if s >= 400:
                    resp.raise_for_status.side_effect = requests.HTTPError(f"{s}")
                return resp
        raise AssertionError(f"unexpected {method} {url}")
    sess.request.side_effect = fake_request
    return sess


def test_test_connection_returns_true_when_stats_ok():
    sess = _mock_session([("GET", "/system_stats", 200, {"system": {}})])
    c = ComfyUIClient(session=sess)
    assert c.test_connection() is True


def test_test_connection_returns_false_on_5xx():
    sess = _mock_session([("GET", "/system_stats", 503, {})])
    c = ComfyUIClient(session=sess)
    assert c.test_connection() is False


def test_test_connection_returns_false_on_connection_error():
    sess = MagicMock(spec=requests.Session)
    sess.request.side_effect = requests.ConnectionError("refused")
    c = ComfyUIClient(session=sess)
    assert c.test_connection() is False


def test_submit_returns_prompt_id():
    sess = _mock_session([("POST", "/prompt", 200, {"prompt_id": "abc123"})])
    c = ComfyUIClient(session=sess)
    pid = c.submit({"nodes": [{"id": 1}]})
    assert pid == "abc123"
    # 确认 POST 路径带正确字段
    args, kwargs = sess.request.call_args
    assert args[0] == "POST"
    assert "prompt" in kwargs["json"]


def test_submit_raises_on_connection_error():
    sess = MagicMock(spec=requests.Session)
    sess.request.side_effect = requests.ConnectionError("refused")
    c = ComfyUIClient(session=sess)
    with pytest.raises(ComfyUIConnectionError):
        c.submit({"nodes": []})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_comfyui_client.py -v`
Expected: `ImportError` 或 `AttributeError`(client 还不存在)

- [ ] **Step 3: 实现 client.py 骨架**

`services/comfyui/client.py`:
```python
"""ComfyUI HTTP 客户端。"""
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Union

import requests

from .errors import (
    ComfyUIConnectionError,
    ComfyUIExecutionError,
    ComfyUITimeoutError,
)

logger = logging.getLogger(__name__)


@dataclass
class WorkflowOutput:
    filename: str
    subfolder: str
    type: str  # "output" / "temp"


class ComfyUIClient:
    """ComfyUI HTTP 客户端,提交-轮询工作流,下载产物。"""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        poll_interval_sec: float = 2.0,
        timeout_sec: float = 600.0,
        session: Optional[requests.Session] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.poll_interval_sec = poll_interval_sec
        self.timeout_sec = timeout_sec
        self.session = session or requests.Session()

    # ---- 连接检测 ----
    def test_connection(self) -> bool:
        try:
            r = self.session.get(
                f"{self.base_url}/system_stats",
                timeout=5,
            )
            return r.status_code == 200
        except requests.RequestException as e:
            logger.warning(f"ComfyUI 不可达: {e}")
            return False

    # ---- 提交 ----
    def submit(self, workflow: dict) -> str:
        try:
            r = self.session.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow},
                timeout=30,
            )
            r.raise_for_status()
        except requests.RequestException as e:
            raise ComfyUIConnectionError(f"提交工作流失败: {e}") from e

        data = r.json()
        if "prompt_id" not in data:
            raise ComfyUIExecutionError(
                f"提交响应缺少 prompt_id: {data}"
            )
        return data["prompt_id"]

    # ---- 占位,后续任务填充 ----
    def wait_for_completion(self, prompt_id: str) -> list[WorkflowOutput]:
        raise NotImplementedError

    def download_outputs(
        self,
        outputs: list[WorkflowOutput],
        save_dir: Union[str, Path],
    ) -> list[Path]:
        raise NotImplementedError
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_comfyui_client.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add services/comfyui/client.py tests/test_comfyui_client.py
git commit -m "feat(comfyui): client submit + connection test"
```

---

## Task 5: ComfyUIClient — 轮询完成与下载产物

**Files:**
- Modify: `services/comfyui/client.py`
- Modify: `tests/test_comfyui_client.py`

**Interfaces:**
- Produces:
  ```python
  def wait_for_completion(self, prompt_id: str) -> list[WorkflowOutput]
  def download_outputs(self, outputs, save_dir) -> list[Path]
  ```

- [ ] **Step 1: 追加失败测试**

追加到 `tests/test_comfyui_client.py`:
```python
def test_wait_returns_outputs_on_success():
    # /history 第一次 pending(empty), 第二次 outputs 就绪
    outputs = {"9": {"outputs": {"12": {"images": [
        {"filename": "out.png", "subfolder": "", "type": "output"}
    ]}}}}
    calls = {"n": 0}
    def req(method, url, json=None, timeout=None, params=None):
        calls["n"] += 1
        resp = MagicMock()
        resp.status_code = 200
        if calls["n"] == 1:
            resp.json.return_value = {}  # 还没好
        else:
            resp.json.return_value = outputs
        return resp
    sess = MagicMock(spec=requests.Session)
    sess.request.side_effect = req
    c = ComfyUIClient(session=sess, poll_interval_sec=0)
    out = c.wait_for_completion("pid")
    assert len(out) == 1
    assert out[0].filename == "out.png"


def test_wait_raises_execution_error_on_status_error():
    sess = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"pid": {"status": {"error": True}}}
    sess.request.return_value = resp
    c = ComfyUIClient(session=sess, poll_interval_sec=0, timeout_sec=2)
    from services.comfyui import ComfyUIExecutionError
    with pytest.raises(ComfyUIExecutionError):
        c.wait_for_completion("pid")


def test_wait_raises_timeout_when_no_outputs():
    sess = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {}  # 永远空
    sess.request.return_value = resp
    c = ComfyUIClient(session=sess, poll_interval_sec=0, timeout_sec=0.1)
    from services.comfyui import ComfyUITimeoutError
    with pytest.raises(ComfyUITimeoutError):
        c.wait_for_completion("pid")


def test_download_outputs_saves_files(tmp_path):
    # GET /view 返回二进制内容
    sess = MagicMock(spec=requests.Session)
    resp = MagicMock()
    resp.status_code = 200
    resp.content = b"\x89PNG_FAKE"
    resp.raise_for_status = MagicMock()
    sess.request.return_value = resp
    c = ComfyUIClient(session=sess)
    paths = c.download_outputs(
        [WorkflowOutput("out.png", "", "output")],
        tmp_path,
    )
    assert paths[0].exists()
    assert paths[0].read_bytes() == b"\x89PNG_FAKE"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_comfyui_client.py -v`
Expected: 新增 4 个失败(`NotImplementedError`)

- [ ] **Step 3: 在 client.py 末尾追加实现**

追加到 `services/comfyui/client.py`(类内):
```python
    def _poll_history(self, prompt_id: str) -> dict:
        """单次 GET /history/{prompt_id};容错 5xx → 返回空 dict。"""
        try:
            r = self.session.get(
                f"{self.base_url}/history/{prompt_id}",
                timeout=10,
            )
            if r.status_code != 200:
                return {}
            return r.json()
        except requests.RequestException as e:
            logger.warning(f"轮询 history 失败: {e}")
            return {}

    def wait_for_completion(self, prompt_id: str) -> list[WorkflowOutput]:
        deadline = time.time() + self.timeout_sec
        while time.time() < deadline:
            history = self._poll_history(prompt_id)
            entry = history.get(prompt_id) or {}
            status = entry.get("status") or {}
            if status.get("error"):
                raise ComfyUIExecutionError(
                    f"工作流执行报错: {status}"
                )
            outputs_raw = entry.get("outputs") or {}
            if outputs_raw:
                return self._parse_outputs(outputs_raw)
            time.sleep(self.poll_interval_sec)
        raise ComfyUITimeoutError(
            f"等待 {prompt_id} 超时 ({self.timeout_sec}s)"
        )

    def _parse_outputs(self, outputs_raw: dict) -> list[WorkflowOutput]:
        """从 /history 的 outputs 字典里抽出所有文件引用。"""
        result: list[WorkflowOutput] = []
        for node_id, node_out in outputs_raw.items():
            for kind in ("images", "gifs", "videos"):
                for item in node_out.get(kind, []) or []:
                    result.append(WorkflowOutput(
                        filename=item["filename"],
                        subfolder=item.get("subfolder", ""),
                        type=item.get("type", "output"),
                    ))
        return result

    def download_outputs(
        self,
        outputs: list[WorkflowOutput],
        save_dir: Union[str, Path],
    ) -> list[Path]:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        for o in outputs:
            try:
                r = self.session.get(
                    f"{self.base_url}/view",
                    params={"filename": o.filename,
                            "subfolder": o.subfolder,
                            "type": o.type},
                    timeout=60,
                )
                r.raise_for_status()
            except requests.RequestException as e:
                raise ComfyUIExecutionError(
                    f"下载 {o.filename} 失败: {e}"
                ) from e
            out_path = save_dir / o.filename
            out_path.write_bytes(r.content)
            paths.append(out_path)
        return paths
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_comfyui_client.py -v`
Expected: 9 PASS

- [ ] **Step 5: Commit**

```bash
git add services/comfyui/client.py tests/test_comfyui_client.py
git commit -m "feat(comfyui): client polling + output download"
```

---

## Task 6: 工作流模板 JSON(Flux Dev + Wan 2.2)

**Files:**
- Create: `workflows/image/flux_dev.json`
- Create: `workflows/video/wan22_t2v.json`
- Create: `workflows/video/wan22_i2v.json`
- Modify: `workflows/README.md`

**Interfaces:**
- Produces: 3 个 ComfyUI API 格式 JSON,含 `{{prompt}}` `{{width}}` `{{height}}` `{{steps}}` `{{seed}}` 占位符

- [ ] **Step 1: 创建 image 模板**

`workflows/image/flux_dev.json`(最小可运行 Flux Dev 工作流):
```json
{
  "nodes": [
    {
      "id": 1,
      "type": "UNETLoader",
      "inputs": {"unet_name": "flux1-dev.safetensors", "weight_dtype": "default"}
    },
    {
      "id": 2,
      "type": "DualCLIPLoader",
      "inputs": {"clip_name1": "clip_l.safetensors", "clip_name2": "t5xxl_fp16.safetensors", "type": "flux"}
    },
    {
      "id": 3,
      "type": "CLIPTextEncode",
      "inputs": {"text": "{{prompt}}", "clip": ["2", 0]}
    },
    {
      "id": 4,
      "type": "CLIPTextEncode",
      "inputs": {"text": "", "clip": ["2", 0]}
    },
    {
      "id": 5,
      "type": "EmptyLatentImage",
      "inputs": {"width": "{{width}}", "height": "{{height}}", "batch_size": 1}
    },
    {
      "id": 6,
      "type": "KSampler",
      "inputs": {
        "model": ["1", 0], "positive": ["3", 0], "negative": ["4", 0],
        "latent_image": ["5", 0], "seed": "{{seed}}",
        "steps": "{{steps}}", "cfg": 1.0, "sampler_name": "euler",
        "scheduler": "simple", "denoise": 1.0
      }
    },
    {
      "id": 7,
      "type": "VAELoader",
      "inputs": {"vae_name": "ae.safetensors"}
    },
    {
      "id": 8,
      "type": "VAEDecode",
      "inputs": {"samples": ["6", 0], "vae": ["7", 0]}
    },
    {
      "id": 9,
      "type": "SaveImage",
      "inputs": {"images": ["8", 0], "filename_prefix": "agent"}
    }
  ]
}
```

- [ ] **Step 2: 创建 video t2v 模板**

`workflows/video/wan22_t2v.json`(Wan 2.2 T2V 5s 720P):
```json
{
  "nodes": [
    {
      "id": 1,
      "type": "WanVideoModelLoader",
      "inputs": {"model": "wan2.2_t2v_5B_fp16.safetensors"}
    },
    {
      "id": 2,
      "type": "CLIPLoader",
      "inputs": {"clip_name": "umt5_xxl_fp8.safetensors", "type": "wan"}
    },
    {
      "id": 3,
      "type": "CLIPTextEncode",
      "inputs": {"text": "{{prompt}}", "clip": ["2", 0]}
    },
    {
      "id": 4,
      "type": "WanVideoSampler",
      "inputs": {
        "model": ["1", 0], "positive": ["3", 0],
        "width": "{{width}}", "height": "{{height}}",
        "steps": "{{steps}}", "seed": "{{seed}}",
        "frames": 81, "cfg": 5.0, "sampler": "uni_pc"
      }
    },
    {
      "id": 5,
      "type": "WanVideoDecode",
      "inputs": {"samples": ["4", 0]}
    },
    {
      "id": 6,
      "type": "SaveVideo",
      "inputs": {"video": ["5", 0], "filename_prefix": "agent_t2v", "format": "mp4"}
    }
  ]
}
```

- [ ] **Step 3: 创建 video i2v 模板**

`workflows/video/wan22_i2v.json`(图生视频;占位符含 `{{image_path}}` —— 留给后续可选工作流,本任务不实现,先留文件):
```json
{
  "_comment": "Wan 2.2 I2V - 图生视频工作流。",
  "nodes": [
    {
      "id": 1,
      "type": "LoadImage",
      "inputs": {"image": "{{image_filename}}"}
    },
    {
      "id": 2,
      "type": "WanVideoModelLoader",
      "inputs": {"model": "wan2.2_i2v_5B_fp16.safetensors"}
    },
    {
      "id": 3,
      "type": "CLIPLoader",
      "inputs": {"clip_name": "umt5_xxl_fp8.safetensors", "type": "wan"}
    },
    {
      "id": 4,
      "type": "CLIPTextEncode",
      "inputs": {"text": "{{prompt}}", "clip": ["3", 0]}
    },
    {
      "id": 5,
      "type": "WanVideoSampler",
      "inputs": {
        "model": ["2", 0], "positive": ["4", 0], "image": ["1", 0],
        "width": "{{width}}", "height": "{{height}}",
        "steps": "{{steps}}", "seed": "{{seed}}",
        "frames": 81, "cfg": 5.0, "sampler": "uni_pc"
      }
    },
    {
      "id": 6,
      "type": "WanVideoDecode",
      "inputs": {"samples": ["5", 0]}
    },
    {
      "id": 7,
      "type": "SaveVideo",
      "inputs": {"video": ["6", 0], "filename_prefix": "agent_i2v", "format": "mp4"}
    }
  ]
}
```

- [ ] **Step 4: 验证 JSON 合法 + 模板可被 `load_template` 加载**

```bash
python -c "
from pathlib import Path
from services.comfyui.template import load_template, render_template
for p in [Path('workflows/image/flux_dev.json'),
          Path('workflows/video/wan22_t2v.json'),
          Path('workflows/video/wan22_i2v.json')]:
    wf = load_template(p)
    out = render_template(wf, prompt='test', width=64, height=64, steps=4, seed=1)
    print(p.name, 'OK', len(out['nodes']), 'nodes')
"
```
Expected: 3 行 `OK ...`

- [ ] **Step 5: 更新 workflows/README.md**

替换 `workflows/README.md` 现状(简化版):
```markdown
# Workflows

ComfyUI 工作流模板。

## 目录
- `image/`   文生图(flux_dev.json)
- `video/`   文生视频(wan22_t2v.json)、图生视频(wan22_i2v.json)
- `tts/`     预留(TTS 不在 E5 范围)

## 占位符
`{{prompt}}` `{{width}}` `{{height}}` `{{steps}}` `{{seed}}`

由 `services/comfyui/template.py` 在调用时插值。
```

- [ ] **Step 6: Commit**

```bash
git add workflows/
git commit -m "feat(workflows): add Flux Dev + Wan 2.2 t2v/i2v templates"
```

---

## Task 7: 枚举扩展 + 服务 __init__ 导出

**Files:**
- Modify: `services/ai_image/base.py:9-13`
- Modify: `services/ai_video/base.py:9-13`
- Modify: `services/ai_image/__init__.py`
- Modify: `services/ai_video/__init__.py`
- Test: smoke

**Interfaces:**
- Produces: `AIProvider.COMFYUI` / `VideoProvider.COMFYUI` 枚举值(但不实现 generator)

- [ ] **Step 1: 改 ai_image/base.py**

在 `AIProvider` 类里加一行:
```python
    COMFYUI = "comfyui"
```

(放在 `BAILIAN` 之后。)

- [ ] **Step 2: 改 ai_video/base.py**

在 `VideoProvider` 类里加一行:
```python
    COMFYUI = "comfyui"
```

(放在 `DASHSCOPE` 之后。)

- [ ] **Step 3: 更新 ai_image/__init__.py**

```python
"""AI 生图服务层"""
from .base import (
    AIGenerationService,
    AIImageRequest,
    AIImageResult,
    AIProvider,
    ImageSize,
    ImageStyle,
)
from .openai_generator import OpenAIImageGenerator
from .dashscope_generator import DashscopeImageGenerator
from .bailian_generator import BailianImageGenerator
# E5
from .comfyui_generator import ComfyUIImageGenerator

__all__ = [
    'AIGenerationService',
    'AIImageRequest',
    'AIImageResult',
    'AIProvider',
    'ImageSize',
    'ImageStyle',
    'OpenAIImageGenerator',
    'DashscopeImageGenerator',
    'BailianImageGenerator',
    'ComfyUIImageGenerator',  # E5
]
```

- [ ] **Step 4: 更新 ai_video/__init__.py**(同模式,加 `ComfyUIVideoGenerator`)

```python
"""AI 生视频服务层"""
from .base import (
    AIVideoGenerationService,
    VideoGenerationRequest,
    VideoGenerationResult,
    VideoGenerationProgress,
    VideoProvider,
    VideoSize,
    VideoResolution,
    VideoTaskStatus,
)
from .dashscope_generator import DashScopeVideoGenerator
# E5
from .comfyui_generator import ComfyUIVideoGenerator

__all__ = [
    'AIVideoGenerationService',
    'VideoGenerationRequest',
    'VideoGenerationResult',
    'VideoGenerationProgress',
    'VideoProvider',
    'VideoSize',
    'VideoResolution',
    'VideoTaskStatus',
    'DashScopeVideoGenerator',
    'ComfyUIVideoGenerator',  # E5
]
```

- [ ] **Step 5: 跑 smoke + 现有 ai 服务测试**

```bash
python -c "from services.ai_image import AIProvider; print(AIProvider.COMFYUI)"
python -c "from services.ai_video import VideoProvider; print(VideoProvider.COMFYUI)"
pytest tests/test_ai_image_service.py -q
```
Expected: 都 PASS,无 import 错误。

注:此时 `comfyui_generator.py` 还不存在 —— **所以 __init__.py 的导入会报错**。本任务先**不**改 `__init__.py`,留给 Task 8/9 创建完 generator 后再改。**回退 Step 3/Step 4 的 __init__.py 改动**,只做 Step 1/Step 2。

修订后的步骤:
- [ ] **Step 1+2**:改 base.py(枚举扩展)
- [ ] **Step 3**:跑 `pytest tests/test_ai_image_service.py -q`,确认 8 PASS(基线)
- [ ] **Step 4**:Commit base.py

- [ ] **Step 6: Commit**

```bash
git add services/ai_image/base.py services/ai_video/base.py
git commit -m "feat(providers): add COMFYUI to AIProvider and VideoProvider enums"
```

---

## Task 8: ComfyUIImageGenerator

**Files:**
- Create: `services/ai_image/comfyui_generator.py`
- Test: `tests/test_comfyui_image_generator.py`

**Interfaces:**
- Produces:
  ```python
  class ComfyUIImageGenerator(AIGenerationService):
      def __init__(self, *, base_url="http://127.0.0.1:8188",
                   workflow_path="workflows/image/flux_dev.json",
                   poll_interval_sec=2.0, timeout_sec=600.0,
                   client=None): ...
      async def generate(self, request: AIImageRequest) -> AIImageResult
      def get_supported_models(self) -> list[str]   # ["flux-dev"]
      def estimate_cost(self, request) -> float    # 0.0
  ```

- [ ] **Step 1: 写失败测试**

`tests/test_comfyui_image_generator.py`:
```python
import pytest
from unittest.mock import MagicMock
from pathlib import Path
from services.ai_image.base import (
    AIImageRequest, AIProvider, ImageSize, AIImageResult,
)
from services.ai_image.comfyui_generator import ComfyUIImageGenerator
from services.comfyui.client import WorkflowOutput


def _fake_client_ok():
    c = MagicMock()
    c.test_connection.return_value = True
    c.submit.return_value = "pid-1"
    c.wait_for_completion.return_value = [WorkflowOutput("a.png", "", "output")]
    c.download_outputs.return_value = [Path("/fake/a.png")]
    return c


@pytest.mark.asyncio
async def test_generate_success(tmp_path):
    fake = _fake_client_ok()
    gen = ComfyUIImageGenerator(
        client=fake,
        workflow_path=tmp_path / "wf.json",  # 不会被实际读
    )
    req = AIImageRequest(
        prompt="a cat", provider=AIProvider.COMFYUI, size=ImageSize.SQUARE_512,
    )
    res = await gen.generate(req)
    assert res.success is True
    assert res.provider == "comfyui"
    assert res.cost == 0.0
    assert fake.submit.called
    assert fake.wait_for_completion.called


@pytest.mark.asyncio
async def test_generate_returns_cached_when_exists(tmp_path, monkeypatch):
    """如果缓存文件已存在,跳过 submit。"""
    cache_dir = Path("output/ai_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / "comfyui_512x512_aaaaaaaaaaaaaaaa.png"
    cached.write_bytes(b"x")
    try:
        fake = MagicMock()
        fake.test_connection.return_value = True
        gen = ComfyUIImageGenerator(client=fake)
        req = AIImageRequest(
            prompt="a cat", provider=AIProvider.COMFYUI, size=ImageSize.SQUARE_512,
        )
        # 用唯一 prompt 避免命中他人缓存
        from services.ai_image.base import AIImageRequest as R
        req.prompt = "e2e-unique-prompt-" + "x" * 8
        # 强制与缓存路径一致:直接复用文件名约定
        import hashlib
        h = hashlib.md5(req.prompt.encode()).hexdigest()[:12]
        cached_path = cache_dir / f"comfyui_512x512_{h}.png"
        cached_path.write_bytes(b"x")
        res = await gen.generate(req)
        assert res.success is True
        assert res.image_path == str(cached_path)
        assert not fake.submit.called
    finally:
        for p in [cached, cached_path]:
            if p.exists():
                p.unlink()


def test_estimate_cost_is_zero():
    fake = MagicMock()
    gen = ComfyUIImageGenerator(client=fake)
    req = AIImageRequest(prompt="x", provider=AIProvider.COMFYUI)
    assert gen.estimate_cost(req) == 0.0


def test_supported_models():
    fake = MagicMock()
    gen = ComfyUIImageGenerator(client=fake)
    assert "flux-dev" in gen.get_supported_models()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_comfyui_image_generator.py -v`
Expected: `ModuleNotFoundError` (comfyui_generator.py 不存在)

- [ ] **Step 3: 实现**

`services/ai_image/comfyui_generator.py`:
```python
"""ComfyUI 生图生成器 - 通过本地 ComfyUI HTTP API。"""
import logging
import time
from pathlib import Path
from typing import Optional

from services.comfyui import (
    ComfyUIClient,
    load_template,
    render_template,
    ComfyUIError,
)
from .base import AIGenerationService, AIImageRequest, AIImageResult

logger = logging.getLogger(__name__)

SIZE_W = {"1024x1024": 1024, "512x512": 512, "1792x1024": 1792,
          "1024x1792": 1024, "1080x1920": 1080, "1080x1080": 1080,
          "1920x1080": 1920}

SIZE_H = {"1024x1024": 1024, "512x512": 512, "1792x1024": 1024,
          "1024x1792": 1792, "1080x1920": 1920, "1080x1080": 1080,
          "1920x1080": 1080}


class ComfyUIImageGenerator(AIGenerationService):
    """本地 ComfyUI 生图。免费、无 API key。"""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8188",
        workflow_path: str = "workflows/image/flux_dev.json",
        poll_interval_sec: float = 2.0,
        timeout_sec: float = 600.0,
        api_key: str = "",  # AIGenerationService 要求;本地不需要
        base_url_parent: Optional[str] = None,  # 父类用 base_url,这里用同名避免冲突
        client: Optional[ComfyUIClient] = None,
    ):
        super().__init__(api_key=api_key or "local",
                         base_url=base_url_parent)  # 满足父类;真正 base_url 在 client
        self._workflow_path = Path(workflow_path)
        self._client = client or ComfyUIClient(
            base_url=base_url,
            poll_interval_sec=poll_interval_sec,
            timeout_sec=timeout_sec,
        )

    def _get_default_base_url(self) -> str:
        return "http://127.0.0.1:8188"

    def get_provider_name(self) -> str:
        return "comfyui"

    def get_supported_models(self) -> list[str]:
        return ["flux-dev"]

    def estimate_cost(self, request) -> float:
        return 0.0

    async def generate(self, request: AIImageRequest) -> AIImageResult:
        t0 = time.time()
        # 缓存命中
        cached = await self.get_cached(request)
        if cached is not None:
            return AIImageResult(
                success=True, image_path=str(cached),
                prompt=request.prompt, provider="comfyui",
                model="flux-dev", cost=0.0,
            )

        # 模板加载
        try:
            wf = load_template(self._workflow_path)
        except FileNotFoundError as e:
            logger.error(f"ComfyUI 工作流模板缺失: {e}")
            return AIImageResult(success=False, error=str(e), provider="comfyui")

        size_v = request.size.value
        w = SIZE_W.get(size_v, 1024)
        h = SIZE_H.get(size_v, 1024)
        rendered = render_template(
            wf, prompt=request.prompt, width=w, height=h,
            steps=getattr(request, "extra_params", {}).get("steps", 20),
        )

        try:
            prompt_id = self._client.submit(rendered)
            outputs = self._client.wait_for_completion(prompt_id)
            paths = self._client.download_outputs(outputs, self._cache_dir)
        except ComfyUIError as e:
            logger.warning(f"ComfyUI 生图失败: {e}")
            return AIImageResult(
                success=False, error=str(e), provider="comfyui",
            )

        if not paths:
            return AIImageResult(
                success=False, error="无产物", provider="comfyui",
            )

        return AIImageResult(
            success=True, image_path=str(paths[0]),
            prompt=request.prompt, provider="comfyui", model="flux-dev",
            generation_time=time.time() - t0, cost=0.0,
        )
```

注意:`__init__` 里 `base_url_parent` 这个名字是为了避免和 `base_url` 参数冲突。**但实际上** 父类 `AIGenerationService.__init__` 只存 `base_url`,而我们真正使用的是 `self._client.base_url`,所以父类的 `base_url` 是没用的死参数。这里把它当 stub 占位即可。

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_comfyui_image_generator.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add services/ai_image/comfyui_generator.py tests/test_comfyui_image_generator.py
git commit -m "feat(comfyui-image): generator with cache + workflow render"
```

---

## Task 9: ComfyUIVideoGenerator

**Files:**
- Create: `services/ai_video/comfyui_generator.py`
- Test: `tests/test_comfyui_video_generator.py`

**Interfaces:**
- Produces:
  ```python
  class ComfyUIVideoGenerator(AIVideoGenerationService):
      async def generate(self, request) -> AsyncGenerator[VideoGenerationProgress, None]
      def estimate_cost(self, request) -> float
      def get_supported_models(self) -> list[str]  # ["wan2.2-t2v"]
      async def cancel(self, task_id) -> bool: ...  # 简化:返回 False
      def get_status(self, task_id) -> Optional[VideoGenerationProgress]: ...
  ```

- [ ] **Step 1: 写失败测试**

`tests/test_comfyui_video_generator.py`:
```python
import asyncio
import pytest
from unittest.mock import MagicMock
from pathlib import Path
from services.ai_video.base import (
    VideoGenerationRequest, VideoProvider, VideoSize,
    VideoGenerationProgress, VideoTaskStatus,
)
from services.ai_video.comfyui_generator import ComfyUIVideoGenerator
from services.comfyui.client import WorkflowOutput


def _fake_client_ok():
    c = MagicMock()
    c.submit.return_value = "pid-1"
    c.wait_for_completion.return_value = [WorkflowOutput("v.mp4", "", "output")]
    c.download_outputs.return_value = [Path("/fake/v.mp4")]
    return c


@pytest.mark.asyncio
async def test_generate_yields_progress_and_succeeds():
    fake = _fake_client_ok()
    gen = ComfyUIVideoGenerator(client=fake, workflow_path="ignored")
    req = VideoGenerationRequest(
        prompt="a dog runs", provider=VideoProvider.COMFYUI,
        size=VideoSize.PORTRAIT_9_16, duration=5,
    )
    progresses = [p async for p in gen.generate(req)]
    # 至少一次 PENDING(可无)、最终 SUCCEEDED
    final = progresses[-1]
    assert final.status == VideoTaskStatus.SUCCEEDED
    assert final.video_path == "/fake/v.mp4"
    assert fake.submit.called
    assert fake.wait_for_completion.called


@pytest.mark.asyncio
async def test_generate_yields_failed_on_error():
    from services.comfyui.errors import ComfyUIExecutionError
    fake = MagicMock()
    fake.submit.return_value = "pid"
    fake.wait_for_completion.side_effect = ComfyUIExecutionError("bad")
    gen = ComfyUIVideoGenerator(client=fake, workflow_path="ignored")
    req = VideoGenerationRequest(
        prompt="x", provider=VideoProvider.COMFYUI,
    )
    progresses = [p async for p in gen.generate(req)]
    assert progresses[-1].status == VideoTaskStatus.FAILED
    assert "bad" in (progresses[-1].error or "")


def test_estimate_cost_zero():
    fake = MagicMock()
    gen = ComfyUIVideoGenerator(client=fake)
    req = VideoGenerationRequest(prompt="x", provider=VideoProvider.COMFYUI)
    assert gen.estimate_cost(req) == 0.0


def test_supported_models_contains_wan():
    fake = MagicMock()
    gen = ComfyUIVideoGenerator(client=fake)
    assert any("wan" in m for m in gen.get_supported_models())
```

- [ ] **Step 2: 跑测试确认失败**

Run: `pytest tests/test_comfyui_video_generator.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 实现**

`services/ai_video/comfyui_generator.py`:
```python
"""ComfyUI 生视频生成器。"""
import asyncio
import logging
import time
from pathlib import Path
from typing import AsyncGenerator, Optional

from services.comfyui import (
    ComfyUIClient,
    load_template,
    render_template,
    ComfyUIError,
)
from .base import (
    AIVideoGenerationService,
    VideoGenerationRequest,
    VideoGenerationResult,
    VideoGenerationProgress,
    VideoTaskStatus,
)

logger = logging.getLogger(__name__)

# 短边长映射(根据 size 比例,长边取 1280 像素)
SIZE_PRESETS = {
    "9:16": (720, 1280),
    "16:9": (1280, 720),
    "1:1": (1024, 1024),
}


class ComfyUIVideoGenerator(AIVideoGenerationService):
    """本地 ComfyUI 生视频。免费、单 GPU 串行。"""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8188",
        workflow_path: str = "workflows/video/wan22_t2v.json",
        poll_interval_sec: float = 5.0,
        timeout_sec: float = 1800.0,  # 视频更慢
        api_key: str = "",
        client: Optional[ComfyUIClient] = None,
    ):
        super().__init__(api_key=api_key or "local", base_url=base_url)
        self._workflow_path = Path(workflow_path)
        self._client = client or ComfyUIClient(
            base_url=base_url,
            poll_interval_sec=poll_interval_sec,
            timeout_sec=timeout_sec,
        )
        self._progress_map: dict[str, VideoGenerationProgress] = {}

    def _get_default_base_url(self) -> str:
        return "http://127.0.0.1:8188"

    def get_provider_name(self) -> str:
        return "comfyui"

    def get_supported_models(self) -> list[str]:
        return ["wan2.2-t2v"]

    def estimate_cost(self, request) -> float:
        return 0.0

    async def cancel(self, task_id: str) -> bool:
        """ComfyUI 不支持 cancel;返回 False 表示不支持。"""
        logger.info(f"ComfyUI 不支持取消任务 {task_id}")
        return False

    def get_status(self, task_id: str) -> Optional[VideoGenerationProgress]:
        return self._progress_map.get(task_id)

    async def generate(
        self, request: VideoGenerationRequest,
    ) -> AsyncGenerator[VideoGenerationProgress, None]:
        t0 = time.time()
        progress = VideoGenerationProgress(
            task_id="pending", status=VideoTaskStatus.PENDING,
            progress=0.0, created_time=t0,
        )
        self._progress_map[progress.task_id] = progress

        # 缓存命中
        cached = await self.get_cached(request)
        if cached is not None:
            yield VideoGenerationProgress(
                task_id="cached", status=VideoTaskStatus.SUCCEEDED,
                progress=1.0, video_path=str(cached),
            )
            return

        # 模板加载
        try:
            wf = load_template(self._workflow_path)
        except FileNotFoundError as e:
            logger.error(f"ComfyUI 视频工作流模板缺失: {e}")
            yield VideoGenerationProgress(
                task_id="missing-template",
                status=VideoTaskStatus.FAILED, error=str(e),
            )
            return

        w, h = SIZE_PRESETS.get(request.size.value, (1024, 1024))
        rendered = render_template(
            wf, prompt=request.prompt, width=w, height=h, steps=20,
        )

        # 提交
        try:
            prompt_id = self._client.submit(rendered)
        except ComfyUIError as e:
            yield VideoGenerationProgress(
                task_id="submit-failed",
                status=VideoTaskStatus.FAILED, error=str(e),
            )
            return

        progress.task_id = prompt_id
        progress.status = VideoTaskStatus.PROCESSING
        yield progress

        # 轮询期间由调用方异步等待;此处一次性等待后 yield 结果
        # (更精细的进度需开后台线程,本阶段 YAGNI)
        try:
            outputs = await asyncio.to_thread(
                self._client.wait_for_completion, prompt_id,
            )
        except ComfyUIError as e:
            yield VideoGenerationProgress(
                task_id=prompt_id,
                status=VideoTaskStatus.FAILED, error=str(e),
            )
            return

        try:
            paths = await asyncio.to_thread(
                self._client.download_outputs, outputs, self._cache_dir,
            )
        except ComfyUIError as e:
            yield VideoGenerationProgress(
                task_id=prompt_id,
                status=VideoTaskStatus.FAILED, error=str(e),
            )
            return

        if not paths:
            yield VideoGenerationProgress(
                task_id=prompt_id,
                status=VideoTaskStatus.FAILED, error="无产物",
            )
            return

        final = VideoGenerationProgress(
            task_id=prompt_id,
            status=VideoTaskStatus.SUCCEEDED,
            progress=1.0,
            video_path=str(paths[0]),
            updated_time=time.time(),
        )
        self._progress_map[prompt_id] = final
        yield final
```

- [ ] **Step 4: 跑测试确认通过**

Run: `pytest tests/test_comfyui_video_generator.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add services/ai_video/comfyui_generator.py tests/test_comfyui_video_generator.py
git commit -m "feat(comfyui-video): generator with progress yields"
```

---

## Task 10: 服务 __init__.py 导出新 generator

**Files:**
- Modify: `services/ai_image/__init__.py`
- Modify: `services/ai_video/__init__.py`

(把 Task 7 中"留到此处"的导出补上。)

- [ ] **Step 1: 更新 ai_image/__init__.py**

```python
"""AI 生图服务层"""
from .base import (
    AIGenerationService,
    AIImageRequest,
    AIImageResult,
    AIProvider,
    ImageSize,
    ImageStyle,
)
from .openai_generator import OpenAIImageGenerator
from .dashscope_generator import DashscopeImageGenerator
from .bailian_generator import BailianImageGenerator
from .comfyui_generator import ComfyUIImageGenerator  # E5

__all__ = [
    'AIGenerationService',
    'AIImageRequest',
    'AIImageResult',
    'AIProvider',
    'ImageSize',
    'ImageStyle',
    'OpenAIImageGenerator',
    'DashscopeImageGenerator',
    'BailianImageGenerator',
    'ComfyUIImageGenerator',
]
```

- [ ] **Step 2: 更新 ai_video/__init__.py**

```python
"""AI 生视频服务层"""
from .base import (
    AIVideoGenerationService,
    VideoGenerationRequest,
    VideoGenerationResult,
    VideoGenerationProgress,
    VideoProvider,
    VideoSize,
    VideoResolution,
    VideoTaskStatus,
)
from .dashscope_generator import DashScopeVideoGenerator
from .comfyui_generator import ComfyUIVideoGenerator  # E5

__all__ = [
    'AIVideoGenerationService',
    'VideoGenerationRequest',
    'VideoGenerationResult',
    'VideoGenerationProgress',
    'VideoProvider',
    'VideoSize',
    'VideoResolution',
    'VideoTaskStatus',
    'DashScopeVideoGenerator',
    'ComfyUIVideoGenerator',
]
```

- [ ] **Step 3: 验证 import 通**

```bash
python -c "
from services.ai_image import ComfyUIImageGenerator, AIProvider
from services.ai_video import ComfyUIVideoGenerator, VideoProvider
print('image:', ComfyUIImageGenerator.__name__, AIProvider.COMFYUI)
print('video:', ComfyUIVideoGenerator.__name__, VideoProvider.COMFYUI)
"
```
Expected: 两行输出,无 traceback。

- [ ] **Step 4: Commit**

```bash
git add services/ai_image/__init__.py services/ai_video/__init__.py
git commit -m "feat(services): export ComfyUI image and video generators"
```

---

## Task 11: MaterialFetchAgent — 按 config 选 provider

**Files:**
- Modify: `core/agents/material_fetch_agent.py`(lazy 属性块)

**Interfaces:**
- Produces:`_ai_generator` / `_ai_video_generator` 根据 `config["ai"]["image_provider"]` 选择 generator,失败时返回 None(沿用现状)

- [ ] **Step 1: 看现状**

读 `core/agents/material_fetch_agent.py:140-200`,确认 lazy 属性当前实现。

- [ ] **Step 2: 写失败测试**

`tests/test_comfyui_integration.py`(先放 agent 集成测试,但标记 skip 真实 ComfyUI):
```python
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


@pytest.mark.integration
def test_real_comfyui_image_end_to_end():
    """真实 ComfyUI 跑通(需本地服务 + GPU)。默认 skip。"""
    from services.comfyui import ComfyUIClient
    c = ComfyUIClient()
    if not c.test_connection():
        pytest.skip("本地 ComfyUI 不可达")
    from services.ai_image.comfyui_generator import ComfyUIImageGenerator
    from services.ai_image.base import AIImageRequest, AIProvider, ImageSize
    import asyncio

    gen = ComfyUIImageGenerator()
    req = AIImageRequest(
        prompt="a small red apple", provider=AIProvider.COMFYUI,
        size=ImageSize.SQUARE_512,
    )
    res = asyncio.run(gen.generate(req))
    assert res.success
    assert Path(res.image_path).exists()
```

(先创建文件,真实跑由用户在本地 GPU 触发。)

- [ ] **Step 3: 改造 material_fetch_agent.py**

定位现有的 `_ai_generator` / `_ai_video_generator` lazy 属性(约 145-190 行),把硬编码 `BailianImageGenerator` / `DashScopeVideoGenerator` 替换为按 config 选择。**关键改动**:

```python
from services.config import load_config

# 在 MaterialFetchAgent.__init__ 末尾或合适位置:
self._config = load_config("config.yaml")

# 把 ai_generator property 改为:
@property
def ai_generator(self):
    if self._ai_generator is not None:
        return self._ai_generator
    try:
        provider = self._config.get("ai", {}).get("image_provider", "bailian")
        if provider == "comfyui":
            from services.ai_image.comfyui_generator import ComfyUIImageGenerator
            self._ai_generator = ComfyUIImageGenerator()
        elif provider == "openai":
            from services.ai_image import OpenAIImageGenerator, AIProvider
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                return None
            self._ai_generator = OpenAIImageGenerator(api_key=api_key)
        else:  # bailian(默认,保持向后兼容)
            from services.ai_image import BailianImageGenerator, AIProvider
            api_key = os.getenv("BAILIAN_API_KEY", "")
            if not api_key:
                return None
            self._ai_generator = BailianImageGenerator(api_key=api_key)
    except Exception as e:
        logger.warning(f"AI 生图 provider {provider} 初始化失败: {e}")
        self._ai_generator = None
    return self._ai_generator
```

`ai_video_generator` 同模式(provider: `comfyui` → `dashscope` → 默认 `dashscope`)。

**注意**:`os` 需要 import(若已 import 就不动)。

- [ ] **Step 4: 单元测试 config-driven 选择**

追加到 `tests/test_comfyui_image_generator.py`(新文件也行,放这里紧凑):
```python
def test_agent_uses_comfyui_when_configured(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("ai:\n  image_provider: comfyui\n")
    monkeypatch.chdir(tmp_path)
    # 清空 agent 的 lazy 缓存
    from core.agents.material_fetch_agent import MaterialFetchAgent
    agent = MaterialFetchAgent.__new__(MaterialFetchAgent)
    agent._ai_generator = None
    agent._config = __import__("services.config", fromlist=["load_config"]).load_config("config.yaml")
    gen = agent.ai_generator
    assert gen.__class__.__name__ == "ComfyUIImageGenerator"
```

(若 MaterialFetchAgent 构造副作用多,可仅测 `_select_image_provider` 之类的纯函数,根据实际代码调整。)

- [ ] **Step 5: 跑相关测试**

```bash
pytest tests/test_comfyui_image_generator.py tests/test_comfyui_video_generator.py -q
pytest tests/ -q -k "ai_image or ai_video or material"  # 现有相关
```
Expected: 全 PASS(包括既有的 `test_ai_image_service.py`)

- [ ] **Step 6: Commit**

```bash
git add core/agents/material_fetch_agent.py tests/test_comfyui_integration.py tests/test_comfyui_image_generator.py
git commit -m "feat(agent): MaterialFetchAgent reads provider from config (comfyui|bailian|...)"
```

---

## Task 12: config.yaml 模板 + 文档更新

**Files:**
- Modify: `config.yaml`(如不存在则创建)
- Modify: `docs/27-E5-comfyui.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: 检查/创建 config.yaml**

若项目根已有 `config.yaml`,**在末尾追加**(不覆盖现有键):
```yaml
# ===== E5: AI provider & ComfyUI =====
ai:
  image_provider: comfyui   # comfyui | bailian | openai
  video_provider: comfyui   # comfyui | dashscope | kling

comfyui:
  base_url: "http://127.0.0.1:8188"
  poll_interval_sec: 2
  timeout_sec: 600
  workflows:
    image: "workflows/image/flux_dev.json"
    video_t2v: "workflows/video/wan22_t2v.json"
    video_i2v: "workflows/video/wan22_i2v.json"
```

若不存在,新建文件(内容同上)。

- [ ] **Step 2: 验证 config 可读**

```bash
python -c "
from services.config import load_config
cfg = load_config('config.yaml')
print('ai:', cfg.get('ai'))
print('comfyui.base_url:', cfg.get('comfyui', {}).get('base_url'))
"
```
Expected: 打印 `comfyui | http://127.0.0.1:8188` 等

- [ ] **Step 3: 改写 docs/27-E5-comfyui.md**

替换原内容,新文档要点:
- 概述(一段)
- 前置条件(本地 ComfyUI、GPU、模型清单)
- 配置示例(引用 config.yaml 片段)
- 工作流模板列表
- 故障排查(连接失败、模板缺失、超时)
- 指向 spec 的链接

- [ ] **Step 4: 更新 CLAUDE.md**

在 §"E 阶段概览"里把 E5 状态从 ⏳ 改为 ✅,并加一行概述;在 §"E 系列工作原则"下加"已交付能力"列表(ComfyUI 客户端 + 2 generator + 3 工作流模板)。

- [ ] **Step 5: Commit**

```bash
git add config.yaml docs/27-E5-comfyui.md CLAUDE.md
git commit -m "docs(e5): mark E5 complete in CLAUDE.md, rewrite design doc with ops notes"
```

---

## Task 13: 完整回归 + devlog

**Files:**
- Create/Modify: `devlog/daily/2026-08-XX.md`(对应日期)

- [ ] **Step 1: 跑完整离线测试套**

```bash
pytest tests/ -q --ignore=tests/integration
```
Expected: 现有 N 项 + 新增 ≥12 项全 PASS;N 数字不重要,目标是**全绿**。

- [ ] **Step 2: 跑一次集成测试(若本地 ComfyUI 可达)**

```bash
pytest tests/test_comfyui_integration.py -v --run-integration
```
若不可达:skip(记录到 devlog)。

- [ ] **Step 3: 跑现有 ai_image 服务测试(回归守门)**

```bash
pytest tests/test_ai_image_service.py -q
```
Expected: 全 PASS(确认未破坏既有云端路径)。

- [ ] **Step 4: 写 E5 阶段 devlog**

新建或更新 `devlog/daily/2026-08-XX.md`:
- ✅ 已完成事项(13 个任务概况)
- 🧪 测试统计(新增 X 个,总 Y 个全绿)
- 🐛 踩坑与设计取舍(简记)
- 📈 E5 价值描述(本地免费 + provider 可切换)

- [ ] **Step 5: 写 devlog/phase-E5-summary.md**

模板参照 `devlog/phase-E0-summary.md`,重点:实现细节、API 兼容性、用户体验、未来扩展点。

- [ ] **Step 6: 最终 commit + 推送(若用户授权)**

```bash
git add devlog/
git commit -m "devlog(e5): E5 phase summary and daily log"
git push origin main   # 仅在用户明确同意时执行
```

---

## 自审报告

### Spec 覆盖核对

| Spec 章节 | 实施任务 |
|-----------|---------|
| §1 范围 | Task 1-12 全覆盖;明确排除在 §11 |
| §2 架构 | Task 4-11 实施;§2 降级链路 = Task 11 复用现有 lazy |
| §3 文件清单 | Task 1-12 全部覆盖新增/修改/不改 |
| §4 核心接口 | Task 4-5(client) + Task 8(image gen) + Task 9(video gen) |
| §5 错误处理 | Task 2(异常类) + Task 5(轮询/下载异常) + Task 8-9(generator 捕获) + Task 11(agent lazy 降级) |
| §6 模板插值约定 | Task 3(template.py + 转义测试) + Task 6(具体模板 JSON) |
| §7 配置 | Task 1(config loader) + Task 12(config.yaml) |
| §8 测试策略 | Task 1/3/4/5/8/9/11/13 全部含测试;集成测试在 Task 11/13 |
| §9 风险与缓解 | Task 6(模板版本兼容性文档化) + Task 11(失败降级) + Task 13(回归) |
| §10 实施节奏 | 4 周切分;本计划不强制周界,允许一次性推完 |
| §11 排除项 | 全文不出现 TTS、RunningHub、WebSocket、新依赖 |

### 占位符扫描

- ✅ 无 TBD / TODO / "fill in"
- ✅ 无 "add appropriate handling" 类无内容指令
- ✅ 每个代码块都是完整可粘贴代码
- ✅ 无 "类似 Task N" 引用(每个代码块自包含)

### 类型/接口一致性核对

| 名称 | 定义位置 | 使用位置 |
|------|---------|---------|
| `ComfyUIClient(base_url, poll_interval_sec, timeout_sec, session)` | Task 4 Step 3 | Task 8/9/11 全部用同名参数 |
| `ComfyUIClient.test_connection() -> bool` | Task 4 | Task 11 lazy 不直接调用,但 Task 8 `get_cached` 流程兼容 |
| `ComfyUIClient.submit(workflow) -> str` | Task 4 | Task 8 image gen + Task 9 video gen |
| `ComfyUIClient.wait_for_completion(prompt_id) -> list[WorkflowOutput]` | Task 5 | Task 8/9 |
| `ComfyUIClient.download_outputs(outputs, save_dir) -> list[Path]` | Task 5 | Task 8/9 |
| `WorkflowOutput(filename, subfolder, type)` | Task 4 dataclass | Task 5/8/9 测试中都用 |
| `load_template(path) -> dict` | Task 3 | Task 8/9 |
| `render_template(workflow, *, prompt, width, height, steps, seed) -> dict` | Task 3 | Task 8/9 |
| `ComfyUIError / ConnectionError / ExecutionError / TimeoutError` | Task 2 | Task 5/8/9 全部用 |
| `AIProvider.COMFYUI` | Task 7 | Task 8 测试 + Task 11 agent |
| `VideoProvider.COMFYUI` | Task 7 | Task 9 测试 + Task 11 agent |
| `ComfyUIImageGenerator(client, workflow_path, base_url, ...)` | Task 8 | Task 10 导出 + Task 11 agent 引用 |
| `ComfyUIVideoGenerator(client, workflow_path, ...)` | Task 9 | Task 10 导出 + Task 11 agent 引用 |

### 发现并修复的问题

1. **Task 7 流程中错误**:`__init__.py` 在 `comfyui_generator.py` 不存在时导入会失败。已在 Task 7 Step 末尾**显式回退** __init__.py 改动,推迟到 Task 10。计划里留有"修订后步骤"明确说明。
2. **Task 8 `__init__` 父类兼容**:`AIGenerationService.__init__` 强制接 `api_key` 和 `base_url`,我们真正用的是 `self._client`。计划里用 `base_url_parent` 占位 + super().__init__(...) 调用满足父类。
3. **Task 11 测试方式**:MaterialFetchAgent 实际构造可能复杂(`__init__` 副作用)。计划里给出"如构造重则测纯函数"的备选,**不**强加具体 mock 结构,留给实施时根据现状调整。
4. **集成测试 Task 13**:默认 skip,要求 `--run-integration` 才跑,与 spec §8 一致。

### 范围聚焦

整个计划 13 个任务产出 13 次 commit + 1 次 devlog commit。每次 commit 单独可回滚、可 review。最大单任务是 Task 9(视频 generator,~140 行实现),其余都在 50-100 行规模。

---

*计划完成。下一步:用户选择执行模式(subagent-driven 或 inline)。*