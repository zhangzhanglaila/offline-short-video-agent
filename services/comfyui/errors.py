"""ComfyUI 相关异常。"""


class ComfyUIError(Exception):
    """ComfyUI 调用失败的基类。"""


class ComfyUIConnectionError(ComfyUIError):
    """服务不可达 / 连接拒绝。"""


class ComfyUIExecutionError(ComfyUIError):
    """工作流执行报错或无 outputs。"""


class ComfyUITimeoutError(ComfyUIError):
    """轮询超过 timeout_sec。"""