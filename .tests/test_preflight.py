"""Tests for dependency preflight helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vicky import preflight
from vicky.frontmatter import parse_frontmatter


def test_missing_commands_reports_missing_binary(monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda command: None if command == "obsidian" else f"/usr/bin/{command}")
    assert preflight.missing_commands(["codex", "obsidian", "rg"]) == ["obsidian"]


def test_missing_modules_reports_missing_import(monkeypatch):
    real_find_spec = preflight.importlib.util.find_spec

    def fake_find_spec(name: str):
        if name == "yaml":
            return None
        return real_find_spec(name)

    monkeypatch.setattr(preflight.importlib.util, "find_spec", fake_find_spec)
    assert preflight.missing_modules(["json", "yaml"]) == ["yaml"]


def test_frontmatter_dates_stay_json_serializable():
    frontmatter = parse_frontmatter("---\ndate_added: 2026-04-28\n---\n")
    assert frontmatter["date_added"] == "2026-04-28"
    json.dumps(frontmatter, ensure_ascii=False)
