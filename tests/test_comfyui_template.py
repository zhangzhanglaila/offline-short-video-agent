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
