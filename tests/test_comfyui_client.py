import pytest
import requests
from unittest.mock import MagicMock
from services.comfyui import (
    ComfyUIClient,
    ComfyUIConnectionError,
    WorkflowOutput,
)


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
