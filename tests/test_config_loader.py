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
