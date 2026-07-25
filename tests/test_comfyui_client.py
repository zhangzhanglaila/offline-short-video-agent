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
