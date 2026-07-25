"""ComfyUI 服务:本地 ComfyUI HTTP 客户端 + 工作流模板加载。"""
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


def __getattr__(name):
    """PEP 562: lazy import of ComfyUIClient/WorkflowOutput from .client.

    Delays loading of services/comfyui/client.py until first attribute access,
    so .errors and .template can be imported before .client exists.
    """
    if name in ("ComfyUIClient", "WorkflowOutput"):
        from . import client as _client
        return getattr(_client, name)
    raise AttributeError(f"module 'services.comfyui' has no attribute {name!r}")
