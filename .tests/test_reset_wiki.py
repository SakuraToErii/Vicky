"""Tests for reset skill tool."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
SCRIPTS_DIR = PROJECT_ROOT / ".codex" / "skills" / "reset" / "scripts"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))
import reset_wiki as rw
import vicky.schema as schema_mod


@pytest.fixture
def project(tmp_path):
    wiki = tmp_path / "wiki"
    for name in rw.INDEXED_DIRS:
        (wiki / name).mkdir(parents=True)
        (wiki / name / ".gitkeep").touch()
    for name in schema_mod.SUPPORT_DIRS:
        (wiki / name).mkdir(parents=True)
    for relative_path, content in schema_mod.BASE_FILE_TEMPLATES.items():
        (wiki / relative_path).write_text(content + "\n# local edit\n", encoding="utf-8")
    (wiki / "sources" / "paper-a.md").write_text("---\ntitle: Paper A\n---\n", encoding="utf-8")
    (wiki / "outputs" / "comparison.md").write_text("# comparison\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Vicky Log\n\n## [2026-04-27] something\n", encoding="utf-8")

    raw = tmp_path / "raw"
    for name in rw.RAW_DIRS:
        (raw / name).mkdir(parents=True)
        (raw / name / ".gitkeep").touch()
    (raw / "papers" / "paper-a.tex").write_text("\\title{Paper A}\n", encoding="utf-8")
    (raw / "inbox" / "scratch.md").write_text("scratch", encoding="utf-8")
    return tmp_path


def test_plan_lists_wiki_content(project):
    payload = rw.plan(project, ["wiki"])
    deletes = set(payload["delete_files"])
    assert "wiki/sources/paper-a.md" in deletes
    assert "wiki/outputs/comparison.md" in deletes
    assert "wiki/log.md" in deletes
    for relative_path in schema_mod.BASE_FILE_TEMPLATES:
        assert f"wiki/{relative_path}" in deletes
        assert f"wiki/{relative_path}" in payload["reset_files"]
    assert "wiki/log.md" in payload["reset_files"]


def test_execute_wiki_removes_pages_and_keeps_gitkeep(project):
    result = rw.execute(project, ["wiki"])
    assert not (project / "wiki" / "sources" / "paper-a.md").exists()
    assert not (project / "wiki" / "outputs" / "comparison.md").exists()
    assert (project / "wiki" / "sources" / ".gitkeep").exists()
    assert not (project / "wiki" / "index.md").exists()
    assert (project / "wiki" / "log.md").read_text(encoding="utf-8") == rw.LOG_TEMPLATE
    for relative_path, content in schema_mod.BASE_FILE_TEMPLATES.items():
        assert (project / "wiki" / relative_path).read_text(encoding="utf-8") == content
    assert result["reset_files"] == 1 + len(schema_mod.BASE_FILE_TEMPLATES)


def test_execute_raw_removes_inbox_and_papers(project):
    rw.execute(project, ["raw"])
    assert not (project / "raw" / "papers" / "paper-a.tex").exists()
    assert not (project / "raw" / "inbox" / "scratch.md").exists()
    assert (project / "raw" / "inbox" / ".gitkeep").exists()


def test_execute_log_resets_template(project):
    rw.execute(project, ["log"])
    assert (project / "wiki" / "log.md").read_text(encoding="utf-8") == "# Vicky Log\n\n"


def test_cli_dry_run(project):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "reset_wiki.py"), "--scope", "wiki", "--project-root", str(project)],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "plan"
    assert (project / "wiki" / "sources" / "paper-a.md").exists()
