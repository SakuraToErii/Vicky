"""Tests for the shared environment loader."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
sys.path.insert(0, str(LIB_DIR))

import env


def test_env_loader_whitelists_project_keys(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "SEMANTIC_SCHOLAR_API_KEY=project-key\n"
        "UNRELATED_SECRET=secret\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("SEMANTIC_SCHOLAR_API_KEY", raising=False)
    monkeypatch.delenv("UNRELATED_SECRET", raising=False)

    env.load(env_path)

    assert env.os.environ["SEMANTIC_SCHOLAR_API_KEY"] == "project-key"
    assert "UNRELATED_SECRET" not in env.os.environ


def test_env_loader_keeps_existing_values(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("SEMANTIC_SCHOLAR_API_KEY=project-key\n", encoding="utf-8")
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "shell-key")

    env.load(env_path)

    assert env.os.environ["SEMANTIC_SCHOLAR_API_KEY"] == "shell-key"


def test_global_env_requires_explicit_opt_in(tmp_path, monkeypatch):
    project_env = tmp_path / "project.env"
    project_env.write_text("", encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir()
    (home / ".env").write_text("SEMANTIC_SCHOLAR_API_KEY=global-key\n", encoding="utf-8")

    monkeypatch.delenv("SEMANTIC_SCHOLAR_API_KEY", raising=False)
    monkeypatch.setattr(env, "_LOADED", False)
    monkeypatch.setattr(env, "PROJECT_ENV_PATH", project_env)
    monkeypatch.setattr(env.pathlib.Path, "home", staticmethod(lambda: home))

    env.load_once()
    assert "SEMANTIC_SCHOLAR_API_KEY" not in env.os.environ

    monkeypatch.setattr(env, "_LOADED", False)
    monkeypatch.setenv(env.GLOBAL_ENV_OPT_IN, "1")
    env.load_once()
    assert env.os.environ["SEMANTIC_SCHOLAR_API_KEY"] == "global-key"


def test_settings_example_uses_scoped_shell_permissions():
    payload = json.loads((PROJECT_ROOT / ".config" / "settings.local.json.example").read_text(encoding="utf-8"))
    allowed = payload["permissions"]["allow"]
    assert "Bash(*)" not in allowed
    assert "WebFetch(*)" not in allowed
    assert "MCP(*)" not in allowed
