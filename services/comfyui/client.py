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
            r = self.session.request(
                "GET",
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
            r = self.session.request(
                "POST",
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
